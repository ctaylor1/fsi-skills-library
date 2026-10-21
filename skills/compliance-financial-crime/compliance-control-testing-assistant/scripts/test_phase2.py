"""Independent behavioral assertions against de-identified synthetic fixtures."""
import copy
import json
from pathlib import Path
import unittest
from domain import compute, validate
from validate_output import validate as validate_output
BASE=json.loads((Path(__file__).resolve().parents[1]/'evals/files/input_complete.json').read_text())

def set_claim(doc,claim,value):
    claim['value']=value
    for source in doc['sources']:
        for fact in source['facts']:
            if fact['fact_id'] in claim['fact_ids']:
                fact['value']=value
                fact['excerpt']='Synthetic changed supplied fact: '+json.dumps(value)

class DomainTests(unittest.TestCase):
    def test_complete_method(self):
        self.assertEqual(validate(BASE)[0],[])
        out=compute(BASE)
        self.assertTrue(out['results']['observed_results'] == {'pass':2,'fail':0,'unknown':0} and out['results']['within_supplied_acceptance_criterion'] is True)
        self.assertEqual(out['status'],'draft-for-human-review')
        self.assertFalse(out['action_taken'])
        self.assertTrue(out['human_review_required'])
    def test_professional_failure_case(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['test']['independent_assessment'],None)
        out=compute(doc)
        self.assertTrue(out['results']['supplied_independence_evidence_consistent'] is None and out['results']['within_supplied_acceptance_criterion'] is None)
        self.assertEqual(out['status'],'needs-evidence')
    def test_exact_detached_native_result(self):
        out=compute(BASE)
        self.assertEqual(validate_output(out,BASE),[])
        self.assertTrue(validate_output(out,None))
    def test_output_edits_and_extra_narrative_fail(self):
        out=compute(BASE)
        out['narrative']='Approved or closed'
        self.assertTrue(validate_output(out,BASE))
        out=compute(BASE)
        out['results']={'decision':'approved'}
        self.assertTrue(validate_output(out,BASE))
    def test_malformed_intake_stops(self):
        doc=copy.deepcopy(BASE)
        doc['data']['undeclared_decision']='approve'
        with self.assertRaises(ValueError): compute(doc)
    def test_claim_value_cannot_diverge_from_exact_source_fact(self):
        doc=copy.deepcopy(BASE)
        claim=doc['data']['test']['independent_assessment']
        claim['fact_ids']=['not-a-stated-fact']
        out=compute(doc)
        self.assertEqual(out['status'],'needs-evidence')
        self.assertTrue(any('fact' in issue for issue in out['unresolved_issues']))
    def test_source_date_access_and_inherited_issues(self):
        doc=copy.deepcopy(BASE)
        doc['sources'][0]['received_at']='2026-10-04'
        out=compute(doc)
        self.assertEqual(out['status'],'needs-evidence')
        doc=copy.deepcopy(BASE)
        doc['sources'][0]['permitted_audiences']=['unrelated-party']
        with self.assertRaises(ValueError): compute(doc)
        doc=copy.deepcopy(BASE)
        doc['workflow']['unresolved_issues']=['UPSTREAM-OPEN-1']
        self.assertIn('UPSTREAM-OPEN-1',compute(doc)['unresolved_issues'])
    def test_scope_mismatch_stops(self):
        doc=copy.deepcopy(BASE)
        doc['workflow']['context']['object_id']='ANOTHER-CASE'
        with self.assertRaises(ValueError): compute(doc)
    def test_operational_tester_role_does_not_prove_independence(self):
        doc=copy.deepcopy(BASE)
        doc['workflow']['role']='independent_testing'
        set_claim(doc,doc['data']['test']['operational_involvement'],True)
        out=compute(doc)
        self.assertFalse(out['results']['supplied_independence_evidence_consistent'])
        self.assertIsNone(out['results']['within_supplied_acceptance_criterion'])
    def test_unobserved_selected_item_is_not_pass(self):
        doc=copy.deepcopy(BASE)
        doc['data']['observations'].pop()
        out=compute(doc)
        self.assertEqual(out['results']['unobserved_selected_items'],['ITEM-2'])
        self.assertIsNone(out['results']['within_supplied_acceptance_criterion'])
    def test_model_validation_keeps_its_owner(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['test']['mandate_type'],'model-validation')
        self.assertFalse(compute(doc)['results']['mandate_method_supported'])

    def test_malformed_claim_is_intake_error(self):
        doc=copy.deepcopy(BASE)
        for value in doc['data'].values():
            row=value[0] if isinstance(value,list) and value else value
            if not isinstance(row,dict): continue
            field=next((k for k,v in row.items() if isinstance(v,dict)),None)
            if field is not None:
                row[field]=['malformed-claim']; break
        self.assertTrue(validate(doc)[0])
        with self.assertRaises(ValueError): compute(doc)
    def test_expired_source_withholds_dependent_facts(self):
        doc=copy.deepcopy(BASE)
        doc['sources'][0]['expires_on']='2026-09-30'
        self.assertEqual(compute(doc)['status'],'needs-evidence')
    def test_control_and_test_period_bound_observations(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['observations'][0]['control_id'],'CONTROL-2')
        self.assertEqual(compute(doc)['results']['observed_results']['unknown'],1)
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['observations'][0]['performed_on'],'2026-09-30')
        self.assertIsNone(compute(doc)['results']['within_supplied_acceptance_criterion'])
    def test_failure_retained_when_tolerance_allows_sample(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['test']['maximum_failures'],1)
        set_claim(doc,doc['data']['observations'][0]['outcome'],'fail')
        out=compute(doc)
        self.assertTrue(out['results']['within_supplied_acceptance_criterion'])
        self.assertEqual(out['results']['observed_results']['fail'],1)
        self.assertIsNotNone(out['results']['observations'][0]['finding'])
if __name__=='__main__': unittest.main()
