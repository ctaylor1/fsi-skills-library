import json
from decimal import Decimal
from pathlib import Path
import unittest
from domain import evaluate, validate
from insurance_contract import build_artifact
from insurance_foundation import run, check_output
NAME = 'insurance-product-economics-modeler'

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

    def test_carrier_bridge_and_mga_revenue_distinct(self):
        carrier, mga = self.calc()['results']['scenarios']
        self.assertEqual(Decimal(carrier['underwriting_result']), Decimal('190'))
        self.assertEqual(Decimal(carrier['period_pre_tax_result']), Decimal('210'))
        self.assertEqual(Decimal(carrier['gross_combined_ratio']), Decimal('.8'))
        self.assertEqual(Decimal(carrier['period_return_on_allocated_capital']), Decimal('.42'))
        self.assertEqual(Decimal(mga['agency_revenue']), Decimal('350'))
        self.assertEqual(Decimal(mga['agency_operating_result']), Decimal('130'))

    def test_unknown_ceded_recovery_is_not_zero(self):
        self.doc['data']['scenarios'][0]['ceded_recoveries'] = None
        row = self.calc()['results']['scenarios'][0]
        self.assertIsNone(row['financial_result'])
        self.assertNotIn('underwriting_result', row)

    def test_mga_hybrid_and_bad_commission_reject_or_withhold(self):
        self.doc['data']['scenarios'][1]['bears_underwriting_risk'] = True
        self.assertIsNone(self.calc()['results']['scenarios'][1]['financial_result'])
        self.doc['data']['scenarios'][1]['commission_rate'] = '1.1'
        with self.assertRaises(ValueError): self.calc()

    def test_currency_and_loss_basis_separate(self):
        for field, val in [('currency','EUR'),('risk_basis','net_retained'),('loss_basis','paid')]:
            self.setUp(); self.doc['data']['scenarios'][0][field] = val
            self.assertIsNone(self.calc()['results']['scenarios'][0]['financial_result'])

    def test_written_expense_denominator_not_silently_earned(self):
        self.doc['data']['scenarios'][0]['expense_denominator'] = 'written_premium'
        result=self.calc()['results']['scenarios'][0]
        self.assertEqual(Decimal(result['gross_expense_ratio']), Decimal(200)/Decimal(1100))
        self.assertEqual(Decimal(result['underwriting_result']), Decimal('190'))

    def test_negative_money_and_nonfinite_reject(self):
        for val in [-1,True,'NaN']:
            self.doc['data']['scenarios'][0]['earned_premium'] = val
            with self.assertRaises(ValueError): self.calc()

    def test_zero_capital_is_undefined_not_zero_return(self):
        self.doc['data']['scenarios'][0]['allocated_capital'] = 0
        self.assertIsNone(self.calc()['results']['scenarios'][0]['period_return_on_allocated_capital'])


if __name__ == "__main__":
    unittest.main()
