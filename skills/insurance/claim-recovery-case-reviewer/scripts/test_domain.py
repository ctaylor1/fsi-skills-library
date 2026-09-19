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

    def test_collection_interest_allocation(self):
        result = self.result()['results']
        self.assertEqual(Decimal(result['allocation_schedule'][0]['net_collection_share']), 400)
        self.assertEqual(Decimal(result['allocation_schedule'][1]['net_collection_share']), 100)
        self.assertEqual(result['rights_register'][0]['days_to_supplied_limitation'], 13)

    def test_unknown_cost_not_zero(self):
        self.doc['data']['collections'][0]['cost_amount'] = None
        self.assertIsNone(self.gap('unknown')['results']['allocation_schedule'])

    def test_explicit_zero_collections(self):
        self.doc['data']['collections'] = []
        result = self.result()
        self.assertEqual(result['status'], 'ready-for-review')
        self.assertEqual(Decimal(result['results']['allocation_schedule'][0]['net_collection_share']), 0)

    def test_missing_collection_inventory(self):
        del self.doc['data']['collections']
        self.gap('inventory')

    def test_duplicate_party_interest(self):
        row = copy.deepcopy(self.doc['data']['interests'][0])
        row['interest_id'] = 'I3'
        self.doc['data']['interests'].append(row)
        self.gap('interest-binding')

    def test_overcollection_withholds_allocation(self):
        self.doc['data']['collections'][0]['gross_amount'] = '1001'
        self.assertIsNone(self.gap('right-overcollection')['results']['allocation_schedule'])

    def test_cost_needs_reviewed_basis(self):
        self.doc['data']['collections'][0]['cost_deduction_reviewed'] = False
        self.gap('collection-binding')

    def test_cost_allocation_is_explicit(self):
        self.doc['data']['collections'][0]['cost_amount'] = '50'
        result = self.result()['results']
        self.assertEqual(Decimal(result['allocation_schedule'][0]['net_collection_share']), 360)
        self.assertEqual(Decimal(result['allocation_schedule'][1]['net_collection_share']), 90)

    def test_limitation_no_automatic_extinguishment(self):
        self.doc['data']['rights'][0]['limitation_date'] = '2026-09-17'
        result = self.result()
        self.assertEqual(result['status'], 'needs-review')
        self.assertFalse(result['results']['legal_rights_determined'])
        self.assertTrue(any(f['code'] == 'task-after-limitation' for f in result['findings']))

    def test_unbound_and_future_collection(self):
        self.doc['data']['collections'][0]['right_id'] = 'UNKNOWN'
        self.gap('collection-binding')
        self.doc['data']['collections'][0]['date'] = '2026-09-20'
        self.gap('date')


if __name__ == '__main__':
    unittest.main()
