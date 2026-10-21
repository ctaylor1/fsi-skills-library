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
        self.assertTrue(out['results']['engagement_reviews'][0]['amount_to_benchmark_ratio'] == '1.000000000000')
        self.assertEqual(out['status'],'draft-for-human-review')
        self.assertFalse(out['action_taken'])
        self.assertTrue(out['human_review_required'])
    def test_professional_failure_case(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['engagements'][0]['policy_applies'],None)
        out=compute(doc)
        self.assertTrue(out['results']['engagement_reviews'][0]['within_supplied_criterion'] is None)
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
        claim=doc['data']['engagements'][0]['policy_applies']
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
    def test_payment_and_benchmark_currency_cannot_be_mixed(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['engagements'][0]['benchmark_currency'],'EUR')
        self.assertIsNone(compute(doc)['results']['engagement_reviews'][0]['amount_to_benchmark_ratio'])
    def test_official_link_does_not_mean_guilt(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['engagements'][0]['government_link'],True)
        out=compute(doc)
        self.assertEqual(out['results']['engagement_reviews'][0]['legal_guilt_determination'],'not-performed')
        self.assertFalse(out['results']['engagement_reviews'][0]['payment_approved'])
        self.assertEqual(out['status'],'needs-evidence')

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
if __name__=='__main__': unittest.main()
