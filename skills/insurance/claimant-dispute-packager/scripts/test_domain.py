"""Deterministic native regressions, not professional or live-source acceptance."""
import copy
import json
import unittest
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

    def test_chronology_reason_counterevidence_requests(self):
        result = self.result()['results']
        self.assertEqual([x['event_id'] for x in result['chronology']], ['E1','E2'])
        reason = result['reason_evidence_matrix'][0]
        self.assertEqual(reason['supporting'][0]['evidence_id'], 'V1')
        self.assertEqual(reason['contrary'][0]['evidence_id'], 'V2')
        self.assertEqual(reason['request_ids'], ['Q1'])

    def test_carrier_cannot_use_claimant_capacity(self):
        self.doc['context']['capacity'] = 'carrier'
        self.gap('claimant-capacity')

    def test_different_claimant_identity(self):
        self.doc['data']['claimant_id'] = 'PARTY-OTHER'
        self.gap('claimant-capacity')

    def test_unknown_deadline_is_not_defaulted(self):
        self.doc['data']['notice']['response_due_date'] = None
        result = self.gap('date')
        self.assertIsNone(result['results']['supplied_response_due_date'])

    def test_expired_deadline_preserves_options(self):
        self.doc['data']['notice']['response_due_date'] = '2026-09-17'
        result = self.result()
        self.assertEqual(result['status'], 'needs-review')
        self.assertFalse(result['results']['merits_determined'])
        self.assertFalse(result['results']['submitted'])

    def test_missing_reason_evidence_relationship(self):
        self.doc['data']['links'] = []
        self.gap('reason-evidence-gap')

    def test_duplicate_pair_cannot_strengthen_evidence(self):
        row = copy.deepcopy(self.doc['data']['links'][0])
        row['link_id'] = 'L3'
        self.doc['data']['links'].append(row)
        self.gap('evidence-link')

    def test_unaddressed_reason_remains_visible(self):
        row = copy.deepcopy(self.doc['data']['reasons'][0])
        row['reason_id'] = 'R2'
        self.doc['data']['reasons'].append(row)
        self.gap('unaddressed-reason')

    def test_request_to_unknown_reason(self):
        self.doc['data']['requests'][0]['reason_ids'] = ['R99']
        self.gap('request-link')

    def test_notice_relationship_and_future_event(self):
        self.doc['data']['reasons'][0]['notice_id'] = 'N2'
        self.gap('reason-binding')
        self.doc['data']['events'][0]['date'] = '2026-09-30'
        self.gap('date')


if __name__ == '__main__':
    unittest.main()
