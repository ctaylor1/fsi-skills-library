import json
from pathlib import Path
import unittest
from copy import deepcopy
from decimal import Decimal
import domain
from payment_foundation import build, validate_request, validate_output

class EconomicsTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((Path(__file__).resolve().parents[1] / 'evals/files/request.json').read_text())
    def run_model(self):
        return build(self.request, domain)
    def test_volume_and_adoption_tie(self):
        r = self.run_model()['result']
        self.assertEqual(Decimal(r['baseline']['expected_successes']), Decimal('9500'))
        self.assertEqual(Decimal(r['scenario']['expected_successes']), Decimal('9480'))
        self.assertEqual(sum(Decimal(x['attempts']) for x in r['scenario']['method_economics']), Decimal('10000'))
        self.assertEqual(Decimal(r['incremental_contribution']), Decimal('1201.6'))
        self.assertNotEqual(r['scenario']['cost_per_attempt'],r['scenario']['cost_per_success'])
    def test_break_even_reconciles(self):
        r = self.run_model()['result']
        breakeven = r['break_even']
        self.assertEqual(breakeven['state'], 'within-feasible-range')
        self.assertEqual(Decimal(breakeven['incremental_fixed_contribution']), Decimal('-100'))
        self.request['data']['scenario']['adoption_rate'] = breakeven['adoption_rate']
        self.assertLess(abs(Decimal(self.run_model()['result']['incremental_contribution'])), Decimal('1e-30'))
    def test_unknown_rate_propagates(self):
        self.request['data']['methods'][1]['components'][0]['rate'] = None
        r = self.run_model()
        self.assertIsNone(r['result']['scenario']['cost'])
        self.assertIsNone(r['result']['incremental_contribution'])
        self.assertEqual(r['status'], 'needs-evidence')
    def test_missing_category_not_zero(self):
        self.request['data']['methods'][1]['components'] = [x for x in self.request['data']['methods'][1]['components'] if x['category'] != 'fraud_loss']
        self.assertIsNone(self.run_model()['result']['scenario']['contribution'])
    def test_unknown_success_does_not_imply_zero(self):
        self.request['data']['methods'][1]['success_rate'] = None
        self.assertIsNone(self.run_model()['result']['scenario']['expected_successes'])
    def test_zero_success_denominator_unknown(self):
        for m in self.request['data']['methods']:
            m['success_rate'] = '0'
        self.assertIsNone(self.run_model()['result']['scenario']['cost_per_success'])
    def test_overlap_rejected(self):
        c = self.request['data']['methods'][0]['components']
        c[1]['coverage_keys'] = c[0]['coverage_keys']
        self.assertTrue(validate_request(self.request, domain))
    def test_mixed_currency_rejected(self):
        self.request['data']['methods'][0]['components'][0]['currency'] = 'EUR'
        self.assertTrue(validate_request(self.request, domain))
    def test_period_mismatch_rejected(self):
        self.request['data']['methods'][0]['components'][0]['period'] = 'annual'
        self.assertTrue(validate_request(self.request, domain))
    def test_overdisplacement_rejected(self):
        self.request['data']['scenario']['adoption_rate'] = '1.1'
        self.assertTrue(validate_request(self.request, domain))
    def test_nonfinite_rejected(self):
        self.request['data']['methods'][0]['components'][0]['rate'] = 'Infinity'
        self.assertTrue(validate_request(self.request, domain))
    def test_participant_side_different(self):
        self.request['data']['perspective'] = 'issuer'
        self.assertTrue(validate_request(self.request, domain))
    def test_fixed_charges_remain_at_zero_adoption(self):
        self.request['data']['scenario']['adoption_rate'] = '0'
        self.assertEqual(Decimal(self.run_model()['result']['incremental_contribution']), Decimal('-100'))
    def test_tampered_economics_rejected(self):
        output = self.run_model()
        output['result']['incremental_contribution'] = '999999'
        self.assertTrue(validate_output(output, domain))
    def test_external_input_source_binding(self):
        output = self.run_model()
        other = deepcopy(self.request)
        other['data']['attempts'] = '5000'
        self.assertTrue(validate_output(output, domain, other))
    def test_each_participant_uses_distinct_revenue_and_costs(self):
        for participant in ('issuer', 'acquirer', 'psp', 'bank'):
            with self.subTest(participant=participant):
                self.setUp()
                self.request['participant'] = participant
                self.request['data']['perspective'] = participant
                for method in self.request['data']['methods']:
                    terms = []
                    for category in sorted(domain.REQUIRED[participant]):
                        terms.append({'component_id':category, 'category':category,
                            'side':'revenue' if category in domain.REVENUES[participant] else 'cost',
                            'basis':'per_success', 'rate':'0.5' if category in domain.REVENUES[participant] else '0.01',
                            'coverage_keys':[category], 'currency':'USD', 'period':'monthly',
                            'assumption_id':'pricing', 'source_ids':['diligence']})
                    method['components'] = terms
                self.assertFalse(validate_request(self.request, domain))
                self.assertIsNotNone(self.run_model()['result']['scenario']['contribution'])
    def test_zero_baseline_share_rejected(self):
        self.request['data']['baseline_mix'][0]['share'] = '0'
        self.assertTrue(validate_request(self.request, domain))
    def test_no_positive_success_uplift_is_invented(self):
        self.request['data']['methods'][1]['success_rate'] = '0.5'
        r = self.run_model()['result']
        self.assertLess(Decimal(r['incremental_contribution']), Decimal(0))
        self.assertEqual(r['break_even']['state'], 'outside-feasible-range')
    def test_feasible_capacity_and_sensitivity(self):
        old = deepcopy(self.request['data']['methods'][0])
        old['method_id'] = 'debit'
        self.request['data']['methods'].append(old)
        self.request['data']['baseline_mix'] = [{'method_id':'card','share':'0.3'}, {'method_id':'debit','share':'0.7'}]
        r = self.run_model()['result']
        self.assertEqual(r['break_even']['max_feasible_adoption'], '0.3')
        self.assertEqual(r['sensitivity'][-1]['state'], 'infeasible-displacement')
        self.request['data']['scenario']['adoption_rate'] = '0.4'
        self.assertTrue(validate_request(self.request, domain))
    def test_execution_blocked(self):
        self.request['requested_action'] = 'execute'
        self.assertTrue(validate_request(self.request, domain))

if __name__ == '__main__':
    unittest.main()
