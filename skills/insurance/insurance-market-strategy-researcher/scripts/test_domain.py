import copy
import json
from decimal import Decimal
from pathlib import Path
import unittest
from domain import evaluate, validate
from insurance_contract import build_artifact
from insurance_foundation import run, check_output
NAME = 'insurance-market-strategy-researcher'

class NativeTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1]/'evals/files/input.json').read_text())

    def calc(self):
        return run(self.doc, NAME, evaluate, validate)

    def test_source_bound_recomputation_and_no_action(self):
        output = self.calc()
        self.assertEqual(check_output(output, NAME, evaluate, validate), [])
        self.assertFalse(output['action_taken'])
        self.assertEqual(output['execution'], 'not_performed')
        output['results']['invented_decision'] = True
        output['artifact'] = build_artifact(self.doc, output, producer=NAME, artifact_type='insurance-workflow-review')
        self.assertTrue(check_output(output, NAME, evaluate, validate))

    def test_profile_scope_and_future_sources(self):
        self.doc['data']['profile']['jurisdictions'] = ['OTHER']
        self.assertEqual(self.calc()['status'], 'needs-data')
        self.setUp()
        self.doc['sources'][0]['as_of'] = '2026-09-19'
        self.assertEqual(self.calc()['status'], 'needs-data')

    def test_unresolved_input_and_duplicate_source_identity(self):
        self.doc['unresolved_issues'] = ['Conflicting raw record remains unresolved']
        self.assertIn('Conflicting raw record remains unresolved', self.calc()['unresolved_issues'])
        self.assertEqual(self.calc()['status'], 'needs-data')
        self.doc['sources'] *= 2
        with self.assertRaises(ValueError): self.calc()

    def test_full_market_shares_and_hhi(self):
        result = self.calc()['results']
        self.assertEqual(Decimal(result['market_hhi_10000']), Decimal('5200'))
        self.assertEqual(Decimal(result['competitor_shares'][0]['market_share']), Decimal('.4'))
        self.assertFalse(result['strategy_selected'])

    def test_partial_market_never_has_hhi(self):
        self.doc['data']['inventory_complete'] = False
        self.assertIsNone(self.calc()['results']['market_hhi_10000'])
        self.assertEqual(self.calc()['status'], 'needs-data')

    def test_mixed_period_and_unknown_value_do_not_enter_concentration(self):
        self.doc['data']['observations'][0]['period'] = '2024'
        self.assertIsNone(self.calc()['results']['competitor_shares'][0]['market_share'])
        self.assertIsNone(self.calc()['results']['market_hhi_10000'])
        self.setUp(); self.doc['data']['observations'][0]['value'] = None
        self.assertIsNone(self.calc()['results']['listed_value'])

    def test_denominator_conflict_and_zero(self):
        self.doc['data']['market_total']['value'] = '900'
        output = self.calc()
        self.assertIsNone(output['results']['market_hhi_10000'])
        self.assertTrue(any(f['code']=='market-total-conflict' for f in output['findings']))
        self.doc['data']['market_total']['value'] = '0'
        with self.assertRaises(ValueError): self.calc()

    def test_contrary_evidence_and_unknown_entities(self):
        self.doc['data']['claims'][0]['contrary_source_refs'] = ['SRC']
        self.assertEqual(self.calc()['status'], 'needs-review')
        self.doc['data']['claims'][0]['entity_ids'] = ['UNKNOWN']
        with self.assertRaises(ValueError): self.calc()

    def test_duplicate_competitor_and_boolean_amount(self):
        self.doc['data']['observations'].append(copy.deepcopy(self.doc['data']['observations'][0]))
        with self.assertRaises(ValueError): self.calc()
        self.setUp();self.doc['data']['observations'][0]['value'] = True
        with self.assertRaises(ValueError): self.calc()


if __name__ == "__main__":
    unittest.main()
