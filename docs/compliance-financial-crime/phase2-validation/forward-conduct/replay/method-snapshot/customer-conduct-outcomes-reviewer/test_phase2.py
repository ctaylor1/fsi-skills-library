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
        self.assertTrue(out['results']['cohort_metrics'][0]['observed_harm_rate'] == 0)
        self.assertEqual(out['status'],'draft-for-human-review')
        self.assertFalse(out['action_taken'])
        self.assertTrue(out['human_review_required'])
    def test_professional_failure_case(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['cohorts'][0]['observed'],None)
        out=compute(doc)
        self.assertTrue(out['results']['cohort_metrics'][0]['observed_harm_rate'] is None)
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
        claim=doc['data']['cohorts'][0]['observed']
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
    def test_missing_vulnerable_segment_is_unresolved(self):
        doc=copy.deepcopy(BASE)
        doc['data']['cohorts'].pop()
        out=compute(doc)
        self.assertEqual(out['results']['missing_expected_cohorts'],['vulnerable-observed'])
        self.assertEqual(out['status'],'needs-evidence')
    def test_zero_denominator_is_not_zero_harm_rate(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['cohorts'][0]['observed'],0)
        self.assertIsNone(compute(doc)['results']['cohort_metrics'][0]['observed_harm_rate'])
    def test_impossible_denominator_stops_intake(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['cohorts'][0]['harms'],101)
        with self.assertRaises(ValueError): compute(doc)

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
    def test_missing_metric_definition_withholds_rate(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['review']['denominator_definition'],None)
        out=compute(doc)
        self.assertFalse(out['results']['metric_definition_evidence_consistent'])
        self.assertIsNone(out['results']['cohort_metrics'][0]['observed_harm_rate'])
    def test_event_numerator_and_customer_denominator_withhold_rate(self):
        doc=copy.deepcopy(BASE)
        set_claim(doc,doc['data']['review']['numerator_unit'],'events')
        out=compute(doc)
        self.assertFalse(out['results']['metric_definition_evidence_consistent'])
        self.assertTrue(all(c['observed_harm_rate'] is None for c in out['results']['cohort_metrics']))
    def test_missing_units_are_unknown_not_inferred_from_descriptions(self):
        doc=copy.deepcopy(BASE)
        for key in ('population_unit','numerator_unit','denominator_unit'): del doc['data']['review'][key]
        out=compute(doc)
        self.assertEqual(validate(doc)[0],[])
        self.assertFalse(out['results']['metric_definition_evidence_consistent'])
        self.assertEqual(out['status'],'needs-evidence')
    def test_exact_rate_threshold_is_not_rounded_into_acceptance(self):
        doc=copy.deepcopy(BASE); row=doc['data']['cohorts'][0]
        set_claim(doc,row['population'],3);set_claim(doc,row['observed'],3);set_claim(doc,row['harms'],1)
        set_claim(doc,row['threshold_rate'],0.3333333333333333)
        self.assertFalse(compute(doc)['results']['cohort_metrics'][0]['within_supplied_harm_criterion'])

if __name__=='__main__': unittest.main()
