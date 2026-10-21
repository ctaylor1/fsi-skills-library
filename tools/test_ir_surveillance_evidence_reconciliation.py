#!/usr/bin/env python3
"""Independent adverse cases for source-bound surveillance spread evidence."""
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
WIDENING = 'spread widened beyond supplied threshold'


def fixture():
    return json.loads((PACKAGE / 'evals/files/phase2_input.json').read_text())


def call(module, method, *args):
    sys.path.insert(0, str(SCRIPTS))
    try:
        for key in ('phase2_domain', 'analysis_contract', 'research_runtime',
                    'native_integrity', 'validate_input', 'calculate_or_transform',
                    'validate_output'):
            sys.modules.pop(key, None)
        spec = importlib.util.spec_from_file_location(module, SCRIPTS / (module + '.py'))
        imported = importlib.util.module_from_spec(spec)
        sys.modules[module] = imported
        spec.loader.exec_module(imported)
        return getattr(imported, method)(*args)
    finally:
        sys.path.pop(0)


def compute(doc):
    return call('calculate_or_transform', 'assemble', doc)


def observation(doc, key):
    return next(r for r in doc['spread_evidence']
                if r['observation_id'] == doc[key]['observation_id'])


class SurveillanceEvidenceReconciliation(unittest.TestCase):
    def assert_withheld(self, doc, reason=None):
        self.assertFalse(call('validate_input', 'validate', doc)[0])
        out = compute(doc)
        self.assertEqual(out['status'], 'partial')
        self.assertIsNone(out['results']['spread_change_bps'])
        self.assertNotIn(WIDENING, out['results']['alerts'])
        self.assertEqual(out['results']['period_metrics']['current']['net_leverage_x'], 3.5)
        self.assertEqual(out['results']['spread_reconciliation'],
                         {'status': 'withheld', 'observations': [], 'instrument_mapping': None})
        if reason:
            self.assertTrue(any(reason in x for x in out['unresolved_issues']), out['unresolved_issues'])
        self.assertFalse(call('validate_output', 'validate', out, doc))
        return out

    def test_independent_valid_math_and_retained_resolved_evidence(self):
        doc = fixture()
        out = compute(doc)
        self.assertEqual(out['status'], 'complete-for-supplied-scope')
        self.assertEqual(out['results']['spread_change_bps'], 190 - 130)
        self.assertAlmostEqual(out['results']['metric_changes']['net_leverage_x'],
                               350 / 100 - 340 / 120)
        self.assertIn(WIDENING, out['results']['alerts'])
        audit = out['results']['spread_reconciliation']
        self.assertEqual(audit['status'], 'reconciled-supplied-evidence')
        self.assertEqual(audit['observations'], doc['spread_evidence'])
        self.assertEqual(audit['instrument_mapping'], doc['instrument_evidence'][0])
        self.assertEqual(audit['observations'][1]['evidence_ref']['source_version'], 'fixture-v1')
        self.assertEqual(out['source_assurance'], 'supplied-not-authenticated')
        self.assertFalse(out['authority_granted'])
        self.assertFalse(call('validate_output', 'validate', out, doc))

    def test_previously_accepted_mutually_matching_unrelated_note(self):
        doc = fixture()
        for key, value in (('prior_spread', 90), ('current_spread', 145)):
            doc[key].update(security_id='UNRELATED-ISSUER-NOTE', spread_bps=value)
        self.assert_withheld(doc, 'asserted security_id differs')

    def test_same_unrelated_assertions_and_records_still_need_registered_mapping(self):
        doc = fixture()
        for key in ('prior_spread', 'current_spread'):
            doc[key]['security_id'] = 'UNRELATED-ISSUER-NOTE'
            observation(doc, key)['security_id'] = 'UNRELATED-ISSUER-NOTE'
        self.assert_withheld(doc, 'explicitly cover security and issuer')
        doc['sources'][1]['subject_ids'].append('UNRELATED-ISSUER-NOTE')
        self.assert_withheld(doc, 'exactly one instrument evidence mapping')

    def test_financial_statement_source_cannot_support_consistent_quote_ledger(self):
        doc = fixture()
        doc['sources'][1]['kind'] = 'financial_statement'
        self.assert_withheld(doc, 'source kind is unsupported')

    def test_market_data_label_alone_does_not_supply_missing_observation_contents(self):
        doc = fixture()
        del doc['spread_evidence']
        self.assert_withheld(doc, 'exactly one selected spread evidence')

    def test_explicit_observation_and_mapping_roles_are_required(self):
        for inventory, role in (('spread_evidence', 'financial-statement-line'),
                                ('instrument_evidence', 'analyst-comment')):
            doc = fixture()
            doc[inventory][0]['role'] = role
            self.assert_withheld(doc, 'evidence role must be')

    def test_requested_security_and_issuer_bind_to_selected_records(self):
        doc = fixture()
        doc['subject'] = {'type': 'security', 'id': 'ACME-BOND', 'issuer_id': 'ACME-ISSUER'}
        self.assertEqual(compute(doc)['results']['spread_change_bps'], 60)
        doc['subject']['id'] = 'OTHER-ACME-BOND'
        self.assert_withheld(doc, 'differs from requested security subject')
        doc = fixture()
        for key in ('prior_spread', 'current_spread'):
            doc[key]['issuer_id'] = 'OTHER-ISSUER'
            observation(doc, key)['issuer_id'] = 'OTHER-ISSUER'
        doc['sources'][1]['subject_ids'].append('OTHER-ISSUER')
        doc['instrument_evidence'][0]['issuer_id'] = 'OTHER-ISSUER'
        self.assert_withheld(doc, 'issuer differs from requested subject')

    def test_source_must_cover_both_security_and_issuer(self):
        for subject_ids in (['ACME-ISSUER'], ['ACME-BOND']):
            doc = fixture()
            doc['sources'][1]['subject_ids'] = subject_ids
            if subject_ids == ['ACME-BOND']:
                doc['subject'] = {'type': 'security', 'id': 'ACME-BOND', 'issuer_id': 'ACME-ISSUER'}
            self.assert_withheld(doc, 'explicitly cover security and issuer')

    def test_mapping_currency_and_issuer_cannot_be_inferred_from_matching_quotes(self):
        for key, value in (('currency', 'EUR'), ('issuer_id', 'OTHER-ISSUER')):
            doc = fixture()
            doc['instrument_evidence'][0][key] = value
            if key == 'issuer_id':
                doc['sources'][1]['subject_ids'].append(value)
            self.assert_withheld(doc, 'instrument mapping ' + key + ' differs')

    def test_foreign_currency_bond_is_supported_when_mapping_and_quotes_agree(self):
        doc = fixture()
        for key in ('prior_spread', 'current_spread'):
            doc[key]['currency'] = 'EUR'
            observation(doc, key)['currency'] = 'EUR'
        doc['instrument_evidence'][0]['currency'] = 'EUR'
        self.assertEqual(compute(doc)['results']['spread_change_bps'], 60)
        self.assertEqual(doc['current']['currency'], 'USD')  # No FX conversion is implied.

    def test_asserted_quote_fields_cannot_change_independently_of_evidence(self):
        for field, value in (('issuer_id', 'OTHER-ISSUER'), ('currency', 'EUR'),
                             ('basis', 'G-spread'), ('spread_bps', 245),
                             ('observed_at', '2026-10-20T19:00:00Z')):
            doc = fixture()
            # Change both assertions where necessary, preserving mutual comparability.
            for key in ('prior_spread', 'current_spread'):
                if field in {'issuer_id', 'currency', 'basis'}:
                    doc[key][field] = value
            if field in {'spread_bps', 'observed_at'}:
                doc['current_spread'][field] = value
            self.assert_withheld(doc, 'asserted ' + field + ' differs')

    def test_wrong_source_version_and_mutually_copied_locator_are_withheld(self):
        for inventory in ('spread_evidence', 'instrument_evidence'):
            doc = fixture()
            doc[inventory][0]['evidence_ref']['source_version'] = 'unavailable-v2'
            self.assert_withheld(doc, 'source version mismatch')
        doc = fixture()
        invented = 'fixture:invented-quote-block'
        doc['evidence_refs'][1]['locator'] = invented
        for key in ('prior_spread', 'current_spread'):
            doc[key]['evidence_refs'][0]['locator'] = invented
            observation(doc, key)['evidence_ref']['locator'] = invented
        doc['instrument_evidence'][0]['evidence_ref']['locator'] = invented
        self.assert_withheld(doc, 'locator differs from registered source block')

    def test_asserted_citation_must_be_exact_selected_evidence_block(self):
        doc = fixture()
        ref = {'source_id': 'synthetic-spreads', 'locator': 'fixture:other-listed-block'}
        doc['evidence_refs'].append(ref)
        doc['current_spread']['evidence_refs'] = [ref]
        self.assert_withheld(doc, 'asserted citation differs')

    def test_missing_observation_record_id_value_time_and_binding_are_gaps(self):
        for field in ('observation_id', 'spread_bps', 'observed_at', 'evidence_ref'):
            doc = fixture()
            del observation(doc, 'current_spread')[field]
            self.assert_withheld(doc)
        for field in ('observation_id', 'issuer_id'):
            doc = fixture()
            del doc['current_spread'][field]
            self.assert_withheld(doc)

    def test_duplicate_selected_ids_and_conflicting_alternate_ids_are_ambiguous(self):
        for mutate in ('duplicate', 'conflicting-value', 'alternate-id'):
            doc = fixture()
            extra = copy.deepcopy(observation(doc, 'current_spread'))
            if mutate == 'conflicting-value':
                extra['spread_bps'] = 245
            if mutate == 'alternate-id':
                extra.update(observation_id='concealed-alternate-id', spread_bps=245)
            doc['spread_evidence'].append(extra)
            self.assert_withheld(doc, 'exactly one selected' if mutate != 'alternate-id'
                                 else 'duplicate or conflicting economic spread evidence')

    def test_missing_and_duplicate_instrument_mapping_are_ambiguous(self):
        for records in ([], fixture()['instrument_evidence'] * 2):
            doc = fixture()
            doc['instrument_evidence'] = records
            self.assert_withheld(doc, 'exactly one instrument evidence mapping')

    def test_mapping_must_cover_both_observation_dates_and_instants(self):
        for field, value in (('valid_from', '2026-10-01'), ('valid_to', '2026-10-19'),
                             ('valid_from', '2026-09-20T20:00:00.000001Z'),
                             ('valid_to', '2026-10-20T19:59:59.999999Z')):
            doc = fixture()
            doc['instrument_evidence'][0][field] = value
            self.assert_withheld(doc, 'does not cover each selected observation')
        doc = fixture()
        doc['instrument_evidence'][0].update(valid_from='2026-09-20T20:00:00Z',
                                            valid_to='2026-10-20T20:00:00Z')
        self.assertEqual(compute(doc)['results']['spread_change_bps'], 60)
        for field in ('valid_from', 'valid_to'):
            doc = fixture()
            del doc['instrument_evidence'][0][field]
            self.assert_withheld(doc, field + ' missing')

    def test_eligible_filing_can_supply_mapping_without_becoming_quote_source(self):
        doc = fixture()
        source = copy.deepcopy(doc['sources'][1])
        source.update(source_id='synthetic-security-terms', kind='filing',
                      version='terms-v3', locator='fixture:issue-terms-block')
        doc['sources'].append(source)
        ref = {'source_id': source['source_id'], 'locator': source['locator']}
        doc['evidence_refs'].append(ref)
        doc['instrument_evidence'][0]['evidence_ref'] = dict(ref, source_version=source['version'])
        self.assertEqual(compute(doc)['results']['spread_change_bps'], 60)

    def test_source_cutoff_permissions_and_precision_preserve_common_projection_gate(self):
        for field, value in (('known_at', '2026-10-21T00:00:00Z'),
                             ('known_at', '2026-10-20'),
                             ('permission_status', 'denied'),
                             ('classification', 'restricted')):
            doc = fixture()
            doc['sources'][1][field] = value
            out = compute(doc)
            self.assertEqual(out['status'], 'partial')
            self.assertIsNone(out['results'])
            self.assertEqual(out['source_register'], [])
            self.assertEqual(out['evidence_refs'], [])
            self.assertFalse(call('validate_output', 'validate', out, doc))

    def test_unused_records_cannot_supply_selected_evidence_or_bypass_source_gating(self):
        doc = fixture()
        source = copy.deepcopy(doc['sources'][1])
        source.update(source_id='unused-denied-source', permission_status='denied')
        doc['sources'].append(source)
        extra = copy.deepcopy(doc['spread_evidence'][0])
        extra.update(observation_id='unused-observation', security_id='OTHER-BOND')
        extra['evidence_ref']['source_id'] = source['source_id']
        doc['spread_evidence'].append(extra)
        out = compute(doc)
        self.assertEqual(out['status'], 'complete-for-supplied-scope')
        self.assertNotIn('unused-observation', json.dumps(out['results']))
        self.assertNotIn(source['source_id'], json.dumps(out['source_register']))
        # Once explicitly declared used, the old source gate remains authoritative.
        doc['evidence_refs'].append({'source_id': source['source_id'], 'locator': source['locator']})
        self.assertIsNone(compute(doc)['results'])

    def test_missing_quotes_are_optional_and_inventory_does_not_select_itself(self):
        doc = fixture()
        del doc['prior_spread']
        del doc['current_spread']
        out = compute(doc)
        self.assertEqual(out['status'], 'complete-for-supplied-scope')
        self.assertIsNone(out['results']['spread_change_bps'])
        self.assertEqual(out['results']['spread_reconciliation']['status'], 'not-requested')

    def test_decimal_spread_difference_and_threshold_have_independent_expected_value(self):
        doc = fixture()
        for key, value in (('prior_spread', 0.1), ('current_spread', 0.3)):
            doc[key]['spread_bps'] = value
            observation(doc, key)['spread_bps'] = value
        doc['thresholds']['spread_widening_bps'] = 0.2
        out = compute(doc)
        self.assertEqual(out['results']['spread_change_bps'], 0.2)
        self.assertIn(WIDENING, out['results']['alerts'])

    def test_malformed_evidence_shapes_dates_and_numbers_reject_without_traceback(self):
        for mutate in ('inventory-shape', 'record-shape', 'time', 'number', 'mapping-bound'):
            doc = fixture()
            if mutate == 'inventory-shape': doc['spread_evidence'] = False
            elif mutate == 'record-shape': doc['spread_evidence'][0] = False
            elif mutate == 'time': doc['spread_evidence'][0]['observed_at'] = '2026-10-20'
            elif mutate == 'number': doc['spread_evidence'][0]['spread_bps'] = True
            else: doc['instrument_evidence'][0]['valid_from'] = 'not-a-date'
            self.assertTrue(call('validate_input', 'validate', doc)[0])
            with self.assertRaises((ValueError, TypeError)):
                compute(doc)

    def test_output_reconstruction_binds_evidence_records_and_withheld_results(self):
        doc = fixture()
        out = compute(doc)
        self.assertTrue(call('validate_output', 'validate', out, None))
        changed = copy.deepcopy(doc)
        changed['spread_evidence'][1]['evidence_ref']['source_version'] = 'other-version'
        self.assertTrue(call('validate_output', 'validate', out, changed))
        partial = self.assert_withheld(changed, 'source version mismatch')
        partial['results']['spread_change_bps'] = 60
        partial['results']['alerts'].append(WIDENING)
        self.assertTrue(call('validate_output', 'validate', partial, changed))
        out['results']['spread_reconciliation']['observations'][1]['spread_bps'] = 245
        self.assertTrue(call('validate_output', 'validate', out, doc))

    def test_public_commands_reconcile_preexisting_bad_cases_and_validate_partials(self):
        with tempfile.TemporaryDirectory(prefix='ir-surveillance-reconciliation-') as temp:
            temp = Path(temp)
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            for mode in ('valid', 'unrelated-note', 'wrong-source-kind', 'missing-ledger'):
                doc = fixture()
                if mode == 'unrelated-note':
                    for key, value in (('prior_spread', 90), ('current_spread', 145)):
                        doc[key].update(security_id='UNRELATED-ISSUER-NOTE', spread_bps=value)
                elif mode == 'wrong-source-kind':
                    doc['sources'][1]['kind'] = 'financial_statement'
                elif mode == 'missing-ledger':
                    del doc['spread_evidence']
                source = temp / (mode + '-input.json')
                source.write_text(json.dumps(doc))
                intake = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'validate_input.py'), str(source)],
                                        cwd=temp, env=env, text=True, capture_output=True)
                self.assertEqual(intake.returncode, 0, intake.stdout + intake.stderr)
                result = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'calculate_or_transform.py'), str(source)],
                                        cwd=temp, env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn('Traceback', result.stdout + result.stderr)
                out = json.loads(result.stdout)
                self.assertEqual(out['results']['spread_change_bps'], 60 if mode == 'valid' else None)
                self.assertEqual(out['status'], 'complete-for-supplied-scope' if mode == 'valid' else 'partial')
                output = temp / (mode + '-output.json')
                output.write_text(result.stdout)
                checked = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'validate_output.py'),
                                          str(output), '--input', str(source)],
                                         cwd=temp, env=env, text=True, capture_output=True)
                self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
                self.assertNotIn('Traceback', checked.stdout + checked.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
