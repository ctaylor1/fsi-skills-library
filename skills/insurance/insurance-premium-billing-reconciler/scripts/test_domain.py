import json
from pathlib import Path
import unittest

from domain import SKILL, evaluate, validate
from insurance_contract import build_artifact
from insurance_foundation import check_output, run


def request():
    return json.loads((Path(__file__).resolve().parents[1] / 'evals/files/request.json').read_text())


def output(doc):
    return run(doc, SKILL, evaluate, validate)


class BillingTests(unittest.TestCase):
    def test_control_bridge_and_invoice_aging(self):
        out = output(request())
        self.assertEqual(out['status'], 'ready-for-review')
        result = out['results']
        self.assertEqual(result['movement_total'], '300')
        self.assertEqual(result['calculated_closing_balance'], '800')
        self.assertEqual(result['difference'], '0')
        self.assertEqual(result['aging_buckets']['1_30'], '800')
        self.assertEqual(result['policy_coverage_state'], 'not-determined')

    def test_partial_ledger_and_unknown_amount_withhold_bridge(self):
        for variant in ('partial', 'unknown'):
            doc = request()
            if variant == 'partial':
                doc['data']['ledger_complete'] = False
            else:
                doc['data']['entries'][0]['amount'] = None
            self.assertIsNone(output(doc)['results']['calculated_closing_balance'])

    def test_duplicate_and_currency_mismatch_withhold_arithmetic(self):
        for variant in ('duplicate', 'currency'):
            doc = request()
            if variant == 'duplicate':
                doc['data']['entries'].append(dict(doc['data']['entries'][0]))
            else:
                doc['data']['entries'][0]['currency'] = 'CAD'
            out = output(doc)
            self.assertIsNone(out['results']['movement_total'])
            self.assertIsNone(out['results']['invoice_aging'])

    def test_full_receipt_reversal_restores_receivable(self):
        doc = request()
        original = doc['data']['entries'][1]
        reversal = dict(original, entry_id='R1', kind='reversal', date='2026-09-16', reverses_id='E2')
        doc['data']['entries'].append(reversal)
        doc['data']['allocations'] = []
        doc['data']['closing_balance']['amount'] = '1500'
        out = output(doc)
        self.assertEqual(out['results']['calculated_closing_balance'], '1500')
        self.assertEqual(out['results']['aging_buckets']['1_30'], '1500')
        self.assertEqual(out['status'], 'ready-for-review')

    def test_unknown_partial_or_double_reversal_not_silently_applied(self):
        for variant in ('missing', 'partial', 'double', 'prior'):
            doc = request()
            row = dict(doc['data']['entries'][1], entry_id='R1', kind='reversal', date='2026-09-16', reverses_id='E2')
            if variant == 'missing':
                row['reverses_id'] = 'UNKNOWN'
            if variant == 'partial':
                row['amount'] = '350'
            if variant == 'prior':
                row['date'] = '2026-09-10'
            doc['data']['entries'].append(row)
            if variant == 'double':
                doc['data']['entries'].append(dict(row, entry_id='R2'))
            self.assertIsNone(output(doc)['results']['movement_total'])

    def test_unapplied_cash_separate_from_aging(self):
        doc = request()
        doc['data']['allocations'] = []
        out = output(doc)
        self.assertEqual(out['results']['unapplied_cash_credits']['E2'], '700')
        self.assertEqual(out['results']['aging_buckets']['1_30'], '1500')
        self.assertEqual(out['results']['calculated_closing_balance'], '800')
        self.assertEqual(out['status'], 'needs-review')

    def test_overallocation_blocks_aging_but_retains_valid_account_bridge(self):
        doc = request()
        doc['data']['allocations'][1]['amount'] = '900'
        out = output(doc)
        self.assertIsNone(out['results']['invoice_aging'])
        self.assertEqual(out['results']['calculated_closing_balance'], '800')
        self.assertTrue(any(f['code'] == 'overallocated-movement' for f in out['findings']))

    def test_known_balance_break_is_not_suppressed(self):
        doc = request()
        doc['data']['closing_balance']['amount'] = '850'
        out = output(doc)
        self.assertEqual(out['results']['difference'], '-50')
        self.assertEqual(out['status'], 'needs-review')

    def test_missing_invoice_inventory_not_asserted_empty(self):
        doc = request()
        del doc['data']['opening_invoices']
        out = output(doc)
        self.assertIsNone(out['results']['invoice_aging'])
        self.assertEqual(out['results']['calculated_closing_balance'], '800')

    def test_future_period_no_assumed_collection(self):
        doc = request()
        doc['data']['period']['end'] = '2026-10-01'
        out = output(doc)
        self.assertIsNone(out['results']['calculated_closing_balance'])
        self.assertFalse(out['results']['collection_or_cancellation_authorized'])

    def test_resealed_control_difference_fails(self):
        doc = request()
        out = output(doc)
        out['results']['difference'] = '999'
        out['artifact'] = build_artifact(doc, out, producer=SKILL, artifact_type='insurance-workflow-review')
        self.assertTrue(check_output(out, SKILL, evaluate, validate))

    def test_boolean_and_negative_movement_rejected(self):
        for value in (True, '-1', 'NaN'):
            doc = request()
            doc['data']['entries'][0]['amount'] = value
            self.assertTrue(validate(doc))


if __name__ == '__main__':
    unittest.main()
