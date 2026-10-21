"""Adversarial evidence, policy and domain regressions; no operational actions."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import compute
from validate_input import validate as validate_input
from validate_output import validate as validate_output
from native_integrity import canonical_hash

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/edd_case_example.json').read_text())
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
    def test_missing_risk_factors_is_unknown_not_low(self):
        self.doc.pop('risk_factors'); r=compute(self.doc)['sections']['residual_risk_assessment']
        self.assertEqual('Unknown',r['residual_risk_band']); self.assertIsNone(r['score'])
    def test_reported_gaps_prevent_present_and_readiness(self):
        self.doc['evidence']['source_of_wealth']['gaps']=['unexplained transfer']
        out=compute(self.doc); self.assertEqual('gap',out['sections']['source_of_wealth']['status']); self.assertEqual('needs-evidence',out['packaging_status'])
    def test_citations_without_item_mapping_are_insufficient(self):
        self.doc['evidence']['source_of_funds'].pop('item_evidence')
        self.assertEqual('needs-evidence',compute(self.doc)['packaging_status'])
    def test_invented_mapping_source_is_insufficient(self):
        self.doc['evidence']['source_of_funds']['item_evidence'][0]['source_ref']='made-up-source'
        self.assertEqual('needs-evidence',compute(self.doc)['packaging_status'])
    def test_assembled_is_not_adjudication_ready(self):
        self.assertEqual('assembled-for-human-review',compute(self.doc)['packaging_status'])
    def test_potential_sanctions_match_routes_and_blocks(self):
        self.doc['risk_factors']['sanctions_potential_match']=True
        out=compute(self.doc); self.assertEqual('blocked',out['packaging_status']); self.assertIn('sanctions-match-investigator',[r['skill'] for r in out['routes']])
    def test_string_match_flag_rejected(self):
        self.doc['risk_factors']['sanctions_true_match']='false'; self.reject()
    def test_approval_names_and_dates_do_not_establish_signoff(self):
        self.doc['recorded_approvals']=[{'role':self.doc['required_approvals'][0],'approver':'A','date':'2026-07-01'}]
        self.assertEqual('pending',compute(self.doc)['sections']['approvals']['ledger'][0]['status'])
    def test_evidenced_approval_remains_unverified(self):
        self.doc['recorded_approvals']=[{'role':self.doc['required_approvals'][0],'approver':'A','date':'2026-07-01','source_ref':'fixture:signoff','approval_ref':'fixture:authority'}]
        self.assertEqual('recorded-unverified',compute(self.doc)['sections']['approvals']['ledger'][0]['status'])
    def test_future_approval_remains_pending(self):
        self.doc['recorded_approvals']=[{'role':self.doc['required_approvals'][0],'approver':'A','date':'2027-07-01','source_ref':'fixture:signoff','approval_ref':'fixture:authority'}]
        self.assertEqual('pending',compute(self.doc)['sections']['approvals']['ledger'][0]['status'])
    def test_recommendation_does_not_invent_cadence(self):
        rec=compute(self.doc)['sections']['recommendation']; self.assertNotIn('6-month',str(rec)); self.assertEqual('human-assessment-required',rec['recommended_review_path'])
    def test_missing_trigger_reference_is_a_gap(self):
        self.doc.pop('trigger_source_ref'); self.assertIn('edd_trigger_scope',compute(self.doc)['gaps'])

if __name__=='__main__': unittest.main()
