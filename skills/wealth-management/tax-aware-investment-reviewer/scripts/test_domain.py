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

    def loss(self):
        self.doc['lots'][0]['unit_price']='70'
        return self.doc

    def buy(self, when='2026-09-01', quantity='5', **updates):
        return {'purchase_id':'BUY','account_id':'B','security_id':'EQ1','acquisition_lot_id':'replacement','quantity':quantity,'trade_date':when,'lifecycle':'executed','source_ids':['ledger'],**updates}

    def test_known_gain_and_no_retirement_harvest(self):
        r=compute(self.doc)['result']
        self.assertEqual(r['proposed_sales'][0]['gain_loss'],'390.00')
        self.assertEqual(r['transition']['positive_gain_tax_reserve'],'78.00')
        self.assertFalse(r['tax_lots'][1]['loss_candidate_for_review'])
        self.assertEqual(r['transition']['deductible_loss'],'not-determined')

    def test_open_future_window_even_without_purchases(self):
        self.loss()
        self.assertIn('forward-window-open',self.codes())
        self.assertEqual(compute(self.doc)['result']['transition']['positive_gain_tax_reserve'],'0.00')

    def test_ira_overlap_and_quantity(self):
        self.loss();self.doc['purchases']=[self.buy()]
        out=compute(self.doc)
        row=out['result']['proposed_sales'][0]['potential_replacements'][0]
        self.assertEqual(row['potential_overlap_quantity'],'5.000000')
        self.assertEqual(row['tax_treatment'],'tax-deferred')
        self.assertIn('potential-wash-sale',self.codes())
        self.assertEqual(out['result']['transition']['taxable_losses_before_wash_review'],'-210.00')

    def test_inclusive_window_and_cancelled_own_lot(self):
        self.loss()
        cases=[('2026-08-17','executed','replacement',True),('2026-08-16','executed','replacement',False),('2026-10-16','proposed','replacement',True),('2026-10-17','proposed','replacement',False),('2026-09-01','cancelled','replacement',False),('2026-09-01','executed','L1',False)]
        for when,lifecycle,lot,wanted in cases:
            self.doc['purchases']=[self.buy(when,lifecycle=lifecycle,acquisition_lot_id=lot)]
            self.assertEqual('potential-wash-sale' in self.codes(),wanted,(when,lifecycle,lot))

    def test_replacement_not_counted_twice(self):
        self.loss();self.doc['purchases']=[self.buy(quantity='25')]
        self.doc['proposed_sales'].append({**self.doc['proposed_sales'][0],'sale_id':'S2'})
        rows=compute(self.doc)['result']['proposed_sales']
        self.assertEqual([r['potential_replacements'][0]['potential_overlap_quantity'] for r in rows],['20.000000','5.000000'])

    def test_unknown_equivalence_scope_and_history(self):
        self.loss();self.doc['purchases']=[self.buy()]
        self.doc['equivalence_map'][0]['source_ids']=[]
        self.doc['accounts'][1]['history_complete']=False
        self.doc['scope_review']['household_scope_complete']=False
        self.assertTrue({'source-gap','equivalence-unknown','wash-coverage-gap','household-scope-gap'} <= self.codes())
        self.assertFalse(compute(self.doc)['result']['proposed_sales'][0]['potential_replacements'])

    def test_unknown_terms_budgets_and_location(self):
        self.doc['lots'][0]['tax_term']='unknown'
        self.assertIsNone(compute(self.doc)['result']['transition']['positive_gain_tax_reserve'])
        self.doc['lots'][0]['tax_term']='long'
        self.doc['tax_profile']['max_positive_gain_amount']='100.00'
        self.doc['tax_profile']['max_tax_reserve']='10.00'
        self.doc['location_policy']['preferences'][0]['preferred_tax_treatments']=['tax-exempt']
        self.assertTrue({'gain-budget','tax-reserve-budget','location-exception'} <= self.codes())

    def test_stale_candidate_and_oversell(self):
        self.loss();self.doc['lots'][0]['price_as_of']='2026-08-01'
        self.assertFalse(compute(self.doc)['result']['tax_lots'][0]['loss_candidate_for_review'])
        self.assertIn('stale-price',self.codes())
        self.doc['proposed_sales'][0]['quantity']='101'
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_historical_sale_rejects_later_quote(self):
        self.doc['proposed_sales'][0]['trade_date']='2026-08-10'
        self.assertTrue(input_errors(self.doc,check))
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_unsupported_values_reject(self):
        for bad in [True,'NaN',-1,'0.000000001']:
            d=deepcopy(self.doc);d['lots'][0]['quantity']=bad
            self.assertTrue(input_errors(d,check))


if __name__ == '__main__':
    unittest.main()
