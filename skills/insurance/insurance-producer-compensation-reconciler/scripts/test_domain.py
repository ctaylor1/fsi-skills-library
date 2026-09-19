"""Deterministic native regressions, not professional or live-source acceptance."""
import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path

from domain import SKILL, evaluate, validate
from insurance_contract import build_artifact
from insurance_foundation import check_output, run


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).parents[1] / 'evals/files/normal.json').read_text())

    def result(self, doc=None):
        return run(self.doc if doc is None else doc, SKILL, evaluate, validate)

    def gap(self, code):
        output = self.result()
        self.assertEqual(output['status'], 'needs-data')
        self.assertTrue(any(f['code'] == code for f in output['findings']), output['findings'])
        self.assertFalse(output['action_taken'])
        return output

    def test_native_roundtrip_retains_unmodified_input(self):
        before = copy.deepcopy(self.doc)
        output = self.result()
        self.assertEqual(output['status'], 'ready-for-review', output['findings'])
        self.assertEqual(self.doc, before)
        self.assertEqual(output['source_document'], before)
        self.assertEqual(check_output(output, SKILL, evaluate, validate), [])

    def test_resealed_tampering_is_not_native_validity(self):
        output = self.result()
        output['results']['invented_approval'] = True
        output['artifact'] = build_artifact(output['source_document'], output, producer=SKILL,
            artifact_type='insurance-workflow-review', completeness=output['completeness'], evaluability=output['evaluability'], issues=output['unresolved_issues'])
        self.assertTrue(check_output(output, SKILL, evaluate, validate))

    def test_source_version_and_duplicate_identity(self):
        output = self.result()
        changed = copy.deepcopy(output)
        changed['source_document']['sources'][0]['version'] = 'changed'
        self.assertTrue(check_output(changed, SKILL, evaluate, validate))
        self.doc['sources'].append(copy.deepcopy(self.doc['sources'][0]))
        with self.assertRaises(ValueError):
            self.result()

    def test_missing_input_and_expired_profile_preserve_gaps(self):
        missing = copy.deepcopy(self.doc)
        missing['data'] = {}
        self.assertEqual(self.result(missing)['status'], 'needs-data')
        self.doc['data']['profile']['effective_to'] = '2025-12-31'
        self.gap('profile')

    def test_future_evidence_is_not_ready(self):
        self.doc['sources'][0]['as_of'] = '2026-09-19'
        self.gap('evidence')

    def test_earned_chargeback_splits_and_controls(self):
        result = self.result()['results']
        self.assertEqual(Decimal(result['net_earned_by_producer']['PROD1']), 450)
        self.assertEqual(Decimal(result['net_earned_by_producer']['PROD2']), 300)
        self.assertEqual(Decimal(result['event_ledger'][1]['gross']), -250)
        self.assertEqual(Decimal(result['reconciliation_differences']['PROD1']), 0)

    def test_unknown_base_is_not_zero(self):
        self.doc['data']['events'][0]['base_amount'] = None
        self.assertIsNone(self.gap('unknown')['results']['net_earned_by_producer'])

    def test_explicit_zero_earning(self):
        self.doc['data']['events'][0]['base_amount'] = 0
        self.assertEqual(Decimal(self.result()['results']['net_earned_by_producer']['PROD1']), 0)

    def test_missing_split_recipient_is_not_residual(self):
        self.doc['data']['agreements'][0]['splits'][0]['share'] = '0.5'
        self.assertIsNone(self.gap('split-total')['results']['net_earned_by_producer'])

    def test_chargeback_over_original(self):
        event = copy.deepcopy(self.doc['data']['events'][1])
        event.update(event_id='E3', fraction='0.8')
        self.doc['data']['events'].append(event)
        self.gap('over-chargeback')

    def test_chargeback_entitlement_cannot_be_invented(self):
        del self.doc['data']['events'][1]['chargeback_basis']
        self.assertIsNone(self.gap('chargeback-basis')['results']['net_earned_by_producer'])

    def test_cross_policy_chargeback(self):
        self.doc['data']['events'][1]['policy_id'] = 'POL2'
        self.gap('chargeback-link')

    def test_wrong_earning_trigger(self):
        self.doc['data']['events'][0]['trigger_evidence'] = 'written-but-unearned'
        self.gap('trigger')

    def test_expired_agreement_for_event(self):
        self.doc['data']['agreements'][0]['effective_to'] = '2026-09-01'
        self.gap('event-period')

    def test_duplicate_event_and_mismatched_basis(self):
        self.doc['data']['events'][1]['event_id'] = 'E1'
        self.gap('duplicate-identity')
        self.doc['data']['events'][0]['basis'] = 'cash-received'
        self.gap('event-basis')

    def test_reported_break_remains_known(self):
        self.doc['data']['reported'][0]['net_earned'] = '440'
        result = self.result()
        self.assertEqual(result['status'], 'needs-review')
        self.assertEqual(Decimal(result['results']['reconciliation_differences']['PROD1']), 10)


if __name__ == '__main__':
    unittest.main()
