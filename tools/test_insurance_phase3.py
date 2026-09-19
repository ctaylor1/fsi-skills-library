"""Synthetic Phase 3 native compositions and installation boundaries."""
import copy
from decimal import Decimal
import importlib.util
import json
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


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


handoffs = load('p3_handoffs', SKILLS / 'insurance-router/scripts/validate_handoff.py')
routing = load('p3_routing', SKILLS / 'insurance-router/scripts/route.py')


class Phase3Integration(unittest.TestCase):
    def fixture(self, name):
        manifest = json.loads((SKILLS / name / 'evals/evals.json').read_text())
        cmd = next(e['command'] for e in manifest['evals'] if 'command' in e and 'scripts/validate_input.py' in e['command'] and e.get('expect_exit', 0) == 0)
        return json.loads((SKILLS / name / shlex.split(cmd)[-1]).read_text())

    def calculate(self, name, doc, directory=None):
        package = directory or SKILLS / name
        result = subprocess.run([sys.executable, '-B', str(package / 'scripts/calculate_or_transform.py')],
                                input=json.dumps(doc), capture_output=True, text=True, cwd=package)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = json.loads(result.stdout)
        checked = subprocess.run([sys.executable, '-B', str(package / 'scripts/validate_output.py')],
                                 input=json.dumps(output), capture_output=True, text=True, cwd=package)
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        return output

    def test_all_specialist_routes_and_remaining_boundaries(self):
        names = set(json.loads((ROOT / 'catalog/insurance-phase3-capabilities.json').read_text())['packages'])
        routes = json.loads((SKILLS / 'insurance-router/references/routes.json').read_text())['intents']
        seen = set()
        for intent, config in routes.items():
            if config.get('target') not in names:
                continue
            request = {'intent': intent, 'available_skills': sorted(p.name for p in SKILLS.iterdir() if p.is_dir())}
            for field in ('participant', 'line_of_business'):
                if config.get(field):
                    request[field] = config[field][0]
            output = routing.route(request)
            self.assertEqual(output['status'], 'routed', intent)
            self.assertEqual(output['lead_skill'], config['target'], intent)
            self.assertFalse(output['authority_granted'])
            seen.add(output['lead_skill'])
        self.assertEqual(seen, names)
        for line in ('pc', 'life', 'disability', 'long-term-care'):
            result = routing.route({'intent': 'claim-appeal', 'participant': 'claimant', 'line_of_business': line})
            self.assertEqual(result['lead_skill'], 'claimant-dispute-packager')
        self.assertEqual(routing.route({'intent': 'claim-appeal', 'participant': 'member', 'line_of_business': 'health'})['lead_skill'], 'health-benefit-appeal-packager')
        self.assertEqual(routing.route({'intent': 'disability-care-benefit', 'participant': 'claimant', 'line_of_business': 'disability'})['status'], 'needs-clarification')
        for intent in ('core-modernization', 'workflow-design', 'health-plan-pricing', 'parametric-trigger'):
            self.assertEqual(routing.route({'intent': intent})['status'], 'capability-gap')

    def test_all_21_packages_work_in_standalone_copies(self):
        names = json.loads((ROOT / 'catalog/insurance-phase3-capabilities.json').read_text())['packages']
        with tempfile.TemporaryDirectory(prefix='insurance-p3-standalone-') as temp:
            for name in names:
                with self.subTest(name=name):
                    target = Path(temp) / name
                    shutil.copytree(SKILLS / name, target, ignore=shutil.ignore_patterns('__pycache__'))
                    output = self.calculate(name, self.fixture(name), target)
                    self.assertFalse(output['action_taken'])
                    self.assertEqual(output['execution'], 'not_performed')

    def capital_packet(self, unresolved=False):
        source = self.fixture('insurance-capital-solvency-analyzer')
        if unresolved:
            source['unresolved_issues'] = ['Stress assumption independent challenge is outstanding']
        output = self.calculate('insurance-capital-solvency-analyzer', source)
        target = self.fixture('insurance-orsa-packager')
        stress = output['results']['stress_bridges'][0]
        target['sources'].append({'source_ref': 'native-capital-stress', 'version': output['artifact']['output_hash'], 'as_of': output['as_of']})
        # The mapping explicitly binds the supplied ORSA measurement bases to this
        # synthetic capital method; no statutory-to-economic conversion is inferred.
        basis = output['results']['basis']
        for key in ('available_capital_basis', 'required_capital_basis'):
            target['data'][key] = basis
            target['data']['profile'][key] = basis
            for row in target['data']['capital_measures']:
                row[key] = basis
        row = next(x for x in target['data']['capital_measures'] if x['scenario_id'] == stress['scenario_id'])
        row.update(available_capital=stress['available_capital'], required_capital=stress['required_capital'],
                   reported_surplus=str(Decimal(stress['available_capital'])-Decimal(stress['required_capital'])),
                   source_refs=['native-capital-stress'])
        target['reviewed_basis_mapping'] = {'reviewed_by': 'Synthetic capital and risk owners',
                                           'basis': 'Same supplied method/basis/horizon in both native schemas',
                                           'denominator_name': output['results']['denominator_name'], 'source_refs': ['native-capital-stress']}
        return make_handoff(output['artifact'], target_skill='insurance-orsa-packager', target_input=target,
                            requested_output='Reconcile supplied capital stress with the ORSA risk/scenario evidence')

    def test_capital_stress_reaches_actual_orsa_receiver(self):
        packet = self.capital_packet()
        self.assertEqual(handoffs.check(packet, ROOT / 'skills'), [])
        output = self.calculate(packet['target_skill'], packet['target_input'])
        stress = next(x for x in output['results']['scenario_reconciliations'] if x['scenario_id'] == 'wind-stress')
        self.assertEqual(Decimal(stress['capital']['calculated_surplus']), Decimal(200))
        self.assertEqual(Decimal(stress['capital']['difference']), Decimal(0))
        self.assertFalse(output['results']['orsa_approved'])

    def test_capital_issues_and_native_receiver_validation_survive_handoff(self):
        packet = self.capital_packet(unresolved=True)
        output = self.calculate(packet['target_skill'], packet['target_input'])
        self.assertIn('Stress assumption independent challenge is outstanding', output['unresolved_issues'])
        self.assertNotEqual(output['completeness'], 'complete')
        bad = copy.deepcopy(packet)
        bad['target_input']['data']['capital_measures'][0]['available_capital'] = True
        bad['target_input_hash'] = stable_hash(bad['target_input'])
        self.assertTrue(handoffs.check(bad, ROOT / 'skills'))
        bad = copy.deepcopy(packet)
        bad['target_input']['unresolved_issues'] = []
        bad['target_input_hash'] = stable_hash(bad['target_input'])
        self.assertTrue(handoffs.check(bad, ROOT / 'skills'))

    def fraud_packet(self, mapped=True):
        source = self.fixture('insurance-fraud-pattern-analyzer')
        output = self.calculate('insurance-fraud-pattern-analyzer', source)
        signal = output['results']['signals'][0]
        target = self.fixture('insurance-siu-investigation-assistant')
        target['context'].update(represented_party=source['context']['represented_party'], object_id=signal['claim_ids'][0], line_of_business='pc')
        target['data']['profile']['lines_of_business'] = ['pc']
        target['data']['claim_id'] = signal['claim_ids'][0]
        target['data']['referral_question'] = 'Review shared payment token; relationship alone does not establish fraud'
        target['sources'].append({'source_ref': 'native-pattern', 'version': output['artifact']['output_hash'], 'as_of': output['as_of']})
        evidence = target['data']['evidence'][0]
        evidence.update(description='Shared '+signal['entity_type']+' across claims '+', '.join(signal['claim_ids']),
                        content_digest=stable_hash(signal), locator='Native pattern signals[0]', source_refs=['native-pattern'])
        target['data']['custody'][0]['content_digest'] = stable_hash(signal)
        target['data']['hypotheses'][0].update(question='Does the shared token reflect a legitimate shared service?',
                                               innocent_alternative='A shared payment processor can serve unrelated claimants')
        target['data']['evidence'][1]['description'] = 'Separately supplied synthetic payment-processor register'
        target['data']['links'][0]['reasoning'] = 'Pattern requires source identity review; no fraud inference'
        target['data']['links'][1]['reasoning'] = 'Registered shared processor is a legitimate alternative'
        target['data']['tasks'][0]['purpose'] = 'Resolve exact token identity and legitimate service explanation'
        if mapped:
            target['context_mappings'] = [{'source_artifact_hash': stable_hash(output['artifact']),
                'source_context': source['context'], 'target_context': target['context'],
                'reviewed_by': 'Synthetic authorized SIU intake owner',
                'basis': 'Explicit selection of one named claim from a book-level screen; separately supplied SIU case evidence and authority',
                'source_refs': ['native-pattern']}]
        return make_handoff(output['artifact'], target_skill='insurance-siu-investigation-assistant', target_input=target,
                            requested_output='Prepare a claim-specific evidence investigation plan; no fraud decision')

    def test_portfolio_signal_to_case_siu_preserves_alternative_and_mapping(self):
        packet = self.fraud_packet()
        self.assertEqual(handoffs.check(packet, ROOT / 'skills'), [])
        output = self.calculate(packet['target_skill'], packet['target_input'])
        self.assertEqual(output['results']['fraud_verdict'], 'not-determined')
        self.assertIn('shared payment processor', output['results']['hypothesis_matrix'][0]['innocent_alternative'].lower())
        self.assertFalse(output['results']['referral_submitted'])
        self.assertIn(packet['source_artifact'], output['source_document']['upstream_artifacts'])

    def test_scope_transition_without_mapping_is_not_complete(self):
        packet = self.fraud_packet(mapped=False)
        output = self.calculate(packet['target_skill'], packet['target_input'])
        self.assertEqual(output['status'], 'needs-data')
        self.assertTrue(any('upstream context differs' in issue for issue in output['unresolved_issues']))


if __name__ == '__main__':
    unittest.main()
