"""Adversarial evidence, policy and domain regressions; no operational actions."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import compute
from validate_input import validate as validate_input
from validate_output import validate as validate_output
from native_integrity import canonical_hash

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/ownership_example.json').read_text())
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
    def test_unrelated_control_does_not_satisfy_root(self):
        self.doc['control_edges'][0]['entity']='E-1'
        out=compute(self.doc); self.assertEqual([],out['control_persons']); self.assertEqual('Escalate',out['readiness'])
    def test_unqualified_control_type_does_not_satisfy_root(self):
        self.doc['control_edges'][0]['type']='unrelated_advisor'
        self.assertEqual([],compute(self.doc)['control_persons'])
    def test_document_dates_are_not_assumed_fresh(self):
        for d in self.doc['documents']: d.pop('issued'); d.pop('expires')
        self.assertTrue(any(g['type']=='expired_document' for g in compute(self.doc)['gaps']))
    def test_other_person_document_cannot_support_owner(self):
        self.doc['documents']=[d for d in self.doc['documents'] if d['subject']!='P-1']; self.doc['declared_ubos'][0]['doc_id']='D-2'
        self.assertTrue(any(g['type']=='missing_document' and g['subject']=='P-1' for g in compute(self.doc)['gaps']))
    def test_incomplete_root_graph_is_a_gap(self):
        self.doc['ownership_edges']=self.doc['ownership_edges'][1:]
        self.assertTrue(any(g['type']=='incomplete_ownership' for g in compute(self.doc)['gaps']))
    def test_rounding_does_not_cross_legal_threshold(self):
        self.doc['ownership_edges']=[dict(self.doc['ownership_edges'][0],pct=24.999999999)]
        person=next(o for o in compute(self.doc)['computed_owners'] if o['person_id']=='P-1')
        self.assertFalse(person['is_ubo'])
    def test_unsupported_voting_test_rejected(self):
        self.doc['config']['ownership_test']='voting-rights'; self.reject()
    def test_unsupported_trust_rejected(self):
        self.doc['nodes'][0]['structure_type']='trust'; self.reject()
    def test_duplicate_edge_rejected(self):
        self.doc['ownership_edges'].append(copy.deepcopy(self.doc['ownership_edges'][0])); self.reject()
    def test_control_target_person_rejected(self):
        self.doc['control_edges'][0]['entity']='P-1'; self.reject()
    def test_uncited_edge_rejected(self):
        self.doc['ownership_edges'][0].pop('source_ref'); self.reject()
    def test_cycle_is_escalated(self):
        self.doc['ownership_edges'].append({'owner':'E-ROOT','owned':'E-1','pct':10,'source_ref':'fixture:cycle'})
        self.assertTrue(any(g['type']=='circular_ownership' for g in compute(self.doc)['gaps']))

if __name__=='__main__': unittest.main()
