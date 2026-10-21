"""Independent boundary regressions for bounded Phase 1 investment operations.

Uses actual detached-input CLI contracts. Expected results below are handwritten,
not loaded from golden outputs. This suite does not establish source truth or acceptance.
"""
import copy,json,subprocess,sys,tempfile,unittest
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'skills/asset-management'
INPUTS={'composite-account-membership-checker':'membership_input.json','holdings-transaction-normalizer':'source_bundle.json','investment-data-quality-exception-detector':'feed_snapshot.json','investment-source-ingester':'source_manifest.json','investment-vendor-feed-reconciler':'feed_reconciliation_example.json','nav-preparation-tie-out':'tie_out_example.json','position-cash-reconciliation-assistant':'reconciliation_example.json','security-master-enricher':'enrichment_example.json','valuation-exception-packet':'prices_example.json','credit-terms-covenant-extractor':'extraction_request.json'}

from asset_management_test_support import package, script as script_path

def fixture(name):return json.loads((package(name)/'evals/files'/INPUTS[name]).read_text())

def cli(name,script,doc,args=()):
    return subprocess.run([sys.executable,'-B',str(script_path(name, script)),*args],input=json.dumps(doc),text=True,capture_output=True,cwd=package(name))

def calculate(name,doc):
    r=cli(name,'calculate_or_transform.py',doc)
    if r.returncode:raise AssertionError(r.stderr+r.stdout)
    return json.loads(r.stdout)

class OperationsPhase1(unittest.TestCase):
    def test_original_binding_and_tamper_all_packages(self):
        for name in INPUTS:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                doc=fixture(name);out=calculate(name,doc)
                self.assertNotIn('source_input',out)
                source=Path(tmp)/'original.json';source.write_text(json.dumps(doc))
                r=cli(name,'validate_output.py',out,['--input',str(source)])
                self.assertEqual(r.returncode,0,r.stderr+r.stdout)
                tampered=copy.deepcopy(out);tampered['unsupported_decision']='approved'
                self.assertNotEqual(cli(name,'validate_output.py',tampered,['--input',str(source)]).returncode,0)
                self.assertNotEqual(cli(name,'validate_output.py',out).returncode,0)
                changed=copy.deepcopy(doc);changed['review_note']='different retained original';source.write_text(json.dumps(changed))
                self.assertNotEqual(cli(name,'validate_output.py',out,['--input',str(source)]).returncode,0)

    def position_doc(self,internal='1.000000001',external='1'):
        def row(side,value):return {'record_id':side,'match_key':'A:XYZ','account':'A','source_system':'custodian' if side=='e' else 'ibor','record_type':'position','security_id':'XYZ','source_ref':side,'date':'2026-06-30','currency':'USD','quantity_unit':'shares','position_basis':'settled','quantity':value}
        return {'entity':'F','as_of':'2026-06-30','config_version':'reviewed-1','base_currency':'USD','internal_records':[row('i',internal)],'external_records':[row('e',external)]}

    def test_fractional_quantity_and_neutral_alternatives(self):
        out=calculate('position-cash-reconciliation-assistant',self.position_doc())
        b=out['breaks'][0];self.assertEqual(Decimal(b['break_amount']),Decimal('0.000000001'))
        self.assertIsNone(b['proposed_item']['selected_alternative']);self.assertIsNone(b['proposed_item']['adjustment_amount'])
        self.assertEqual([x['side'] for x in b['proposed_item']['alternatives']],['internal','external',None])
        self.assertNotIn('corrected_internal_total',out['tie_out']['groups'][0])

    def test_thirty_digit_reconciliation_and_nav_preserve_exact_amounts(self):
        value='1000000000000.00000000000000001'
        doc=self.position_doc(value,'1000000000000.00000000000000000')
        out=calculate('position-cash-reconciliation-assistant',doc)
        self.assertEqual(out['breaks'][0]['break_amount'],'0.00000000000000001')
        self.assertEqual(out['tie_out']['groups'][0]['internal_total'],value)
        nav=self.nav_doc();nav['lines'][0]['value']=value;nav['lines'][1]['value']='0'
        out=calculate('nav-preparation-tie-out',nav)
        self.assertEqual(out['tie_out']['control_totals'][0]['difference'],value)
        self.assertEqual(out['breaks'][0]['impact'],value)

    def test_exact_fx_product_and_process_context_isolation(self):
        doc=self.position_doc('1','1')
        for row in doc['internal_records']+doc['external_records']:
            row.update(record_type='cash',currency='EUR',amount='1')
        doc['internal_records'][0]['amount']='1.000000000000000000000000000001'
        doc['config']={'cash_tolerance':'0','fx_rates':{'EUR':'1.000000000000000000000000000001'}}
        out=calculate('position-cash-reconciliation-assistant',doc)
        self.assertEqual(out['breaks'][0]['base_impact'],'0.'+'0'*29+'1'+'0'*29+'1')
        for name,request in [('position-cash-reconciliation-assistant',doc),('nav-preparation-tie-out',self.nav_doc())]:
            code=('import decimal,json,sys; from calculate_or_transform import compute; '
                  'decimal.getcontext().prec=3; before=str(decimal.getcontext()); '
                  'compute(json.load(sys.stdin)); assert str(decimal.getcontext())==before; print("context unchanged")')
            result=subprocess.run([sys.executable,'-B','-c',code],cwd=script_path(name,'calculate_or_transform.py').parent,input=json.dumps(request),text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr+result.stdout)

    def test_unsupported_precision_and_magnitude_fail_closed(self):
        for value in ['1.'+'1'*38,'1e39','1e-39','0e-39']:
            with self.subTest(value=value):
                recon=self.position_doc(value,'0');nav=self.nav_doc();nav['lines'][0]['value']=value
                for name,doc in [('position-cash-reconciliation-assistant',recon),('nav-preparation-tie-out',nav)]:
                    result=cli(name,'calculate_or_transform.py',doc)
                    self.assertNotEqual(result.returncode,0)
                    self.assertIn('supported precision/magnitude',result.stderr)
                    self.assertNotEqual(cli(name,'validate_input.py',doc).returncode,0)
        recon=self.position_doc('1','1');recon['config']={'fx_rates':{'EUR':'1e39'}}
        self.assertNotEqual(cli('position-cash-reconciliation-assistant','calculate_or_transform.py',recon).returncode,0)
        nav=self.nav_doc();nav['config']={'materiality':{'cash':'1e39'}}
        self.assertNotEqual(cli('nav-preparation-tie-out','calculate_or_transform.py',nav).returncode,0)

    def test_lots_require_explicit_aggregation_not_duplicate(self):
        doc=self.position_doc('2','5');extra=copy.deepcopy(doc['internal_records'][0]);extra.update(record_id='lot2',quantity='3');doc['internal_records'].append(extra)
        out=calculate('position-cash-reconciliation-assistant',doc)
        self.assertEqual(out['breaks'][0]['type'],'not_comparable')
        doc['config']={'aggregation_mode':'sum'};out=calculate('position-cash-reconciliation-assistant',doc)
        self.assertEqual(out['breaks'],[]);self.assertEqual(Decimal(out['tie_out']['groups'][0]['internal_total']),5)

    def test_basis_mismatch_and_missing_fx_remain_unknown(self):
        doc=self.position_doc();doc['external_records'][0]['position_basis']='trade-date'
        out=calculate('position-cash-reconciliation-assistant',doc);self.assertIsNone(out['breaks'][0]['break_amount'])
        for row in doc['internal_records']+doc['external_records']:row.update(record_type='cash',currency='EUR',position_basis='settled',amount='7')
        doc['external_records'][0]['amount']='2';out=calculate('position-cash-reconciliation-assistant',doc)
        self.assertIsNone(out['breaks'][0]['material']);self.assertEqual(out['summary']['unknown_materiality_breaks'],1)

    def test_future_settlement_does_not_prove_cause(self):
        doc=self.position_doc('10','0');doc['internal_records'][0]['settle_date']='2026-07-01'
        self.assertEqual(calculate('position-cash-reconciliation-assistant',doc)['breaks'][0]['type'],'quantity_break')
        for row in doc['internal_records']+doc['external_records']:row.update(settle_date='2026-07-01',settlement_evidence_ref='reviewed-trade-1')
        self.assertEqual(calculate('position-cash-reconciliation-assistant',doc)['breaks'][0]['type'],'pending_settlement')

    def vendor_doc(self):
        row={'instrument_id':'X','domain':'price','field':'price','as_of':'2026-06-20','source_ref':'r','currency':'USD','unit':'per_share','value':100}
        return {'entity':'F','as_of':'2026-06-30','config_version':'reviewed-1','internal_source':'i','vendor_source':'v','internal_observations':[row],'vendor_observations':[{**row,'source_ref':'v','value':102}]}

    def test_vendor_stale_and_value_are_independent_cell_count(self):
        out=calculate('investment-vendor-feed-reconciler',self.vendor_doc())
        self.assertEqual({b['type'] for b in out['breaks']},{'stale_as_of','value_mismatch'})
        self.assertEqual(out['tie_out']['break_cells'],1);self.assertEqual(out['summary']['total_breaks'],2)

    def test_vendor_units_currency_future_and_duplicate(self):
        n='investment-vendor-feed-reconciler'
        for key,val in [('currency','EUR'),('unit','per_100'),('as_of','2026-07-01')]:
            doc=self.vendor_doc();doc['vendor_observations'][0][key]=val
            out=calculate(n,doc);self.assertIn('not_comparable',{b['type'] for b in out['breaks']})
            self.assertNotIn('value_mismatch',{b['type'] for b in out['breaks']})
        doc=self.vendor_doc();doc['internal_observations']*=2;self.assertNotEqual(cli(n,'calculate_or_transform.py',doc).returncode,0)

    def test_dq_missing_and_future_prices(self):
        n='investment-data-quality-exception-detector';doc={'portfolio_id':'F','as_of':'2026-06-30','config_version':'v1','instruments':[{'instrument_key':'A','asset_class':'equity','source_ref':'r','held':True},{'instrument_key':'B','asset_class':'equity','source_ref':'r2','held':True}], 'prices':[{'instrument_key':'B','price':100,'prev_price':1,'price_asof':'2026-07-01'}]}
        out=calculate(n,doc);types={e['type'] for e in out['exceptions']}
        self.assertIn('missing_price',types);self.assertIn('temporal_invalid',types);self.assertNotIn('implausible_move',types)

    def test_dq_price_move_requires_comparable_dated_prior(self):
        n='investment-data-quality-exception-detector';doc=fixture(n)
        for p in doc['prices']:p.pop('comparison_basis_reviewed',None)
        out=calculate(n,doc);self.assertNotIn('implausible_move',{x['type'] for x in out['exceptions']})
        self.assertTrue(any(x['check']=='implausible_move' for x in out['not_evaluable']))

    def test_refdata_latest_future_invalid_and_duplicate_identity(self):
        n='security-master-enricher';doc={'entity':'F','as_of':'2026-06-30','config_version':'v','source_hierarchy':['a'],'securities':[{'security_key':'S','attributes':[{'field':'rating','value':'B','source':'a','as_of':'2026-06-01'},{'field':'rating','value':'A','source':'a','as_of':'2026-06-29'},{'field':'rating','value':'AAA','source':'a','as_of':'2026-07-01'},{'field':'currency','value':'USD','source':'a','as_of':'invalid'}]}]}
        out=calculate(n,doc);ratings=[p for p in out['enrichment_proposals'] if p['field']=='rating']
        self.assertEqual(ratings[0]['proposed_value'],'A');self.assertTrue(all(p['requires_steward_review'] for p in out['enrichment_proposals']))
        self.assertEqual(sum(c['type']=='invalid_observation_date' for c in out['conflict_queue']),2)
        doc['securities']*=2;self.assertNotEqual(cli(n,'calculate_or_transform.py',doc).returncode,0)

    def test_refdata_same_source_same_date_conflict_preserved(self):
        n='security-master-enricher';doc=fixture(n);a=doc['securities'][0]['attributes'][0];doc['securities'][0]['attributes'].append({**a,'value':'conflicting-same-revision'})
        out=calculate(n,doc);self.assertTrue(any(c['type']=='attribute_conflict' and c['field']==a['field'] for c in out['conflict_queue']))

    def test_model_only_price_is_not_missing_or_automatically_level3(self):
        n='valuation-exception-packet';doc={'as_of':'2026-06-30','book':'F','config_version':'v','instruments':[{'instrument_id':'PRIVATE','asset_class':'private_placement','currency':'USD','unit':'per_unit','source_ref':'r','candidate_prices':[{'source_id':'m','source_type':'model_price','price':100,'as_of':'2026-06-30','evidence_kind':'estimate','method':'DCF','method_approved':True,'currency':'USD','unit':'per_unit'}]}]}
        out=calculate(n,doc)['exceptions'][0];self.assertEqual(out['disposition'],'no-exception-detected');self.assertIsNone(out['candidate_prices'][0]['fair_value_level'])
        doc['instruments'][0]['candidate_prices'][0]['method_approved']=False
        self.assertEqual(calculate(n,doc)['exceptions'][0]['disposition'],'needs-data')

    def test_pricing_mixed_dates_no_false_dispersion(self):
        n='valuation-exception-packet';doc=fixture(n);ins=doc['instruments'][0];ins['open_challenge']=False;ins.pop('prior_price',None)
        ins['candidate_prices']=[{'source_id':'a','source_type':'trade_print','price':100,'as_of':'2026-06-29','evidence_kind':'observation','currency':'USD','unit':'price_per_unit'},{'source_id':'b','source_type':'trade_print','price':200,'as_of':'2026-06-30','evidence_kind':'observation','currency':'USD','unit':'price_per_unit'}];doc['instruments']=[ins]
        self.assertIsNone(calculate(n,doc)['exceptions'][0]['metrics']['max_source_dispersion_pct'])

    def test_composite_termination_full_period_and_calendar_lag(self):
        n='composite-account-membership-checker';doc=fixture(n);p=doc['portfolios'][0];doc['portfolios']=[p];p['termination_date']='2026-06-20'
        self.assertEqual(calculate(n,doc)['exceptions'][0]['exception_type'],'stale_inclusion')
        doc['as_of']='2026-02-28';p['termination_date']=None;p['under_mgmt_date']='2026-01-31';p['assigned_composite_ids']=[]
        self.assertEqual(calculate(n,doc)['exceptions'][0]['exception_type'],'missing_inclusion')
        doc['ruleset_effective_date']='2026-03-01';self.assertNotEqual(cli(n,'calculate_or_transform.py',doc).returncode,0)

    def test_credit_negation_draft_amendment_and_grower(self):
        n='credit-terms-covenant-extractor';doc=fixture(n);doc['candidates']=[{'field':'collateral','raw_value':'No collateral or lien is granted','page':1,'locator':'s1'},{'field':'basket','raw_value':'Greater of $10 million and 20% of EBITDA','page':2,'locator':'s2'}]
        self.assertEqual(calculate(n,doc)['coverage']['needs_review'],2)
        for field,val in [('doc_version','draft'),('is_amendment',True)]:
            d=fixture(n);d[field]=val;out=calculate(n,d);self.assertEqual(out['coverage']['extracted'],0)

    def test_normalizer_ruleset_source_hash_precision_and_basis(self):
        n='holdings-transaction-normalizer';doc={'bundle_id':'B','as_of':'2026-06-30','ruleset_version':'canon-ruleset-2026.07','records':[{'source_system':'custodian','source_record_id':'r','source_as_of':'2026-06-30','record_type':'position','payload':{'acct':'A','sec':'S','qty':'1.000000000001','ccy':'USD'}}]}
        out=calculate(n,doc);c=out['canonical_records'][0];self.assertEqual(c['canonical']['quantity'],'1.000000000001');self.assertIsNone(c['canonical']['position_basis'])
        doc['bundle_id']='C';self.assertEqual(calculate(n,doc)['canonical_records'][0]['lineage']['source_hash'],c['lineage']['source_hash'])
        doc['ruleset_version']='uninstalled-v99';self.assertNotEqual(cli(n,'calculate_or_transform.py',doc).returncode,0)

    def test_source_permissions_are_declared_not_authenticated(self):
        n='investment-source-ingester';doc=fixture(n);out=calculate(n,doc);self.assertTrue(all(x['permission_assurance']=='supplied_not_authenticated' for x in out['index']));self.assertTrue(all(x['content_fetched'] is False for x in out['index']))
        doc['sources']=[doc['sources'][0]];doc['sources'][0]['entitlement'].pop('reviewed_by',None)
        self.assertEqual(calculate(n,doc)['rejected'][0]['reject_reason'],'permission_unknown')

    def nav_doc(self):
        def row(side,value):return {'line_id':side,'component':'cash','key':'cash','source':'book' if side=='b' else 'custodian','value':value,'currency':'USD','unit':'currency_amount','as_of':'2026-06-30','source_ref':side}
        return {'fund':'F','as_of':'2026-06-30','config_version':'v','base_currency':'USD','expected_components':['cash'],'lines':[row('b','1.001'),row('v','1')]}

    def test_nav_tolerance_accounted_without_forced_break(self):
        out=calculate('nav-preparation-tie-out',self.nav_doc());self.assertEqual(out['breaks'],[])
        c=out['tie_out']['control_totals'][0];self.assertEqual(Decimal(c['within_tolerance_difference']),Decimal('.001'));self.assertEqual(c['residual'],'0.000')

    def test_nav_stale_equal_inputs_not_clean_and_missing_price_routes(self):
        n='nav-preparation-tie-out';d=self.nav_doc()
        for r in d['lines']:r['as_of']='2026-06-29'
        out=calculate(n,d);self.assertFalse(out['tie_out']['ties_out']);self.assertEqual(out['tie_out']['status'],'needs_data')
        d=self.nav_doc();d['expected_components']=['price'];d['lines']=d['lines'][:1];d['lines'][0].update(component='price',unit='price_per_unit')
        out=calculate(n,d);self.assertEqual(out['breaks'][0]['proposed_resolution']['route_to'],'fund-valuation-oversight-reviewer')

if __name__=='__main__':unittest.main()
