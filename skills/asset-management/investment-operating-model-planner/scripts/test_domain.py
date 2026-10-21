"""Independent literal expectations and adverse evidence cases; synthetic only."""
import copy
import json
from pathlib import Path
import unittest
from domain import compute
from foundation_contract import validate_result
from shared_operations import evaluate, validate
from workflow_foundation import run

FIXTURE = Path(__file__).resolve().parents[1] / 'evals/files/input.json'


class OperatingModelTests(unittest.TestCase):
    def setUp(self): self.doc = json.loads(FIXTURE.read_text())
    def test_literal_baseline_and_no_action(self):
        result = compute(self.doc)
        self.assertEqual(result['results']['operating_baseline']['queue_counts'],
                         {'opening': 1, 'arrivals': 2, 'completed': 2, 'cancelled': 0, 'closing': 1})
        self.assertEqual(result['results']['operating_baseline']['cost_per_completed'], '75')
        self.assertEqual(result['results']['dependency_order'], ['trade-confirmation'])
        self.assertTrue(result['results']['ready_for_owner_review'])
        self.assertFalse(result['results']['operating_change_authorized'])
        self.assertFalse(result['results']['staffing_change_authorized'])
    def test_maker_checker_gap(self):
        self.doc['controls'][0]['checker'] = self.doc['controls'][0]['maker']
        self.assertFalse(compute(self.doc)['results']['ready_for_owner_review'])
    def test_cycle(self):
        self.doc['services'][0]['depends_on'] = ['trade-confirmation']
        self.assertIsNone(compute(self.doc)['results']['dependency_order'])
    def test_missing_dependency(self):
        self.doc['services'][0]['depends_on'] = ['invented']
        self.assertIsNone(compute(self.doc)['results']['dependency_order'])
    def test_incomparable_population(self):
        self.doc['services'][0]['population'] = 'NAV'
        self.assertFalse(compute(self.doc)['results']['services'][0]['baseline_comparable'])
    def test_outsourcing_missing_rights(self):
        self.doc['services'][0]['delivery_model'] = 'outsourced'
        self.assertFalse(compute(self.doc)['results']['ready_for_owner_review'])
    def test_inventory_discrepancy(self):
        self.doc['service_inventory'].append('NAV')
        self.assertFalse(compute(self.doc)['results']['ready_for_owner_review'])
    def test_source_version_drift(self):
        self.doc['sources'][0]['version'] = 'different'
        with self.assertRaises(ValueError): compute(self.doc)
    def test_future_observation(self):
        self.doc['controls'][0]['tested_on'] = '2026-10-05'
        with self.assertRaises(ValueError): compute(self.doc)
    def test_control_version_drift(self):
        self.doc['controls'][0]['tested_version'] = 'old'
        self.assertFalse(compute(self.doc)['results']['ready_for_owner_review'])
    def test_unresolved_inherited(self):
        self.doc['unresolved_issues'] = ['Open provider incident']
        self.assertFalse(compute(self.doc)['results']['ready_for_owner_review'])
    def test_native_shared_issue_propagation(self):
        pair = self.doc['shared_reviews']['operations']
        pair['input']['unresolved_issues'] = ['Missing source records']
        pair['output'] = run(pair['input'], 'operations-performance-analyzer', evaluate, validate)
        out = compute(self.doc)
        self.assertIn('Missing source records', out['unresolved_issues'])
        self.assertFalse(out['results']['ready_for_owner_review'])
    def test_forged_shared_review(self):
        self.doc['shared_reviews']['operations']['output']['results']['cost_per_completed'] = '0'
        with self.assertRaises(ValueError): compute(self.doc)
    def test_changed_source_context(self):
        self.doc['shared_reviews']['operations']['input']['context']['object_id'] = 'other'
        with self.assertRaises(ValueError): compute(self.doc)
    def test_output_reconstruction(self):
        output = compute(self.doc)
        self.assertEqual(validate_result(output, self.doc, compute), [])
        output['results']['ready_for_owner_review'] = False
        self.assertTrue(validate_result(output, self.doc, compute))
    def test_boolean_exception_count(self):
        self.doc['transitions'][0]['open_exceptions'] = False
        with self.assertRaises(ValueError): compute(self.doc)


if __name__ == '__main__': unittest.main()
