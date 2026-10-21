#!/usr/bin/env python3
"""Public entrypoint regressions for retiring the legacy surveillance bypass.

Historical fixtures are rejection inputs; current supplied-evidence arithmetic,
partial behavior and detached reconstruction remain independently asserted.
"""
from __future__ import annotations
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'skills/investment-research/issuer-credit-surveillance-reviewer'
SCRIPTS = PACKAGE / 'scripts'
MIGRATION = 'legacy surveillance migration required'
WIDENING = 'spread widened beyond supplied threshold'


def fixture(name='phase2_input.json'):
    return json.loads((PACKAGE / 'evals/files' / name).read_text())


def call(module, entry, *args, scripts=SCRIPTS):
    sys.path.insert(0, str(scripts))
    try:
        for name in ('phase2_domain', 'analysis_contract', 'research_runtime',
                     'native_integrity', 'surveillance_contract'):
            sys.modules.pop(name, None)
        spec = importlib.util.spec_from_file_location('_legacy_gate_' + module,
                                                       scripts / (module + '.py'))
        imported = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(imported)
        return getattr(imported, entry)(*args)
    finally:
        sys.path.pop(0)


def resolve_current_package(identifier):
    spec = importlib.util.spec_from_file_location('_legacy_gate_resolver', ROOT / 'tools/resolve_skill.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.resolve(identifier)


class SurveillanceLegacyGate(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='ir-legacy-gate-')
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)

    def cli(self, script, doc=None, original=None, *, stdin=False, raw=None, option='--input', extra=(), package=PACKAGE):
        args = [sys.executable, '-B', str(package / 'scripts' / (script + '.py'))]
        encoded = raw if raw is not None else json.dumps(doc)
        if stdin:
            input_text = encoded
        else:
            path = self.work / 'payload.json'
            path.write_text(encoded)
            args.append(str(path))
            input_text = None
        if original is not None:
            path = self.work / 'original.json'
            path.write_text(json.dumps(original))
            args += [option, str(path)]
        args += list(extra)
        result = subprocess.run(args, input=input_text, text=True, capture_output=True,
                                cwd=PACKAGE, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertNotIn('Traceback', result.stdout + result.stderr)
        return result

    def assert_legacy_rejected(self, doc):
        errors, warnings = call('validate_input', 'validate', doc)
        self.assertEqual(warnings, [])
        self.assertTrue(any(MIGRATION in error for error in errors), errors)
        with self.assertRaisesRegex(ValueError, MIGRATION):
            call('calculate_or_transform', 'assemble', doc)
        packet = fixture('surveillance_packet_example.json')
        self.assertTrue(any(MIGRATION in error for error in
                            call('validate_output', 'validate', packet, doc)))
        for script in ('validate_input', 'calculate_or_transform', 'validate_output'):
            result = self.cli(script, packet if script == 'validate_output' else doc,
                              original=doc if script == 'validate_output' else None)
            self.assertEqual(result.returncode, 1, result)
            self.assertIn(MIGRATION, result.stdout + result.stderr)
            self.assertNotIn('"spread_delta_bps"', result.stdout)
            self.assertNotIn('"spread_change_bps"', result.stdout)

    def assert_current_partial(self, doc, reason):
        intake = self.cli('validate_input', doc)
        self.assertEqual(intake.returncode, 0, intake)
        result = self.cli('calculate_or_transform', doc)
        self.assertEqual(result.returncode, 0, result)
        out = json.loads(result.stdout)
        self.assertEqual(out['status'], 'partial')
        self.assertIsNone(out['results']['spread_change_bps'])
        self.assertNotIn(WIDENING, out['results']['alerts'])
        self.assertEqual(out['results']['period_metrics']['current']['net_leverage_x'], (400 - 50) / 100)
        self.assertTrue(any(reason in issue for issue in out['unresolved_issues']), out)
        self.assertEqual(self.cli('validate_output', out, doc).returncode, 0)
        self.assertFalse(call('validate_output', 'validate', out, doc))
        return out

    def assert_alias_legacy_rejected(self, identifier):
        resolved = resolve_current_package(identifier)
        package = ROOT / resolved['path']
        self.assertEqual(package, PACKAGE)
        self.assertIsNone(resolved['mode'])
        self.assertFalse(resolved['authority_granted'])
        doc = fixture('surveillance_request_example.json')
        packet = fixture('surveillance_packet_example.json')
        for script in ('validate_input', 'calculate_or_transform', 'validate_output'):
            result = self.cli(script, packet if script == 'validate_output' else doc,
                              original=doc if script == 'validate_output' else None,
                              package=package)
            self.assertEqual(result.returncode, 1, result)
            self.assertIn(MIGRATION, result.stdout + result.stderr)
        self.assertTrue(call('validate_input', 'validate', doc, scripts=package / 'scripts')[0])
        with self.assertRaisesRegex(ValueError, MIGRATION):
            call('calculate_or_transform', 'assemble', doc, scripts=package / 'scripts')
        self.assertTrue(call('validate_output', 'validate', packet, doc, scripts=package / 'scripts'))

    def assert_alias_current_reconstructs(self, identifier):
        resolved = resolve_current_package(identifier)
        package = ROOT / resolved['path']
        self.assertEqual(package, PACKAGE)
        doc = fixture()
        self.assertEqual(self.cli('validate_input', doc, package=package).returncode, 0)
        result = self.cli('calculate_or_transform', doc, package=package)
        self.assertEqual(result.returncode, 0, result)
        out = json.loads(result.stdout)
        self.assertEqual(out['status'], 'complete-for-supplied-scope')
        self.assertEqual(out['results']['spread_change_bps'], 190 - 130)
        self.assertEqual(out['results']['period_metrics']['current']['net_leverage_x'], (400 - 50) / 100)
        self.assertEqual(self.cli('validate_output', out, doc, package=package).returncode, 0)
        out['results']['spread_change_bps'] = 999
        self.assertEqual(self.cli('validate_output', out, doc, package=package).returncode, 1)

    def test_historical_alias_cannot_bypass_live_legacy_gate(self):
        self.assert_alias_legacy_rejected('credit-surveillance-packet')

    def test_old_package_path_cannot_bypass_live_legacy_gate(self):
        self.assert_alias_legacy_rejected('skills/asset-management/credit-surveillance-packet')

    def test_current_contract_reconstructs_through_historical_alias(self):
        self.assert_alias_current_reconstructs('credit-surveillance-packet')

    def test_current_contract_reconstructs_through_old_package_path(self):
        self.assert_alias_current_reconstructs('skills/asset-management/credit-surveillance-packet/SKILL.md')

    def test_legacy_former_success_fixture_fails_all_public_endpoints(self):
        self.assert_legacy_rejected(fixture('surveillance_request_example.json'))

    def test_legacy_future_reported_periods_cannot_bypass_live_gate(self):
        doc = fixture('surveillance_request_example.json')
        doc['financials']['period'] = 'LTM-2030-06-30'
        doc['prior_financials']['period'] = 'LTM-2029-06-30'
        self.assert_legacy_rejected(doc)

    def test_legacy_undated_quotes_cannot_bypass_live_gate(self):
        doc = fixture('surveillance_request_example.json')
        self.assertNotIn('observed_at', doc['spreads'])
        self.assert_legacy_rejected(doc)

    def test_legacy_stale_quotes_cannot_bypass_live_gate(self):
        doc = fixture('surveillance_request_example.json')
        doc['spreads'].update(prior_observed_at='2020-01-01T16:00:00Z',
                              current_observed_at='2020-02-01T16:00:00Z')
        doc['spread_freshness_policy'] = {'max_current_age_hours': 24}
        self.assert_legacy_rejected(doc)

    def test_legacy_unmapped_security_cannot_bypass_live_gate(self):
        doc = fixture('surveillance_request_example.json')
        doc['spreads']['instrument_id'] = 'UNRELATED-BOND'
        doc['instrument_evidence'] = []
        self.assert_legacy_rejected(doc)

    def test_explicit_old_schema_label_still_requires_migration(self):
        doc = fixture('surveillance_request_example.json')
        doc['schema_version'] = 'ir-phase1/1.0'
        self.assert_legacy_rejected(doc)

    def test_current_fields_without_explicit_schema_cannot_select_a_fallback(self):
        doc = fixture()
        del doc['schema_version']
        self.assert_legacy_rejected(doc)

    def test_unknown_schema_cannot_select_a_fallback(self):
        doc = fixture()
        doc['schema_version'] = 'ir-phase2/999.0'
        self.assert_legacy_rejected(doc)

    def test_relabeling_legacy_as_current_does_not_invent_missing_evidence(self):
        doc = fixture('surveillance_request_example.json')
        doc['schema_version'] = 'ir-phase2/1.0'
        self.assertTrue(call('validate_input', 'validate', doc)[0])
        with self.assertRaises(ValueError):
            call('calculate_or_transform', 'assemble', doc)
        for script in ('validate_input', 'calculate_or_transform'):
            result = self.cli(script, doc)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn('"spread_change_bps"', result.stdout)

    def test_legacy_output_without_original_fails_migration_gate(self):
        result = self.cli('validate_output', fixture('surveillance_packet_example.json'))
        self.assertEqual(result.returncode, 1)
        self.assertIn(MIGRATION, result.stdout + result.stderr)

    def test_legacy_output_cannot_be_laundered_with_current_original(self):
        result = self.cli('validate_output', fixture('surveillance_packet_example.json'), fixture())
        self.assertEqual(result.returncode, 1)
        self.assertIn(MIGRATION, result.stdout + result.stderr)

    def test_current_output_cannot_validate_against_legacy_original(self):
        result = self.cli('validate_output', fixture('phase2_valid.json'),
                          fixture('surveillance_request_example.json'), option='--source')
        self.assertEqual(result.returncode, 1)
        self.assertIn(MIGRATION, result.stdout + result.stderr)

    def test_stdin_uses_same_legacy_gate(self):
        for script in ('validate_input', 'calculate_or_transform'):
            result = self.cli(script, fixture('surveillance_request_example.json'), stdin=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn(MIGRATION, result.stdout + result.stderr)

    def test_current_public_dispatch_preserves_independent_arithmetic(self):
        doc = fixture()
        self.assertEqual(self.cli('validate_input', doc, stdin=True).returncode, 0)
        result = self.cli('calculate_or_transform', doc, stdin=True)
        self.assertEqual(result.returncode, 0)
        out = json.loads(result.stdout)
        self.assertEqual(out['schema_version'], 'ir-analysis/2.0')
        self.assertEqual(out['status'], 'complete-for-supplied-scope')
        self.assertEqual(out['results']['spread_change_bps'], 190 - 130)
        self.assertAlmostEqual(out['results']['metric_changes']['net_leverage_x'],
                               (400 - 50) / 100 - (400 - 60) / 120)
        self.assertFalse(out['authority_granted'])
        self.assertEqual(out, call('calculate_or_transform', 'assemble', doc))
        self.assertEqual(self.cli('validate_output', out, doc, option='--source').returncode, 0)

    def test_current_future_reported_periods_reject_both_dispatchers(self):
        doc = fixture()
        doc['prior']['period'].update(start='2029-01-01', end='2029-09-30')
        doc['current']['period'].update(start='2030-01-01', end='2030-09-30')
        for script in ('validate_input', 'calculate_or_transform'):
            result = self.cli(script, doc)
            self.assertEqual(result.returncode, 1)
            self.assertIn('reported financial period ends after as_of', result.stdout + result.stderr)

    def test_current_stale_evidence_remains_partial(self):
        doc = fixture()
        doc['spread_freshness_policy']['max_current_age_hours'] = 1
        self.assert_current_partial(doc, 'exceeds supplied maximum age')

    def test_current_undated_evidence_remains_partial(self):
        doc = fixture()
        doc['current_spread'].pop('observed_at')
        self.assert_current_partial(doc, 'source known_at cannot substitute')

    def test_current_missing_mapping_remains_partial(self):
        doc = fixture()
        doc['instrument_evidence'] = []
        self.assert_current_partial(doc, 'mapping')

    def test_current_output_mutation_and_substituted_original_reject(self):
        doc = fixture()
        out = call('calculate_or_transform', 'assemble', doc)
        for key, value in (('spread_change_bps', 999), ('position_action', 'increase')):
            altered = copy.deepcopy(out)
            altered['results'][key] = value
            self.assertEqual(self.cli('validate_output', altered, doc).returncode, 1)
        altered = copy.deepcopy(out)
        altered['unchecked_narrative'] = 'fabricated assertion'
        self.assertEqual(self.cli('validate_output', altered, doc).returncode, 1)
        original = copy.deepcopy(doc)
        original['request_id'] += '-substituted'
        self.assertEqual(self.cli('validate_output', out, original).returncode, 1)
        self.assertEqual(self.cli('validate_output', out).returncode, 1)

    def test_current_selftests_exercise_only_supported_contract(self):
        for script in ('validate_input', 'calculate_or_transform', 'validate_output'):
            result = subprocess.run([sys.executable, '-B', str(SCRIPTS / (script + '.py')), '--selftest'],
                                    text=True, capture_output=True, cwd=PACKAGE,
                                    env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            self.assertEqual(result.returncode, 0, result)
            self.assertNotIn(MIGRATION, result.stdout + result.stderr)
            if script == 'calculate_or_transform':
                out = json.loads(result.stdout)
                self.assertEqual(out['schema_version'], 'ir-analysis/2.0')
                self.assertEqual(out['results']['spread_change_bps'], 60)

    def test_duplicate_keys_and_nonfinite_json_are_controlled_rejections(self):
        for raw in ('{"schema_version":"ir-phase2/1.0","schema_version":"legacy"}',
                    '{"schema_version":"ir-phase2/1.0","x":NaN}'):
            for script in ('validate_input', 'calculate_or_transform', 'validate_output'):
                result = self.cli(script, raw=raw)
                self.assertEqual(result.returncode, 1)
                self.assertIn('ERROR', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
