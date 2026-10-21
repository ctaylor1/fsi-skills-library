"""Consequential source mapping, scope, chronology and native integrity contracts."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'shared/investment-data'))
spec = importlib.util.spec_from_file_location('cfc_phase2_foundation', ROOT/'shared/compliance-financial-crime/foundation_contract.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def fixture():
    context = dict(institution_id='SYNTHETIC-FI',legal_entity_id='SYNTHETIC-ENTITY',capacity='compliance',
                   represented_party='SYNTHETIC-FI',object_id='REVIEW-01',object_type='control_review',
                   jurisdiction='US',line_of_business='synthetic-banking',purpose='Synthetic control evidence review')
    source = dict(source_ref='SYNTHETIC-R1',version='test-1',publication_date='2026-09-29',received_at='2026-10-02',
                  classification='compliance_confidential',permitted_audiences=['internal-review'],
                  facts=[dict(fact_id='F1',value=False,excerpt='Synthetic control did not pass the observed sample.')])
    return dict(request_id='SYNTHETIC-REQ1',object_id='REVIEW-01',object_type='control_review',as_of='2026-10-03',
                knowledge_cutoff='2026-10-03',workflow=dict(context=context,as_of='2026-10-03',role='oversight',
                classification='compliance_confidential',audience='internal-review',allowed_audiences=['internal-review'],
                sources=[dict(source_ref='SYNTHETIC-R1',version='test-1')],unresolved_issues=[]),sources=[source],
                data=dict(observed_result=dict(value=False,source_refs=['SYNTHETIC-R1'],fact_ids=['F1'])))


def compute(doc):
    c.require_valid(doc,c.validate_common)
    value,issues = c.claim_value(doc,doc['data'].get('observed_result'), 'observed control')
    return c.result(doc,'synthetic-contract-test','observed-control/1.0',{'observed':value},issues)


class FoundationContract(unittest.TestCase):
    def setUp(self):
        self.doc=fixture()

    def test_exact_false_is_supported_and_never_unknown(self):
        value,issues=c.claim_value(self.doc,self.doc['data']['observed_result'])
        self.assertIs(value,False);self.assertEqual(issues,[])
        self.assertEqual(compute(self.doc)['results']['observed'],False)

    def test_claim_binding_locators_preserve_exact_or_unresolved_state_without_raw_values(self):
        binding=compute(self.doc)['claim_bindings'][0]
        self.assertEqual(binding['native_input_pointer'],'/data/observed_result')
        self.assertEqual(binding['source_refs'],['SYNTHETIC-R1'])
        self.assertEqual(binding['fact_ids'],['F1'])
        self.assertEqual(binding['consistency'],'exact-supplied-fact')
        self.assertNotIn('value',binding)
        self.doc['data']['observed_result']['value']=True
        binding=compute(self.doc)['claim_bindings'][0]
        self.assertEqual(binding['consistency'],'unresolved')
        self.assertTrue(binding['issues'])

    def test_empty_and_zero_observations_are_not_invented(self):
        self.doc['sources'][0]['facts'][0]['value']=0
        self.doc['data']['observed_result']['value']=0
        self.assertEqual(c.claim_value(self.doc,self.doc['data']['observed_result']),(0,[]))
        self.doc['data']['observed_result']['value']=None
        self.assertIsNone(compute(self.doc)['results']['observed'])
        self.assertEqual(compute(self.doc)['status'],'needs-evidence')

    def test_changed_claim_with_existing_citation_is_withheld(self):
        self.doc['data']['observed_result']['value']=True
        output=compute(self.doc)
        self.assertIsNone(output['results']['observed']);self.assertEqual(output['status'],'needs-evidence')

    def test_conflicting_corroboration_cannot_be_cherry_picked(self):
        second=copy.deepcopy(self.doc['sources'][0]);second['source_ref']='SYNTHETIC-R2'
        second['facts']=[dict(fact_id='F2',value=True,excerpt='Synthetic second record contradicts the first.')]
        self.doc['sources'].append(second);self.doc['workflow']['sources'].append(dict(source_ref='SYNTHETIC-R2',version='test-1'))
        claim=self.doc['data']['observed_result'];claim['source_refs'].append('SYNTHETIC-R2');claim['fact_ids'].append('F2')
        self.assertIsNone(compute(self.doc)['results']['observed'])

    def test_each_cited_source_needs_the_actual_claim_fact(self):
        second=copy.deepcopy(self.doc['sources'][0]);second['source_ref']='SYNTHETIC-R2';second['facts']=[]
        self.doc['sources'].append(second);self.doc['workflow']['sources'].append(dict(source_ref='SYNTHETIC-R2',version='test-1'))
        self.doc['data']['observed_result']['source_refs'].append('SYNTHETIC-R2')
        self.assertFalse(c.claim_check(self.doc,self.doc['data']['observed_result'])[0])

    def test_future_source_cannot_support_current_evidence(self):
        self.doc['sources'][0]['received_at']='2026-10-04'
        self.assertEqual(c.validate_common(self.doc),[])
        output=compute(self.doc);self.assertIsNone(output['results']['observed'])
        self.assertTrue(any('future' in issue for issue in output['unresolved_issues']))

    def test_expiry_is_explicit_and_no_universal_max_age_is_invented(self):
        self.doc['sources'][0]['received_at']='2024-01-01';self.doc['sources'][0]['publication_date']='2023-12-31'
        self.assertFalse(c.evidence_issues(self.doc,['SYNTHETIC-R1']))
        self.doc['sources'][0]['expires_on']='2026-10-02'
        self.assertTrue(c.evidence_issues(self.doc,['SYNTHETIC-R1']))

    def test_empty_registry_and_missing_fact_leave_a_gap(self):
        self.doc['sources']=[];self.doc['workflow']['sources']=[]
        output=compute(self.doc);self.assertEqual(output['status'],'needs-evidence')
        self.assertFalse(output['action_taken'])

    def test_native_context_cannot_change_identity_or_clock(self):
        for field,value in [('object_id','OTHER'),('object_type','customer'),('as_of','2026-10-02')]:
            doc=fixture()
            if field=='as_of':doc['workflow'][field]=value
            else:doc['workflow']['context'][field]=value
            self.assertTrue(c.validate_common(doc))

    def test_source_version_is_bound_to_declared_workflow(self):
        self.doc['sources'][0]['version']='different'
        self.assertTrue(c.validate_common(self.doc))

    def test_sar_or_mnpi_cannot_be_downgraded(self):
        for classification in ('sar_restricted','mnpi','legal_restricted','customer_pii'):
            doc=fixture();doc['sources'][0]['classification']=classification
            self.assertTrue(c.validate_common(doc))
        self.doc['workflow']['classification']='sar_restricted';self.doc['sources'][0]['classification']='sar_restricted'
        self.assertTrue(c.validate_common(self.doc))

    def test_unlisted_source_audience_rejects_intake(self):
        self.doc['sources'][0]['permitted_audiences']=['customer']
        with self.assertRaises(ValueError):compute(self.doc)

    def test_roles_never_grant_execution_or_authenticated_approval(self):
        self.doc['workflow']['role']='independent_testing'
        output=compute(self.doc)
        self.assertFalse(output['action_taken']);self.assertEqual(output['approval'],'not_requested')
        self.assertEqual(output['execution'],'not_performed');self.assertEqual(output['source_truth'],'unverified')

    def test_rehashed_or_added_native_narrative_rejected(self):
        output=compute(self.doc);output['results']['observed']=True
        self.assertTrue(c.validate_result(output,self.doc,compute))
        output=compute(self.doc);output['narrative']='Everything passed.'
        self.assertTrue(c.validate_result(output,self.doc,compute))

    def test_detached_original_required_and_source_changes_rejected(self):
        output=compute(self.doc)
        self.assertTrue(c.validate_result(output,None,compute))
        self.doc['request_id']='OTHER'
        self.assertTrue(c.validate_result(output,self.doc,compute))

    def test_malformed_containers_return_errors_without_success(self):
        for path,value in [('object_type',{}),('workflow',[]),('sources',{}),('data',None)]:
            doc=fixture();doc[path]=value
            self.assertTrue(c.validate_common(doc))
        self.doc['sources'][0]['source_ref']=[]
        self.assertTrue(c.validate_common(self.doc))

    def test_nonfinite_in_optional_fields_is_rejected(self):
        self.doc['unused']=float('nan')
        self.assertTrue(c.validate_common(self.doc))

    def test_decimal_preserves_exact_legal_boundary_and_bool_is_not_numeric(self):
        self.assertEqual(sum(c.decimal(v) for v in [.01,32.16,17.83]),c.decimal(50))
        with self.assertRaises(ValueError):c.decimal(True)

    def test_knowledge_date_never_advances_past_assessment(self):
        for value in ('2026-10-04','20261003','2026-02-30'):
            self.doc['knowledge_cutoff']=value;self.assertTrue(c.validate_common(self.doc))

    def test_cli_parser_rejects_duplicate_keys_and_nonfinite_json(self):
        for raw in ('{"key":1,"key":2}','{"key":NaN}'):
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'input.json';p.write_text(raw)
                with self.assertRaises(ValueError):c._read(p)


if __name__=='__main__':unittest.main()
