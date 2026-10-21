"""Independent expected examples for the bounded AM data adapter."""
import copy
import json
from pathlib import Path
import unittest

from domain import compute
from validate_input import validate as validate_input
from validate_output import validate as validate_output
from native_integrity import canonical_hash
from workflow_foundation import run
import shared_architecture
import shared_data_value

FIXTURE = Path(__file__).resolve().parents[1] / 'evals/files/request.json'


class DataArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text())

    def resolved(self):
        return compute(self.doc)['results']['resolved_sample']

    def test_late_correction_preserves_then_known_value(self):
        self.assertEqual([x['value'] for x in self.resolved()], ['100.25', '101.75'])

    def test_correction_boundary_is_half_open(self):
        self.doc['queries'][0]['known_on'] = '2026-09-19'
        rows = self.resolved()
        self.assertEqual(rows[0]['record_ids'], ['original'])
        self.assertEqual(rows[1]['record_ids'], ['late-correction'])

    def test_ambiguous_history_never_chooses_latest(self):
        self.doc['history'][0]['known_to'] = None
        rows = self.resolved()
        self.assertEqual(rows[0]['value'], '100.25')
        self.assertIsNone(rows[1]['value'])
        self.assertEqual(rows[1]['status'], 'withheld')
        self.assertIn('ambiguous active history', rows[1]['issues'])

    def test_valid_end_is_exclusive(self):
        self.doc['queries'][0]['valid_on'] = '2026-09-02'
        self.assertIsNone(self.resolved()[0]['value'])

    def test_missing_historical_knowledge_is_not_zero(self):
        self.doc['queries'][0]['known_on'] = '2026-09-01'
        self.assertIsNone(self.resolved()[0]['value'])

    def test_source_future_knowledge_rejected(self):
        self.doc['sources'][0]['known_at'] = '2026-10-05'
        self.assertTrue(validate_input(self.doc))

    def test_record_claim_later_than_source_capture_rejected(self):
        self.doc['history'][0]['known_to'] = '2026-10-05'
        self.assertTrue(validate_input(self.doc))

    def test_currency_mismatch_rejected(self):
        self.doc['history'][0]['currency'] = 'EUR'
        self.assertTrue(validate_input(self.doc))

    def test_unit_mismatch_rejected(self):
        self.doc['history'][0]['unit'] = 'percent'
        self.assertTrue(validate_input(self.doc))

    def test_missing_grain_cannot_aggregate(self):
        self.doc['queries'][0]['dimensions'].pop('account')
        self.assertTrue(validate_input(self.doc))

    def test_namespaces_prevent_false_join(self):
        identity = copy.deepcopy(self.doc['identities'][0])
        identity.update(identity_id='security-other', namespace='DIFFERENT-VENDOR')
        self.doc['identities'].append(identity)
        self.doc['queries'][0]['dimensions']['security'] = 'security-other'
        self.assertIsNone(self.resolved()[0]['value'])

    def test_same_namespaced_identity_under_new_id_rejected(self):
        identity = copy.deepcopy(self.doc['identities'][0])
        identity['identity_id'] = 'different-id-same-security'
        self.doc['identities'].append(identity)
        self.assertTrue(validate_input(self.doc))

    def test_denied_access_withholds_sample(self):
        self.doc['permission_observations'][0]['decision'] = 'denied'
        self.assertTrue(all(r['value'] is None for r in self.resolved()))

    def test_permission_for_other_principal_withheld(self):
        self.doc['permission_observations'][0]['principal'] = 'someone-else'
        self.assertTrue(all(r['value'] is None for r in self.resolved()))

    def test_old_permission_withheld(self):
        self.doc['permission_observations'][0]['observed_on'] = '2026-10-03'
        self.assertTrue(all(r['value'] is None for r in self.resolved()))

    def test_wrong_license_purpose_withheld(self):
        self.doc['licenses'][0]['purposes'] = ['trade-execution']
        self.assertTrue(all(r['value'] is None for r in self.resolved()))

    def test_expired_license_withheld(self):
        self.doc['licenses'][0]['effective_to'] = '2026-10-03'
        self.assertTrue(all(r['value'] is None for r in self.resolved()))

    def test_unproven_access_not_authenticated(self):
        output = compute(self.doc)
        self.assertFalse(output['results']['permission_verified'])
        self.assertFalse(output['results']['source_authentication'])
        self.assertFalse(output['action_taken'])
        self.assertEqual(output['source_truth'], 'unverified')
        self.assertEqual(output['results']['access_evidence'][0]['evidence_status'], 'declared-allowed-unverified')

    def test_projected_monitor_is_not_observed(self):
        self.doc['monitors'][0]['basis'] = 'projected'
        result = compute(self.doc)
        monitor = result['results']['observability'][0]
        self.assertIsNone(monitor['meets'])
        self.assertIsNone(monitor['observed_value'])
        self.assertEqual(monitor['projected_value'], '7')
        self.assertEqual(result['status'], 'needs-review')

    def test_measured_breach_retained(self):
        self.doc['monitors'][0]['value'] = '16'
        result = compute(self.doc)
        self.assertFalse(result['results']['observability'][0]['meets'])
        self.assertEqual(result['status'], 'needs-review')

    def test_monitor_snapshot_binding(self):
        self.doc['monitors'][0]['snapshot_id'] = 'different-snapshot'
        self.assertTrue(validate_input(self.doc))

    def test_missing_source_locator_rejected(self):
        self.doc['sources'][0].pop('locator')
        self.assertTrue(validate_input(self.doc))

    def test_restricted_source_does_not_leak(self):
        self.doc['sources'][0]['permitted_audiences'] = ['external-client']
        self.assertTrue(validate_input(self.doc))

    def test_shared_fabrication_rejected(self):
        self.doc['shared_reviews']['architecture']['output']['results']['supplied_period_cost'] = '0'
        self.assertTrue(validate_input(self.doc))

    def test_shared_detached_scope_change_rejected(self):
        pair = self.doc['shared_reviews']['architecture']
        pair['input']['context']['object_id'] = 'DIFFERENT-PORTFOLIO'
        pair['output'] = run(pair['input'], 'solution-architecture-planner', shared_architecture.evaluate, shared_architecture.validate)
        self.assertTrue(validate_input(self.doc))

    def test_shared_review_gap_propagates(self):
        pair = self.doc['shared_reviews']['architecture']
        pair['input']['data']['measurements'] = []
        pair['output'] = run(pair['input'], 'solution-architecture-planner', shared_architecture.evaluate, shared_architecture.validate)
        result = compute(self.doc)
        self.assertEqual(result['status'], 'needs-review')
        self.assertTrue(all(r['value'] is None for r in result['results']['resolved_sample']))

    def test_output_requires_detached_original(self):
        self.assertTrue(validate_output(compute(self.doc)))

    def test_rehashed_result_cannot_forge_authentication(self):
        result = compute(self.doc)
        result['results']['permission_verified'] = True
        result['input_hash'] = canonical_hash(self.doc)
        self.assertTrue(validate_output(result, self.doc))

    def test_detached_source_change_is_detected(self):
        result = compute(self.doc)
        self.doc['history'][0]['value'] = '999'
        self.assertTrue(validate_output(result, self.doc))

    def test_bool_and_nonfinite_prices_rejected(self):
        for value in (True, 'NaN', 'Infinity'):
            self.doc['history'][0]['value'] = value
            self.assertTrue(validate_input(self.doc))

    def test_empty_history_not_reported_complete(self):
        self.doc['history'] = []
        self.assertTrue(validate_input(self.doc))

    def test_original_bound_output_valid(self):
        self.assertEqual(validate_output(compute(self.doc), self.doc), [])

    def test_optional_data_value_native_result(self):
        doc = json.loads((FIXTURE.parent / 'request_data_value.json').read_text())
        result = compute(doc)['results']['shared_reviews'][1]
        self.assertEqual(result['producer'], 'data-product-value-evaluator')
        self.assertEqual(result['results']['observed_outcome_cost_reduction'], '110')
        self.assertEqual(result['results']['projected_annual_net'], '40000')
        self.assertFalse(result['results']['causal_uplift_established'])

    def test_optional_data_value_wrong_purpose_rejected(self):
        doc = json.loads((FIXTURE.parent / 'request_data_value.json').read_text())
        pair = doc['shared_reviews']['data_value']
        pair['input']['data']['purpose'] = 'different-purpose'
        pair['input']['data']['license']['purpose'] = 'different-purpose'
        pair['output'] = run(pair['input'], 'data-product-value-evaluator', shared_data_value.evaluate, shared_data_value.validate)
        self.assertTrue(validate_input(doc))


if __name__ == '__main__':
    unittest.main()
