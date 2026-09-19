"""P1 catalog, handoff and independently authored financial forward scenarios.

These tests verify the bounded implementations, not professional acceptance or source truth.
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
from sync_wealth_contract import ANALYSIS_PACKAGES, PACKAGE_PATHS, P1_PACKAGES

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tools/fixtures/wealth-p1-forward'
MANAGER = 'investment-manager-due-diligence-reviewer'


def package(name):
    return ROOT / 'skills' / ('asset-management' if name == MANAGER else 'wealth-management') / name


def read_case(name):
    return json.loads((FIXTURES / (name + '.json')).read_text())


def run_script(name, script, doc, expected_exit=0):
    with tempfile.TemporaryDirectory(prefix='fsi-p1-check-') as folder:
        path = Path(folder) / 'input.json'
        path.write_text(json.dumps(doc, allow_nan=False))
        result = subprocess.run([sys.executable, 'scripts/' + script, str(path)], cwd=package(name), capture_output=True, text=True)
    if result.returncode != expected_exit:
        raise AssertionError(f'{name}/{script}: exit {result.returncode}; {result.stdout}{result.stderr}')
    if script == 'validate_input.py':
        return result.stdout
    # Some validators emit a JSON result followed by a human-readable PASS/FAIL line.
    return json.JSONDecoder().raw_decode(result.stdout.lstrip())[0] if result.stdout.strip() else None


def calculate(name, doc):
    return run_script(name, 'calculate_or_transform.py', doc)


def codes(out):
    return {f['code'] for f in out['findings']}


class IntegrationTests(unittest.TestCase):
    def test_catalog_scope_and_reproducible_metadata(self):
        import yaml
        cat = json.loads((ROOT / 'catalog/skills-catalog.json').read_text())
        by = {row['name']: row for row in cat['skills']}
        self.assertGreaterEqual(cat['count'], 233)
        self.assertGreaterEqual(len(list((ROOT / 'skills/wealth-management').glob('*/SKILL.md'))), 21)
        self.assertNotIn('financial-goal-progress-analyzer', by)
        self.assertEqual(len(P1_PACKAGES), 12)
        for name in (*P1_PACKAGES, MANAGER, 'wealth-management-router'):
            front = yaml.safe_load((package(name) / 'SKILL.md').read_text().split('---', 2)[1])
            self.assertEqual(front['metadata'], yaml.safe_load(card(by[name])[0])['metadata'], name)
            if name != 'wealth-management-router':
                self.assertEqual(by[name]['delivery_wave'], 'Wave 7 - wealth management P1')
        self.assertEqual(by['portfolio-rebalancing-assistant']['risk_tier'].split()[0], 'R4')
        self.assertIn('Draft', by['portfolio-rebalancing-assistant']['action_mode'])
        self.assertEqual(by[MANAGER]['category'], 'Asset Management')

    def test_catalog_regeneration_preserves_both_migrations(self):
        cat = json.loads((ROOT / 'catalog/skills-catalog.json').read_text())['skills']
        adds = json.loads((ROOT / 'catalog/provisional-additions.json').read_text())
        changes = json.loads((ROOT / 'catalog/approved-overrides.json').read_text())
        self.assertGreaterEqual(len(adds), 60)
        self.assertEqual(changes['renames']['financial-goal-progress-analyzer'], 'household-financial-planning-assistant')
        self.assertEqual(changes['renames']['suitability-reg-bi-reviewer'], 'investment-recommendation-evidence-reviewer')
        rebuilt = apply_changes(cat, adds, changes)
        self.assertEqual(rebuilt, apply_changes(rebuilt, adds, changes))
        self.assertEqual({s['name'] for s in rebuilt}, {s['name'] for s in cat})

    def test_all_shared_copies_and_resources_exist(self):
        contract = (ROOT / 'shared/wealth-management/wealth_contract.py').read_bytes()
        self.assertGreaterEqual(len(PACKAGE_PATHS), 20)
        for name in PACKAGE_PATHS:
            self.assertEqual((ROOT / 'skills' / name / 'scripts/wealth_contract.py').read_bytes(), contract, name)
        helper = (ROOT / 'shared/wealth-management/wealth_analysis.py').read_bytes()
        for name in ANALYSIS_PACKAGES:
            self.assertEqual((package(name) / 'scripts/wealth_analysis.py').read_bytes(), helper)
        for name in (*P1_PACKAGES, MANAGER):
            for path in ['assets/output-template.md', 'references/domain-rules.md', 'references/source-map.md', 'references/controls.md', 'references/handoffs.md']:
                self.assertTrue((package(name) / path).is_file(), (name, path))

    def test_all_router_destinations_and_p0_scope_preserved(self):
        # Separate process prevents package-local module names colliding.
        script = 'import json; from route import ROUTES; print(json.dumps(ROUTES))'
        result = subprocess.run([sys.executable, '-c', script], cwd=package('wealth-management-router') / 'scripts', capture_output=True, text=True, check=True)
        routes = json.loads(result.stdout)
        self.assertGreaterEqual(len(routes), 21)
        for name, _ in routes.values():
            self.assertTrue((package(name) / 'SKILL.md').exists(), name)
        for intent in ['discovery', 'onboarding', 'risk-profile', 'recommendation-evidence', 'client-review', 'follow-up', 'investor-protection', 'household-reconciliation']:
            self.assertIn(intent, routes)

    def test_router_issue_maps_into_tax_review_without_clearance(self):
        route_request = json.loads((package('wealth-management-router') / 'evals/files/request.json').read_text())
        issue = {'code': 'basis-reconciliation', 'message': 'Custodian and household basis still differ', 'source_ids': ['statement']}
        route_request.update(intents=['tax-review'], unresolved_issues=[issue], upstream_artifact_ids=['reconciliation-artifact-42'])
        routed = run_script('wealth-management-router', 'route.py', route_request)
        self.assertEqual(routed['status'], 'needs-data')
        tax = json.loads((package('tax-aware-investment-reviewer') / 'evals/files/request_example.json').read_text())
        # Explicit schema adapter: preserve identity/context, merge source identity, carry the issue.
        context = routed['result']['handoff_context']
        for field in ('household_id', 'as_of', 'engagement'):
            tax[field] = context[field]
        tax['sources'].append(next(s for s in context['sources'] if s['source_id'] == 'statement'))
        tax['unresolved_issues'] = deepcopy(context['unresolved_issues'])
        tax['upstream_artifact_ids'] = context['upstream_artifact_ids']
        out = calculate('tax-aware-investment-reviewer', tax)
        self.assertEqual(out['status'], 'needs-data')
        self.assertIn(issue, out['findings'])
        self.assertFalse(out['action_taken'])
        self.assertEqual(run_script('tax-aware-investment-reviewer', 'validate_output.py', out), {'errors': []})

    def test_every_p1_workflow_requires_and_retains_upstream_inventory(self):
        for name in (*P1_PACKAGES, MANAGER):
            with self.subTest(name=name):
                fixture = package(name) / 'evals/files/request_example.json'
                if not fixture.exists():
                    fixture = package(name) / 'evals/files/request.json'
                doc = json.loads(fixture.read_text())
                field = 'unresolved_issues' if name in ANALYSIS_PACKAGES else 'upstream_issues'
                issue = {'artifact_id': 'reconciler-case-42', 'code': 'ownership-conflict',
                         'message': 'Ownership of the funding account remains unresolved.',
                         'status': 'unresolved', 'source_ids': [doc['sources'][0]['source_id']]}
                doc[field] = [issue]
                out = calculate(name, doc)
                self.assertEqual(out['status'], 'needs-data')
                self.assertIn(issue['message'], json.dumps(out['findings']))
                self.assertFalse(out['action_taken'])
                del doc[field]
                if name in {'household-financial-planning-assistant', 'investment-policy-statement-builder', 'retirement-income-scenario-modeler'}:
                    # Planning preserves absent domain data in a validated needs-data draft.
                    incomplete = calculate(name, doc)
                    self.assertEqual(incomplete['status'], 'needs-data')
                    self.assertIn('upstream_issues', json.dumps(incomplete['findings']))
                else:
                    run_script(name, 'validate_input.py', doc, expected_exit=1)


class IndependentForwardTests(unittest.TestCase):
    def test_estate_separates_record_differences_from_legal_effect(self):
        out = calculate('estate-wealth-transfer-reviewer', read_case('estate-wealth-transfer-reviewer'))
        self.assertEqual(out['result']['review_summary']['coordination_differences'], 2)
        self.assertEqual(out['result']['asset_comparisons'][0]['legal_effect'], 'not-determined')
        self.assertEqual(out['status'], 'needs-data')

    def test_estate_consistent_records_and_unknown_share(self):
        n = 'estate-wealth-transfer-reviewer'; doc = read_case(n)
        doc['assets'][0].update(owner_party_ids=['TRUST'], document_ids=['TRUSTDOC'], registration='trust')
        self.assertEqual(calculate(n, doc)['status'], 'review-ready')
        beneficiary = {'party_id': 'CHILD', 'tier': 'primary', 'share': None, 'source_ids': ['records']}
        doc['assets'][0]['designation_status'] = 'documented'
        doc['intentions'][0]['beneficiaries'] = [beneficiary]
        doc['designations'] = [{'designation_id': 'NEW', 'asset_id': 'BROKER', 'status': 'current', 'document_ids': ['TRUSTDOC'], 'beneficiaries': [beneficiary], 'source_ids': ['records']}]
        self.assertIn('unknown-share', codes(calculate(n, doc)))

    def test_protection_four_known_scenarios_and_no_additive_total(self):
        n = 'protection-needs-reviewer'; out = calculate(n, read_case(n))
        self.assertEqual(out['status'], 'review-ready')
        rows = {r['type']: r['calculation'] for r in out['result']['scenarios']}
        self.assertEqual(rows['survivor']['remaining_scenario_gap'], '370000.00')
        self.assertEqual(rows['disability']['resource_surplus_under_assumptions'], '9500.00')
        self.assertEqual(rows['long-term-care']['modeled_insurance_offset'], '150000.00')
        self.assertEqual(rows['long-term-care']['remaining_scenario_gap'], '130000.00')
        self.assertEqual(rows['liability']['remaining_scenario_gap'], '150000.00')
        self.assertIsNone(out['result']['portfolio_total'])
        self.assertEqual(len(out['result']['resource_reuse'][0]['scenario_ids']), 4)

    def test_protection_unknown_resources_and_benefits_suppress(self):
        n = 'protection-needs-reviewer'; doc = read_case(n)
        doc['scenarios'][0]['assumptions']['life_benefit'] = None
        doc['scenarios'][1]['designated_resources'][0]['availability'] = 'uncertain'
        out = calculate(n, doc)
        self.assertIsNone(out['result']['scenarios'][0]['calculation'])
        self.assertIsNone(out['result']['scenarios'][1]['calculation'])
        self.assertTrue({'unknown-assumption', 'resource-gap'} <= codes(out))

    def test_combined_service_requests_cannot_reuse_cash(self):
        n = 'wealth-account-service-packager'; out = calculate(n, read_case(n))
        self.assertIn('aggregate-cash-shortfall', codes(out))
        self.assertEqual(out['result']['aggregate_cash_requests'][0]['requested_cash_total'], '75000.00')
        self.assertEqual(out['result']['submission_status'], 'not-submitted')

    def test_extra_conflicting_service_evidence_remains_open(self):
        n = 'wealth-account-service-packager'; doc = read_case(n)
        doc['accounts'][0]['available_cash'] = 100000
        self.assertEqual(calculate(n, doc)['status'], 'review-ready')
        doc['conditions'].append({'condition_id': 'EXTRA', 'service_request_id': 'TRANSFER', 'requirement': 'optional-detail', 'description': 'Conflicting instruction received', 'status': 'conflicting', 'source_ids': ['records']})
        self.assertIn('condition-conflict', codes(calculate(n, doc)))

    def test_manager_fees_and_cumulative_household_liquidity(self):
        out = calculate(MANAGER, read_case(MANAGER)); fees = out['result']['fee_illustration']
        self.assertEqual(fees['base_fee'], '30000.00')
        self.assertEqual(fees['incentive_fee'], '16500.00')
        self.assertEqual(fees['total_illustrated_fee'], '46500.00')
        self.assertEqual(fees['illustrated_net_gain'], '193500.00')
        rows = out['result']['household_liquidity_review']
        self.assertEqual(rows[0]['assessment'], 'modeled-timing-and-amount-fit')
        self.assertEqual(rows[1]['assessment'], 'liquidity-concern')
        self.assertEqual(rows[1]['cumulative_amount'], '300000.00')
        self.assertEqual(out['result']['monitoring_plan']['next_scheduled_review'], '2026-11-15')
        self.assertEqual(out['result']['selection_decision'], 'not-made')

    def test_manager_negative_documented_and_nonindependent_evidence(self):
        doc = read_case(MANAGER); doc['evidence'][1]['value'] = False
        self.assertIn('diligence-concern', codes(calculate(MANAGER, doc)))
        doc['evidence'][1]['value'] = 'Report'
        doc['evidence'][1]['origin'] = 'manager-reported'
        self.assertIn('diligence-data-gap', codes(calculate(MANAGER, doc)))

    def test_each_forward_artifact_reconstructs_and_rejects_altered_identity(self):
        for path in FIXTURES.glob('*.json'):
            name = path.stem
            with self.subTest(name=name):
                out = calculate(name, read_case(name))
                run_script(name, 'validate_output.py', out)
                out['result']['input_snapshot']['household_id'] = 'CHANGED'
                run_script(name, 'validate_output.py', out, expected_exit=1)


if __name__ == '__main__':
    unittest.main()
