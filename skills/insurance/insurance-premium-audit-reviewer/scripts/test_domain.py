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

    def test_audit_and_deposit_tieout(self):
        result = self.result()['results']
        self.assertEqual(Decimal(result['manual_premium']), Decimal(220))
        self.assertEqual(Decimal(result['audited_premium']), Decimal(230))
        self.assertEqual(Decimal(result['deposit_adjustment']), Decimal(30))
        self.assertEqual(Decimal(result['reconciliation_difference']), 0)

    def test_unknown_exposure_is_not_zero(self):
        self.doc['data']['exposures'][0]['exposure'] = None
        self.assertIsNone(self.gap('unknown')['results']['audited_premium'])

    def test_explicit_zero_uses_minimum(self):
        self.doc['data']['exposures'][0]['exposure'] = 0
        self.assertEqual(Decimal(self.result()['results']['audited_premium']), 100)

    def test_duplicate_exposure_withholds_premium(self):
        self.doc['data']['exposures'].append(copy.deepcopy(self.doc['data']['exposures'][0]))
        self.assertIsNone(self.gap('duplicate-identity')['results']['audited_premium'])

    def test_relabelled_source_record_cannot_double_count(self):
        row = copy.deepcopy(self.doc['data']['exposures'][0])
        row['exposure_id'] = 'X2'
        self.doc['data']['exposures'].append(row)
        self.assertIsNone(self.gap('duplicate-identity')['results']['audited_premium'])

    def test_mixed_payroll_sales_basis_withholds_total(self):
        self.doc['data']['exposures'][0]['basis'] = 'sales-USD'
        self.assertIsNone(self.gap('exposure-basis')['results']['audited_premium'])

    def test_exposure_outside_policy(self):
        self.doc['data']['exposures'][0]['end'] = '2026-09-11'
        self.gap('exposure-period')

    def test_rate_not_covering_full_policy(self):
        self.doc['data']['rates'][0]['effective_from'] = '2026-02-01'
        self.gap('rate-period')

    def test_manual_identity_unknown(self):
        del self.doc['data']['rates'][0]['manual_version']
        self.gap('manual-basis')

    def test_final_rounding_after_minimum(self):
        self.doc['data']['exposures'][0]['exposure'] = '10000.25'
        self.assertEqual(self.result()['results']['audited_premium'], '230.01')

    def test_zero_denominator_and_malformed_number(self):
        self.doc['data']['rates'][0]['unit_size'] = 0
        self.gap('unit')
        self.doc['data']['rates'][0]['unit_size'] = True
        with self.assertRaises(ValueError):
            self.result()


if __name__ == '__main__':
    unittest.main()
