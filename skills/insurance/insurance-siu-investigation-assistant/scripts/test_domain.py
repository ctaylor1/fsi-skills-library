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

    def test_hypotheses_counterevidence_custody(self):
        result = self.result()['results']
        self.assertEqual(result['hypothesis_matrix'][0]['contradicts'][0]['evidence_id'], 'E2')
        self.assertEqual(result['custody_register'][0]['current_holder'], 'siu-custodian')
        self.assertEqual(result['fraud_verdict'], 'not-determined')
        self.assertEqual(result['task_plan'][0]['draft_state'], 'review-ready')

    def test_innocent_alternative_required(self):
        self.doc['data']['hypotheses'][0]['innocent_alternative'] = None
        self.gap('alternative')

    def test_no_counterevidence_requires_alternative_task(self):
        self.doc['data']['links'] = self.doc['data']['links'][:1]
        self.doc['data']['tasks'][0]['tests_alternative'] = False
        self.gap('alternative-test')

    def test_unknown_authority_not_approval(self):
        self.doc['data']['tasks'][0]['authority_reviewed'] = None
        result = self.gap('task-authority')
        self.assertEqual(result['results']['task_plan'][0]['draft_state'], 'needs-data')

    def test_surveillance_not_a_supported_task(self):
        self.doc['data']['tasks'][0]['method'] = 'covert-surveillance'
        self.gap('task-authority')

    def test_custody_different_offsets_follow_utc_instants(self):
        self.doc['data']['custody'][0]['at'] = '2026-09-10T10:00:00+02:00'
        later = copy.deepcopy(self.doc['data']['custody'][0])
        later.update(transfer_id='T3', at='2026-09-10T09:00:00Z', from_holder='siu-custodian', to_holder='review-custodian')
        self.doc['data']['custody'].append(later)
        result = self.result()
        self.assertEqual(result['status'], 'ready-for-review')
        self.assertEqual(result['results']['custody_register'][0]['current_holder'], 'review-custodian')

    def test_custody_asof_uses_utc_day_not_written_offset(self):
        self.doc['data']['custody'][0]['at'] = '2026-09-19T00:30:00+02:00'
        self.assertEqual(self.result()['status'], 'ready-for-review')
        self.doc['data']['custody'][0]['at'] = '2026-09-18T23:30:00-02:00'
        self.gap('custody-date')

    def test_custody_holder_break(self):
        self.doc['data']['custody'][0]['from_holder'] = 'unexplained-third-party'
        result = self.gap('custody-break')
        self.assertIsNone(result['results']['custody_register'][0]['current_holder'])

    def test_changed_digest_break(self):
        self.doc['data']['custody'][0]['content_digest'] = 'c' * 64
        self.gap('custody-break')

    def test_missing_custody_and_future_record(self):
        self.doc['data']['custody'] = self.doc['data']['custody'][1:]
        self.gap('custody-missing')
        self.doc['data']['custody'][0]['at'] = '2026-09-20T10:00:00Z'
        self.gap('custody-date')

    def test_duplicate_relationship_and_unknown_hypothesis(self):
        row = copy.deepcopy(self.doc['data']['links'][0])
        row['link_id'] = 'L3'
        self.doc['data']['links'].append(row)
        self.gap('hypothesis-link')
        self.doc['data']['tasks'][0]['hypothesis_id'] = 'H99'
        self.gap('task-binding')

    def test_claimant_role_routes_away(self):
        self.doc['context']['capacity'] = 'claimant'
        self.gap('capacity')

    def test_malformed_digest_and_collection_unknown(self):
        self.doc['data']['evidence'][0]['content_digest'] = 'not-a-digest'
        self.gap('evidence-identity')
        self.doc['data']['evidence'][0]['lawful_collection_reviewed'] = None
        self.gap('collection-authority')


if __name__ == '__main__':
    unittest.main()
