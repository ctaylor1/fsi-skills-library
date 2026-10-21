"""Adversarial evidence, policy and domain regressions; no operational actions."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import compute
from validate_input import validate as validate_input
from validate_output import validate as validate_output
from native_integrity import canonical_hash

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/case_example.json').read_text())
    def reject(self):
        self.assertTrue(validate_input(self.doc)[0])
        with self.assertRaises(ValueError): compute(self.doc)
    def test_golden_round_trip(self):
        output=compute(self.doc)
        self.assertEqual([],validate_output(output,self.doc))
        self.assertEqual('unverified',output['source_truth'])
        self.assertNotIn('source_input',output)
    def test_detached_source_is_mandatory(self):
        self.assertTrue(validate_output(compute(self.doc)))
    def test_rehashed_fabricated_output_is_rejected(self):
        output=compute(self.doc); output['adjudication_required']=False; output['input_hash']=canonical_hash(self.doc)
        self.assertTrue(validate_output(output,self.doc))
    def test_added_decision_is_rejected(self):
        output=compute(self.doc); output['narrative']='Customer approved. Case closed. SAR filed.'
        self.assertTrue(validate_output(output,self.doc))
    def test_raw_source_embedding_is_rejected(self):
        output=compute(self.doc); output['source_input']=self.doc
        self.assertTrue(validate_output(output,self.doc))
    def test_changed_detached_input_is_rejected(self):
        output=compute(self.doc); self.doc['unrelated_source_note']='changed'
        self.assertTrue(validate_output(output,self.doc))
    def test_source_authentication_claim_is_rejected(self):
        output=compute(self.doc); output['source_truth']='verified'
        self.assertTrue(validate_output(output,self.doc))
    def test_missing_policy_is_rejected(self):
        self.doc.pop('policy_profile'); self.reject()
    def test_fixture_policy_cannot_be_used_for_review(self):
        self.doc['execution_context']='review'; self.reject()
    def test_expired_policy_is_rejected(self):
        self.doc['policy_profile']['review_due_date']='2025-01-01'; self.reject()
    def test_nonfinite_input_is_rejected(self):
        self.doc['unrelated_value']=float('nan'); self.reject()
    def test_invalid_calendar_date_is_rejected(self):
        key='as_of_date' if 'as_of_date' in self.doc else 'as_of'; self.doc[key]='2026-02-30'; self.reject()
    def test_missing_screening_is_not_clean(self):
        self.doc.pop('screening_hits'); out=compute(self.doc)
        self.assertEqual('Needs-Data',out['recommended_track'])
        self.assertTrue(any(s['signal']=='sanctions_potential_match' for s in out['not_evaluable']))
    def test_empty_hits_without_coverage_is_not_clean(self):
        self.doc['screening_hits']={k:[] for k in self.doc['screening_hits']}; self.doc.pop('screening_coverage')
        self.assertEqual('Needs-Data',compute(self.doc)['recommended_track'])
    def test_expired_screening_is_unknown(self):
        self.doc['screening_coverage']['sanctions']['as_of']='2020-01-01'
        self.assertEqual('Needs-Data',compute(self.doc)['recommended_track'])
    def test_unrelated_verified_document_does_not_establish_identity(self):
        self.doc['documents']=[self.doc['documents'][1]]
        self.assertIn('unverified_identity',compute(self.doc)['fired_signals'])
    def test_string_verification_is_rejected(self):
        self.doc['documents'][0]['verified']='false'; self.reject()
    def test_missing_owners_is_unknown(self):
        self.doc['beneficial_owners']=[]
        self.assertEqual('Needs-Data',compute(self.doc)['recommended_track'])
    def test_missing_identity_checks_is_unknown(self):
        self.doc.pop('identity_checks')
        self.assertEqual('Needs-Data',compute(self.doc)['recommended_track'])
    def test_missing_country_is_unknown(self):
        self.doc['customer'].pop('country')
        self.assertEqual('Needs-Data',compute(self.doc)['recommended_track'])
    def test_negative_ownership_is_rejected(self):
        self.doc['beneficial_owners'][0]['ownership_pct']=-1; self.reject()
    def test_partial_config_is_rejected(self):
        self.doc['config'].pop('high_risk_countries'); self.reject()
    def test_pep_does_not_route_to_sanctions(self):
        out=compute(self.doc)
        self.assertFalse(any('sanctions-match-investigator' in x for x in out['recommended_next_steps']))
    def test_sanctions_route_retains_unknowns(self):
        self.doc['screening_hits']['sanctions']=[{'source_ref':'fixture:potential'}]; self.doc.pop('screening_coverage')
        out=compute(self.doc); self.assertEqual('Escalate-For-Adjudication',out['recommended_track']); self.assertTrue(out['not_evaluable'])

if __name__=='__main__': unittest.main()
