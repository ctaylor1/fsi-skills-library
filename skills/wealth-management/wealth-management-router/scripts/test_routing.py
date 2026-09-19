import json
import unittest
from pathlib import Path
from route import ROUTES, route, validate_output


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / "evals/files/request.json").read_text())
        self.doc.update(unresolved_issues=[], upstream_artifact_ids=[])

    def test_every_p0_p1_p2_p3_intent_has_distinct_route(self):
        self.doc["intents"] = list(ROUTES)
        out = route(self.doc)
        self.assertEqual(len({s["target_skill"] for s in out["result"]["steps"]}), 27)
        self.assertEqual(out["result"]["steps"][0]["intent"], "investor-protection")
        self.assertFalse(out["action_taken"])
        self.assertEqual(validate_output(out), [])

    def test_book_scope_is_distinct_from_household(self):
        self.doc['intents'] = ['book-review']
        self.assertEqual(route(self.doc)['status'], 'needs-data')
        self.doc.update(scope_type='advisor-book', book_id='TEAM42', household_id='book:TEAM42')
        out = route(self.doc)
        self.assertEqual(out['status'], 'review-ready')
        self.assertEqual(out['result']['steps'][0]['target_scope'], 'advisor-book')
        self.assertEqual(out['result']['handoff_context']['book_id'], 'TEAM42')
        self.doc['intents'].append('client-review')
        self.assertIn('separate-subject-requests', {r['code'] for r in route(self.doc)['findings']})

    def test_p2_workflow_boundaries(self):
        self.doc['intents'] = ['prospect-referral', 'lending-liquidity', 'private-markets']
        out = route(self.doc)
        self.assertEqual(len(out['result']['steps']), 3)
        self.assertEqual(out['result']['steps'][0]['target_scope'], 'prospect-case')
        self.assertNotIn('investment-manager-due-diligence-reviewer', {r['target_skill'] for r in out['result']['steps']})
        del self.doc['upstream_artifact_ids']
        with self.assertRaises(ValueError):
            route(self.doc)

    def test_family_and_trust_need_explicit_matching_scope(self):
        for intent, scope, key, prefix in [('family-governance', 'family-group', 'family_id', 'family:'),
                                          ('trust-administration', 'trust', 'trust_id', 'trust:')]:
            with self.subTest(intent=intent):
                doc = {**self.doc, 'intents': [intent]}
                self.assertEqual(route(doc)['status'], 'needs-data')
                doc.update(scope_type=scope, household_id=prefix + '42', **{key: '42'})
                out = route(doc)
                self.assertEqual(out['status'], 'review-ready')
                self.assertEqual(out['result']['steps'][0]['target_scope'], scope)
                self.assertEqual(out['result']['handoff_context'][key], '42')
                doc[key] = 'OTHER'
                self.assertEqual(route(doc)['status'], 'needs-data')

    def test_reserved_prefix_without_scope_cannot_be_clean_household_route(self):
        for prefix in ['book:', 'family:', 'trust:']:
            doc = {**self.doc, 'intents': ['client-review'], 'household_id': prefix + '42'}
            self.assertIn('separate-subject-requests', {r['code'] for r in route(doc)['findings']})

    def test_mixed_family_trust_household_need_separate_requests(self):
        self.doc.update(intents=['family-governance', 'trust-administration', 'estate-review'],
                        scope_type='family-group', family_id='42', household_id='family:42')
        out = route(self.doc)
        self.assertEqual({s['target_scope'] for s in out['result']['steps']}, {'family-group', 'trust', 'household'})
        self.assertTrue({'separate-subject-requests', 'trust-scope-required'} <= {r['code'] for r in out['findings']})
        self.assertFalse(out['action_taken'])
        out['result']['handoff_context']['family_id'] = 'ALTERED'
        self.assertTrue(validate_output(out))

    def test_malformed_subject_fields_reject(self):
        for change in [{'scope_type': []}, {'family_id': None}, {'trust_id': {'id': '42'}}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                route({**self.doc, **change})

    def test_provisional_prospect_scope_needs_reviewed_household_mapping(self):
        self.doc.update(scope_type='prospect-case', intents=['prospect-referral'])
        self.assertEqual(route(self.doc)['status'], 'review-ready')
        self.doc['intents'].append('financial-plan')
        out = route(self.doc)
        self.assertIn('separate-subject-requests', {f['code'] for f in out['findings']})
        self.assertEqual(out['status'], 'needs-data')

    def test_single_intent_does_not_expand_scope(self):
        self.doc["intents"] = ["client-review"]
        self.assertEqual([r["target_skill"] for r in route(self.doc)["result"]["steps"]], ["client-review-preparer"])

    def test_execution_and_unimplemented_intents_remain_unrouted(self):
        self.doc["intents"] = ["trade", "charitable-giving-plan", "follow-up"]
        out = route(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(len(out["result"]["steps"]), 1)
        self.assertEqual(out["result"]["unrouted_intents"], ["trade", "charitable-giving-plan"])

    def test_goal_alias_and_asset_management_destination(self):
        self.doc['intents'] = ['goal-progress', 'financial-plan', 'manager-due-diligence']
        out = route(self.doc)
        self.assertEqual(len(out['result']['steps']), 2)
        self.assertEqual(out['result']['steps'][0]['requested_modes'], ['goal-progress', 'financial-plan'])
        self.assertEqual(out['result']['steps'][1]['target_category'], 'asset-management')

    def test_upstream_gap_remains_in_route_and_handoff(self):
        issue = {'code': 'basis-gap', 'message': 'Lot basis remains unknown', 'source_ids': ['statement']}
        self.doc['unresolved_issues'] = [issue]
        self.doc['upstream_artifact_ids'] = ['source-artifact']
        out = route(self.doc)
        self.assertIn(issue, out['findings'])
        self.assertEqual(out['status'], 'needs-data')
        self.assertEqual(out['result']['handoff_context']['unresolved_issues'], [issue])
        self.assertEqual(out['result']['handoff_context']['upstream_artifact_ids'], ['source-artifact'])
        self.doc['unresolved_issues'][0]['source_ids'] = ['absent']
        with self.assertRaises(ValueError):
            route(self.doc)

    def test_p1_requires_explicit_issue_and_lineage_inventory(self):
        self.doc['intents'] = ['financial-plan']
        del self.doc['unresolved_issues']
        with self.assertRaises(ValueError):
            route(self.doc)
        self.doc['intents'] = ['discovery']
        self.assertEqual(route(self.doc)['status'], 'review-ready')

    def test_tampered_empty_outputs_rejected(self):
        self.assertTrue(validate_output({}))
        out = route(self.doc)
        out["result"]["steps"] = []
        self.assertTrue(validate_output(out))

    def test_capacity_and_jurisdiction_required(self):
        for key, value in [("capacity", "retail"), ("jurisdiction", "UK")]:
            self.doc["engagement"][key] = value
            with self.assertRaises(ValueError):
                route(self.doc)


if __name__ == "__main__":
    unittest.main()
