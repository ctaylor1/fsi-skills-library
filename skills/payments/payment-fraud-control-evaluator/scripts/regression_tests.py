"""Strategy, multi-rule, maturity and authority boundary regressions."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest
import domain
from payment_foundation import build, validate_request, validate_output


class Tests(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/request.json').read_text())
    def out(self):return build(self.doc,domain)
    def replay(self,which=1):return self.out()['result']['portfolio_replay'][which]
    def metric(self,which=1):return self.replay(which)['currency_metrics'][0]
    def codes(self):return {f['code'] for f in self.out()['findings']}
    def invalid(self):self.assertTrue(validate_request(self.doc,domain))
    def test_rule_overlap_not_double_block(self):
        m=self.metric();self.assertEqual(m['action_counts']['block'],3);self.assertEqual(self.replay()['pairwise_overlaps'],[{'rule_ids':['R2','R3'],'transactions':1}])
    def test_review_is_not_block(self):
        self.assertEqual(self.metric()['confusion_by_mature_label']['legit'],{'block':1,'review':1,'allow':1})
    def test_value_weighted_exposure(self):
        self.assertEqual(self.metric()['observed_mature_fraud_value_by_replayed_action']['block'],'600');self.assertEqual(self.metric(0)['observed_mature_fraud_value_by_replayed_action']['allow'],'100')
    def test_friction_separate_from_loss(self):
        m=self.metric();self.assertEqual(m['modeled_review_cost'],'2');self.assertEqual(m['modeled_mature_legitimate_block_friction_cost'],'5');self.assertIsNone(self.out()['result']['causal_avoided_loss'])
    def test_pending_label_excluded(self):
        t=self.doc['data']['transactions'][0];t['label']='pending';t['observed_net_fraud_loss']=None;m=self.metric();self.assertEqual(m['mature_evaluable_size'],4);self.assertEqual(m['observed_mature_fraud_value_by_replayed_action']['block'],'100')
    def test_late_maturity_excluded(self):
        self.doc['data']['transactions'][0]['maturity_due']='2026-10-01';self.assertEqual(self.metric()['mature_evaluable_size'],4);self.assertIn('immature-labels',self.codes())
    def test_early_legit_observation_not_mature(self):
        self.doc['data']['transactions'][2]['label_observed_on']='2026-08-01';self.assertEqual(self.metric()['mature_evaluable_size'],4)
    def test_future_labels_quarantine(self):
        self.doc['data']['transactions'][0]['label_observed_on']='2026-09-19';self.assertTrue(self.out()['result']['replay_quarantined'])
    def test_hindsight_feature_quarantine(self):
        self.doc['data']['transactions'][0]['features_observed_on']='2026-07-11';self.assertIn('feature-leakage',self.codes());self.assertEqual(self.out()['result']['portfolio_replay'],[])
    def test_missing_feature_unknown(self):
        self.doc['data']['transactions'][0]['features'].pop('velocity');self.assertEqual(self.replay()['rows'][0]['replayed_action'],'unknown');self.assertIn('missing-rule-feature',self.codes())
    def test_null_feature_unknown(self):
        self.doc['data']['transactions'][0]['features']['velocity']=None;self.assertEqual(self.replay()['rows'][0]['replayed_action'],'unknown')
    def test_duplicate_transaction_rejected(self):
        self.doc['data']['transactions'].append(deepcopy(self.doc['data']['transactions'][0]));self.invalid()
    def test_duplicate_rules_rejected(self):
        self.doc['data']['rules'].append(deepcopy(self.doc['data']['rules'][0]));self.invalid()
    def test_unknown_portfolio_rule_rejected(self):
        self.doc['data']['portfolios']['proposed'].append('UNKNOWN');self.invalid()
    def test_unsupported_predicate_rejected(self):
        self.doc['data']['rules'][0]['op']='eval';self.invalid()
    def test_missing_cost_unknown(self):
        self.doc['data']['friction_costs'][0]['per_review']=None;self.assertIsNone(self.metric()['modeled_review_cost']);self.assertIn('friction-assumptions-gap',self.codes())
    def test_missing_loss_not_zero(self):
        self.doc['data']['transactions'][0]['observed_net_fraud_loss']=None;self.assertIsNone(self.metric()['observed_net_fraud_loss_by_replayed_action']['block'])
    def test_currency_separation(self):
        self.doc['data']['transactions'][0]['currency']='USD';self.assertEqual(len(self.replay()['currency_metrics']),2);self.assertIn('friction-assumptions-gap',self.codes())
    def test_false_positive_guardrail(self):
        self.assertEqual(self.metric()['guardrails'][1]['state'],'outside-supplied-appetite')
    def test_no_threshold_default(self):
        self.doc['data']['risk_appetite'].pop('max_review_rate');self.assertEqual(self.metric()['guardrails'][0]['state'],'unknown')
    def test_strategy_coverage_gap(self):
        self.doc['data']['controls'].pop();self.assertIn('threat-coverage-gap',self.codes());self.assertEqual(self.out()['result']['strategy_coverage'][0]['uncovered_kinds'],['responsive'])
    def test_strategy_only(self):
        self.doc['data']['mode']='strategy'
        for k in ('transactions','rules','portfolios'):self.doc['data'].pop(k)
        self.assertEqual(self.out()['result']['portfolio_replay'],[]);self.assertFalse(self.out()['result']['strategy_coverage'][0]['effectiveness_established'])
    def test_strategy_does_not_ignore_portfolio(self):
        self.doc['data']['mode']='strategy';self.invalid()
    def test_unknown_threat_rejected(self):
        self.doc['data']['controls'][0]['threat_ids']=['missing'];self.invalid()
    def test_negative_cost_rejected(self):
        self.doc['data']['friction_costs'][0]['per_review']='-1';self.invalid()
    def test_nan_rejected(self):
        self.doc['data']['rules'][0]['threshold']='NaN';self.invalid()
    def test_nonfraud_loss_conflict(self):
        self.doc['data']['transactions'][2]['observed_net_fraud_loss']='1';self.invalid()
    def test_upstream_issue_preserved(self):
        self.doc['upstream_issues']=[{'code':'biased-sample','message':'Unrepresentative sample','source_ids':['S1']}];self.assertIn('upstream:biased-sample',self.codes());self.assertEqual(self.out()['status'],'needs-evidence')
    def test_unknown_source_rejected(self):
        self.doc['data']['rules'][0]['source_ids']=['UNKNOWN'];self.invalid()
    def test_stale_source_gap(self):
        self.doc['sources'][0]['review_due']='2026-09-17';self.assertIn('stale-source',self.codes())
    def test_secret_rejected(self):
        self.doc['data']['transactions'][0]['pin']='1234';self.invalid()
    def test_execution_rejected(self):
        self.doc['requested_action']='deploy';self.invalid()
    def test_tampered_replay_rejected(self):
        out=self.out();out['result']['portfolio_replay'][0]['rows'][0]['replayed_action']='allow';self.assertTrue(validate_output(out,domain,self.doc))
    def test_tampered_authority_rejected(self):
        out=self.out();out['authority_granted']=True;self.assertTrue(validate_output(out,domain,self.doc))
    def test_external_source_binding(self):
        out=self.out();self.doc['request_id']='other';self.assertTrue(validate_output(out,domain,self.doc))
    def test_unsupported_region(self):
        self.doc['jurisdiction']='CA';self.assertEqual(self.out()['status'],'unsupported')
    def test_legacy_kernel_retained(self):
        path=Path(__file__).resolve().parent/'legacy/calculate_or_transform.py'
        r=subprocess.run([sys.executable,'-B',str(path),'--selftest'],capture_output=True,text=True,check=True)
        out=json.loads(r.stdout);self.assertEqual((out['blocked_now'],out['blocked_proposed']),(2,4));self.assertEqual(out['confusion_delta']['caught_fraud'],1)
    def test_legacy_invalid_output_rejected(self):
        root=Path(__file__).resolve().parents[1]
        r=subprocess.run([sys.executable,'-B',str(root/'scripts/legacy/validate_output.py'),str(root/'evals/files/estimate_bad.json')],capture_output=True,text=True)
        self.assertEqual(r.returncode,1);self.assertIn('deployment/live-decision',r.stdout)

    def test_review_guardrail_unknown_bound(self):
        self.doc['data']['risk_appetite']['max_review_rate']='0.3'
        self.doc['data']['transactions'][0]['features']['velocity']=None
        self.assertEqual(self.metric()['guardrails'][0]['state'],'unknown')
        self.assertEqual(self.metric()['review_rate_upper_bound'],'0.4')
    def test_excluded_value_visible(self):
        self.doc['data']['transactions'][0]['maturity_due']='2026-10-01'
        self.assertEqual(self.metric()['excluded_immature_or_unknown_feature_face_value'],'500')

if __name__=='__main__':unittest.main()
