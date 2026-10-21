#!/usr/bin/env python3
"""Reported-period and adjustment-identity regressions through the native API/CLIs."""
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
PACKAGE = ROOT / 'skills/investment-research/issuer-credit-researcher'


def fixture(name='input.json'):
    return json.loads((PACKAGE / 'evals/files' / name).read_text())


def call(module, method, *args):
    sys.path.insert(0, str(PACKAGE / 'scripts'))
    try:
        for name in ('domain', 'analysis_contract', 'research_runtime', 'native_integrity',
                     'validate_input', 'calculate_or_transform', 'validate_output'):
            sys.modules.pop(name, None)
        spec = importlib.util.spec_from_file_location(module, PACKAGE / 'scripts' / (module + '.py'))
        loaded = importlib.util.module_from_spec(spec)
        sys.modules[module] = loaded
        spec.loader.exec_module(loaded)
        return getattr(loaded, method)(*args)
    finally:
        sys.path.pop(0)


def run_cli(script, *args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH', None)
    return subprocess.run([sys.executable, '-B', 'scripts/' + script + '.py',
                           *map(str, args)], cwd=PACKAGE, capture_output=True,
                          text=True, env=env)


def set_source_known_at(doc, source_id, known_at):
    """Keep retained source bindings explicit for date-boundary test evidence."""
    next(source for source in doc['sources']
         if source['source_id'] == source_id)['known_at'] = known_at

    def bind(value):
        if isinstance(value, dict):
            binding = value.get('source_binding')
            if isinstance(binding, dict) and binding.get('source_id') == source_id:
                binding['known_at'] = known_at
            for child in value.values():
                bind(child)
        elif isinstance(value, list):
            for child in value:
                bind(child)
    bind(doc)


class IssuerControlRepairs(unittest.TestCase):
    def assert_rejected(self, doc, message):
        errors, _ = call('validate_input', 'validate', doc)
        self.assertTrue(any(message in error for error in errors), errors)
        with self.assertRaisesRegex(ValueError, message):
            call('domain', 'compute', doc)

    def test_reported_period_cannot_exceed_as_of(self):
        doc = fixture('future-financial-period.json')
        self.assert_rejected(doc, 'financials reported period')
        doc = fixture()
        doc['financials']['period']['end'] = '2026-10-21'
        self.assert_rejected(doc, 'financials reported period')

    def test_reported_period_cannot_exceed_earlier_knowledge_cutoff(self):
        doc = fixture()
        doc['knowledge_cutoff'] = '2026-09-29T23:59:59Z'
        self.assert_rejected(doc, 'financials reported period')
        # Timestamp offsets compare using the UTC cutoff calendar date.
        doc['knowledge_cutoff'] = '2026-09-30T00:30:00+02:00'
        self.assert_rejected(doc, 'financials reported period')

    def test_reported_period_boundary_retains_declared_date_precision(self):
        for cutoff, source_known in [('2026-09-30T23:59:59Z', '2026-09-30T12:00:00Z'),
                                     ('2026-09-30', '2026-09-30')]:
            with self.subTest(cutoff=cutoff):
                doc = fixture()
                doc.update(as_of='2026-09-30', use_on='2026-09-30', knowledge_cutoff=cutoff)
                set_source_known_at(doc, doc['sources'][0]['source_id'], source_known)
                out = call('domain', 'compute', doc)
                self.assertEqual(out['status'], 'complete-for-supplied-scope')
                self.assertEqual(out['results']['credit_metrics']['reported_ebitda']['gross_leverage_x'], 4)

    def test_forecast_label_cannot_bypass_reported_period_boundary(self):
        for label in ('analyst_forecast', 'scenario'):
            doc = fixture('future-financial-period.json')
            doc['financials']['claim_type'] = label
            self.assert_rejected(doc, 'financials reported period')

    def test_exact_duplicate_adjustment_rejected_before_summation(self):
        self.assert_rejected(fixture('duplicate-adjustment.json'),
                             'ebitda_adjustments duplicate adjustment_id')

    def test_conflicting_amount_or_citation_cannot_reuse_adjustment_id(self):
        for conflict in ('amount', 'evidence_refs'):
            with self.subTest(conflict=conflict):
                doc = fixture('duplicate-adjustment.json')
                if conflict == 'amount':
                    doc['ebitda_adjustments'][1]['amount'] = -15
                else:
                    citation = copy.deepcopy(doc['evidence_refs'][0])
                    citation['locator'] = 'fixture:table-2;separate-adjustment-evidence'
                    doc['evidence_refs'].append(citation)
                    doc['ebitda_adjustments'][1]['evidence_refs'] = [citation]
                self.assert_rejected(doc, 'ebitda_adjustments duplicate adjustment_id')

    def test_adjustment_identity_is_required(self):
        for value in ('', '   ', None):
            doc = fixture()
            doc['ebitda_adjustments'][0]['adjustment_id'] = value
            errors, _ = call('validate_input', 'validate', doc)
            self.assertTrue(errors)

    def test_distinct_signed_adjustments_and_original_arithmetic(self):
        doc = fixture()
        out = call('domain', 'compute', doc)
        self.assertEqual(out, fixture('valid.json'))
        original = out['results']['credit_metrics']
        self.assertEqual(original['reported_ebitda']['ebitda'], 100)
        self.assertEqual(original['analyst_adjusted_ebitda']['ebitda'], 110)
        self.assertAlmostEqual(original['analyst_adjusted_ebitda']['gross_leverage_x'], 400 / 110)
        # Supply a separate source block and economic-event ledger for the
        # signed reversal; another adjustment ID alone is not independent evidence.
        source = copy.deepcopy(doc['sources'][0])
        source.update(source_id='synthetic-recurring-cost-reversal',
                      locator='fixture:recurring-cost-reversal-table')
        doc['sources'].append(source)
        reference = {'source_id': source['source_id'], 'locator': source['locator']}
        doc['evidence_refs'].append(reference)
        event = copy.deepcopy(doc['ebitda_adjustment_events'][0])
        event.update(ledger_id='RECURRING-COST-REVERSAL-LEDGER',
                     economic_event_id='RECURRING-COST-REVERSAL-EVENT', amount=-3,
                     components=[], evidence_refs=[copy.deepcopy(reference)])
        event['source_binding'].update(source_id=source['source_id'],
                                       locator=source['locator'],
                                       economic_event_key='recurring-cost-reversal-2026')
        doc['ebitda_adjustment_events'].append(event)
        doc['ebitda_adjustments'].append({
            'adjustment_id': 'RECURRING-COST-2', 'amount': -3,
            'rationale': 'Distinct signed reversal supplied by analyst',
            'economic_event_id': event['economic_event_id'],
            'event_version': event['event_version'], 'aggregation_role': 'event-total',
            'evidence_refs': [copy.deepcopy(reference)]})
        adjusted = call('domain', 'compute', doc)
        self.assertEqual(adjusted['status'], 'complete-for-supplied-scope')
        result = adjusted['results']['credit_metrics']
        self.assertEqual(result['reported_ebitda']['ebitda'], 100)
        self.assertEqual(result['analyst_adjusted_ebitda']['ebitda'], 107)
        self.assertAlmostEqual(result['analyst_adjusted_ebitda']['gross_leverage_x'], 400 / 107)
        self.assertAlmostEqual(result['analyst_adjusted_ebitda']['net_leverage_x'], 350 / 107)
        self.assertEqual(result['analyst_adjusted_ebitda']['interest_coverage_x'], 107 / 20)

    def test_future_source_still_withholds_projection_instead_of_period_failure(self):
        doc = fixture()
        doc['sources'][0]['known_at'] = '2027-01-01T00:00:00Z'
        self.assertEqual(call('validate_input', 'validate', doc)[0], [])
        out = call('domain', 'compute', doc)
        self.assertIsNone(out['results'])
        self.assertEqual(out['status'], 'partial')
        self.assertEqual(out['evidence_refs'], [])
        self.assertEqual(out['calculation_lineage'], [])
        self.assertEqual(call('validate_output', 'validate', out, doc)[0], [])

    def test_public_clis_preserve_valid_result_and_reject_adverse_originals(self):
        with tempfile.TemporaryDirectory(prefix='ir-issuer-controls-cli-') as temp:
            source = PACKAGE / 'evals/files/input.json'
            intake = run_cli('validate_input', source)
            self.assertEqual(intake.returncode, 0, intake.stdout + intake.stderr)
            calculated = run_cli('calculate_or_transform', source)
            self.assertEqual(calculated.returncode, 0, calculated.stdout + calculated.stderr)
            baseline = json.loads(calculated.stdout)
            target = Path(temp) / 'valid-output.json'
            target.write_text(calculated.stdout)
            checked = run_cli('validate_output', target, '--input', source)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            for name, message in [('future-financial-period.json', 'financials reported period'),
                                  ('duplicate-adjustment.json', 'ebitda_adjustments duplicate adjustment_id')]:
                with self.subTest(fixture=name):
                    source = PACKAGE / 'evals/files' / name
                    for script in ('validate_input', 'calculate_or_transform'):
                        rejected = run_cli(script, source)
                        self.assertEqual(rejected.returncode, 1, rejected.stdout + rejected.stderr)
                        self.assertIn(message, rejected.stdout)
                        self.assertNotIn('Traceback', rejected.stdout + rejected.stderr)
                    # Bind a legacy-like candidate to the exact adverse original.
                    # Output rejection must identify the intake defect, not just a hash mismatch.
                    candidate = call('native_integrity', 'attach_source', baseline, fixture(name))
                    target.write_text(json.dumps(candidate))
                    rejected = run_cli('validate_output', target, '--input', source)
                    self.assertEqual(rejected.returncode, 1, rejected.stdout + rejected.stderr)
                    self.assertIn(message, rejected.stdout)
                    self.assertNotIn('input_hash does not match', rejected.stdout)
                    self.assertNotIn('Traceback', rejected.stdout + rejected.stderr)


if __name__ == '__main__':
    unittest.main()
