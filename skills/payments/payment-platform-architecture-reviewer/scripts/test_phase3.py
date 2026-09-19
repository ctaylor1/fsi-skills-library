import json
from pathlib import Path
import unittest
import resilience_domain as domain
from payment_contract import stable_hash
from payment_foundation import build, validate_output, validate_request


class ResilienceTests(unittest.TestCase):
    def setUp(self): self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/resilience.json').read_text())
    def run_doc(self): return build(self.doc,domain)
    def codes(self): return {r['code'] for r in self.run_doc()['findings']}
    def rebind(self,row): row['inspection']['scope_hash']=stable_hash(domain.artifact_scope(row))
    def test_complete_native_artifacts_draft_only(self):
        out=self.run_doc();self.assertEqual(out['status'],'draft');self.assertTrue(all(r['evidence_satisfied'] for r in out['result']['negative_path_coverage']));self.assertFalse(out['result']['go_live_authorized'])
    def test_pointer_or_pass_flag_not_test(self):
        self.doc['data']['test_artifacts'][0]['steps']=[];self.assertIn('unsupported-pass-claim',self.codes())
    def test_missing_negative_path(self):
        self.doc['data']['test_artifacts'].pop();self.assertIn('negative-path-unresolved',self.codes())
    def test_old_release_not_current(self):
        row=self.doc['data']['test_artifacts'][0];row['release_version']='old';self.rebind(row);self.assertEqual(self.run_doc()['status'],'needs-evidence')
    def test_different_mode_not_current(self):
        row=self.doc['data']['test_artifacts'][0];row['mode']='hub';self.rebind(row);self.assertEqual(self.run_doc()['status'],'needs-evidence')
    def test_scope_tamper_invalidates_review(self):
        self.doc['data']['test_artifacts'][0]['component_scope'].append('new');self.assertIn('test-evidence-gap',self.codes())
    def test_duplicate_effect_fails(self):
        row=self.doc['data']['test_artifacts'][0];row['observations']['financial_effect_count']=2;self.rebind(row);self.assertEqual(self.run_doc()['status'],'needs-evidence')
    def test_boolean_not_integer_effect_count(self):
        row=self.doc['data']['test_artifacts'][0];row['observations']['financial_effect_count']=True;self.rebind(row);self.assertEqual(self.run_doc()['status'],'needs-evidence')
    def test_missing_fence_fails(self):
        self.doc['data']['controls']['fenced_financial_writes']=False;self.assertIn('writer-ownership-gap',self.codes())
    def test_silent_payload_overwrite_fails(self):
        self.doc['data']['controls']['payload_conflict_behavior']='overwrite';self.assertIn('payload-conflict-gap',self.codes())
    def test_blind_retry_design_fails(self):
        self.doc['data']['controls']['uncertain_outcome_strategy']='retry-new-key';self.assertIn('uncertain-money-gap',self.codes())
    def test_partition_two_writers_fails(self):
        self.doc['data']['controls']['partition_policy']='both-keep-writing';self.assertIn('partition-policy-gap',self.codes())
    def test_rollback_settlement_fails(self):
        self.doc['data']['migration']['rollback_mode']='reverse-settled-payments';self.assertIn('rollback-unsafe',self.codes())
    def test_future_review_fails(self):
        self.doc['data']['test_artifacts'][0]['inspection']['reviewed_on']='2027-01-01';self.assertIn('test-evidence-gap',self.codes())
    def test_duplicate_artifact_fails(self):
        self.doc['data']['test_artifacts'].append(self.doc['data']['test_artifacts'][0]);self.assertIn('test-evidence-gap',self.codes())
    def test_each_failed_invariant_remains_gap(self):
        for row in self.doc['data']['test_artifacts']:
            key=next(iter(row['observations']));row['observations'][key]=None;self.rebind(row)
        self.assertFalse(any(r['evidence_satisfied'] for r in self.run_doc()['result']['negative_path_coverage']))
    def test_observation_change_without_reinspection(self):
        self.doc['data']['test_artifacts'][0]['steps'][0]['observed']='changed';self.assertIn('test-evidence-gap',self.codes())
    def test_all_modes_are_scoped(self):
        for mode in domain.MODES:
            self.doc['data']['design']['mode']=mode
            for row in self.doc['data']['test_artifacts']: row['mode']=mode;self.rebind(row)
            self.assertEqual(self.run_doc()['status'],'draft')
    def test_upstream_issue_survives(self):
        self.doc['upstream_issues']=[{'code':'unresolved-money','message':'Open ledger break'}];self.assertEqual(self.run_doc()['status'],'needs-evidence')
    def test_output_cannot_approve(self):
        out=self.run_doc();out['result']['go_live_authorized']=True;self.assertTrue(validate_output(out,domain,self.doc))
    def test_execute_rejected(self):
        self.doc['requested_action']='execute';self.assertTrue(validate_request(self.doc,domain))

if __name__=='__main__': unittest.main()
