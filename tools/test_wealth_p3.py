"""P3 catalog, subject identity, issue lineage and output-integrity integration checks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from build_catalog_from_xlsx import apply_changes
from spec_card import card
from sync_wealth_contract import PACKAGE_PATHS, P3_PACKAGES, WORKFLOW_PACKAGES

ROOT = Path(__file__).resolve().parents[1]
SCOPES = {
    'family-wealth-governance-preparer': ('family-group', 'family_id', 'family:', 'family-governance'),
    'trust-administration-reviewer': ('trust', 'trust_id', 'trust:', 'trust-administration'),
}


def package(name):
    return ROOT / 'skills/wealth-management' / name


def request(name):
    # Author fixtures establish schema shape here; independent forward harnesses use fresh cases.
    return json.loads((package(name) / 'evals/files/request.json').read_text())


def cli(name, script, doc, expected=0):
    with tempfile.TemporaryDirectory(prefix='wealth-p3-integration-') as folder:
        path = Path(folder) / 'input.json'
        path.write_text(json.dumps(doc, allow_nan=False))
        result = subprocess.run([sys.executable, str(package(name) / 'scripts' / script), str(path)], capture_output=True, text=True)
    if result.returncode != expected:
        raise AssertionError(f'{name}/{script}: {result.returncode}; {result.stdout}{result.stderr}')
    return json.loads(result.stdout)


class P3Integration(unittest.TestCase):
    def test_current_catalog_scope_metadata_and_idempotence(self):
        import yaml
        catalog = json.loads((ROOT / 'catalog/skills-catalog.json').read_text())
        rows = catalog['skills']; by = {r['name']: r for r in rows}
        disk = {p.parent.name for p in (ROOT / 'skills').glob('*/*/SKILL.md')}
        self.assertEqual(catalog['count'], len(rows))
        self.assertEqual(len(by), len(rows))
        self.assertEqual(set(by), disk)
        self.assertEqual(len(list((ROOT / 'skills/wealth-management').glob('*/SKILL.md'))), 27)
        adds = json.loads((ROOT / 'catalog/provisional-additions.json').read_text())
        overrides = json.loads((ROOT / 'catalog/approved-overrides.json').read_text())
        # Other domain milestones may add packages; preserve catalog integrity
        # and the explicit wealth inventory without fixing a portfolio-wide count.
        self.assertEqual(len({r['name'] for r in adds}), len(adds))
        self.assertEqual(apply_changes(rows, adds, overrides), rows)
        self.assertNotIn('financial-goal-progress-analyzer', by)
        self.assertNotIn('suitability-reg-bi-reviewer', by)
        for name in (*P3_PACKAGES, 'wealth-management-router'):
            front = yaml.safe_load((package(name) / 'SKILL.md').read_text().split('---', 2)[1])
            self.assertEqual(front['name'], name)
            self.assertEqual(front['description'], by[name]['description'])
            self.assertEqual(front['metadata'], yaml.safe_load(card(by[name])[0])['metadata'])
            self.assertEqual(by[name]['delivery_wave'], 'Wave 9 - wealth management P3')
            self.assertEqual(by[name]['version'], '0.4.0' if name == 'wealth-management-router' else '0.1.0')
            self.assertEqual(by[name]['recertification_date'], '2027-09-17')

    def test_shared_contracts_and_full_package_resources(self):
        self.assertEqual(len(PACKAGE_PATHS), 26)
        self.assertEqual(len(WORKFLOW_PACKAGES), 6)
        for relative in PACKAGE_PATHS:
            self.assertEqual((ROOT / 'skills' / relative / 'scripts/wealth_contract.py').read_bytes(), (ROOT / 'shared/wealth-management/wealth_contract.py').read_bytes())
        for name in WORKFLOW_PACKAGES:
            self.assertEqual((package(name) / 'scripts/wealth_workflow.py').read_bytes(), (ROOT / 'shared/wealth-management/wealth_workflow.py').read_bytes())
        for name in P3_PACKAGES:
            for resource in ['SKILL.md', 'CHANGELOG.md', 'assets/output-template.md', 'references/domain-rules.md', 'references/source-map.md', 'references/controls.md', 'references/handoffs.md', 'evals/evals.json']:
                self.assertTrue((package(name) / resource).is_file(), (name, resource))

    def test_router_preserves_all_27_targets_and_subject_context(self):
        result = subprocess.run([sys.executable, '-c', 'import json; from route import ROUTES; print(json.dumps(ROUTES))'], cwd=package('wealth-management-router') / 'scripts', capture_output=True, text=True, check=True)
        routes = json.loads(result.stdout)
        self.assertEqual(len(routes), 27)
        self.assertEqual(len({v[0] for v in routes.values()}), 27)
        for name, (scope, key, prefix, intent) in SCOPES.items():
            source = request(name)
            doc = {k: source[k] for k in ('schema_version', 'request_id', 'household_id', 'as_of', 'engagement', 'sources', 'scope_type', key)}
            doc.update(intents=[intent], upstream_artifact_ids=[], unresolved_issues=[])
            out = cli('wealth-management-router', 'route.py', doc)
            self.assertEqual(out['status'], 'review-ready')
            self.assertEqual(out['result']['steps'][0]['target_skill'], name)
            self.assertEqual(out['result']['steps'][0]['target_scope'], scope)
            self.assertEqual(out['result']['handoff_context'][key], source[key])
            self.assertEqual(out['household_id'], prefix + source[key])

    def test_mismatched_subject_id_or_scope_rejects_at_target(self):
        for name, (scope, key, prefix, intent) in SCOPES.items():
            for field, value in [(key, 'UNRELATED'), ('scope_type', 'household'), ('household_id', 'ACTUAL-HOUSEHOLD')]:
                with self.subTest(name=name, field=field):
                    doc = request(name); doc[field] = value
                    cli(name, 'validate_input.py', doc, 1)

    def test_origin_issue_survives_routing_and_target_reconstruction(self):
        for name, (scope, key, prefix, intent) in SCOPES.items():
            with self.subTest(name=name):
                doc = request(name); sid = doc['sources'][0]['source_id']
                issue = {'artifact_id': 'ORIGIN-P3-42', 'code': 'authority-disputed', 'message': 'The supplied authority is disputed by its record owner.', 'source_ids': [sid]}
                route_input = {k: doc[k] for k in ('schema_version', 'request_id', 'household_id', 'as_of', 'engagement', 'sources', 'scope_type', key)}
                route_input.update(intents=[intent], upstream_artifact_ids=[issue['artifact_id']], unresolved_issues=[issue])
                routed = cli('wealth-management-router', 'route.py', route_input)
                item = {**routed['result']['handoff_context']['unresolved_issues'][0], 'status': 'unresolved'}
                doc['upstream_issues'].append(item)
                out = cli(name, 'calculate_or_transform.py', doc)
                finding = next(f for f in out['findings'] if f.get('upstream_artifact_id') == issue['artifact_id'])
                self.assertEqual(finding['upstream_code'], issue['code'])
                self.assertEqual(finding['message'], issue['message'])
                self.assertEqual(out['status'], 'needs-data')
                self.assertIn(item, out['result']['handoff_context']['upstream_issues'])
                self.assertEqual(out['result']['handoff_context'][key], doc[key])
                self.assertEqual(cli(name, 'validate_output.py', out)['errors'], [])
                item.update(status='resolved', resolution={'owner': 'Attributed source owner', 'reference': 'synthetic://resolution/42', 'as_of': doc['as_of'], 'source_ids': [sid]})
                resolved = cli(name, 'calculate_or_transform.py', doc)
                self.assertIn(item, resolved['result']['upstream_issues'])
                self.assertFalse(any(f.get('upstream_artifact_id') == issue['artifact_id'] for f in resolved['findings']))
                self.assertFalse(resolved['action_taken'])

    def test_omitted_inventory_unmapped_alias_and_unattributed_resolution_reject(self):
        for name in P3_PACKAGES:
            for variant in ('omitted', 'alias', 'resolution'):
                with self.subTest(name=name, variant=variant):
                    doc = request(name)
                    if variant == 'omitted':
                        del doc['upstream_issues']
                    elif variant == 'alias':
                        doc['unresolved_issues'] = []
                    else:
                        doc['upstream_issues'] = [{'artifact_id': 'A', 'code': 'C', 'message': 'Unattributed resolution', 'status': 'resolved', 'source_ids': [doc['sources'][0]['source_id']]}]
                    cli(name, 'validate_input.py', doc, 1)

    def test_output_cannot_change_subject_or_claim_action(self):
        for name in P3_PACKAGES:
            for key, value in [('household_id', 'UNRELATED'), ('action_taken', True), ('human_review_required', False), ('delivery_status', 'delivered')]:
                with self.subTest(name=name, field=key):
                    out = cli(name, 'calculate_or_transform.py', request(name))
                    out[key] = value
                    cli(name, 'validate_output.py', out, 1)


if __name__ == '__main__':
    unittest.main()
