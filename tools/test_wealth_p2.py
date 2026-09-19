"""P2 integration and independently authored prospect forward scenarios.

Tests use the published schema and fresh synthetic evidence; source truth and professional
acceptance remain deployment responsibilities. Other P2 forward modules cover financial work.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from build_catalog_from_xlsx import apply_changes
from spec_card import card
from sync_wealth_contract import ANALYSIS_PACKAGES, PACKAGE_PATHS, P2_PACKAGES

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tools/fixtures/wealth-p2-forward'
PROSPECT = 'wealth-prospect-referral-preparer'


def package(name):
    return ROOT / 'skills/wealth-management' / name


def fixture(name=PROSPECT):
    return json.loads((FIXTURES / (name + '.json')).read_text())


def run(name, script, doc, expected_exit=0):
    with tempfile.TemporaryDirectory(prefix='fsi-p2-forward-') as folder:
        path = Path(folder) / 'request.json'
        path.write_text(json.dumps(doc, allow_nan=False))
        result = subprocess.run([sys.executable, 'scripts/' + script, str(path)], cwd=package(name), capture_output=True, text=True)
    if result.returncode != expected_exit:
        raise AssertionError(f'{name}: exit {result.returncode}; {result.stdout}{result.stderr}')
    return json.loads(result.stdout)


def build(doc):
    return run(PROSPECT, 'calculate_or_transform.py', doc)


def codes(out):
    return {f['code'] for f in out['findings']}


class P2Integration(unittest.TestCase):
    def test_p2_catalog_coverage_metadata_and_migrations(self):
        import yaml
        catalog = json.loads((ROOT / 'catalog/skills-catalog.json').read_text())
        rows = catalog['skills']; by = {r['name']: r for r in rows}
        self.assertGreaterEqual(catalog['count'], 237)
        self.assertGreaterEqual(len(list((ROOT / 'skills/wealth-management').glob('*/SKILL.md'))), 25)
        self.assertEqual(len(P2_PACKAGES), 4)
        additions = json.loads((ROOT / 'catalog/provisional-additions.json').read_text())
        changes = json.loads((ROOT / 'catalog/approved-overrides.json').read_text())
        self.assertGreaterEqual(len(additions), 64)
        self.assertEqual(apply_changes(rows, additions, changes), rows)
        self.assertNotIn('financial-goal-progress-analyzer', by)
        self.assertNotIn('suitability-reg-bi-reviewer', by)
        for name in (*P2_PACKAGES, 'wealth-management-router'):
            front = yaml.safe_load((package(name) / 'SKILL.md').read_text().split('---', 2)[1])
            self.assertEqual(front['metadata'], yaml.safe_load(card(by[name])[0])['metadata'], name)
            if name != 'wealth-management-router':
                self.assertEqual(by[name]['delivery_wave'], 'Wave 8 - wealth management P2')
                self.assertEqual(by[name]['recertification_date'], '2027-09-17')

    def test_shared_helpers_and_required_package_resources(self):
        self.assertGreaterEqual(len(PACKAGE_PATHS), 24)
        for relative in PACKAGE_PATHS:
            self.assertEqual((ROOT / 'skills' / relative / 'scripts/wealth_contract.py').read_bytes(), (ROOT / 'shared/wealth-management/wealth_contract.py').read_bytes())
        for helper, names in [('wealth_analysis.py', ANALYSIS_PACKAGES), ('wealth_workflow.py', P2_PACKAGES)]:
            for name in names:
                self.assertEqual((package(name) / 'scripts' / helper).read_bytes(), (ROOT / 'shared/wealth-management' / helper).read_bytes())
        for name in P2_PACKAGES:
            for relative in ['SKILL.md', 'CHANGELOG.md', 'assets/output-template.md', 'references/domain-rules.md', 'references/controls.md', 'references/source-map.md', 'references/handoffs.md', 'evals/evals.json']:
                self.assertTrue((package(name) / relative).is_file(), (name, relative))

    def test_router_targets_are_real_and_scope_is_separate(self):
        script = 'import json; from route import ROUTES; print(json.dumps(ROUTES))'
        result = subprocess.run([sys.executable, '-c', script], cwd=package('wealth-management-router') / 'scripts', capture_output=True, text=True, check=True)
        routes = json.loads(result.stdout)
        self.assertGreaterEqual(len(routes), 25)
        self.assertEqual(len({r[0] for r in routes.values()}), len(routes))
        catalog = {r['name'] for r in json.loads((ROOT / 'catalog/skills-catalog.json').read_text())['skills']}
        self.assertTrue({r[0] for r in routes.values()} <= catalog)
        doc = {k: v for k, v in fixture().items() if k in ('schema_version', 'request_id', 'household_id', 'as_of', 'engagement', 'sources')}
        doc.update(scope_type='advisor-book', book_id='B42', household_id='book:B42', intents=['book-review', 'private-markets'], upstream_artifact_ids=[], unresolved_issues=[])
        out = run('wealth-management-router', 'route.py', doc)
        self.assertIn('separate-subject-requests', codes(out))
        self.assertEqual([s['target_scope'] for s in out['result']['steps']], ['advisor-book', 'household'])
        self.assertFalse(out['action_taken'])

    def test_router_issue_mapping_retains_origin_and_target_blocks_draft(self):
        doc = fixture()
        issue = {'artifact_id':'SOURCE-ARTIFACT-42', 'code':'permission-dispute', 'message':'The recorded permission is disputed.', 'source_ids':['evidence']}
        request = {k: v for k, v in doc.items() if k in ('schema_version', 'request_id', 'household_id', 'as_of', 'engagement', 'sources')}
        request.update(intents=['prospect-referral'], upstream_artifact_ids=['SOURCE-ARTIFACT-42'], unresolved_issues=[issue])
        routed = run('wealth-management-router', 'route.py', request)
        preserved = routed['result']['handoff_context']['unresolved_issues'][0]
        doc['upstream_issues'] = [{**preserved, 'status':'unresolved'}]
        out = build(doc)
        finding = next(f for f in out['findings'] if f['code'] == 'upstream-unresolved')
        self.assertEqual(finding['upstream_artifact_id'], issue['artifact_id'])
        self.assertEqual(finding['upstream_code'], issue['code'])
        self.assertIsNone(out['result']['outreach_draft'])
        doc['unresolved_issues'] = []
        run(PROSPECT, 'validate_input.py', doc, 1)

    def test_current_policy_and_explicit_upstream_inventory_required(self):
        for name in P2_PACKAGES:
            for change in ['inventory', 'capacity', 'policy-date', 'resolution']:
                with self.subTest(name=name, change=change):
                    doc = fixture(name)
                    if change == 'inventory':
                        del doc['upstream_issues']
                    elif change == 'capacity':
                        doc['policy']['capacity'] = 'invalid-capacity'
                    elif change == 'policy-date':
                        doc['policy']['valid_until'] = '2020-01-01'
                    else:
                        doc['upstream_issues'] = [{'artifact_id':'A', 'code':'C', 'message':'Resolved without record', 'status':'resolved', 'source_ids':[doc['sources'][0]['source_id']]}]
                    run(name, 'validate_input.py', doc, 1)

    def test_every_p2_target_preserves_issue_origin_and_resolution_evidence(self):
        for name in P2_PACKAGES:
            with self.subTest(name=name):
                doc = fixture(name); source = doc['sources'][0]['source_id']
                issue = {'artifact_id':'ORIGIN-42', 'code':'scope-disputed', 'message':'A source owner disputes the reviewed scope.', 'status':'unresolved', 'source_ids':[source]}
                doc['upstream_issues'].append(issue)
                out = run(name, 'calculate_or_transform.py', doc)
                finding = next(f for f in out['findings'] if f.get('upstream_artifact_id') == 'ORIGIN-42')
                self.assertEqual(finding['upstream_code'], 'scope-disputed')
                self.assertEqual(out['status'], 'needs-data')
                self.assertIn(issue, out['result']['upstream_issues'])
                self.assertEqual(run(name, 'validate_output.py', out)['errors'], [])
                issue.update(status='resolved', resolution={'owner':'Attributed record owner', 'reference':'synthetic://resolution/42', 'as_of':doc['as_of'], 'source_ids':[source]})
                out = run(name, 'calculate_or_transform.py', doc)
                self.assertFalse(any(f.get('upstream_artifact_id') == 'ORIGIN-42' for f in out['findings']))
                self.assertIn(issue, out['result']['upstream_issues'])
                self.assertFalse(out['action_taken'])


class ProspectForwardScenarios(unittest.TestCase):
    def assert_withheld(self, doc, code):
        out = build(doc)
        self.assertIn(code, codes(out))
        self.assertEqual(out['status'], 'needs-data')
        self.assertIsNone(out['result']['outreach_draft'])
        self.assertFalse(out['action_taken'])
        self.assertEqual(out['delivery_status'], 'not-delivered')
        return out

    def test_fresh_nonreferral_phone_discussion_is_sourced_internal_draft(self):
        out = build(fixture())
        self.assertEqual(out['status'], 'review-ready')
        draft = out['result']['outreach_draft']
        self.assertEqual(draft['channel'], 'manual-phone')
        self.assertIn('Which planning priorities would you like to discuss?', draft['body'])
        self.assertNotIn('Prospect requested a conversation', draft['body'])
        self.assertFalse(draft['send_authorization'])
        self.assertEqual(out['result']['prospect_qualification'], 'not-decided')
        self.assertEqual(run(PROSPECT, 'validate_output.py', out)['errors'], [])

    def test_global_optout_overrides_clear_channel_and_recorded_permission(self):
        doc = fixture(); doc['contact_controls'][0]['opt_out_status'] = 'opted-out'
        self.assert_withheld(doc, 'contact-suppression')

    def test_public_source_and_referral_basis_never_supply_contact_permission(self):
        for basis in ['public-record', 'referral-only']:
            with self.subTest(basis=basis):
                doc = fixture(); doc['research_permissions'][0]['kind'] = 'approved-public-record'
                doc['channel_permissions'][0]['basis'] = basis
                out = self.assert_withheld(doc, 'contact-permission-gap')
                self.assertEqual(len(out['result']['supported_facts']), 1)

    def test_internal_research_permission_does_not_authorize_outreach_content(self):
        doc = fixture(); doc['research_permissions'][0]['permitted_uses'] = ['internal-research']
        out = self.assert_withheld(doc, 'outreach-service-gap')
        self.assertEqual(len(out['result']['supported_facts']), 1)

    def test_conflicting_and_stale_permission_records_withhold(self):
        doc = fixture(); competing = deepcopy(doc['channel_permissions'][0])
        competing.update(permission_id='OLD', status='withdrawn')
        doc['channel_permissions'].append(competing)
        self.assert_withheld(doc, 'contact-permission-gap')
        doc = fixture(); doc['channel_permissions'][0]['valid_until'] = '2026-09-16'
        self.assert_withheld(doc, 'current-evidence-gap')

    def test_unknown_observation_and_missing_global_screen_remain_open(self):
        doc = fixture(); doc['facts'][0]['observed_date'] = None
        out = self.assert_withheld(doc, 'fact-date-gap')
        self.assertEqual(out['result']['supported_facts'], [])
        doc = fixture(); doc['contact_controls'] = doc['contact_controls'][1:]
        self.assert_withheld(doc, 'suppression-inventory-gap')

    def test_extra_conflicting_review_is_not_hidden_by_required_clear_reviews(self):
        doc = fixture(); extra = deepcopy(doc['review_records'][0])
        extra.update(review_id='EXTRA', topic='referral-compensation', status='conflicting')
        doc['review_records'].append(extra)
        self.assert_withheld(doc, 'review-conflict')

    def test_altered_recipient_text_and_removed_block_cannot_validate(self):
        out = build(fixture()); out['result']['outreach_draft']['body'] += '\nGuaranteed results.'
        run(PROSPECT, 'validate_output.py', out, 1)
        doc = fixture(); doc['contact_controls'][0]['screening_status'] = 'block-recorded'
        out = build(doc); out['findings'] = []; out['status'] = 'review-ready'
        run(PROSPECT, 'validate_output.py', out, 1)


if __name__ == '__main__':
    unittest.main()
