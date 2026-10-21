"""Real producer-to-consumer adapter checks with independent expected outcomes."""
import copy,json,subprocess,sys,unittest,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'shared/investment-research'),str(ROOT/'shared/investment-data')]
from reviewed_handoffs import review
from analysis_contract import load_json,validate_base,finish
from native_integrity import validate_reconstruction

def fixture(name):
    p=ROOT/'skills/investment-research'/name/'evals/files'
    for filename in ('phase2-input.json','phase2_input.json','input.json'):
        if (p/filename).exists():return json.loads((p/filename).read_text())
    raise AssertionError('missing Phase2 fixture '+name)
def compute(name,doc):
    p=ROOT/'skills/investment-research'/name
    r=subprocess.run([sys.executable,'-B',str(p/'scripts/calculate_or_transform.py')],input=json.dumps(doc),text=True,capture_output=True,cwd=p)
    if r.returncode:raise AssertionError(r.stdout+r.stderr)
    return json.loads(r.stdout)
def request(adapter,producer,receiver,selection=None):
    original=fixture(producer);target=fixture(receiver)
    if adapter=='forecast-to-dcf':target['forecast_rows']=[]
    if adapter=='terms-to-covenant':target['tests']=[]
    if adapter=='model-review-to-initiation':
        for k in ('subject','as_of','knowledge_cutoff','use_on','purpose','audience','information_barrier'):
            target[k]=copy.deepcopy(original[k])
        for source in target['sources']:
            source['subject_ids']=[original['subject']['id']]
            # This fresh synthetic caller supplies actual timestamp precision;
            # the adapter itself must never invent one from a date-only source.
            source['known_at']='2026-10-19T17:00:00Z'
        target['unit']=original['units'];target['currency']=original['currency'];target['accounting_basis']=original['accounting_basis'];target['consolidation_scope']=original['consolidation_scope']
        for method in target['method_outputs']:
            method.update(subject_id=original['subject']['id'],currency=target['currency'],unit=target['unit'],accounting_basis=target['accounting_basis'],consolidation_scope=target['consolidation_scope'])
        target['model_review']={'state':'not-supplied','issues':[]}
    if adapter=='dcf-to-reconciliation':target['methods']=[r for r in target['methods'] if r['method_id']=='nav']
    if adapter=='capital-structure-to-liquidity':
        target.update(cash={'unrestricted':100,'restricted':999,'evidence_refs':target['evidence_refs']},minimum_cash=5,cash_flows=[],facilities=[],refinancing=[],horizon_end='2027-12-31')
        target['maturities']=[]
    return {'adapter_id':adapter,'producer_input':original,'producer_output':compute(producer,original),'receiver_input':target,'selection':selection or {}}

class ReviewedAdapters(unittest.TestCase):
    def test_forecast_to_dcf_consumes_actual_cashflows(self):
        d=request('forecast-to-dcf','three-statement-model-builder','dcf-modeler')
        d['receiver_input']['discounting']='end_year';d['receiver_input']['wacc']=0.1;d['receiver_input']['terminal_growth']=0
        out=review(d,ROOT);rows=d['producer_output']['results']['forecast_rows'];r=out['receiver_output']['results']
        expected=sum(row['ufcf']/1.1**i for i,row in enumerate(rows,1))+rows[-1]['ufcf']/0.1/1.1**len(rows)
        self.assertAlmostEqual(expected,r['enterprise_value'],places=6)
        self.assertEqual(rows,out['receiver_input']['forecast_rows']);self.assertFalse(out['authority_granted'])
    def test_selected_maturity_inventory_has_independent_funding_gap(self):
        d=request('capital-structure-to-liquidity','issuer-capital-structure-mapper','issuer-liquidity-refinancing-analyzer',{'currency':'USD','unit':'USD_m'})
        out=review(d,ROOT);self.assertEqual(out['receiver_input']['maturities'][0]['amount'],100)
        self.assertEqual(out['receiver_output']['results']['scenarios']['committed_base']['maximum_funding_gap_known_schedule'],5)
        d['receiver_input']['maturity_inventory_complete']=False
        with self.assertRaisesRegex(ValueError,'completeness'):review(d,ROOT)
    def test_conflicting_receiver_obligations_and_forecasts_are_not_overwritten(self):
        d=request('capital-structure-to-liquidity','issuer-capital-structure-mapper','issuer-liquidity-refinancing-analyzer',{'currency':'USD','unit':'USD_m'})
        d['receiver_input']['maturities']=[{'id':'loan-X','instrument_id':'loan-X','date':'2027-06-30','amount':80,'currency':'USD','unit':'USD_m','evidence_refs':d['receiver_input']['evidence_refs']}]
        with self.assertRaisesRegex(ValueError,'conflicting populated receiver field'):review(d,ROOT)
        d=request('forecast-to-dcf','three-statement-model-builder','dcf-modeler');d['receiver_input']['forecast_rows']=fixture('dcf-modeler')['forecast_rows'];d['receiver_input']['forecast_rows'][0]['ufcf']+=1
        with self.assertRaisesRegex(ValueError,'conflicting populated receiver field'):review(d,ROOT)
    def test_terms_map_only_explicit_reviewed_definition(self):
        d=request('terms-to-covenant','credit-document-terms-reviewer','covenant-headroom-analyzer')
        out=review(d,ROOT);test=out['receiver_output']['results']['tests'][0]
        # Reviewed definition: (400 debt - 50 cash) / 100 EBITDA; maximum 4.5x.
        self.assertAlmostEqual(test['ratio_x'],3.5);self.assertAlmostEqual(test['ratio_headroom_x'],1)
        self.assertEqual(out['receiver_input']['tests'][0]['document_version'],'v2')
    def test_indexed_dcf_does_not_become_spot_nav(self):
        d=request('dcf-to-reconciliation','dcf-modeler','valuation-reconciliation-analyzer')
        out=review(d,ROOT);r=out['receiver_output']['results']
        self.assertIsNone(r['comparable_range'])
        mapped=out['receiver_input']['methods'][-1]
        self.assertEqual(mapped['equity_value'],d['producer_output']['results']['equity_value'])
        self.assertEqual(mapped['valuation_timing'],'annual-period-index')
    def test_explicit_share_basis_and_discount_origin_are_preserved(self):
        d=request('dcf-to-reconciliation','dcf-modeler','valuation-reconciliation-analyzer')
        source=d['producer_input'];result=d['producer_output']['results'];other=d['receiver_input']['methods'][0]
        other.update(method_id='independent-indexed-method',share_basis=source['valuation_subject']['share_count_basis'],valuation_timing=source['valuation_timing'],discount_origin=result['discount_origin'],first_forecast_year=result['first_forecast_year'])
        out=review(d,ROOT);mapped=out['receiver_input']['methods'][-1]
        self.assertEqual(mapped['share_basis'],source['valuation_subject']['share_count_basis'])
        self.assertTrue(out['receiver_output']['results']['comparisons'][0]['comparable'])
    def test_model_review_cannot_clear_inititation(self):
        d=request('model-review-to-initiation','research-financial-model-reviewer','coverage-initiation-researcher')
        out=review(d,ROOT);result=out['receiver_output']
        self.assertEqual(result['results']['model_review']['state'],'review-required')
        self.assertTrue(any('funding' in x for x in result['unresolved_issues']))
        self.assertFalse(out['action_taken'])
    def test_tampering_and_cross_context_are_rejected(self):
        d=request('forecast-to-dcf','three-statement-model-builder','dcf-modeler')
        bad=copy.deepcopy(d);bad['producer_output']['results']['forecast_rows'][0]['ufcf']+=10
        with self.assertRaises(ValueError):review(bad,ROOT)
        for field,value in [('as_of','2026-10-19'),('subject',{'type':'issuer','id':'OTHER'}),('currency','EUR'),('knowledge_cutoff','2026-10-20T17:00:00Z')]:
            bad=copy.deepcopy(d);bad['receiver_input'][field]=value
            with self.assertRaises(ValueError):review(bad,ROOT)
    def test_expired_evidence_releases_no_payload(self):
        d=request('forecast-to-dcf','three-statement-model-builder','dcf-modeler')
        d['producer_input']['sources'][0]['expires_on']='2020-01-01'
        d['producer_output']=compute('three-statement-model-builder',d['producer_input'])
        with self.assertRaises(ValueError):review(d,ROOT)
    def test_handoff_itself_is_original_bound(self):
        d=request('forecast-to-dcf','three-statement-model-builder','dcf-modeler');o=review(d,ROOT)
        errors=[];validate_reconstruction(o,lambda doc:review(doc,ROOT),errors,original_input=d);self.assertEqual(errors,[])
        o['receiver_input']['forecast_rows'][0]['ufcf']+=1;errors=[]
        validate_reconstruction(o,lambda doc:review(doc,ROOT),errors,original_input=d);self.assertTrue(errors)
    def test_shared_contract_rejects_lost_precision_unknowns_and_source_identity(self):
        for raw in ('{"a":1,"a":2}','{"x":NaN}'):
            with self.assertRaises(ValueError):load_json(raw)
        d=fixture('dcf-modeler');d['accounting_basis']=' unknown '
        with self.assertRaises(ValueError):validate_base(d)
        d=fixture('dcf-modeler');d['sources'][0]['subject_ids']=['FOREIGN']
        out=finish(d,'probe',{'financial_value':12345})
        self.assertIsNone(out['results']);self.assertEqual(out['evidence_refs'],[])
    def test_duplicate_json_is_controlled_in_every_phase2_public_reader(self):
        capabilities=json.loads((ROOT/'catalog/investment-research-capabilities.json').read_text())['capabilities']
        with tempfile.TemporaryDirectory() as tmp:
            duplicate=Path(tmp)/'duplicate.json';duplicate.write_text('{"request_id":"first","request_id":"second"}')
            original=Path(tmp)/'original.json'
            for row in capabilities:
                if row['roadmap_phase']!=2:continue
                original.write_text(json.dumps(fixture(row['name'])))
                for script in ('validate_input.py','calculate_or_transform.py','validate_output.py'):
                    with self.subTest(skill=row['name'],script=script):
                        args=[sys.executable,'-B',str(ROOT/row['path']/'scripts'/script),str(duplicate)]
                        if script=='validate_output.py':args+=['--input',str(original)]
                        proc=subprocess.run(args,text=True,capture_output=True)
                        self.assertEqual(proc.returncode,1)
                        self.assertIn('duplicate JSON object key',proc.stdout+proc.stderr)
                        self.assertNotIn('Traceback',proc.stdout+proc.stderr)
if __name__=='__main__':unittest.main()
