"""Financial basis, denominator, partition and authority regressions."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
import domain
from payment_foundation import build, validate_request, validate_output


class BusinessTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / 'evals/files/request.json').read_text())
        self.segment = self.doc['data']['segments'][0]

    def result(self):
        return build(self.doc, domain)

    def gap(self, code):
        self.assertIn(code, [f['code'] for f in self.result()['findings']])

    def test_gross_bridge(self):
        r = self.result()['result']['segments'][0]
        self.assertEqual(r['net_revenue'], '70000')
        self.assertEqual(r['net_take_rate_bps'], '70.000')
        self.assertEqual(r['contribution_before_fixed'], '40000')
        self.assertEqual(r['contribution_after_allocated_fixed'], '25000')

    def test_comparison(self):
        self.assertEqual(self.result()['result']['comparisons'][0]['left_minus_right_net_take_rate_bps'], '10.000')

    def test_already_net_not_twice(self):
        r = self.doc['data']['segments'][1]
        r['pass_through'] = '10000'
        r['incentives'] = '5000'
        self.assertEqual(self.result()['result']['segments'][1]['net_revenue'], '60000')

    def test_unknown_gross_reduction(self):
        self.segment['pass_through'] = None
        self.gap('unknown-revenue-bridge')
        self.assertIsNone(self.result()['result']['segments'][0]['net_revenue'])

    def test_net_reconciliation(self):
        self.segment['reported_net_revenue'] = '80000'
        self.gap('net-revenue-reconciliation')
        self.assertIsNone(self.result()['result']['segments'][0]['net_take_rate_bps'])

    def test_net_mode_bridge_conflict(self):
        self.segment['revenue_basis'] = 'net-revenue'
        self.segment['gross_billings'] = '260000'
        self.gap('net-revenue-reconciliation')

    def test_unknown_net(self):
        self.doc['data']['segments'][1]['reported_net_revenue'] = None
        self.gap('unknown-net-revenue')

    def test_negative_net_preserved(self):
        self.segment['reported_net_revenue'] = '-10000'
        self.segment['gross_billings'] = '170000'
        self.assertEqual(self.result()['result']['segments'][0]['net_revenue'], '-10000')
        self.assertEqual(self.result()['result']['segments'][0]['contribution_before_fixed'], '-40000')

    def test_zero_denominator(self):
        self.segment['payment_volume'] = '0'
        self.gap('take-rate-denominator')
        self.assertIsNone(self.result()['result']['segments'][0]['net_take_rate_bps'])

    def test_transaction_count_denominator(self):
        self.segment['volume_unit'] = 'transaction-count'
        self.gap('take-rate-denominator')
        self.assertIsNone(self.result()['result']['segments'][0]['net_take_rate_bps'])

    def test_unknown_denominator(self):
        self.segment['payment_volume'] = None
        self.gap('take-rate-denominator')

    def test_incomplete_costs(self):
        self.segment['costs_complete'] = False
        self.gap('unknown-contribution')
        self.assertIsNone(self.result()['result']['segments'][0]['contribution_before_fixed'])

    def test_unknown_fixed(self):
        self.segment['allocated_fixed_cost'] = None
        self.gap('unknown-fixed-cost-result')

    def test_negative_contribution(self):
        self.segment['variable_cost'] = '100000'
        self.assertEqual(self.result()['result']['segments'][0]['contribution_before_fixed'], '-30000')

    def test_duplicate_id(self):
        self.doc['data']['segments'].append(deepcopy(self.segment))
        self.assertTrue(validate_request(self.doc, domain))

    def test_overlapping_partition(self):
        dup = deepcopy(self.segment)
        dup['segment_id'] = 'A-duplicate'
        self.doc['data']['segments'].append(dup)
        self.gap('overlapping-economic-partition')
        self.assertIsNone(self.result()['result']['segments'][0]['net_revenue'])

    def test_nonoverlapping_period(self):
        dup = deepcopy(self.segment)
        dup.update(segment_id='A-prior',period_start='2025-07-01',period_end='2025-12-31')
        self.doc['data']['segments'].append(dup)
        self.assertNotIn('overlapping-economic-partition',[f['code'] for f in self.result()['findings']])

    def test_future_actuals(self):
        self.segment['period_end'] = '2026-12-31'
        self.gap('future-reported-period')

    def test_unknown_company(self):
        self.segment['company_id'] = 'missing-company'
        self.gap('unknown-company')

    def test_different_currency(self):
        self.segment['currency'] = 'EUR'
        self.gap('noncomparable-segments')
        self.assertIsNone(self.result()['result']['comparisons'][0]['left_minus_right_net_take_rate_bps'])
        self.assertIsNone(self.result()['result']['cross_currency_total'])

    def test_different_period(self):
        self.segment['period_start'] = '2026-04-01'
        self.gap('noncomparable-segments')

    def test_different_denominator_definition(self):
        self.segment['volume_definition'] = 'transaction count'
        self.gap('noncomparable-segments')

    def test_no_accounting_review(self):
        self.doc['data']['comparisons'][0].pop('accounting_comparability_review_ref')
        self.gap('noncomparable-segments')

    def test_unknown_comparison_segment(self):
        self.doc['data']['comparisons'][0]['left_segment'] = 'missing'
        self.gap('noncomparable-segments')

    def test_unknown_option_segment(self):
        self.doc['data']['strategic_options'][0]['segment_ids'] = ['missing']
        self.gap('option-unknown-segment')

    def test_required_monetization(self):
        self.doc['data']['companies'][0].pop('monetization')
        self.assertTrue(validate_request(self.doc, domain))

    def test_boolean_money(self):
        self.segment['gross_billings'] = True
        self.assertTrue(validate_request(self.doc, domain))

    def test_upstream(self):
        self.doc['upstream_issues'] = [{'code':'source-unaudited','message':'Source completeness unconfirmed','source_ids':['case']}]
        self.gap('upstream:source-unaudited')

    def test_unsupported(self):
        self.doc['jurisdiction'] = 'XX'
        self.assertEqual(self.result()['status'], 'unsupported')

    def test_no_execute(self):
        self.doc['requested_action'] = 'place-trade'
        self.assertTrue(validate_request(self.doc, domain))

    def test_tampered_take_rate(self):
        r = self.result()
        r['result']['segments'][0]['net_take_rate_bps'] = '999'
        self.assertTrue(validate_output(r, domain, self.doc))

    def test_independent_input(self):
        r = self.result()
        self.segment['payment_volume'] = '5000'
        self.assertTrue(validate_output(r, domain, self.doc))

    def test_authority(self):
        r = self.result()
        self.assertFalse(r['authority_granted'])
        self.assertFalse(r['result']['securities_recommendation'])
        self.assertFalse(r['result']['strategy_approved'])
        self.assertTrue(all(not o['approved'] for o in r['result']['strategic_options']))


if __name__ == '__main__':
    unittest.main()
