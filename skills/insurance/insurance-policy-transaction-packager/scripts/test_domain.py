import copy
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


class PolicyTransactionTests(unittest.TestCase):
    def test_proposal_preserves_original_and_exact_premium_basis(self):
        doc = request()
        out = output(doc)
        self.assertEqual(out['status'], 'ready-for-review')
        self.assertEqual(out['results']['proposed_changes'][0]['before'], '1000000')
        self.assertEqual(out['results']['policy_binding']['values']['coverage_limit'], '1000000')
        self.assertEqual(out['results']['premium_effect']['amount'], '200.00')
        self.assertEqual(out['results']['resulting_policy_state'], 'not-established')
        self.assertFalse(out['action_taken'])

    def test_stale_version_and_before_value_conflicts(self):
        for field in ('version', 'before'):
            doc = request()
            if field == 'version':
                doc['data']['request']['expected_policy_version'] = 'v2'
            else:
                doc['data']['request']['changes'][0]['before'] = '500000'
            self.assertNotEqual(output(doc)['status'], 'ready-for-review')

    def test_pending_and_duplicate_requests(self):
        for rid in ('REQ-1', 'ANOTHER'):
            doc = request()
            doc['data']['pending_transactions'] = [{'request_id': rid, 'policy_id': 'P1', 'status': 'pending', 'source_refs': ['policy-export']}]
            self.assertEqual(output(doc)['status'], 'needs-review')
        doc = request()
        del doc['data']['pending_inventory_complete']
        self.assertEqual(output(doc)['status'], 'needs-data')

    def test_change_table_uses_current_snapshot_and_retains_stale_request(self):
        doc = request()
        doc['data']['request']['changes'][0]['before'] = '500000'
        row = output(doc)['results']['proposed_changes'][0]
        self.assertEqual(row['before'], '1000000')
        self.assertEqual(row['requested_before'], '500000')
        self.assertFalse(row['before_matches_request'])
        del doc['data']['policy']['values']['coverage_limit']
        row = output(doc)['results']['proposed_changes'][0]
        self.assertIsNone(row['before'])
        self.assertFalse(row['before_known'])

    def test_notice_deadline_and_sent_assumptions(self):
        doc = request()
        doc['data']['notices'][0]['planned_send_date'] = '2026-09-20'
        out = output(doc)
        self.assertTrue(any(f['code'] == 'insufficient-notice' for f in out['findings']))
        doc['data']['notices'][0]['planned_send_date'] = '2026-09-10'
        out = output(doc)
        self.assertTrue(any(f['code'] == 'notice-plan-in-past' for f in out['findings']))
        self.assertFalse(out['results']['notice_plan'][0]['delivered'])

    def test_backdate_and_wrong_authority_do_not_grant_execution(self):
        doc = request()
        doc['data']['request']['effective_date'] = '2026-09-01'
        doc['data']['authority']['actor_id'] = 'UNRELATED'
        out = output(doc)
        self.assertFalse(out['results']['execution_authorized'])
        self.assertTrue({'backdating-unresolved', 'request-authority'} <= {f['code'] for f in out['findings']})

    def test_premium_unknown_and_foreign_currency_not_zero(self):
        for field, value in [('amount', None), ('currency', 'EUR')]:
            doc = request()
            doc['data']['premium_effect'][field] = value
            out = output(doc)
            self.assertIsNone(out['results']['premium_effect']['amount'])
            self.assertEqual(out['status'], 'needs-data')

    def test_profile_scope_and_false_source(self):
        doc = request()
        doc['data']['rule_profile']['jurisdictions'] = ['US-OTHER']
        doc['data']['authority']['source_refs'] = ['missing']
        self.assertEqual(output(doc)['status'], 'needs-data')

    def test_resealed_proposal_cannot_change_source_version(self):
        doc = request()
        out = output(doc)
        out['results']['policy_binding']['version'] = 'v99'
        out['artifact'] = build_artifact(doc, out, producer=SKILL, artifact_type='insurance-workflow-review')
        self.assertTrue(check_output(out, SKILL, evaluate, validate))

    def test_malformed_action_and_boolean_money_reject(self):
        for action, value in [({}, '200'), ('endorsement', True)]:
            doc = copy.deepcopy(request())
            doc['data']['request']['transaction_type'] = action
            doc['data']['premium_effect']['amount'] = value
            self.assertTrue(validate(doc))


if __name__ == '__main__':
    unittest.main()
