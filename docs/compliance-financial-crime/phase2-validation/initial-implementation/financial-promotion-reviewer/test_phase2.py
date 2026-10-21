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
        self.assertTrue(out['results']['profile_method_supported'] is True and out['results']['approval_granted'] is False)
        self.assertEqual(out['status'],'draft-for-human-review')
        self.assertFalse(out['action_taken'])
        self.assertTrue(out['human_review_required'])
    def test_professional_failure_case(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['promotion']['profile_id'],'unsupported-sector-law-profile')
        out=compute(doc)
        self.assertTrue(out['results']['profile_method_supported'] is False)
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
        claim=doc['data']['promotion']['profile_id']
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
    def test_approval_binds_content_version(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['approval']['content_version'],'v0')
        out=compute(doc)
        self.assertFalse(out['results']['approval_scope_consistent'])
        self.assertFalse(out['results']['approval_granted'])
    def test_content_claim_and_visible_disclosure_need_evidence(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['claims'][0]['substantiation'],'Fees may vary.')
        set_claim(doc,doc['data']['disclosures'][0]['visible'],None)
        out=compute(doc)
        self.assertFalse(out['results']['claim_reviews'][0]['source_statement_matches'])
        self.assertTrue(out['results']['disclosure_reviews'][0]['review_issues'])

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
    def test_approval_exact_channel_and_use_period(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['approval']['channel'],'email')
        self.assertFalse(compute(doc)['results']['approval_scope_consistent'])
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['promotion']['use_to'],'2026-11-01')
        self.assertFalse(compute(doc)['results']['approval_scope_consistent'])
    def test_context_jurisdiction_and_source_profile_must_match(self):
        doc=copy.deepcopy(BASE)
        doc['workflow']['context']['jurisdiction']='US'
        self.assertFalse(compute(doc)['results']['profile_method_supported'])
if __name__=='__main__': unittest.main()
