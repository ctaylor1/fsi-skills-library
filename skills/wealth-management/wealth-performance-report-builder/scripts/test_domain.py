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

    def test_known_compounded_returns_and_transfer(self):
        r=compute(self.doc)['result']
        self.assertEqual(r['household']['net_return_pct'],'15.401562')
        self.assertEqual(r['household']['gross_return_pct'],'15.500000')
        self.assertEqual(r['household']['ending_value'],'179392.50')
        self.assertEqual(r['household']['observed_fees'],'150.00')
        self.assertEqual(r['household']['observed_net_external_flows'],'5000.00')
        self.assertEqual(r['benchmark_return_pct'],'12.320000')
        self.assertEqual(r['net_less_benchmark_percentage_points'],'3.081562')
        self.assertFalse(r['annualized']);self.assertFalse(r['gips_compliance_asserted'])

    def test_missing_flow_suppresses_not_zero(self):
        self.doc['subperiods'][1]['accounts'][0]['external_flow_end']=None
        out=compute(self.doc)
        self.assertIsNone(out['result']['household']['net_return_pct'])
        self.assertEqual(out['result']['household']['ending_value'],'179392.50')
        self.assertIn('account-data-gap',self.codes())

    def test_missing_fee_does_not_invent_unbalanced_transfer(self):
        self.doc['subperiods'][1]['accounts'][1]['fees_end']=None
        self.assertIn('account-data-gap',self.codes())
        self.assertNotIn('internal-transfer-break',self.codes())
        self.assertIsNone(compute(self.doc)['result']['household']['net_return_pct'])

    def test_missing_account_and_internal_break(self):
        self.doc['subperiods'][1]['accounts'][0]['internal_flow_start']='-9000.00'
        self.assertIn('internal-transfer-break',self.codes())
        self.assertIsNone(compute(self.doc)['result']['household']['net_return_pct'])
        self.doc['subperiods'][1]['accounts'].pop()
        self.assertIsNone(compute(self.doc)['result']['household']['ending_value'])

    def test_unknown_flow_timing_suppresses(self):
        self.doc['methodology']['all_flows_at_boundaries']=False
        self.assertIn('flow-timing',self.codes())
        r=compute(self.doc)['result']
        self.assertIsNone(r['household']['net_return_pct'])
        self.assertTrue(all(a['net_return_pct'] is None for a in r['account_returns']))

    def test_gaps_overlap_and_continuity(self):
        for start in ['2026-01-30','2026-02-01']:
            d=deepcopy(self.doc);d['subperiods'][1]['start']=start
            self.assertIsNone(compute(d)['result']['household']['net_return_pct'])
            self.assertIn('period-coverage',self.codes(d))
        self.doc['subperiods'][1]['accounts'][0]['opening_value']='120901.00'
        self.assertIn('valuation-continuity',self.codes())
        self.assertIsNone(compute(self.doc)['result']['household']['net_return_pct'])

    def test_known_inactive_account_keeps_household_return(self):
        from domain import FIELDS
        self.doc['accounts'].append({'account_id':'EMPTY','source_ids':['ledger']})
        for period in self.doc['subperiods']:
            period['accounts'].append({'account_id':'EMPTY','source_ids':['ledger'],**dict.fromkeys(FIELDS,'0.00')})
        out=compute(self.doc)
        self.assertEqual(out['status'],'review-ready')
        self.assertEqual(out['result']['household']['net_return_pct'],'15.401562')
        empty=out['result']['account_returns'][-1]
        self.assertIsNone(empty['net_return_pct'])
        self.assertEqual(empty['status'],'not-applicable-no-invested-capital')

    def test_zero_capital_and_invalid_amounts(self):
        self.doc['subperiods'][0]['accounts'][0]['opening_value']='0.00'
        self.doc['subperiods'][0]['accounts'][0]['external_flow_start']='0.00'
        self.assertIn('return-not-evaluable',self.codes())
        self.assertIsNone(compute(self.doc)['result']['household']['net_return_pct'])
        for bad in [True,'NaN',-1,'1.001']:
            d=deepcopy(self.doc);d['subperiods'][0]['accounts'][0]['ending_value']=bad
            self.assertTrue(input_errors(d,check))

    def test_benchmark_and_official_comparability(self):
        self.doc['benchmark']['currency']='EUR'
        self.assertIsNone(compute(self.doc)['result']['benchmark_return_pct'])
        self.assertIn('benchmark-comparability',self.codes())
        self.doc['benchmark']['currency']='USD'
        self.doc['benchmark']['returns'].pop()
        self.assertIn('benchmark-comparability',self.codes())
        self.doc['official_reference']['household_end_value']='1.00'
        self.doc['official_reference']['household_net_return_pct']='1'
        self.assertTrue({'closing-value-tieout','official-return-tieout'}<=self.codes())

    def test_missing_source_and_not_applicable_benchmark(self):
        self.doc['benchmark']={'applicable':False,'reason':'approved no-benchmark mandate','source_ids':['policy']}
        self.assertEqual(compute(self.doc)['status'],'review-ready')
        self.doc['subperiods'][0]['accounts'][0]['source_ids']=[]
        self.assertIn('source-gap',self.codes())


if __name__ == '__main__':
    unittest.main()
