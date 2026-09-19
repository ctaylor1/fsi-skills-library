"""Known-value and adverse scenarios; fixtures are synthetic, never client records."""
import json
import unittest
from copy import deepcopy
from pathlib import Path

from domain import compute, check, validate_output
from wealth_analysis import input_errors


class DomainTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / 'evals/files/request_example.json').read_text())

    def codes(self, doc=None):
        return {f['code'] for f in compute(doc or self.doc)['findings']}

    def test_fixture_and_reconstruction(self):
        out = compute(self.doc)
        self.assertEqual(out['status'], 'review-ready')
        self.assertEqual(validate_output(out), [])
        self.assertFalse(out['action_taken'])
        self.assertTrue(out['human_review_required'])

    def test_source_gap_and_upstream_issue_survive(self):
        issue = {'code': 'upstream-break', 'message': 'Unresolved source difference', 'source_ids': ['ledger']}
        self.doc['unresolved_issues'] = [issue]
        out = compute(self.doc)
        self.assertIn(issue, out['findings'])
        self.assertEqual(out['status'], 'needs-data')
        self.doc['sources'][0]['valid_until'] = '2026-01-01'
        self.assertTrue(input_errors(self.doc, check))

    def test_tampering_and_input_rebinding(self):
        out = compute(self.doc)
        for field, value in [('action_taken', True), ('human_review_required', False), ('status', 'approved')]:
            tampered = deepcopy(out)
            tampered[field] = value
            self.assertTrue(validate_output(tampered))
        tampered = deepcopy(out)
        tampered['result']['input_snapshot']['household_id'] = 'different'
        self.assertTrue(validate_output(tampered))
        tampered = deepcopy(out)
        tampered['result']['invented_claim'] = 'approved'
        self.assertTrue(validate_output(tampered))

    def test_household_tiers_and_exclusion(self):
        out = compute(self.doc)['result']
        self.assertEqual(out['segments'][0]['billable_assets'], '1000000.00')
        self.assertEqual(out['calculation']['expected_fee'], '7500.00')
        self.assertEqual(out['calculation']['assessed_minus_expected'], '0.00')
        self.doc['agreement']['schedule_type'] = 'cliff'
        out = compute(self.doc)
        self.assertEqual(out['result']['calculation']['expected_fee'], '5000.00')
        self.assertIn('fee-variance', {f['code'] for f in out['findings']})

    def test_exact_cliff_boundary_and_zero(self):
        from domain import annual_fee
        from decimal import Decimal
        self.doc['agreement']['schedule_type'] = 'cliff'
        self.assertEqual(annual_fee(Decimal('500000'), self.doc['agreement']), Decimal('5000'))
        self.assertEqual(annual_fee(Decimal('500000.01'), self.doc['agreement']), Decimal('2500.00005'))
        self.assertEqual(annual_fee(Decimal('0'), self.doc['agreement']), Decimal('0'))

    def test_proration_leap_and_cross_year(self):
        from domain import year_fraction
        from datetime import date
        from decimal import Decimal
        self.assertEqual(year_fraction(date(2024,1,1), date(2024,12,31), 'actual/actual'), Decimal(1))
        self.assertEqual(year_fraction(date(2024,1,1), date(2024,12,31), 'actual/365'), Decimal(366)/365)
        self.assertEqual(year_fraction(date(2024,12,31), date(2025,1,1), 'actual/actual'), Decimal(1)/366+Decimal(1)/365)

    def test_two_segments_use_changed_value(self):
        first = self.doc['valuation_segments'][0]
        second = deepcopy(first)
        first['end'] = '2025-06-30'
        second.update(segment_id='second', start='2025-07-01')
        second['accounts'][0]['assets'][0]['market_value'] = '200000.00'
        second['accounts'][0]['reported_total'] = '400000.00'
        self.doc['valuation_segments'].append(second)
        self.assertEqual(compute(self.doc)['result']['calculation']['expected_fee'], '6491.78')

    def test_coverage_unknown_and_tieout_suppress(self):
        cases=[]
        d=deepcopy(self.doc); d['valuation_segments'][0]['start']='2025-01-02'; cases.append(d)
        d=deepcopy(self.doc); d['valuation_segments'].append({**deepcopy(d['valuation_segments'][0]),'segment_id':'overlap'}); cases.append(d)
        d=deepcopy(self.doc); d['valuation_segments'][0]['accounts'].pop(); cases.append(d)
        d=deepcopy(self.doc); d['valuation_segments'][0]['accounts'][0]['assets'][0]['fee_eligible']=None; cases.append(d)
        d=deepcopy(self.doc); d['valuation_segments'][0]['accounts'][0]['reported_total']='1.00'; cases.append(d)
        for d in cases:
            with self.subTest(doc=d):
                out=compute(d)
                self.assertIsNone(out['result']['calculation']['expected_fee'])
                self.assertEqual(out['status'],'needs-data')

    def test_credit_minimum_and_incomplete_assessment(self):
        self.doc['agreement']['minimum_period_fee']='8000.00'
        self.doc['adjustments']=[{'adjustment_id':'credit','amount':'-500.00','reason':'contract credit','source_ids':['policy']}]
        self.assertEqual(compute(self.doc)['result']['calculation']['expected_fee'],'7500.00')
        self.doc['billing_records_complete']=False
        self.assertIsNone(compute(self.doc)['result']['calculation']['assessed_minus_expected'])
        self.assertIn('billing-record-gap',self.codes())

    def test_conflicts_missing_citations_and_invalid_values(self):
        self.doc['conflict_review']['items']=[{'conflict_id':'C','description':'affiliate benefit','status':'open','treatment':'pending','source_ids':['policy']}]
        self.assertIn('economic-conflict',self.codes())
        self.doc['agreement']['source_ids']=[]
        self.assertIn('source-gap',self.codes())
        for bad in [True, 'NaN', -1, '1.001']:
            d=deepcopy(self.doc);d['agreement']['minimum_period_fee']=bad
            self.assertTrue(input_errors(d,check))
        self.doc['assessed_charges'].append(deepcopy(self.doc['assessed_charges'][0]))
        self.assertTrue(input_errors(self.doc,check))


if __name__ == '__main__':
    unittest.main()
