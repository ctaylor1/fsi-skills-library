#!/usr/bin/env python3
"""Independent credit arithmetic and adverse supplied-evidence reconciliation."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'skills/investment-research/issuer-credit-researcher'

def fixture():
    return json.loads((PACKAGE/'evals/files/input.json').read_text())

def call(module,method,*args):
    sys.path.insert(0,str(PACKAGE/'scripts'))
    try:
        for name in ('domain','analysis_contract','research_runtime','native_integrity','validate_input','calculate_or_transform','validate_output'):
            sys.modules.pop(name,None)
        spec=importlib.util.spec_from_file_location(module,PACKAGE/'scripts'/(module+'.py'))
        loaded=importlib.util.module_from_spec(spec);sys.modules[module]=loaded;spec.loader.exec_module(loaded)
        return getattr(loaded,method)(*args)
    finally:sys.path.pop(0)

def run_cli(script,*args):
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONPATH',None)
    return subprocess.run([sys.executable,'-B','scripts/'+script+'.py',*map(str,args)],cwd=PACKAGE,capture_output=True,text=True,env=env)

def add_event(doc,event_id,amount):
    ledger=copy.deepcopy(doc['ebitda_adjustment_events'][0]);ledger.update(ledger_id='LEDGER-'+event_id,economic_event_id=event_id,amount=amount)
    ledger['source_binding']['economic_event_key']='source-event-'+event_id
    row=copy.deepcopy(doc['ebitda_adjustments'][0]);row.update(adjustment_id='ROW-'+event_id,economic_event_id=event_id,amount=amount)
    doc['ebitda_adjustment_events'].append(ledger);doc['ebitda_adjustments'].append(row)

class IssuerEvidenceReconciliation(unittest.TestCase):
    def result(self,doc):
        errors,_=call('validate_input','validate',doc);self.assertEqual(errors,[])
        out=call('domain','compute',doc)
        errors,_=call('validate_output','validate',out,doc);self.assertEqual(errors,[])
        return out

    def adjustment_gap(self,doc,fragment):
        out=self.result(doc);self.assertEqual(out['status'],'partial');r=out['results'];m=r['credit_metrics']
        self.assertEqual(m['reported_ebitda']['ebitda'],100)
        self.assertEqual(m['reported_ebitda']['gross_leverage_x'],4)
        self.assertTrue(all(value is None for value in m['analyst_adjusted_ebitda'].values()))
        self.assertTrue(any(fragment in x for x in out['unresolved_issues']),out['unresolved_issues'])
        self.assertEqual(r['evidence_reconciliation']['ebitda_adjustments']['status'],'unavailable')
        return out

    def debt_gap(self,doc,fragment):
        out=self.result(doc);self.assertEqual(out['status'],'partial');r=out['results']
        for row in r['credit_metrics'].values():
            self.assertIsNone(row['gross_leverage_x']);self.assertIsNone(row['net_leverage_x'])
        self.assertEqual(r['credit_metrics']['reported_ebitda']['ebitda'],100)
        self.assertEqual(r['credit_metrics']['reported_ebitda']['interest_coverage_x'],5)
        self.assertEqual(r['cash_flow']['free_cash_flow'],50)
        self.assertIsNone(r['cash_flow']['ffo_to_debt'])
        self.assertTrue(any(fragment in x for x in out['unresolved_issues']),out['unresolved_issues'])
        return out

    def test_complete_fixture_has_independently_expected_math_and_lineage(self):
        out=self.result(fixture());self.assertEqual(out['status'],'complete-for-supplied-scope');r=out['results']
        self.assertEqual(r['credit_metrics']['analyst_adjusted_ebitda']['ebitda'],110)
        self.assertAlmostEqual(r['credit_metrics']['analyst_adjusted_ebitda']['gross_leverage_x'],40/11)
        self.assertAlmostEqual(r['cash_flow']['ffo_to_debt'],7/40)
        self.assertEqual(r['evidence_reconciliation']['debt_inventory']['reconstructed_gross_debt'],400)
        self.assertEqual(out['calculation_lineage'][0]['included_instrument_ids'],['TERM-1'])

    def test_same_event_total_under_different_row_ids_is_unavailable(self):
        doc=fixture();row=copy.deepcopy(doc['ebitda_adjustments'][0]);row['adjustment_id']='RENAMED-ROW';doc['ebitda_adjustments'].append(row)
        self.adjustment_gap(doc,'repeated total')

    def test_same_source_event_under_different_ledger_and_event_ids_is_unavailable(self):
        doc=fixture();add_event(doc,'ALIAS',10)
        doc['ebitda_adjustment_events'][1]['source_binding']=copy.deepcopy(doc['ebitda_adjustment_events'][0]['source_binding'])
        self.adjustment_gap(doc,'source economic event duplicates')

    def test_event_alias_across_distinct_registered_sources_or_locators_is_not_additive(self):
        doc=fixture();add_event(doc,'CORROBORATING-DOCUMENT',10)
        source=copy.deepcopy(doc['sources'][0]);source.update(source_id='corroborating-source',locator='fixture:second-source:charge')
        doc['sources'].append(source);ref={'source_id':source['source_id'],'locator':source['locator']};doc['evidence_refs'].append(ref)
        event=doc['ebitda_adjustment_events'][1];event['source_binding'].update(source_id=source['source_id'],locator=source['locator'],economic_event_key=doc['ebitda_adjustment_events'][0]['source_binding']['economic_event_key'])
        event['evidence_refs']=[copy.deepcopy(ref)];doc['ebitda_adjustments'][1]['evidence_refs']=[copy.deepcopy(ref)]
        self.adjustment_gap(doc,'source economic event duplicates')

    def test_target_issuer_and_registered_source_block_are_explicit(self):
        for mutation in ('issuer-missing','issuer-other','invented-block'):
            doc=fixture();binding=doc['ebitda_adjustment_events'][0]['source_binding']
            if mutation=='issuer-missing':binding.pop('subject_issuer_id')
            elif mutation=='issuer-other':binding['subject_issuer_id']='OTHER-ISSUER'
            else:
                binding['locator']='invented:uncorroborated-block';ref={'source_id':binding['source_id'],'locator':binding['locator']}
                doc['evidence_refs'].append(ref);doc['ebitda_adjustment_events'][0]['evidence_refs']=[ref];doc['ebitda_adjustments'][0]['evidence_refs']=[copy.deepcopy(ref)]
            self.adjustment_gap(doc,'identity' if mutation=='issuer-missing' else 'subject_issuer_id' if mutation=='issuer-other' else 'registered precise source block')

    def test_security_request_binds_issuer_separately_from_security_source_coverage(self):
        doc=fixture();doc['subject']={'type':'security','id':'ACME-BOND','issuer_id':'ACME-ISSUER'}
        doc['sources'][0]['subject_ids']=['ACME-ISSUER','ACME-BOND']
        out=self.result(doc);self.assertEqual(out['status'],'complete-for-supplied-scope')
        doc['sources'][0]['subject_ids']=['ACME-BOND']
        out=self.result(doc);self.assertEqual(out['status'],'partial')
        self.assertIsNotNone(out['results'])
        self.assertTrue(any('does not identify target issuer' in reason for reason in out['unresolved_issues']))
        self.assertIsNone(out['results']['credit_metrics']['analyst_adjusted_ebitda']['ebitda'])
        self.assertIsNone(out['results']['credit_metrics']['reported_ebitda']['gross_leverage_x'])

    def test_debt_target_issuer_binding_cannot_be_omitted_or_substituted(self):
        for where in ('inventory','bridge','inclusion'):
            doc=fixture()
            if where=='inventory':doc['debt_reconciliation']['source_binding']['subject_issuer_id']='OTHER-ISSUER'
            elif where=='bridge':doc['debt_reconciliation']['bridge'][0]['source_binding'].pop('subject_issuer_id')
            else:doc['instruments'][0]['debt_inclusion']['subject_issuer_id']='OTHER-ISSUER'
            self.debt_gap(doc,'subject_issuer_id' if where!='bridge' else 'identity')

    def test_selected_adjustment_must_retain_exact_event_or_component_citations(self):
        for components in (False,True):
            doc=self.component_case() if components else fixture();source=copy.deepcopy(doc['sources'][0]);source.update(source_id='unrelated-valid-source',locator='fixture:unrelated-table')
            doc['sources'].append(source);ref={'source_id':source['source_id'],'locator':source['locator']};doc['evidence_refs'].append(ref);doc['ebitda_adjustments'][0]['evidence_refs']=[ref]
            self.adjustment_gap(doc,'citations differ')

    def test_missing_event_identity_or_context_does_not_infer_additivity(self):
        for target,key in [('adjustment','economic_event_id'),('event','source_binding'),('event','consolidation_scope')]:
            with self.subTest(target=target,key=key):
                doc=fixture();row=doc['ebitda_adjustments'][0] if target=='adjustment' else doc['ebitda_adjustment_events'][0];row.pop(key)
                self.adjustment_gap(doc,'missing' if key!='source_binding' else 'source_binding')

    def test_multiple_versions_and_conflicting_amounts_are_not_summed(self):
        doc=fixture();event=copy.deepcopy(doc['ebitda_adjustment_events'][0]);event.update(ledger_id='LEDGER-V2',event_version='v2',amount=9);doc['ebitda_adjustment_events'].append(event)
        self.adjustment_gap(doc,'multiple ledger candidates')
        doc=fixture();doc['ebitda_adjustments'][0]['amount']=9
        self.adjustment_gap(doc,'differs from signed event total')
        doc=fixture();doc['ebitda_adjustments'][0]['event_version']='superseded'
        self.adjustment_gap(doc,'event version')

    def test_same_amount_distinct_source_bound_events_are_legitimately_additive(self):
        doc=fixture();add_event(doc,'DISTINCT-ECONOMIC-EVENT',10)
        out=self.result(doc);self.assertEqual(out['status'],'complete-for-supplied-scope')
        self.assertEqual(out['results']['credit_metrics']['analyst_adjusted_ebitda']['ebitda'],120)
        self.assertEqual(out['results']['credit_metrics']['reported_ebitda']['ebitda'],100)

    def component_case(self):
        doc=fixture();event=doc['ebitda_adjustment_events'][0];event.update(aggregation='additive-components',amount=9)
        event['components']=[{'component_id':'C1','amount':4,'evidence_refs':copy.deepcopy(doc['evidence_refs'])},{'component_id':'C2','amount':5,'evidence_refs':copy.deepcopy(doc['evidence_refs'])}]
        template=doc['ebitda_adjustments'][0];doc['ebitda_adjustments']=[]
        for component in event['components']:
            row=copy.deepcopy(template);row.update(adjustment_id='ROW-'+component['component_id'],aggregation_role='component',component_id=component['component_id'],amount=component['amount']);doc['ebitda_adjustments'].append(row)
        return doc

    def test_complete_nonoverlapping_components_reconcile_exactly(self):
        out=self.result(self.component_case());self.assertEqual(out['status'],'complete-for-supplied-scope')
        self.assertEqual(out['results']['credit_metrics']['analyst_adjusted_ebitda']['ebitda'],109)

    def test_component_alias_duplicate_missing_and_total_overlap_withhold(self):
        doc=self.component_case();row=copy.deepcopy(doc['ebitda_adjustments'][0]);row['adjustment_id']='ALIAS';doc['ebitda_adjustments'].append(row);self.adjustment_gap(doc,'multiple adjustment IDs')
        doc=self.component_case();doc['ebitda_adjustments'].pop();self.adjustment_gap(doc,'do not cover')
        doc=self.component_case();row=copy.deepcopy(doc['ebitda_adjustments'][0]);row.update(adjustment_id='TOTAL',aggregation_role='event-total',amount=9);doc['ebitda_adjustments'].append(row);self.adjustment_gap(doc,'overlap')

    def test_nonadditive_or_inconsistent_component_inventory_withholds(self):
        doc=self.component_case();doc['ebitda_adjustment_events'][0]['aggregation']='overlapping-components';self.adjustment_gap(doc,'additive treatment')
        doc=self.component_case();doc['ebitda_adjustment_events'][0]['amount']=10;self.adjustment_gap(doc,'component sum')
        doc=self.component_case();doc['ebitda_adjustments'][0]['amount']=8;self.adjustment_gap(doc,'component amount conflicts')

    def test_event_context_currency_unit_basis_period_are_not_inferred(self):
        for field,value in [('currency','EUR'),('unit','USD_thousands'),('accounting_basis','IFRS'),('consolidation_scope','parent-only'),('period',{'start':'2025-01-01','end':'2025-09-30','fiscal_calendar_id':'ACME-calendar'})]:
            with self.subTest(field=field):
                doc=fixture();doc['ebitda_adjustment_events'][0][field]=value;self.adjustment_gap(doc,field+' differs')

    def test_event_source_version_known_at_and_precise_locator_must_match(self):
        for field,value in [('version','new-version'),('known_at','2026-10-19'),('locator','uncited:table')]:
            with self.subTest(field=field):
                doc=fixture();doc['ebitda_adjustment_events'][0]['source_binding'][field]=value;self.adjustment_gap(doc,'source_binding')

    def test_missing_new_metadata_is_partial_without_changing_reported_ebitda(self):
        doc=fixture();doc.pop('ebitda_adjustment_events');doc.pop('debt_reconciliation')
        out=self.result(doc);self.assertEqual(out['status'],'partial')
        self.assertEqual(out['results']['credit_metrics']['reported_ebitda']['ebitda'],100)
        self.assertIsNone(out['results']['credit_metrics']['analyst_adjusted_ebitda']['ebitda'])
        self.assertIsNone(out['results']['cash_flow']['ffo_to_debt'])

    def test_currency_and_unit_mismatch_withhold_debt_even_when_totals_match(self):
        for field,value in [('currency','EUR'),('unit','USD_thousands'),('accounting_basis','IFRS'),('consolidation_scope','subsidiary-only')]:
            with self.subTest(field=field):
                doc=fixture();doc['instruments'][0][field]=value;self.debt_gap(doc,field)

    def test_missing_null_principal_and_context_do_not_become_zero(self):
        for missing in (False,True):
            doc=fixture()
            if missing:doc['instruments'][0].pop('principal')
            else:doc['instruments'][0]['principal']=None
            self.debt_gap(doc,'principal is missing')
        doc=fixture();doc['instruments'][0].pop('unit');self.debt_gap(doc,'missing unit')

    def test_inventory_total_mismatch_cannot_emit_leverage(self):
        doc=fixture();doc['financials']['gross_debt']=585;doc['instruments'][0]['principal']=700
        self.debt_gap(doc,'does not equal reported gross debt')
        doc['instruments'][0]['currency']='EUR';self.debt_gap(doc,'FX unsupported')

    def test_cited_principal_to_carrying_value_bridge_preserves_real_difference(self):
        doc=fixture();doc['instruments'][0]['principal']=410;doc['debt_reconciliation']['bridge'][0]['amount']=-10
        out=self.result(doc);self.assertEqual(out['status'],'complete-for-supplied-scope')
        debt=out['results']['evidence_reconciliation']['debt_inventory'];self.assertEqual(debt['included_principal_total'],410);self.assertEqual(debt['carrying_value_bridge_total'],-10)
        self.assertEqual(out['results']['credit_metrics']['reported_ebitda']['gross_leverage_x'],4)

    def test_bridge_duplicate_economic_identity_and_unsupported_basis_withhold(self):
        doc=fixture();row=copy.deepcopy(doc['debt_reconciliation']['bridge'][0]);row['bridge_id']='BRIDGE-ALIAS';doc['debt_reconciliation']['bridge'].append(row);self.debt_gap(doc,'economic bridge event')
        doc=fixture();row=copy.deepcopy(doc['debt_reconciliation']['bridge'][0]);row.update(bridge_id='BRIDGE-ALIAS',economic_event_id='RENAMED-EVENT');doc['debt_reconciliation']['bridge'].append(row);self.debt_gap(doc,'source economic bridge event duplicates')
        doc=fixture();doc['debt_reconciliation']['bridge'][0]['bridge_type']='valuation-to-market';self.debt_gap(doc,'measurement bridge basis')

    def test_bridge_context_missing_coverage_and_unbound_source_withhold(self):
        for target,key,value in [('inventory','inventory_coverage','partial'),('inventory','source_binding',None),('bridge','unit','USD_thousands'),('bridge','period',{'start':'2025-01-01','end':'2025-09-30','fiscal_calendar_id':'ACME-calendar'})]:
            with self.subTest(target=target,key=key):
                doc=fixture();row=doc['debt_reconciliation'] if target=='inventory' else doc['debt_reconciliation']['bridge'][0];row[key]=value;self.debt_gap(doc,'coverage' if key=='inventory_coverage' else 'source_binding' if key=='source_binding' else key)

    def test_explicit_out_of_scope_structural_instrument_is_not_automatically_debt(self):
        doc=fixture();instrument=copy.deepcopy(doc['instruments'][0]);instrument.update(instrument_id='SUB-STRUCTURAL',issuer_id='SUB-ISSUER',estate_id='SUB-ESTATE',currency='EUR',unit='EUR_m',consolidation_scope='unconsolidated-subsidiary',principal=700)
        instrument['debt_inclusion'].update(treatment='excluded',reason='Unconsolidated subsidiary obligation supplied only for structural legal-entity review, not consolidated reported gross debt.')
        doc['instruments'].append(instrument);out=self.result(doc);self.assertEqual(out['status'],'complete-for-supplied-scope')
        self.assertEqual(out['results']['credit_metrics']['reported_ebitda']['gross_leverage_x'],4)
        self.assertEqual(out['results']['structural_risks'][0]['instrument_id'],'SUB-STRUCTURAL')
        self.assertEqual(out['results']['evidence_reconciliation']['debt_inventory']['excluded_instrument_ids'],['SUB-STRUCTURAL'])

    def test_missing_exclusion_reason_is_not_a_blanket_scope_override(self):
        doc=fixture();doc['instruments'][0]['debt_inclusion']['treatment']='excluded';doc['instruments'][0]['debt_inclusion'].pop('reason');self.debt_gap(doc,'scoped reason')

    def test_no_adjustments_needs_no_event_ledger(self):
        doc=fixture();doc['ebitda_adjustments']=[];doc.pop('ebitda_adjustment_events');out=self.result(doc)
        self.assertEqual(out['status'],'complete-for-supplied-scope');self.assertEqual(out['results']['credit_metrics']['analyst_adjusted_ebitda']['ebitda'],100)

    def test_decimal_event_and_debt_tieouts_are_exact_not_float_epsilon(self):
        doc=self.component_case();event=doc['ebitda_adjustment_events'][0];event['amount']=0.3
        for component,row,value in zip(event['components'],doc['ebitda_adjustments'],(0.1,0.2)):component['amount']=value;row['amount']=value
        doc['instruments'][0]['principal']=400.1;doc['debt_reconciliation']['bridge'][0]['amount']=-0.1
        out=self.result(doc);self.assertEqual(out['status'],'complete-for-supplied-scope')
        doc['debt_reconciliation']['bridge'][0]['amount']=-0.1000000000001;self.debt_gap(doc,'does not equal')

    def test_source_eligibility_still_withholds_whole_result_projection(self):
        for mutation in ('future','denied'):
            doc=fixture()
            if mutation=='future':doc['sources'][0]['known_at']='2026-10-21T00:00:00Z'
            else:doc['sources'][0]['permission_status']='denied'
            out=self.result(doc);self.assertEqual(out['status'],'partial');self.assertIsNone(out['results']);self.assertEqual(out['calculation_lineage'],[])

    def test_duplicate_technical_ids_remain_structural_rejections(self):
        doc=fixture();doc['ebitda_adjustments'].append(copy.deepcopy(doc['ebitda_adjustments'][0]))
        errors,_=call('validate_input','validate',doc);self.assertTrue(any('duplicate adjustment_id' in x for x in errors))
        with self.assertRaisesRegex(ValueError,'duplicate adjustment_id'):call('domain','compute',doc)

    def test_public_input_compute_and_original_bound_output_for_both_gaps(self):
        cases=[];doc=fixture();row=copy.deepcopy(doc['ebitda_adjustments'][0]);row['adjustment_id']='SECOND-ID';doc['ebitda_adjustments'].append(row);cases.append(doc)
        doc=fixture();doc['financials']['gross_debt']=585;doc['instruments'][0].update(currency='EUR',principal=700);cases.append(doc)
        with tempfile.TemporaryDirectory(prefix='ir-issuer-reconciliation-') as temp:
            for index,doc in enumerate(cases):
                source=Path(temp)/(str(index)+'-input.json');source.write_text(json.dumps(doc));output=Path(temp)/(str(index)+'-output.json')
                checked=run_cli('validate_input',source);self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)
                computed=run_cli('calculate_or_transform',source);self.assertEqual(computed.returncode,0,computed.stdout+computed.stderr);output.write_text(computed.stdout)
                result=json.loads(computed.stdout);self.assertEqual(result['status'],'partial')
                validated=run_cli('validate_output',output,'--input',source);self.assertEqual(validated.returncode,0,validated.stdout+validated.stderr)
                result['results']['credit_metrics']['analyst_adjusted_ebitda']['ebitda']=120
                output.write_text(json.dumps(result));tampered=run_cli('validate_output',output,'--input',source);self.assertEqual(tampered.returncode,1)
                self.assertNotIn('Traceback',tampered.stderr)

if __name__=='__main__':unittest.main()
