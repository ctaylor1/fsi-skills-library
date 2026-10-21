"""Independent numerical expectations and adverse evidence/control regressions."""
import copy
import json
from pathlib import Path
import unittest
from decimal import Context, localcontext
from domain import compute, validate
from foundation_contract import validate_result
from workflow_foundation import run
import shared_automation


class Native(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).parents[1] / 'evals/files/input.json').read_text())

    def result(self):
        return compute(self.doc)

    def withheld(self):
        out = self.result()
        self.assertEqual(out['status'], 'needs-review', out)
        self.assertFalse(out['results']['review_candidate'])
        self.assertFalse(out['action_taken'])
        return out['results']['evaluation']

    def rejected(self):
        self.assertTrue(validate(self.doc))

    def refresh_shared(self):
        pair = self.doc['shared_reviews']['automation']
        pair['output'] = run(pair['input'], 'workflow-automation-assessor', shared_automation.evaluate, shared_automation.validate)

    def test_native_roundtrip(self):
        out = self.result()
        self.assertEqual(validate_result(out, self.doc, compute), [])
        self.assertTrue(out['results']['review_candidate'])
        self.assertEqual(out['results']['evidence_kind'], 'synthetic-fixture')

    def test_no_authority(self):
        out = self.result()
        self.assertFalse(out['results']['deployment_authorized'])
        self.assertFalse(out['results']['model_or_tool_invoked'])
        self.assertFalse(out['results']['source_and_label_independence_authenticated'])
        self.assertEqual(out['results']['permission_verification'], 'not-authenticated-by-offline-review')

    def test_source_immutable(self):
        original = copy.deepcopy(self.doc)
        self.result()
        self.assertEqual(self.doc, original)

    def test_independent_numerical_expectations(self):
        r = self.result()['results']['evaluation']
        self.assertEqual(r['confirmed_correct_count'], 6)
        self.assertEqual(r['timeout_count'], 1)
        self.assertEqual(r['timeout_rate_among_observed'], '0.166666666667')
        self.assertEqual(r['total_observed_episode_cost'], '2.1')
        self.assertEqual(r['mean_cost_per_observed_episode'], '0.350000000000')
        self.assertEqual(r['mean_latency_ms'], '350.000000000000')
        self.assertEqual(r['p95_latency_ms_nearest_rank'], '600')

    def test_shared_economics_native(self):
        r = self.result()['results']['automation_assessment']['results']
        self.assertEqual(r['human_minutes_saved_per_case'], '13')
        self.assertEqual(r['scenarios'][0]['annual_cash_net'], '26500.00')

    def test_shared_uncertainty_propagates(self):
        self.doc['shared_reviews']['automation']['input']['data']['controls'][0]['status'] = 'failed'
        self.refresh_shared()
        self.withheld()

    def test_shared_tamper(self):
        self.doc['shared_reviews']['automation']['output']['results']['pilot_candidate'] = False
        self.rejected()

    def test_shared_detached_input_required(self):
        del self.doc['shared_reviews']['automation']['input']
        self.rejected()

    def test_shared_object_mismatch(self):
        self.doc['shared_reviews']['automation']['input']['context']['object_id'] = 'OTHER'
        self.refresh_shared()
        self.rejected()

    def test_rehash_tampering_rejected(self):
        out = self.result()
        out['results']['evaluation']['confirmed_correct_count'] = 600
        self.assertTrue(validate_result(out, self.doc, compute))

    def test_output_requires_detached_input(self):
        self.assertTrue(validate_result(self.result(), None, compute))

    def test_manifest_leakage(self):
        self.doc['experiment']['training_case_ids'].append('CASE-1')
        self.rejected()

    def test_unknown_training_inventory(self):
        self.doc['experiment']['training_case_ids'] = None
        self.rejected()

    def test_duplicate_episode_case(self):
        self.doc['episodes'][1]['case_id'] = 'CASE-1'
        self.rejected()

    def test_foreign_episode_case(self):
        self.doc['episodes'][0]['case_id'] = 'UNLISTED'
        self.rejected()

    def test_missing_case_manifest(self):
        self.doc['test_cases'].pop()
        self.rejected()

    def test_missing_episode_retains_denominator(self):
        self.doc['episodes'].pop()
        r = self.withheld()
        self.assertEqual(r['requested_heldout_count'], 6)
        self.assertEqual(r['observed_episode_count'], 5)
        self.assertEqual(r['confirmed_correct_fraction_of_requested'], '0.833333333333')
        self.assertEqual(r['missing_case_ids'], ['CASE-6'])

    def test_no_episodes_is_unknown(self):
        self.doc['episodes'] = []
        r = self.withheld()
        self.assertEqual(r['episode_coverage'], '0.000000000000')
        self.assertIsNone(r['timeout_rate_among_observed'])
        self.assertIsNone(r['total_observed_episode_cost'])
        self.assertIsNone(r['mean_latency_ms'])

    def test_unknown_label_not_zero_error(self):
        self.doc['episodes'][0]['observed_label'] = None
        r = self.withheld()
        self.assertEqual(r['unknown_label_count'], 1)
        self.assertEqual(r['observed_label_count'], 5)
        self.assertEqual(r['confirmed_correct_count'], 5)

    def test_wrong_label(self):
        self.doc['episodes'][0]['observed_label'] = 'abstain'
        r = self.withheld()
        self.assertEqual(r['label_error_count'], 1)
        self.assertEqual(r['label_error_rate_among_known'], '0.166666666667')

    def test_versions_pinned(self):
        self.doc['episodes'][0]['versions']['model'] = 'new-model'
        self.rejected()

    def test_latest_model_not_pinned(self):
        self.doc['workflow']['versions']['model'] = 'latest'
        self.rejected()

    def test_snapshot_pinned(self):
        self.doc['datasets'][0]['snapshot_id'] = 'other-snapshot'
        self.rejected()

    def test_training_label_reviewer_separate(self):
        self.doc['experiment']['label_reviewer_id'] = self.doc['workflow']['executor_id']
        self.rejected()

    def test_label_source_separate(self):
        self.doc['episodes'][0]['source_ref'] = 'expected-labels'
        self.rejected()

    def test_future_labels(self):
        self.doc['test_cases'][0]['label_known_on'] = '2026-10-05'
        self.rejected()

    def test_historical_episode_cannot_use_later_known_dataset(self):
        self.doc['test_cases'][0]['label_known_on'] = '2026-10-03'
        self.doc['episodes'][0]['observed_on'] = '2026-10-03'
        self.rejected()

    def test_historical_episode_cannot_use_future_valid_dataset(self):
        self.doc['datasets'][0]['known_on'] = '2026-10-02'
        self.doc['test_cases'][0]['label_known_on'] = '2026-10-02'
        self.doc['episodes'][0]['observed_on'] = '2026-10-02'
        self.rejected()

    def test_historical_episode_requires_then_effective_license(self):
        self.doc['datasets'][0]['known_on'] = '2026-10-03'
        self.doc['datasets'][0]['license_valid_from'] = '2026-10-04'
        self.doc['test_cases'][0]['label_known_on'] = '2026-10-03'
        self.doc['episodes'][0]['observed_on'] = '2026-10-03'
        self.rejected()

    def test_retrospective_export_can_describe_valid_historical_episode(self):
        self.doc['datasets'][0]['known_on'] = '2026-10-03'
        self.doc['test_cases'][0]['label_known_on'] = '2026-10-03'
        self.doc['episodes'][0]['observed_on'] = '2026-10-03'
        self.assertTrue(self.result()['results']['review_candidate'])

    def test_unregistered_label_source(self):
        self.doc['test_cases'][0]['label_source_ref'] = 'unknown-labels'
        self.rejected()

    def test_rights_expired(self):
        self.doc['datasets'][0]['license_valid_to'] = '2026-10-03'
        self.doc['datasets'][0]['known_on'] = '2026-10-03'
        for case in self.doc['test_cases']:
            case['label_known_on'] = '2026-10-03'
        for episode in self.doc['episodes']:
            episode['observed_on'] = '2026-10-03'
        self.withheld()

    def test_license_purpose_unavailable(self):
        self.doc['datasets'][0]['permitted_purposes'] = ['index-calculation']
        self.withheld()

    def test_entitlement_not_granted(self):
        self.doc['datasets'][0]['permitted_principals'] = ['different-principal']
        self.withheld()

    def test_case_crosses_dataset_scope(self):
        self.doc['datasets'][0]['portfolio_ids'] = []
        self.rejected()

    def test_case_crosses_tenant(self):
        self.doc['test_cases'][0]['tenant_id'] = 'OTHER'
        self.rejected()

    def test_episode_crosses_portfolio(self):
        self.doc['episodes'][0]['portfolio_ids'] = ['OTHER']
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_tool_crosses_client(self):
        self.doc['episodes'][0]['tool_calls'][0]['client_ids'] = ['UNPERMITTED']
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_tool_unknown_denied_safely(self):
        out = self.result()
        observed = out['results']['evaluation']['observations'][2]
        self.assertTrue(observed['failed_closed'])
        self.assertFalse(observed['unsafe_observation'])

    def test_tool_unknown_executed(self):
        self.doc['episodes'][0]['tool_calls'][0]['tool_id'] = 'unknown'
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_tool_version_mismatch(self):
        self.doc['episodes'][0]['tool_calls'][0]['version'] = '2'
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_tool_write_effect(self):
        self.doc['episodes'][0]['tool_calls'][0]['effect'] = 'write'
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_tool_message_effect(self):
        self.doc['episodes'][0]['tool_calls'][0]['effect'] = 'message'
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_denied_but_read(self):
        self.doc['episodes'][2]['tool_calls'][0]['effect'] = 'read'
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_injection_followed(self):
        self.doc['episodes'][1]['injected_instructions_followed'] = True
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_timeout_not_stopped(self):
        self.doc['episodes'][3]['stopped'] = False
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_timeout_answered(self):
        self.doc['episodes'][3]['observed_label'] = 'answer'
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_tool_timeout_counted_even_without_episode_flag(self):
        self.doc['episodes'][3]['timed_out'] = False
        self.assertEqual(self.result()['results']['evaluation']['timeout_count'], 1)

    def test_runtime_error_denominator(self):
        self.doc['episodes'][3]['tool_calls'][0]['status'] = 'error'
        self.assertEqual(self.result()['results']['evaluation']['runtime_error_rate_among_observed'], '0.166666666667')

    def test_retry_limit(self):
        self.doc['episodes'][0]['attempts'] = 3
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_fractional_attempts_invalid(self):
        self.doc['episodes'][0]['attempts'] = '1.5'
        self.rejected()

    def test_latency_limit_failclosed(self):
        self.doc['episodes'][0]['latency_ms'] = 1001
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_cost_limit_failclosed(self):
        self.doc['episodes'][0]['cost'] = '1.01'
        self.assertEqual(self.withheld()['unsafe_episode_count'], 1)

    def test_unknown_cost_keeps_full_cost_unknown(self):
        self.doc['episodes'][0]['cost'] = None
        r = self.withheld()
        self.assertEqual(r['known_cost_count'], 5)
        self.assertEqual(r['known_cost_sum'], '2.0')
        self.assertIsNone(r['total_observed_episode_cost'])
        self.assertIsNone(r['mean_cost_per_observed_episode'])

    def test_unknown_latency_keeps_mean_unknown(self):
        self.doc['episodes'][0]['latency_ms'] = None
        r = self.withheld()
        self.assertEqual(r['known_latency_count'], 5)
        self.assertIsNone(r['mean_latency_ms'])
        self.assertIsNone(r['p95_latency_ms_nearest_rank'])

    def test_bool_cost_invalid(self):
        self.doc['episodes'][0]['cost'] = False
        self.rejected()

    def test_nonfinite_cost_invalid(self):
        self.doc['episodes'][0]['cost'] = 'NaN'
        self.rejected()

    def test_unrepresentable_precision_rejected(self):
        self.doc['episodes'][0]['cost'] = '0.' + '1' * 39
        self.rejected()

    def test_currency_mismatch(self):
        self.doc['episodes'][0]['currency'] = 'EUR'
        self.rejected()

    def test_mutating_allowlist_invalid(self):
        self.doc['tools'][0]['allowed_actions'].append('trade-order')
        self.rejected()

    def test_missing_denied_action(self):
        self.doc['workflow']['denied_actions'].pop()
        self.rejected()

    def test_risk_coverage_not_pretended(self):
        self.doc['test_cases'][-1]['risk_case'] = 'normal'
        self.withheld()

    def test_source_known_after_cutoff(self):
        self.doc['sources'][0]['known_at'] = '2026-10-05'
        self.rejected()

    def test_explicit_unresolved_blocks_candidate(self):
        self.doc['unresolved_issues'] = ['Runtime evidence is incomplete']
        self.withheld()

    def test_shared_decimal_context_isolation(self):
        baseline = self.result()
        with localcontext(Context(prec=9)):
            self.assertEqual(self.result(), baseline)


if __name__ == '__main__':
    unittest.main()
