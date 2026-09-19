"""Financial identities and independent expected-value/adverse lending scenarios."""
import json
import unittest
from copy import deepcopy
from pathlib import Path

from domain import build, schedule, validate, validate_output
from wealth_workflow import dec


class LendingTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / 'evals/files/request.json').read_text())

    def codes(self, doc=None):
        return {f['code'] for f in build(doc or self.doc)['findings']}

    def loan(self):
        return self.doc['loan_options'][0]

    def projected(self, index=0):
        return build(self.doc)['result']['loan_alternatives'][0]['scenarios'][index]

    def test_golden_independent_financial_values(self):
        out = build(self.doc)
        self.assertEqual(out['status'], 'review-ready')
        self.assertEqual(validate_output(out), [])
        self.assertEqual([r['net_proceeds'] for r in out['result']['liquidity_alternatives']], ['150000.00', '194500.00'])
        loan = out['result']['loan_alternatives'][0]
        self.assertEqual(loan['new_net_proceeds'], '199000.00')
        self.assertEqual(loan['opening_total_principal'], '250000.00')
        self.assertEqual([r['borrowing_base'] for r in loan['scenarios']], ['480000.00', '300000.00'])
        self.assertEqual([r['loan_projection']['horizon_financing_cost'] for r in loan['scenarios']], ['16120.00', '21120.04'])
        self.assertIsNone(out['result']['selected_option'])
        self.assertFalse(out['action_taken'])

    def test_monthly_principal_and_interest_identity(self):
        for result in build(self.doc)['result']['loan_alternatives'][0]['scenarios']:
            for row in result['loan_projection']['months']:
                self.assertEqual(dec(row['opening_principal']) - dec(row['scheduled_principal']) - dec(row['balloon_principal']), dec(row['ending_principal']))
                self.assertEqual(dec(row['interest']) + dec(row['scheduled_principal']) + dec(row['balloon_principal']) + dec(row['fee']), dec(row['total_payment']))

    def test_zero_interest_amortization(self):
        result = schedule(dec(12000), dec(0), 12, 12, 'amortizing', dec(0))
        self.assertEqual(result['ending_principal'], '0.00')
        self.assertEqual(result['principal_repaid'], '12000.00')
        self.assertEqual(result['total_interest'], '0.00')
        self.assertTrue(all(r['total_payment'] == '1000.00' for r in result['months']))

    def test_two_period_positive_rate_amortization(self):
        result = schedule(dec(2010), dec(12), 2, 2, 'amortizing', dec(0))
        self.assertEqual([r['total_payment'] for r in result['months']], ['1020.10', '1020.10'])
        self.assertEqual([r['interest'] for r in result['months']], ['20.10', '10.10'])
        self.assertEqual(result['total_interest'], '30.20')
        self.assertEqual(result['ending_principal'], '0.00')

    def test_interest_only_balloon_and_no_double_principal(self):
        self.loan()['term_months'] = 12
        self.loan()['maturity_funding'] = '200000.00'
        p = self.projected()['loan_projection']
        self.assertEqual(p['ending_principal'], '0.00')
        self.assertEqual(p['balloon_within_horizon'], '250000.00')
        self.assertEqual(p['maximum_budgeted_service'], '1260.00')
        self.assertEqual(p['maturity_funding_gap'], '50000.00')
        self.assertIn('maturity-funding-gap', self.codes())

    def test_fixed_rate_and_cap_floor_stresses(self):
        self.loan()['rate_type'] = 'fixed'
        self.assertEqual(self.projected(1)['annual_rate_pct'], '6')
        self.loan()['rate_type'] = 'floating'; self.loan()['rate_cap_pct'] = '7'
        self.assertEqual(self.projected(1)['annual_rate_pct'], '7')
        self.doc['scenarios'][0]['rate_shock_bps'] = -900
        self.assertEqual(self.projected(1)['annual_rate_pct'], '2')
        self.loan()['rate_floor_pct'] = None
        self.assertIsNone(self.projected(1)['loan_projection'])
        self.assertIn('unsupported-rate', self.codes())

    def test_collateral_haircut_capacity_and_nonpurpose_use(self):
        self.doc['scenarios'][0]['collateral_price_change_pct'] = -50
        row = self.projected(1)
        self.assertEqual(row['borrowing_base'], '200000.00')
        self.assertEqual(row['maintenance_paydown_illustration'], '50000.00')
        self.assertIn('borrowing-capacity-gap', self.codes())
        self.doc['funding_need']['purpose_category'] = 'securities-purchase'
        self.assertIn('use-of-proceeds-review', self.codes())

    def test_origination_only_does_not_create_maintenance_call(self):
        self.loan().update(type='property-secured', collateral_test='origination-only')
        self.doc['scenarios'][0]['collateral_price_change_pct'] = -75
        self.assertIsNone(self.projected(1)['maintenance_paydown_illustration'])
        self.assertEqual(self.projected(1)['debt_over_capacity'], '150000.00')

    def test_collateral_reserved_elsewhere_and_ineligible(self):
        self.loan()['collateral'][0]['value_reserved_elsewhere'] = '400000.00'
        self.assertEqual(self.projected()['borrowing_base'], '360000.00')
        self.loan()['collateral'][0]['eligible'] = False
        self.assertEqual(self.projected()['borrowing_base'], '0.00')
        self.loan()['collateral'][0]['eligible'] = None
        self.assertIsNone(self.projected()['borrowing_base'])
        self.assertIn('collateral-data-gap', self.codes())

    def test_stale_missing_collateral_and_encumbrance_conflict(self):
        for key, value in [('valuation_date', '2026-09-01'), ('value_reserved_elsewhere', None), ('value_reserved_elsewhere', '1000001.00')]:
            doc = deepcopy(self.doc); doc['loan_options'][0]['collateral'][0][key] = value
            self.assertIsNone(build(doc)['result']['loan_alternatives'][0]['scenarios'][0]['borrowing_base'])
            self.assertEqual(build(doc)['status'], 'needs-data')

    def test_unsecured_no_pledge_and_credit_limit(self):
        self.loan().update(type='unsecured', collateral_test='none', collateral=[], credit_limit='200000.00')
        row = self.projected()
        self.assertIsNone(row['borrowing_base'])
        self.assertEqual(row['debt_over_capacity'], '50000.00')
        self.assertIsNone(row['maintenance_paydown_illustration'])

    def test_budget_and_quote_freshness(self):
        self.doc['debt_budget']['monthly_available'] = '1000.00'
        self.assertEqual(self.projected()['loan_projection']['monthly_budget_shortfall'], '260.00')
        self.loan()['quote_date'] = '2026-08-01'
        self.loan()['quote_valid_until'] = '2026-09-20'
        self.assertTrue({'debt-service-gap', 'stale-quote', 'quote-expired'} <= self.codes())

    def test_late_funding_and_liquidation_unknown_tax(self):
        self.doc['liquidation_options'][0]['available_date'] = '2026-10-02'
        self.assertIn('late-funding', self.codes())
        self.doc['liquidation_options'][0]['tax_reserve'] = None
        self.assertIsNone(build(self.doc)['result']['liquidity_alternatives'][1]['net_proceeds'])
        self.assertIn('liquidation-data-gap', self.codes())

    def test_unknown_cash_and_interest_never_zero(self):
        self.doc['liquid_resources']['available_cash'] = None
        self.loan()['annual_rate_pct'] = None
        out = build(self.doc)
        self.assertIsNone(out['result']['liquidity_alternatives'][0]['net_proceeds'])
        self.assertIsNone(out['result']['loan_alternatives'][0]['scenarios'][0]['loan_projection'])
        self.assertEqual(out['status'], 'needs-data')

    def test_upstream_preservation_and_resolution_evidence(self):
        issue = {'artifact_id': 'prior42', 'code': 'ownership', 'message': 'Pledged account ownership remains unresolved', 'status': 'unresolved', 'source_ids': ['case']}
        self.doc['upstream_issues'] = [issue]
        self.assertIn('upstream-unresolved', self.codes())
        out = build(self.doc)
        self.assertEqual(out['result']['handoff_context']['upstream_issues'], [issue])
        issue['status'] = 'resolved'
        self.assertTrue(validate(self.doc))
        issue['resolution'] = {'owner': 'cited reviewer', 'reference': 'synthetic:resolution', 'as_of': '2026-09-17', 'source_ids': []}
        self.assertIn('evidence-gap', self.codes())

    def test_input_structure_types_and_duplicate_ids(self):
        for bad in [True, 'NaN', '1.001', -1, {}, []]:
            doc = deepcopy(self.doc); doc['loan_options'][0]['draw_amount'] = bad
            self.assertTrue(validate(doc), bad)
        self.loan()['collateral'].append(deepcopy(self.loan()['collateral'][0]))
        self.assertTrue(validate(self.doc))

    def test_policy_dates_capacity_and_missing_upstream(self):
        for key, value in [('valid_until', '2026-09-16'), ('capacity', 'brokerage')]:
            doc = deepcopy(self.doc); doc['policy'][key] = value
            self.assertTrue(validate(doc))
        del self.doc['upstream_issues']
        self.assertTrue(validate(self.doc))

    def test_changed_arithmetic_identity_findings_or_action_rejected(self):
        out = build(self.doc)
        for key, value in [('action_taken', True), ('household_id', 'wrong'), ('status', 'approved'), ('human_review_required', False)]:
            altered = deepcopy(out); altered[key] = value
            self.assertTrue(validate_output(altered))
        altered = deepcopy(out); altered['result']['loan_alternatives'][0]['new_net_proceeds'] = '999999.00'
        self.assertTrue(validate_output(altered))
        altered = deepcopy(out); altered['result']['input_snapshot']['policy']['version'] = 'changed'
        self.assertTrue(validate_output(altered))


if __name__ == '__main__':
    unittest.main()
