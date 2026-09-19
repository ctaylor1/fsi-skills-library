"""Phase 2 native compositions and deployment invariants; synthetic evidence only."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / 'skills/insurance'
sys.path.insert(0, str(ROOT / 'shared/insurance'))
from insurance_contract import make_handoff, stable_hash


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


handoffs = module('insurance_phase2_handoffs', SKILLS / 'insurance-router/scripts/validate_handoff.py')
routing = module('insurance_phase2_routing', SKILLS / 'insurance-router/scripts/route.py')


class Phase2Integration(unittest.TestCase):
    def fixture(self, name):
        manifest = json.loads((SKILLS / name / 'evals/evals.json').read_text())
        command = next(e['command'] for e in manifest['evals'] if 'command' in e and 'scripts/validate_input.py' in e['command'] and e.get('expect_exit', 0) == 0)
        return json.loads((SKILLS / name / shlex.split(command)[-1]).read_text())

    def calculate(self, name, doc, directory=None):
        package = directory or SKILLS / name
        result = subprocess.run([sys.executable, '-B', str(package / 'scripts/calculate_or_transform.py')],
                                input=json.dumps(doc), capture_output=True, text=True,
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, cwd=package)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = json.loads(result.stdout)
        validated = subprocess.run([sys.executable, '-B', str(package / 'scripts/validate_output.py')],
                                   input=json.dumps(output), capture_output=True, text=True, cwd=package)
        self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
        return output

    def test_all_phase2_routes_have_installed_targets_and_role_boundaries(self):
        names = set(json.loads((ROOT / 'catalog/insurance-phase2-capabilities.json').read_text())['packages'])
        routes = json.loads((SKILLS / 'insurance-router/references/routes.json').read_text())['intents']
        exercised = set()
        for intent, config in routes.items():
            if config.get('target') not in names:
                continue
            request = {'intent': intent, 'available_skills': sorted(p.name for p in SKILLS.iterdir() if p.is_dir())}
            for field in ('participant', 'line_of_business'):
                if config.get(field):
                    request[field] = config[field][0]
            out = routing.route(request)
            self.assertEqual(out['lead_skill'], config['target'], intent)
            self.assertEqual(out['status'], 'routed', intent)
            self.assertFalse(out['authority_granted'])
            exercised.add(config['target'])
        self.assertEqual(exercised, names)
        for intent in ('life-underwriting', 'claim-coverage', 'pc-rate-adequacy'):
            self.assertNotEqual(routing.route({'intent': intent, 'participant': 'carrier', 'line_of_business': 'health'})['status'], 'routed')

    def test_every_new_package_runs_without_repo_dependencies(self):
        names = json.loads((ROOT / 'catalog/insurance-phase2-capabilities.json').read_text())['packages']
        with tempfile.TemporaryDirectory(prefix='insurance-phase2-standalone-') as temporary:
            for name in names:
                with self.subTest(name=name):
                    destination = Path(temporary) / name
                    shutil.copytree(SKILLS / name, destination, ignore=shutil.ignore_patterns('__pycache__'))
                    output = self.calculate(name, self.fixture(name), destination)
                    self.assertFalse(output['action_taken'])
                    self.assertEqual(output['execution'], 'not_performed')

    def coverage_handoff(self):
        source = self.fixture('claim-coverage-reviewer')
        source['data']['hypotheses'][0]['contrary_evidence_reviewed'] = False
        output = self.calculate('claim-coverage-reviewer', source)
        target = self.fixture('claim-handling-plan-builder')
        target['sources'].append({'source_ref': 'coverage-review', 'version': output['artifact']['output_hash']})
        target['data']['tasks'].append({
            'task_id': 'T-COVERAGE', 'description': 'Review contrary evidence for ' + output['results']['coverage_hypotheses'][0]['hypothesis_id'],
            'owner': 'Authorized coverage specialist', 'state': 'open', 'due_date': '2026-09-21',
            'deadline_basis': 'service_target', 'depends_on': ['T-1'], 'source_refs': ['coverage-review'],
            'mapping_basis': 'Synthetic reviewer selected this investigation task; no coverage conclusion inferred'})
        return make_handoff(output['artifact'], target_skill='claim-handling-plan-builder', target_input=target,
                            requested_output='Prepare handling tasks while preserving the unresolved contrary-evidence review')

    def test_coverage_findings_reach_real_handling_receiver(self):
        packet = self.coverage_handoff()
        self.assertEqual(handoffs.check(packet, ROOT / 'skills'), [])
        output = self.calculate(packet['target_skill'], packet['target_input'])
        self.assertEqual(output['status'], 'needs-data')
        self.assertTrue(any('contrary evidence' in x for x in output['unresolved_issues']))
        self.assertEqual(output['results']['claim_resolution'], 'not_determined')
        self.assertIn('T-COVERAGE', [t['task_id'] for t in output['results']['task_queue']])
        self.assertIn(packet['source_artifact'], output['source_document']['upstream_artifacts'])

    def test_receiver_validation_rejects_invalid_dependencies_and_dropped_issues(self):
        packet = self.coverage_handoff()
        for change in ('cycle', 'issues'):
            changed = copy.deepcopy(packet)
            if change == 'cycle':
                changed['target_input']['data']['tasks'][0]['depends_on'] = ['T-COVERAGE']
            else:
                changed['target_input']['unresolved_issues'] = []
            changed['target_input_hash'] = stable_hash(changed['target_input'])
            self.assertTrue(handoffs.check(changed, ROOT / 'skills'))

    def test_financial_scenario_does_not_supply_payment_authority(self):
        financial = self.calculate('claim-financial-evaluation-assistant', self.fixture('claim-financial-evaluation-assistant'))
        target = self.fixture('claim-payment-closure-reviewer')
        selected = financial['results']['scenarios'][0]
        target['sources'].append({'source_ref': 'reviewed-scenario-selection', 'version': 'synthetic-v1'})
        target['data']['payment_request']['amount'] = selected['future_indemnity']
        target['data']['payment_request']['source_refs'].append('reviewed-scenario-selection')
        target['selection_basis'] = {'scenario_id': selected['scenario_id'], 'reviewed_by': 'Synthetic claims reviewer',
                                     'note': 'Separate draft selection for this test; a financial scenario alone is not authority'}
        packet = make_handoff(financial['artifact'], target_skill='claim-payment-closure-reviewer', target_input=target,
                              requested_output='Review selected draft payment against separately supplied authority and controls')
        self.assertEqual(handoffs.check(packet, ROOT / 'skills'), [])
        output = self.calculate(packet['target_skill'], packet['target_input'])
        self.assertEqual(output['results']['payment_review_status'], 'blocked')
        self.assertFalse(output['results']['payment_executed'])
        # Separately supplied authority, not the scenario envelope, changes the review gate.
        packet['target_input']['data']['authority']['limit'] = '100000'
        packet['target_input']['data']['authority']['source_refs'] = ['reviewed-scenario-selection']
        output = self.calculate(packet['target_skill'], packet['target_input'])
        self.assertEqual(output['results']['payment_review_status'], 'ready_for_authorized_review')
        self.assertEqual(output['results']['closure_review_status'], 'blocked')
        self.assertFalse(output['results']['payment_executed'])

    def test_unrelated_claim_cannot_promote_receiver_readiness(self):
        source = self.fixture('claim-financial-evaluation-assistant')
        source['context']['object_id'] = 'ANOTHER-CLAIM'
        upstream = self.calculate('claim-financial-evaluation-assistant', source)
        target = self.fixture('claim-handling-plan-builder')
        packet = make_handoff(upstream['artifact'], target_skill='claim-handling-plan-builder', target_input=target,
                              requested_output='Review handling plan')
        output = self.calculate(packet['target_skill'], packet['target_input'])
        self.assertEqual(output['status'], 'needs-data')
        self.assertTrue(any('upstream context differs' in x for x in output['unresolved_issues']))


if __name__ == '__main__':
    unittest.main()
