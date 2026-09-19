import json
from decimal import Decimal
from pathlib import Path
import unittest
from domain import evaluate, validate
from insurance_contract import build_artifact
from insurance_foundation import run, check_output
NAME = 'insurance-portfolio-performance-analyzer'

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

    def test_weighted_ratios_and_mix_bridge(self):
        result=self.calc()['results']; a,b=result['period_totals'];bridge=result['loss_ratio_bridge']
        self.assertEqual(Decimal(b['loss_ratio']),Decimal('.75'))
        self.assertEqual(Decimal(b['severity']),Decimal('60'))
        self.assertEqual(Decimal(bridge['loss_ratio_change']),Decimal('0'))
        self.assertEqual(Decimal(bridge['mix_effect']),Decimal('-.125'))
        self.assertEqual(Decimal(bridge['within_segment_effect']),Decimal('.125'))
        self.assertEqual(Decimal(bridge['rounding_residual']),Decimal('0'))

    def test_new_segment_not_imputed(self):
        self.doc['data']['segments'][-1]['segment_id']='C'
        self.assertIsNone(self.calc()['results']['loss_ratio_bridge'])

    def test_missing_and_incomplete_inventory_withhold_totals(self):
        self.doc['data']['segments'][0]['incurred_loss_lae']=None
        self.assertIsNone(self.calc()['results']['period_totals'][0]['loss_ratio'])
        self.setUp(); self.doc['data']['segment_inventory_complete']=False
        self.assertIsNone(self.calc()['results']['period_totals'][0]['earned_premium'])

    def test_mixed_risk_basis_withholds(self):
        self.doc['data']['segments'][0]['risk_basis']='net_retained'
        self.assertIsNone(self.calc()['results']['period_totals'][0]['loss_ratio'])

    def test_period_overlap_or_unequal_length_not_compared(self):
        for field,val in [('start','2025-08-01'),('end','2026-08-30')]:
            self.setUp();self.doc['data']['periods'][1][field]=val
            self.assertIsNone(self.calc()['results']['loss_ratio_bridge'])

    def test_duplicate_segment_and_fractional_count(self):
        self.doc['data']['segments'][1]['segment_id']='A'
        with self.assertRaises(ValueError):self.calc()
        self.setUp();self.doc['data']['segments'][0]['claim_count']='1.5'
        with self.assertRaises(ValueError):self.calc()

    def test_zero_premium_and_signed_calendar_loss(self):
        self.doc['data']['segments'][0]['earned_premium']=0
        self.assertIsNone(self.calc()['results']['loss_ratio_bridge'])
        self.setUp();self.doc['data']['segments'][0]['incurred_loss_lae']='-100'
        self.assertEqual(Decimal(self.calc()['results']['segments'][0]['loss_ratio']),Decimal('-.1'))


if __name__ == "__main__":
    unittest.main()
