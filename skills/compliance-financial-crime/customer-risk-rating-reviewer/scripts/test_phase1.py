"""Adversarial evidence, policy and domain regressions; no operational actions."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import compute
from validate_input import validate as validate_input
from validate_output import validate as validate_output
from native_integrity import canonical_hash

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/risk_case_example.json').read_text())
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
    def fresh(self):
        for f in self.doc['factors']: f['observed_date']=self.doc['as_of']
        self.doc['overrides']=[]; self.doc['trigger_events']=[]
    def test_missing_required_factor_withholds_band(self):
        self.fresh(); self.doc['factors']=self.doc['factors'][1:]
        out=compute(self.doc); self.assertIsNone(out['score_pct']); self.assertIsNone(out['recommended_band'])
    def test_missing_optional_factor_does_not_shrink_denominator(self):
        self.fresh(); self.doc['factors']=self.doc['factors'][:-1]
        self.assertIsNone(compute(self.doc)['score_pct'])
    def test_arbitrary_input_weight_rejected(self):
        self.doc['factors'][0]['weight']=999; self.reject()
    def test_out_of_scale_factor_rejected(self):
        self.doc['factors'][0]['risk_value']=6; self.reject()
    def test_duplicate_factor_rejected(self):
        self.doc['factors'].append(copy.deepcopy(self.doc['factors'][0])); self.reject()
    def test_stale_data_cannot_align(self):
        self.doc['overrides']=[];self.doc['trigger_events']=[]
        out=compute(self.doc); self.assertEqual('Remediate-Data-First',out['recommended_review_outcome']); self.assertIsNone(out['recommended_band'])
    def test_future_factor_is_unknown(self):
        self.fresh(); self.doc['factors'][0]['observed_date']='2027-01-01'
        self.assertIsNone(compute(self.doc)['recommended_band'])
    def test_prohibited_risk_band_rejected(self):
        self.doc['config']['band_order'][-1]='Prohibited'; self.doc['config']['band_thresholds'][-1]['band']='Prohibited'; self.reject()
    def test_missing_override_expiry_requires_review(self):
        self.fresh(); self.doc['overrides']=[{'from_band':'High','to_band':'Low','rationale':'test','approver_role':'MLRO','approved_date':'2026-07-01','source_ref':'fixture:override','approval_ref':'fixture:approval'}]
        self.assertEqual('Escalate-For-Adjudication',compute(self.doc)['recommended_review_outcome'])
    def test_documented_override_explains_difference_but_not_approval(self):
        self.fresh(); band=compute(self.doc)['recommended_band']
        self.doc['overrides']=[{'from_band':band,'to_band':'Low','rationale':'test','approver_role':'MLRO','approved_date':'2026-07-01','expiry_date':'2026-08-01','source_ref':'fixture:override','approval_ref':'fixture:approval'}]
        out=compute(self.doc); self.assertNotIn('rating_discrepancy',[f['type'] for f in out['findings']]); self.assertIn('documented_override',[f['type'] for f in out['findings']])
    def test_assessed_flag_without_record_does_not_dispose_trigger(self):
        self.doc['trigger_events'][0]['assessed']=True
        self.assertIn('unassessed_trigger',[f['type'] for f in compute(self.doc)['findings']])
    def test_partial_methodology_rejected(self):
        self.doc['config'].pop('factor_catalog'); self.reject()

if __name__=='__main__': unittest.main()
