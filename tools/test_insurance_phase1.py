"""Phase 1 packaging, catalog and native receiver integration invariants."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from build_catalog_from_xlsx import apply_changes
from check_insurance_handoffs import check

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'shared/insurance'))
from insurance_contract import build_artifact, make_handoff, stable_hash

spec = importlib.util.spec_from_file_location('insurance_native_handoff', ROOT / 'skills/insurance/insurance-router/scripts/validate_handoff.py')
handoffs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handoffs)


class InsuranceIntegration(unittest.TestCase):
    def test_routes_catalog_and_migration(self):
        self.assertEqual(check(), [])

    def test_regeneration_is_idempotent_and_preserves_other_domains(self):
        current = json.loads((ROOT / 'catalog/skills-catalog.json').read_text())['skills']
        additions = json.loads((ROOT / 'catalog/provisional-additions.json').read_text())
        overrides = json.loads((ROOT / 'catalog/approved-overrides.json').read_text())
        first = apply_changes(current, additions, overrides)
        self.assertEqual(first, apply_changes(first, additions, overrides))
        before = {r['name']: r for r in current if r['category'] != 'Insurance'}
        after = {r['name']: r for r in first if r['category'] != 'Insurance'}
        self.assertEqual(before, after)

    def test_original_workbook_names_merge_without_duplicates(self):
        aliases = json.loads((ROOT / 'catalog/insurance-phase1-migrations.json').read_text())['aliases']
        rows = [{'name': old, 'description': f'Use {old}.'} for old in aliases]
        rows.append({'name': 'unrelated', 'description': 'preserved'})
        changes = {'renames': {old: v['target'] for old, v in aliases.items()}}
        output = apply_changes(rows, [], changes)
        self.assertEqual({r['name'] for r in output}, {v['target'] for v in aliases.values()} | {'unrelated'})
        self.assertEqual(output, apply_changes(output, [], changes))
        self.assertIn(rows[-1], output)

    def test_standalone_router(self):
        with tempfile.TemporaryDirectory(prefix='insurance-router-standalone-') as directory:
            target = Path(directory) / 'insurance-router'
            shutil.copytree(ROOT / 'skills/insurance/insurance-router', target,
                            ignore=shutil.ignore_patterns('__pycache__'))
            result = subprocess.run([sys.executable, '-B', 'scripts/test_routing.py'], cwd=target,
                                    env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def native_handoff(self):
        intake = ROOT / 'skills/insurance/claim-intake-preparer'
        source = json.loads((intake / 'evals/files/fnol_example.json').read_text())
        source.update(context={'capacity': 'carrier', 'represented_party': 'synthetic-insurer',
                               'object_id': source['raw_fnol']['fnol_id']},
                      as_of='2026-09-18', sources=[{'source_ref': 'synthetic-notice', 'version': '1'}])
        with tempfile.TemporaryDirectory(prefix='insurance-intake-source-') as directory:
            path = Path(directory) / 'notice.json'
            path.write_text(json.dumps(source))
            result = subprocess.run([sys.executable, '-B', str(intake / 'scripts/calculate_or_transform.py'), str(path)],
                                    cwd=intake, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = json.loads(result.stdout)
        issues = [e['reason'] for e in output.get('exceptions', [])]
        artifact = output.get('artifact') or build_artifact(
            source, output, producer='claim-intake-preparer', artifact_type='claim-intake',
            completeness='partial', evaluability='partial', issues=issues)
        native = json.loads((ROOT / 'skills/insurance/claims-triage-assistant/evals/files/claims_example.json').read_text())
        native['claims'] = [native['claims'][0]]
        native['as_of'] = '2026-09-18'
        # Deliberate reviewed mapping/enrichment, not a universal adapter:
        # FNOL reference and assigned claim reference are different identifiers.
        record = native['claims'][0]
        record.update(policy_id=output['normalized']['policy_number'],
                      loss_date=output['normalized']['loss_date'],
                      reported_date=output['normalized']['reported_date'],
                      source_ref=output['normalization_id'], claim_type='auto_collision')
        native['identity_mapping'] = {'fnol_id': output['fnol_id'], 'claim_id': record['claim_id'],
                                      'mapping_basis': 'synthetic reviewed assignment'}
        return make_handoff(artifact, target_skill='claims-triage-assistant', target_input=native,
                            requested_output='carrier triage with unresolved intake issues')

    def test_actual_intake_to_native_triage(self):
        packet = self.native_handoff()
        self.assertEqual(handoffs.check(packet, ROOT / 'skills'), [])
        self.assertTrue(packet['target_input']['unresolved_issues'])
        self.assertIn(packet['source_artifact'], packet['target_input']['upstream_artifacts'])
        self.assertFalse(packet['authority_granted'])

    def test_envelope_cannot_replace_native_input_or_drop_issues(self):
        packet = self.native_handoff()
        broken = copy.deepcopy(packet)
        broken['target_input']['claims'] = []
        broken['target_input_hash'] = stable_hash(broken['target_input'])
        errors = handoffs.check(broken, ROOT / 'skills')
        self.assertTrue(any('receiver:' in e for e in errors), errors)
        broken = copy.deepcopy(packet)
        broken['target_input']['unresolved_issues'] = []
        broken['target_input_hash'] = stable_hash(broken['target_input'])
        self.assertTrue(handoffs.check(broken, ROOT / 'skills'))

    def test_missing_receiver_and_path_injection_rejected(self):
        packet = self.native_handoff()
        packet['target_skill'] = '../../tools'
        self.assertTrue(handoffs.check(packet, ROOT / 'skills'))
        packet['target_skill'] = 'uninstalled-insurance-skill'
        self.assertTrue(handoffs.check(packet, ROOT / 'skills'))

    def test_spec_cards_reproduce_insurance_metadata(self):
        import yaml
        from spec_card import card
        rows = json.loads((ROOT / 'catalog/skills-catalog.json').read_text())['skills']
        for row in rows:
            if row['category'] != 'Insurance':
                continue
            text = (ROOT / 'skills/insurance' / row['name'] / 'SKILL.md').read_text()
            self.assertEqual(yaml.safe_load(text.split('---', 2)[1])['metadata'],
                             yaml.safe_load(card(row)[0])['metadata'], row['name'])


if __name__ == '__main__':
    unittest.main()
