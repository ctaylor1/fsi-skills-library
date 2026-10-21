#!/usr/bin/env python3
"""Independent numerical, point-in-time and adverse checks for macro/theme methods."""
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
BASE = ROOT / 'skills/investment-research'
MACRO = 'macroeconomic-researcher'
THEME = 'cross-asset-theme-researcher'
NAMES = (MACRO, THEME)


def fixture(name):
    return json.loads((BASE / name / 'evals/files/input.json').read_text())


def call(name, module, method, *args):
    path = BASE / name / 'scripts'
    sys.path.insert(0, str(path))
    try:
        for key in ('domain', 'analysis_contract', 'research_runtime', 'native_integrity', 'validate_input', 'validate_output', 'calculate_or_transform'):
            sys.modules.pop(key, None)
        spec = importlib.util.spec_from_file_location(module, path / (module + '.py'))
        obj = importlib.util.module_from_spec(spec)
        sys.modules[module] = obj
        spec.loader.exec_module(obj)
        return getattr(obj, method)(*args)
    finally:
        sys.path.pop(0)


def compute(name, doc=None):
    return call(name, 'calculate_or_transform', 'compute', fixture(name) if doc is None else doc)


def validate(name, output, doc):
    return call(name, 'validate_output', 'validate', output, doc)[0]


class MacroThemePhase4(unittest.TestCase):
    def test_saved_outputs_and_complete_original_binding(self):
        for name in NAMES:
            with self.subTest(name=name):
                d = fixture(name)
                out = compute(name, d)
                self.assertEqual(out, json.loads((BASE / name / 'evals/files/valid.json').read_text()))
                self.assertFalse(validate(name, out, d))
                self.assertTrue(validate(name, out, None))
                self.assertFalse(out['authority_granted'])
                self.assertFalse(out['action_taken'])
                self.assertEqual(out['source_truth'], 'unverified')
                self.assertEqual(out['professional_acceptance'], 'not-established')
                self.assertNotIn('source_input', out)
                self.assertEqual(out['status'], 'complete-for-supplied-scope')

    def test_whole_output_and_detached_original_mutations(self):
        for name in NAMES:
            d = fixture(name)
            original = compute(name, d)
            for mode in ('results', 'delete', 'extra', 'source', 'authority'):
                with self.subTest(name=name, mode=mode):
                    out = copy.deepcopy(original)
                    if mode == 'results': out['results'] = {'invented': 0}
                    elif mode == 'delete': del out['unresolved_issues']
                    elif mode == 'extra': out['unchecked'] = 'claim'
                    elif mode == 'source': out['source_input'] = d
                    else: out['authority_granted'] = True
                    self.assertTrue(validate(name, out, d))
            altered = copy.deepcopy(d)
            altered['sources'][0]['version'] = 'different'
            self.assertTrue(validate(name, original, altered))

    def test_public_clis_compute_and_validate(self):
        with tempfile.TemporaryDirectory(prefix='ir-phase4-macro-theme-') as temp:
            for name in NAMES:
                with self.subTest(name=name):
                    cwd = BASE / name
                    source = cwd / 'evals/files/input.json'
                    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
                    p = subprocess.run([sys.executable, '-B', 'scripts/calculate_or_transform.py', str(source)], cwd=cwd, env=env, capture_output=True, text=True)
                    self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
                    self.assertEqual(json.loads(p.stdout)['method_id'], name)
                    output = Path(temp) / (name + '.json')
                    output.write_text(p.stdout)
                    q = subprocess.run([sys.executable, '-B', 'scripts/validate_output.py', str(output), '--input', str(source)], cwd=cwd, env=env, capture_output=True, text=True)
                    self.assertEqual(q.returncode, 0, q.stdout + q.stderr)

    def test_duplicate_keys_nonfinite_and_bad_shapes_are_controlled(self):
        for name in NAMES:
            for module in ('calculate_or_transform', 'validate_input'):
                for raw in ('{"request_id":"x","request_id":"y"}', '{"v":NaN}', '{"v":Infinity}', '[]', 'null', 'true', '"text"'):
                    with self.subTest(name=name, module=module, raw=raw):
                        p = subprocess.run([sys.executable, '-B', 'scripts/' + module + '.py'], cwd=BASE/name, input=raw, capture_output=True, text=True)
                        self.assertNotEqual(p.returncode, 0)
                        self.assertIn('ERROR:', p.stdout)
                        self.assertNotIn('Traceback', p.stdout + p.stderr)

    def test_output_reader_is_strict(self):
        with tempfile.TemporaryDirectory(prefix='ir-phase4-strict-') as temp:
            for name in NAMES:
                for raw in ('{"x":1,"x":2}', '{"v":NaN}', '{"v":-Infinity}'):
                    pth = Path(temp) / 'bad.json'
                    pth.write_text(raw)
                    p = subprocess.run([sys.executable, '-B', 'scripts/validate_output.py', str(pth), '--input', 'evals/files/input.json'], cwd=BASE/name, capture_output=True, text=True)
                    self.assertNotEqual(p.returncode, 0)
                    self.assertIn('ERROR:', p.stdout)
                    self.assertNotIn('Traceback', p.stdout + p.stderr)

    def test_permission_identity_expiry_and_barrier_withhold_all(self):
        for name in NAMES:
            for mode in ('denied', 'subject', 'expired', 'private', 'future'):
                d = fixture(name)
                s = d['sources'][0]
                if mode == 'denied': s['permission_status'] = 'denied'
                elif mode == 'subject': s['subject_ids'] = ['DIFFERENT']
                elif mode == 'expired': s['expires_on'] = '2026-10-19'
                elif mode == 'private': s['classification'] = 'confidential'
                else:
                    # Source knows more than cutoff: move all row knowledge beyond
                    # source time while keeping cutoff unchanged. Native row
                    # checks may reject; either route cannot produce a projection.
                    s['known_at'] = '2026-10-21'
                with self.subTest(name=name, mode=mode):
                    if mode == 'future':
                        with self.assertRaises(ValueError): compute(name, d)
                    else:
                        out = compute(name, d)
                        self.assertIsNone(out['results'])
                        self.assertEqual(out['calculation_lineage'], [])
                        self.assertEqual(out['evidence_refs'], [])
                        self.assertEqual(out['source_register'], [])
                        self.assertEqual(out['status'], 'partial')

    def test_row_citations_must_be_permission_gated(self):
        for name in NAMES:
            d = fixture(name)
            d['evidence_refs'] = []
            with self.subTest(name=name), self.assertRaises(ValueError): compute(name, d)

    def test_missing_inputs_are_not_zero_and_nonfinite_reject(self):
        for name in NAMES:
            for value in (True, float('inf'), float('nan'), '1'):
                d = fixture(name)
                if name == MACRO: d['series'][0]['observations'][0]['value'] = value
                else: d['exposures'][0]['sensitivity'] = value
                with self.subTest(name=name, value=value), self.assertRaises(ValueError): compute(name, d)

    def test_unknown_actions_and_probabilities_reject(self):
        for name in NAMES:
            d = fixture(name)
            d['trade_instructions'] = 'execute'
            with self.subTest(name=name), self.assertRaises(ValueError): compute(name, d)
        d = fixture(MACRO); d['outlooks'][0]['probability'] = 0.75
        with self.assertRaises(ValueError): compute(MACRO, d)
        d = fixture(THEME); d['scenarios'][0]['probability'] = 0.75
        with self.assertRaises(ValueError): compute(THEME, d)

    def test_independent_growth_revision_and_annualization(self):
        out = compute(MACRO)['results']
        self.assertEqual([r['observation_id'] for r in out['selected_observations']], ['q1-revised', 'q2-first'])
        self.assertEqual(out['revisions'][0]['value_change'], 1)
        self.assertAlmostEqual(out['calculations'][0]['value'], 2.0)
        self.assertAlmostEqual(out['calculations'][1]['value'], 8.243216, places=6)
        self.assertEqual(out['calculations'][0]['from_observation_id'], 'q1-revised')
        self.assertEqual(out['calculations'][0]['unit'], 'percent')

    def test_release_order_not_input_order_controls_selection(self):
        d = fixture(MACRO)
        expected = compute(MACRO, d)['results']
        d['series'][0]['observations'].reverse()
        self.assertEqual(compute(MACRO, d)['results'], expected)

    def test_historical_cutoff_excludes_later_revision_and_value(self):
        d = fixture(MACRO)
        d['as_of'] = d['knowledge_cutoff'] = '2026-08-01'
        d['outlooks'] = []
        out = compute(MACRO, d)
        self.assertEqual([r['observation_id'] for r in out['results']['selected_observations']], ['q1-first'])
        self.assertEqual(out['results']['selected_observations'][0]['value'], 100)
        self.assertTrue(all('value' not in r for r in out['results']['excluded_observations']))
        self.assertIsNone(out['results']['calculations'][0]['value'])
        self.assertEqual(out['status'], 'partial')

    def test_future_release_with_future_source_withholds_whole_projection(self):
        d = fixture(MACRO)
        future = copy.deepcopy(d['sources'][0]);future['source_id'] = 'future';future['known_at'] = '2026-10-21'
        ref = {'source_id':'future', 'locator':'synthetic:future#table'}
        d['sources'].append(future);d['evidence_refs'].append(ref)
        d['series'][0]['observations'].append({'observation_id':'future','period_end':'2026-06-30','release_at':'2026-10-21','vintage_id':'future','value':999999,'evidence_refs':[ref]})
        out = compute(MACRO, d)
        self.assertIsNone(out['results'])
        self.assertEqual(out['evidence_refs'], [])
        self.assertTrue(validate(MACRO, dict(out, results={'leaked':999999}), d))

    def test_intraday_cutoff_does_not_create_midnight(self):
        d = fixture(MACRO)
        d['knowledge_cutoff'] = '2026-10-20T12:00:00Z'
        d['outlooks'] = []
        out = compute(MACRO, d)
        # Date-only source metadata itself cannot prove intraday eligibility.
        self.assertIsNone(out['results'])
        self.assertEqual(out['status'], 'partial')

    def test_aware_release_cutoff_selection(self):
        d = fixture(MACRO)
        d['knowledge_cutoff'] = '2026-10-20T14:00:00Z'
        d['sources'][0]['known_at'] = '2026-07-30T12:00:00Z'
        d['outlooks'] = []
        for r in d['series'][0]['observations']: r['release_at'] += 'T13:00:00Z'
        late = copy.deepcopy(d['series'][0]['observations'][-1]);late.update(observation_id='q2-after-cutoff',release_at='2026-10-20T14:01:00Z',vintage_id='later',value=888)
        d['series'][0]['observations'].append(late)
        out = compute(MACRO, d)['results']
        self.assertEqual(out['selected_observations'][-1]['value'], 103.02)
        self.assertIn('q2-after-cutoff', [r['observation_id'] for r in out['excluded_observations']])

    def test_latest_null_does_not_fall_back(self):
        d = fixture(MACRO);d['series'][0]['observations'][1]['value'] = None
        out = compute(MACRO, d)
        self.assertIsNone(out['results']['selected_observations'][0]['value'])
        self.assertIsNone(out['results']['revisions'][0]['value_change'])
        self.assertIsNone(out['results']['calculations'][0]['value'])
        self.assertEqual(out['status'], 'partial')

    def test_requested_missing_series_and_question_coverage(self):
        d = fixture(MACRO);d['requested_series_ids'].append('inflation');d['series_inventory_complete'] = False
        d['research_questions'][0]['counter_evidence'] = None
        out = compute(MACRO, d)
        self.assertFalse(out['results']['requested_coverage'][-1]['eligible_observation_supplied'])
        self.assertEqual(out['results']['research_questions'][0]['review_status'], 'needs-review')
        self.assertEqual(out['status'], 'partial')

    def test_rate_difference_has_percentage_point_units(self):
        d = fixture(MACRO);s=d['series'][0];s.update(measure_kind='rate',unit='percent',price_basis='not-applicable',price_base='not-applicable',annualization='not-applicable')
        s['observations'][0]['value']=4;s['observations'][1]['value']=4.1;s['observations'][2]['value']=4.3
        d['calculations']=d['calculations'][:1];d['calculations'][0]['operation']='difference'
        d['research_questions'][0]['required_calculation_ids']=['quarter-growth'];d['outlooks']=[]
        out=compute(MACRO,d)['results']
        self.assertAlmostEqual(out['calculations'][0]['value'],0.2)
        self.assertEqual(out['calculations'][0]['unit'],'percentage-point')
        self.assertEqual(out['revisions'][0]['unit'],'percentage-point')
        d['calculations'][0]['operation']='percent-change'
        with self.assertRaises(ValueError):compute(MACRO,d)

    def test_monthly_and_two_quarter_annualization(self):
        d=fixture(MACRO);s=d['series'][0];s['frequency']='monthly';s['observations']=s['observations'][1:]
        s['observations'][0].update(period_end='2026-05-31',value=200)
        s['observations'][1].update(period_end='2026-06-30',value=202)
        for c in d['calculations']:c['from_period']='2026-05-31'
        d['outlooks']=[]
        self.assertAlmostEqual(compute(MACRO,d)['results']['calculations'][1]['value'],12.682503013196978)
        s['frequency']='quarterly';s['observations'][0].update(period_end='2025-12-31',value=100);s['observations'][1]['value']=110
        for c in d['calculations']:c['from_period']='2025-12-31'
        self.assertAlmostEqual(compute(MACRO,d)['results']['calculations'][1]['value'],21.0)

    def test_bad_periods_basis_and_duplicate_release_reject(self):
        for mode in ('quarter','period','unknown','realbase','basisoverride','duplicate','beforeperiod','negative','unadjusted'):
            d=fixture(MACRO);s=d['series'][0]
            if mode=='quarter':s['observations'][0]['period_end']='2026-02-28'
            elif mode=='period':s['observations'][0]['period_end']='2026-03-30'
            elif mode=='unknown':s['unit']=' unknown '
            elif mode=='realbase':s['price_base']='not-applicable'
            elif mode=='basisoverride':s['observations'][0]['unit']='EUR millions'
            elif mode=='duplicate':
                r=copy.deepcopy(s['observations'][1]);r['observation_id']='ambiguous';s['observations'].append(r)
            elif mode=='beforeperiod':s['observations'][0]['release_at']='2026-01-01'
            elif mode=='negative':s['observations'][1]['value']=-1
            else:s['seasonal_adjustment']='not-seasonally-adjusted'
            with self.subTest(mode=mode):
                if mode=='negative':
                    out=compute(MACRO,d);self.assertIsNone(out['results']['calculations'][0]['value']);self.assertEqual(out['status'],'partial')
                else:
                    with self.assertRaises(ValueError):compute(MACRO,d)

    def test_outlook_types_consensus_and_cutoff(self):
        d=fixture(MACRO);o=d['outlooks'][0];o['kind']='consensus'
        with self.assertRaises(ValueError):compute(MACRO,d)
        o['consensus_provider']='SYNTH-CONSENSUS'
        self.assertEqual(compute(MACRO,d)['results']['outlooks'][0]['kind'],'consensus')
        o['known_at']='2026-10-21'
        with self.assertRaises(ValueError):compute(MACRO,d)

    def test_independent_duration_linear_and_reverse_shock(self):
        out=compute(THEME)['results']
        self.assertEqual([r['value'] for r in out['scenario_responses']],[-5.0,-2.0])
        self.assertFalse(out['causality_established']);self.assertFalse(out['probabilities_estimated']);self.assertFalse(out['portfolio_allocation_proposed'])
        d=fixture(THEME);d['scenarios'][0]['shocks'][0]['value']=-25
        self.assertEqual([r['value'] for r in compute(THEME,d)['results']['scenario_responses']],[1.25,0.5])

    def test_qualitative_response_never_implies_number(self):
        d=fixture(THEME);e=d['exposures'][1];e.update(method='qualitative',sensitivity=None,response_unit='qualitative',qualitative_response='Conditional funding cost pressure; sign is uncertain.')
        row=compute(THEME,d)['results']['scenario_responses'][1]
        self.assertIsNone(row['value']);self.assertIsNone(row['unavailable_reason']);self.assertIn('uncertain',row['conditional_qualitative_response'])
        e['sensitivity']=0
        with self.assertRaises(ValueError):compute(THEME,d)

    def test_missing_shock_and_unmodeled_driver_are_partial(self):
        d=fixture(THEME);d['exposures'][1]['driver_id']='earnings'
        out=compute(THEME,d);self.assertIsNone(out['results']['scenario_responses'][1]['value']);self.assertEqual(out['status'],'partial')
        d['scenarios'][0]['shocks'].append({'driver_id':'unmodeled','unit':'percent','value':10})
        self.assertTrue(any('no supplied exposure' in i for i in compute(THEME,d)['unresolved_issues']))

    def test_shock_denominator_mismatch_is_not_converted(self):
        d=fixture(THEME);d['scenarios'][0]['shocks'][0]['unit']='percentage-point'
        with self.assertRaises(ValueError):compute(THEME,d)

    def test_nonpositive_price_approximation_is_withheld(self):
        d=fixture(THEME);d['scenarios'][0]['shocks'][0]['value']=2000
        out=compute(THEME,d)
        self.assertIsNone(out['results']['scenario_responses'][0]['value'])
        self.assertIn('outside positive-price',out['results']['scenario_responses'][0]['unavailable_reason'])
        self.assertEqual(out['status'],'partial')

    def test_counter_evidence_coverage_and_inventory_gaps(self):
        d=fixture(THEME);d['evidence']=d['evidence'][:1];d['coverage']['required_asset_classes'].append('credit');d['coverage']['inventory_complete']=False
        out=compute(THEME,d)
        self.assertEqual(out['results']['coverage']['missing_asset_classes'],['credit'])
        self.assertEqual(out['status'],'partial')
        self.assertTrue(any('counter-evidence' in i for i in out['unresolved_issues']))

    def test_falsifier_observed_challenges_and_due_untested_is_gap(self):
        d=fixture(THEME);f=d['falsifiers'][0];f['due_on']='2026-10-19'
        self.assertEqual(compute(THEME,d)['status'],'partial')
        f.update(status='observed',known_at='2026-10-20',evidence_refs=d['evidence_refs'])
        out=compute(THEME,d)
        self.assertEqual(out['results']['hypothesis_status'],'challenged-by-supplied-falsifier')
        self.assertEqual(out['status'],'partial')
        f['status']='not-observed'
        self.assertEqual(compute(THEME,d)['results']['hypothesis_status'],'supplied-hypothesis-for-review')
        d['falsifiers']=[]
        self.assertEqual(compute(THEME,d)['status'],'partial')

    def test_fx_quote_and_horizon_duration_constraints(self):
        for mode in ('fxquote','negative-duration','asset','horizon','weight'):
            d=fixture(THEME)
            if mode=='fxquote':d['exposures'][1]['asset_class']='fx'
            elif mode=='negative-duration':d['exposures'][0]['sensitivity']=-1
            elif mode=='asset':d['exposures'][0]['asset_class']='equity'
            elif mode=='horizon':d['scenarios'][0]['horizon_date']='2027-06-30'
            else:d['exposures'][0]['portfolio_weight']=0.5
            with self.subTest(mode=mode),self.assertRaises(ValueError):compute(THEME,d)
        d=fixture(THEME);e=d['exposures'][1];e.update(asset_class='fx',quote_convention='USD per EUR')
        out=compute(THEME,d)['results']['scenario_responses'][1]
        self.assertEqual(out['quote_convention'],'USD per EUR');self.assertEqual(out['value'],-2)

    def test_macro_selected_driver_rows_are_preserved_without_shock_inference(self):
        rows=compute(MACRO)['results']['selected_observations'];d=fixture(THEME);d['driver_observations']=rows
        original_responses=compute(THEME,d)['results']['scenario_responses']
        out=compute(THEME,d)
        self.assertEqual(out['results']['driver_observations'],rows)
        self.assertEqual(out['results']['scenario_responses'],original_responses)
        d['driver_observations'][0]['value']=None
        self.assertEqual(compute(THEME,d)['status'],'partial')
        d['driver_observations'].append(copy.deepcopy(d['driver_observations'][0]));d['driver_observations'][-1]['observation_id']='other-vintage'
        with self.assertRaises(ValueError):compute(THEME,d)

    def test_driver_rows_require_cutoff_basis_and_citations(self):
        for mode in ('time','base','unit','citation','period'):
            d=fixture(THEME);d['driver_observations']=compute(MACRO)['results']['selected_observations'];r=d['driver_observations'][0]
            if mode=='time':r['release_at']='2026-10-21'
            elif mode=='base':r['price_base']='not-applicable'
            elif mode=='unit':r['unit']='unknown'
            elif mode=='citation':r['evidence_refs']=[]
            else:r['period_end']='2026-02-28'
            with self.subTest(mode=mode),self.assertRaises(ValueError):compute(THEME,d)

    def test_inherited_findings_remain_open(self):
        for name in NAMES:
            d=fixture(name);d['unresolved_issues']=['Institution model validation pending']
            out=compute(name,d)
            self.assertIn('Institution model validation pending',out['unresolved_issues'])
            self.assertEqual(out['status'],'partial')


if __name__ == '__main__':
    unittest.main()
