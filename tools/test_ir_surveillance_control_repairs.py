#!/usr/bin/env python3
"""Adverse and independent numerical tests for reported credit/spread time controls."""
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


def set_quote(doc, key, **updates):
    """Supply matching assertion and retained observation for time-control cases.

    Unbound assertions are covered by the evidence-reconciliation regressions.
    These earlier cases deliberately isolate chronology and freshness controls.
    """
    quote = doc[key]
    record = next(row for row in doc['spread_evidence']
                  if row['observation_id'] == quote['observation_id'])
    quote.update(updates)
    record.update(updates)


class SurveillanceControlRepairs(unittest.TestCase):
    def assert_withheld(self, doc, reason):
        self.assertFalse(call('validate_input', 'validate', doc)[0])
        out = compute(doc)
        self.assertEqual(out['status'], 'partial')
        self.assertIsNone(out['results']['spread_change_bps'])
        self.assertNotIn(WIDENING, out['results']['alerts'])
        self.assertEqual(out['results']['period_metrics']['current']['net_leverage_x'], 3.5)
        self.assertTrue(any(reason in issue for issue in out['unresolved_issues']), out)
        self.assertFalse(call('validate_output', 'validate', out, doc))
        return out

    def test_valid_independent_spread_and_financial_math(self):
        doc = fixture()
        out = compute(doc)
        self.assertEqual(out['status'], 'complete-for-supplied-scope')
        self.assertEqual(out['results']['spread_change_bps'], 190 - 130)
        self.assertAlmostEqual(out['results']['metric_changes']['net_leverage_x'],
                               (400 - 50) / 100 - (400 - 60) / 120)
        self.assertIn(WIDENING, out['results']['alerts'])
        self.assertFalse(call('validate_output', 'validate', out, doc))

    def test_future_reported_financial_periods_reject_at_intake_and_compute(self):
        for key in ('prior', 'current'):
            with self.subTest(period=key):
                doc = fixture()
                year = '2027' if key == 'prior' else '2028'
                doc[key]['period'].update(start=year + '-01-01', end=year + '-09-30')
                errors, _ = call('validate_input', 'validate', doc)
                self.assertTrue(any('reported financial period ends after as_of' in e for e in errors))
                with self.assertRaisesRegex(ValueError, 'after as_of'):
                    compute(doc)

    def test_both_future_reported_periods_reject_even_if_ordered(self):
        doc = fixture()
        for key, year in (('prior', '2027'), ('current', '2028')):
            doc[key]['period'].update(start=year + '-01-01', end=year + '-09-30')
        self.assertTrue(call('validate_input', 'validate', doc)[0])
        with self.assertRaises(ValueError):
            compute(doc)

    def test_reported_periods_cannot_follow_earlier_knowledge_cutoff(self):
        for cutoff in ('2026-09-29T23:59:59Z', '2026-09-29'):
            doc = fixture()
            doc['knowledge_cutoff'] = cutoff
            errors, _ = call('validate_input', 'validate', doc)
            self.assertTrue(any('period ends after knowledge_cutoff date' in e for e in errors))
            with self.assertRaisesRegex(ValueError, 'after knowledge_cutoff date'):
                compute(doc)

    def test_date_only_cutoff_withholds_spreads_without_inventing_midnight(self):
        doc = fixture()
        doc['knowledge_cutoff'] = '2026-10-20'
        for source in doc['sources']:
            source['known_at'] = '2026-10-20'
        self.assert_withheld(doc, 'knowledge_cutoff lacks timestamp precision')

    def test_reported_period_end_equal_as_of_is_allowed(self):
        doc = fixture()
        doc['as_of'] = doc['current']['period']['end']
        doc.pop('prior_spread')
        doc.pop('current_spread')
        out = compute(doc)
        self.assertEqual(out['status'], 'complete-for-supplied-scope')
        self.assertEqual(out['results']['period_metrics']['current']['gross_leverage_x'], 4)

    def test_undated_quotes_never_use_source_knowledge_as_observation(self):
        for key in ('prior_spread', 'current_spread'):
            with self.subTest(quote=key):
                doc = fixture()
                del doc[key]['observed_at']
                self.assert_withheld(doc, 'observed_at missing')

    def test_missing_policy_withholds_instead_of_inventing_age_limit(self):
        doc = fixture()
        del doc['spread_freshness_policy']
        self.assert_withheld(doc, 'freshness_policy missing')

    def test_stale_current_withholds_but_old_prior_is_allowed(self):
        doc = fixture()
        set_quote(doc, 'current_spread', observed_at='2026-10-19T21:59:59Z')
        self.assert_withheld(doc, 'maximum age')
        doc = fixture()
        set_quote(doc, 'prior_spread', observed_at='2020-01-01T00:00:00Z')
        doc['instrument_evidence'][0]['valid_from'] = '2020-01-01'
        self.assertEqual(compute(doc)['results']['spread_change_bps'], 60)

    def test_exact_age_boundary_and_subsecond_overrun(self):
        doc = fixture()
        doc['spread_freshness_policy']['max_current_age_hours'] = 2
        self.assertEqual(compute(doc)['results']['spread_change_bps'], 60)
        set_quote(doc, 'current_spread', observed_at='2026-10-20T19:59:59.999999Z')
        self.assert_withheld(doc, 'maximum age')

    def test_zero_age_policy_only_accepts_exact_cutoff(self):
        doc = fixture()
        doc['spread_freshness_policy']['max_current_age_hours'] = 0
        self.assert_withheld(doc, 'maximum age')
        set_quote(doc, 'current_spread', observed_at=doc['knowledge_cutoff'])
        doc['sources'][1]['known_at'] = doc['knowledge_cutoff']
        self.assertEqual(compute(doc)['results']['spread_change_bps'], 60)

    def test_future_cutoff_and_future_economic_date_are_separate_guards(self):
        doc = fixture()
        set_quote(doc, 'current_spread', observed_at='2026-10-20T22:00:00.000001Z')
        self.assert_withheld(doc, 'after knowledge_cutoff')
        doc = fixture()
        doc['knowledge_cutoff'] = '2026-10-21T22:00:00Z'
        doc['sources'][1]['known_at'] = '2026-10-21T21:00:00Z'
        set_quote(doc, 'current_spread', observed_at='2026-10-21T20:00:00Z')
        self.assert_withheld(doc, 'after economic as_of')

    def test_reversed_or_equal_instants_withhold_change(self):
        for instant in ('2026-10-20T21:00:00Z', '2026-10-20T20:00:00Z'):
            doc = fixture()
            set_quote(doc, 'prior_spread', observed_at=instant)
            self.assert_withheld(doc, 'prior observation must precede')

    def test_security_currency_and_basis_mismatch_withhold_change(self):
        for key, value in (('security_id', 'OTHER-BOND'), ('currency', 'EUR'), ('basis', 'G-spread')):
            doc = fixture()
            set_quote(doc, 'current_spread', **{key: value})
            self.assert_withheld(doc, 'incomparable')

    def test_timezone_offsets_compare_instants_and_utc_economic_dates(self):
        doc = fixture()
        set_quote(doc, 'current_spread', observed_at='2026-10-21T01:30:00+05:30')
        self.assertEqual(compute(doc)['results']['spread_change_bps'], 60)
        # Two offset representations of the same instant cannot form a trend.
        set_quote(doc, 'prior_spread', observed_at='2026-10-20T16:00:00-04:00')
        self.assert_withheld(doc, 'prior observation must precede')

    def test_source_can_publish_after_observation_but_not_before_it(self):
        doc = fixture()
        self.assertEqual(doc['sources'][1]['known_at'], '2026-10-20T21:00:00Z')
        self.assertEqual(compute(doc)['results']['spread_change_bps'], 60)
        doc['sources'][1]['known_at'] = '2026-10-20T19:59:59Z'
        self.assert_withheld(doc, 'source known_at precedes observation')

    def test_source_precision_or_future_vintage_preserves_common_source_gate(self):
        for known_at in ('2026-10-20', '2026-10-21T00:00:00Z'):
            doc = fixture()
            doc['sources'][1]['known_at'] = known_at
            out = compute(doc)
            self.assertEqual(out['status'], 'partial')
            self.assertIsNone(out['results'])
            self.assertEqual(out['evidence_refs'], [])
            self.assertFalse(call('validate_output', 'validate', out, doc))

    def test_malformed_quote_time_and_policy_reject(self):
        for observed_at in ('2026-10-20', '2026-10-20T20:00:00', 'not-a-time', True):
            doc = fixture()
            set_quote(doc, 'current_spread', observed_at=observed_at)
            self.assertTrue(call('validate_input', 'validate', doc)[0])
        for policy in ({}, {'max_current_age_hours': -1}, {'max_current_age_hours': True},
                       {'max_current_age_hours': float('inf')}, False):
            doc = fixture()
            doc['spread_freshness_policy'] = policy
            self.assertTrue(call('validate_input', 'validate', doc)[0])

    def test_one_missing_quote_withholds_and_both_absent_are_optional(self):
        doc = fixture()
        del doc['prior_spread']
        self.assert_withheld(doc, 'baseline missing')
        del doc['current_spread']
        out = compute(doc)
        self.assertEqual(out['status'], 'complete-for-supplied-scope')
        self.assertIsNone(out['results']['spread_change_bps'])

    def test_output_reconstruction_rejects_invented_delta_and_changed_original(self):
        doc = fixture()
        del doc['current_spread']['observed_at']
        out = self.assert_withheld(doc, 'observed_at missing')
        forged = copy.deepcopy(out)
        forged['results']['spread_change_bps'] = 60
        forged['results']['alerts'].append(WIDENING)
        self.assertTrue(call('validate_output', 'validate', forged, doc))
        changed_original = copy.deepcopy(doc)
        changed_original['spread_freshness_policy']['max_current_age_hours'] = 48
        self.assertTrue(call('validate_output', 'validate', out, changed_original))

    def test_public_clis_reject_future_financials_and_validate_faithful_partials(self):
        with tempfile.TemporaryDirectory(prefix='ir-surveillance-repairs-') as temp:
            temp = Path(temp)
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            for mutation in ('valid', 'undated', 'stale', 'future-financials'):
                doc = fixture()
                if mutation == 'undated':
                    del doc['current_spread']['observed_at']
                elif mutation == 'stale':
                    set_quote(doc, 'current_spread', observed_at='2026-10-19T20:00:00Z')
                elif mutation == 'future-financials':
                    doc['current']['period'].update(start='2027-01-01', end='2027-09-30')
                source = temp / (mutation + '-input.json')
                source.write_text(json.dumps(doc))
                commands = ('validate_input.py', 'calculate_or_transform.py')
                for command in commands:
                    proc = subprocess.run([sys.executable, '-B', str(SCRIPTS / command), str(source)],
                                          cwd=temp, env=env, text=True, capture_output=True)
                    self.assertNotIn('Traceback', proc.stdout + proc.stderr)
                    self.assertEqual(proc.returncode, 1 if mutation == 'future-financials' else 0,
                                     proc.stdout + proc.stderr)
                    if command == 'calculate_or_transform.py' and proc.returncode == 0:
                        out = json.loads(proc.stdout)
                        self.assertEqual(out['results']['spread_change_bps'],
                                         60 if mutation == 'valid' else None)
                        output = temp / (mutation + '-output.json')
                        output.write_text(proc.stdout)
                        check = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'validate_output.py'),
                                                str(output), '--input', str(source)],
                                               cwd=temp, env=env, text=True, capture_output=True)
                        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
