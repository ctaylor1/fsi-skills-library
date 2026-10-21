#!/usr/bin/env python3
"""Independent bounded regressions for Phase 1 credit, earnings and publication methods.

No network calls, real-source authentication, practitioner or deployment acceptance is claimed.
Run with PYTHONDONTWRITEBYTECODE=1 python3 -B tools/test_ir_credit_phase1.py.
"""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from datetime import date

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'skills/investment-research'
META = {
    'capital-structure-maturity-mapper': ('debt_example.json', 'map_example.json', 'compute'),
    'credit-document-terms-reviewer': ('extraction_request.json', 'extraction_package.json', 'compute'),
    'issuer-credit-surveillance-reviewer': ('surveillance_request_example.json', 'surveillance_packet_example.json', 'assemble'),
    'earnings-preview-packet-builder': ('preview_request_example.json', 'preview_packet_example.json', 'assemble'),
    'earnings-results-analyzer': ('earnings_example.json', 'pack_example.json', 'compute'),
    'research-publication-preparation-assistant': ('note_example.json', 'packet_example.json', 'compute'),
}
# Parent coordinates the mapper rename only after this worker completes. Keep the tests valid
# after that migration without making the legacy directory an independent primary package.
if not (BASE / 'capital-structure-maturity-mapper').exists():
    META['issuer-capital-structure-mapper'] = META.pop('capital-structure-maturity-mapper')
MAPPER = 'capital-structure-maturity-mapper' if 'capital-structure-maturity-mapper' in META else 'issuer-capital-structure-mapper'
TERMS = 'credit-document-terms-reviewer'
SURV = 'issuer-credit-surveillance-reviewer'
PREVIEW = 'earnings-preview-packet-builder'
RESULTS = 'earnings-results-analyzer'
PUB = 'research-publication-preparation-assistant'


def load(name):
    path = BASE / name
    scripts = path / 'scripts'
    sys.path.insert(0, str(scripts))
    try:
        modules = {}
        for key in ('native_integrity', 'validate_input', 'calculate_or_transform', 'validate_output'):
            sys.modules.pop(key, None)
            spec = importlib.util.spec_from_file_location(key, scripts / (key + '.py'))
            mod = importlib.util.module_from_spec(spec)
            sys.modules[key] = mod
            spec.loader.exec_module(mod)
            modules[key] = mod
        source, golden, entry = META[name]
        return (modules['validate_input'].validate,
                getattr(modules['calculate_or_transform'], entry),
                modules['validate_output'].validate,
                json.loads((path / 'evals/files' / source).read_text()),
                json.loads((path / 'evals/files' / golden).read_text()))
    finally:
        sys.path.pop(0)


class Phase1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packages = {n: load(n) for n in META}

    def bundle(self, name):
        vi, compute, vo, source, golden = self.packages[name]
        return vi, compute, vo, copy.deepcopy(source), copy.deepcopy(golden)

    def assert_rejected_input(self, name, source):
        vi, compute, _, _, _ = self.packages[name]
        self.assertTrue(vi(source)[0])
        with self.assertRaises(ValueError):
            compute(source)

    def test_golden_and_separate_original(self):
        for name in META:
            with self.subTest(package=name):
                vi, compute, vo, source, golden = self.bundle(name)
                self.assertFalse(vi(source)[0])
                self.assertEqual(compute(source), golden)
                self.assertFalse(vo(golden, source))
                self.assertTrue(vo(golden))
                self.assertNotIn('source_input', golden)
                self.assertEqual(golden['source_truth'], 'unverified')

    def test_every_output_field_is_reconstructed(self):
        for name in META:
            with self.subTest(package=name):
                _, compute, vo, source, _ = self.bundle(name)
                output = compute(source)
                output['unchecked_narrative'] = 'fabricated extra content'
                self.assertTrue(vo(output, source))
                output = compute(source)
                output['source_truth'] = 'authenticated'
                self.assertTrue(vo(output, source))
                output = compute(source)
                output['source_input'] = copy.deepcopy(source)
                self.assertTrue(vo(output, source))
                changed = copy.deepcopy(source)
                changed['unused_source_metadata'] = 'different original'
                self.assertTrue(vo(compute(source), changed))

    def test_numeric_mutations_rejected(self):
        for name in META:
            with self.subTest(package=name):
                _, compute, vo, source, _ = self.bundle(name)
                out = compute(source)
                if name == MAPPER: out['wac_pct'] += 1
                elif name == TERMS: out['fields'][1]['value']['rate_pct'] += 1
                elif name == SURV: out['metrics']['gross_leverage_x'] += 1
                elif name == PREVIEW: out['consensus_vs_guidance'][0]['gap_to_midpoint'] += 1
                elif name == RESULTS: out['metric_findings'][0]['surprise_pct'] += 1
                else: out['gap_count'] += 1
                self.assertTrue(vo(out, source))

    def test_invalid_top_shapes_and_nonfinite(self):
        for name in META:
            vi, compute, vo, source, _ = self.bundle(name)
            for bad in (None, [], True, 17, 'input'):
                with self.subTest(package=name, shape=repr(bad)):
                    self.assert_rejected_input(name, bad)
                    self.assertTrue(vo(bad, source))
            for number in (float('nan'), float('inf'), -float('inf')):
                bad = copy.deepcopy(source)
                bad['ignored_metadata'] = number
                self.assert_rejected_input(name, bad)

    def test_invalid_nested_shapes_and_boolean_numbers(self):
        shapes = {MAPPER: ('instruments', [False]), TERMS: ('candidates', [None]),
                  SURV: ('financials', []), PREVIEW: ('items', [False]),
                  RESULTS: ('metrics', [None]), PUB: ('note', [])}
        for name, (key, value) in shapes.items():
            _, _, _, source, _ = self.bundle(name)
            source[key] = value
            self.assert_rejected_input(name, source)
        for name in META:
            _, _, _, source, _ = self.bundle(name)
            if name == MAPPER: source['instruments'][0]['principal'] = True
            elif name == TERMS: source['candidates'][0]['page'] = True
            elif name == SURV: source['financials']['cash'] = True
            elif name == PREVIEW: source['metrics'][0]['consensus_value'] = True
            elif name == RESULTS: source['metrics'][0]['actual'] = True
            else: source['note']['target_price'] = True
            self.assert_rejected_input(name, source)

    def test_mapper_independent_arithmetic_and_detail(self):
        _, compute, _, source, _ = self.bundle(MAPPER)
        out = compute(source)
        self.assertEqual(out['total_debt'], 1200)
        self.assertEqual(out['wac_pct'], 6.125)
        self.assertEqual(out['near_term_24m'], 600)
        # Independent days-to-maturity calculation from explicitly expected fixture terms.
        start = date(2026, 7, 18)
        expected = sum(p * (date.fromisoformat(d) - start).days / 365.25 for p, d in
                       ((500, '2027-06-30'), (100, '2028-06-30'),
                        (400, '2030-01-15'), (200, '2032-03-01'))) / 1200
        self.assertEqual(out['wam_years'], round(expected, 2))
        self.assertEqual(len(out['instruments']), 4)
        self.assertEqual(out['instruments'][0]['source_ref'], source['instruments'][0]['source_ref'])
        self.assertEqual(out['instruments'][0]['issuer_id'], source['company']['company_id'])

    def test_mapper_currency_and_unknowns(self):
        _, compute, vo, source, _ = self.bundle(MAPPER)
        source['instruments'][0]['currency'] = 'EUR'
        out = compute(source)
        self.assertIsNone(out['total_debt'])
        self.assertEqual(out['by_currency']['EUR']['total_debt'], 500)
        self.assertEqual(out['by_currency']['USD']['total_debt'], 700)
        self.assertFalse(vo(out, source))
        _, compute, vo, source, _ = self.bundle(MAPPER)
        source['instruments'][0].update(coupon_pct=None, maturity_date=None)
        out = compute(source)
        self.assertIsNone(out['wac_pct']); self.assertIsNone(out['wam_years'])
        self.assertIsNone(out['near_term_24m'])
        self.assertEqual(out['known_coupon_wac_pct'], round(4600 / 700, 4))
        self.assertEqual(out['maturity_wall']['undated'], 500)
        self.assertFalse(vo(out, source))
        for row in source['instruments']: row['principal'] = None
        out = compute(source)
        self.assertIsNone(out['total_debt'])
        self.assertEqual(out['known_principal'], 0)
        self.assertEqual(len(out['excluded_instruments']), 4)

    def test_mapper_calendar_horizon_and_identity(self):
        _, compute, _, source, _ = self.bundle(MAPPER)
        source['instruments'] = [source['instruments'][0]]
        source['instruments'][0]['maturity_date'] = '2028-07-18'
        self.assertEqual(compute(source)['near_term_24m'], 500)
        del source['instruments'][0]['issuer_id']
        self.assert_rejected_input(MAPPER, source)

    def test_terms_identity_version_and_amendments(self):
        _, compute, vo, source, _ = self.bundle(TERMS)
        out = compute(source)
        self.assertEqual(out['fields'][0]['value']['maturity_date'], '2031-04-15')
        self.assertEqual(out['fields'][1]['value']['rate_pct'], 6.5)
        self.assertEqual(sum(r['status'] == 'needs_review' for r in out['fields']), 2)
        for version in ('draft', 'amended', 'unknown'):
            changed = copy.deepcopy(source); changed['doc_version'] = version
            out = compute(changed)
            self.assertTrue(all(r['status'] == 'needs_review' and r['value'] is None for r in out['fields']))
            self.assertFalse(vo(out, changed))
        changed = copy.deepcopy(source); changed['amendments'] = ['unresolved-amendment']
        self.assertTrue(all(r['value'] is None for r in compute(changed)['fields']))
        for key in ('issuer_id', 'instrument_id', 'doc_version', 'governing_law'):
            changed = copy.deepcopy(source); del changed[key]
            self.assert_rejected_input(TERMS, changed)

    def test_terms_conflict_invalid_date_and_signed_coupon(self):
        _, compute, _, source, _ = self.bundle(TERMS)
        source['candidates'].append({**source['candidates'][0], 'raw_value': 'April 16, 2031'})
        out = compute(source)
        self.assertTrue(all(r['value'] is None for r in out['fields'] if r['field'] == 'maturity'))
        source['candidates'][0]['raw_value'] = 'February 30, 2031'
        source['candidates'][1]['raw_value'] = '-6.5% per annum'
        out = compute(source)
        self.assertEqual(out['fields'][0]['status'], 'needs_review')
        self.assertEqual(out['fields'][1]['status'], 'needs_review')

    def test_terms_seniority_negation_and_floating_percentage_spread(self):
        _, compute, vo, source, _ = self.bundle(TERMS)
        source['candidates'][2]['raw_value'] = 'The Notes are not subordinated obligations of the Issuer.'
        source['candidates'][1]['raw_value'] = 'Term SOFR + 2.50% per annum, paid quarterly'
        out = compute(source)
        self.assertEqual(out['fields'][2]['status'], 'needs_review')
        self.assertIsNone(out['fields'][2]['value'])
        self.assertEqual(out['fields'][1]['value']['index'], 'SOFR')
        self.assertEqual(out['fields'][1]['value']['spread_bps'], 250)
        self.assertEqual(out['fields'][1]['value']['frequency'], 'quarterly')
        self.assertFalse(vo(out, source))
        source['candidates'][1]['raw_value'] = 'Term SOFR floating coupon, paid quarterly'
        out = compute(source)
        self.assertEqual(out['fields'][1]['status'], 'needs_review')
        self.assertIsNone(out['fields'][1]['value'])

    def test_surveillance_independent_ratios_and_scope(self):
        _, compute, _, source, _ = self.bundle(SURV)
        out = compute(source)
        for key, expected in {'gross_leverage_x': 5, 'net_leverage_x': 4.5,
                              'interest_coverage_x': 2.5, 'fccr_x': 2,
                              'near_term_maturities': 250, 'total_liquidity': 500}.items():
            self.assertEqual(out['metrics'][key], expected)
        self.assertIsNone(out['metrics']['liquidity_covers_near_term'])
        self.assertTrue(out['metrics']['maturity_funding_comparison'])
        self.assertIn('not contractual FCCR or DSCR', out['metrics']['fccr_method'])
        self.assertEqual(out['changes']['spread_delta_bps'], 60)
        self.assertEqual(out['changes']['rating_changes'][0]['rated_object_type'], 'issuer')
        self.assertEqual(out['covenant_changes'][0]['doc_version'], source['covenants'][0]['doc_version'])

    def test_surveillance_availability_and_inventory_partial(self):
        _, compute, vo, source, _ = self.bundle(SURV)
        source['liquidity_basis'].update(cash_accessibility='restricted', revolver_availability='conditional')
        out = compute(source)
        self.assertIsNone(out['metrics']['total_liquidity'])
        self.assertIsNone(out['metrics']['maturity_funding_comparison'])
        self.assertEqual(out['support_status'], 'PARTIAL')
        self.assertFalse(vo(out, source))
        source['liquidity_basis']['maturity_schedule_complete'] = False
        source['maturities'] = []
        out = compute(source)
        self.assertIsNone(out['metrics']['near_term_maturities'])
        self.assertEqual(out['metrics']['known_near_term_maturities'], 0)
        self.assertFalse(vo(out, source))

    def test_surveillance_nonpositive_denominators_are_not_negative_leverage(self):
        _, compute, vo, source, _ = self.bundle(SURV)
        source['financials'].update(ebitda=-100, interest_expense=0)
        for key in tuple(source['financials']):
            if key.startswith('stated_'): del source['financials'][key]
        out = compute(source)
        for key in ('gross_leverage_x', 'net_leverage_x', 'interest_coverage_x', 'fccr_x'):
            self.assertIsNone(out['metrics'][key])
        self.assertFalse(vo(out, source))

    def test_surveillance_source_type_and_knowledge_eligibility(self):
        _, compute, _, source, _ = self.bundle(SURV)
        changed = copy.deepcopy(source)
        changed['sources'][3]['type'] = 'filing'
        self.assert_rejected_input(SURV, changed)
        changed = copy.deepcopy(source)
        changed['sources'][4]['type'] = 'market'
        self.assert_rejected_input(SURV, changed)
        changed = copy.deepcopy(source)
        changed['sources'][0]['known_at'] = '2026-07-04T00:00:00Z'
        self.assert_rejected_input(SURV, changed)
        # An economic period does not itself assert that information was known in the future.
        changed = copy.deepcopy(source)
        changed['sources'][0]['as_of'] = '2027-12-31'
        self.assertEqual(compute(changed)['source_truth'], 'unverified')
        changed = copy.deepcopy(source); changed['sources'][3]['approved'] = False
        out = compute(changed)
        self.assertEqual(out['support_status'], 'PARTIAL')
        self.assertTrue(any(f['code'] == 'unapproved-source' for f in out['flags']))

    def test_surveillance_missing_maturity_identity_and_docversion(self):
        _, compute, vo, source, _ = self.bundle(SURV)
        source['maturities'][0]['maturity_date'] = None
        out = compute(source)
        self.assertIsNone(out['metrics']['near_term_maturities'])
        self.assertFalse(vo(out, source))
        for target, key in (('maturities', 'instrument_id'), ('covenants', 'doc_version')):
            _, _, _, changed, _ = self.bundle(SURV)
            del changed[target][0][key]
            self.assert_rejected_input(SURV, changed)
        _, _, _, changed, _ = self.bundle(SURV)
        changed['ratings'][0]['rated_object_id'] = 'ANOTHER-ISSUER'
        self.assert_rejected_input(SURV, changed)

    def test_preview_intraday_cutoff_and_roles(self):
        _, compute, _, source, _ = self.bundle(PREVIEW)
        self.assertEqual(compute(source)['packet_status'], 'ready-for-control-review')
        for cutoff in ('2026-07-31T20:01:00Z', '2026-07-31T21:00:00Z', '2026-07-20'):
            changed = copy.deepcopy(source); changed['knowledge_cutoff'] = cutoff
            self.assert_rejected_input(PREVIEW, changed)
        changed = copy.deepcopy(source); changed['metrics'][0]['consensus_known_at'] = '2026-07-20T20:01:00Z'
        self.assert_rejected_input(PREVIEW, changed)
        changed = copy.deepcopy(source); changed['required_approvals'] = ['preparer']
        self.assert_rejected_input(PREVIEW, changed)
        changed = copy.deepcopy(source); changed['approvals'][0]['approver'] = changed['preparer_id']
        self.assert_rejected_input(PREVIEW, changed)

    def test_preview_fiscal_comparisons_not_array_positions(self):
        _, compute, _, source, _ = self.bundle(PREVIEW)
        source['kpi_history'][0]['series'].reverse()
        row = compute(source)['kpi_trends'][0]
        self.assertEqual(row['qoq_delta'], -700)
        self.assertEqual(row['yoy_delta'], 4800)
        source['kpi_history'][0]['series'] = [p for p in source['kpi_history'][0]['series'] if p['period'] != 'FY2025 Q4']
        row = compute(source)['kpi_trends'][0]
        self.assertIsNone(row['qoq_delta'])
        self.assertEqual(row['yoy_delta'], 4800)
        self.assertTrue(row['gaps'])

    def test_preview_partial_hold_is_reproducible(self):
        _, compute, vo, source, _ = self.bundle(PREVIEW)
        source['approvals'] = []
        source['items'][0]['sources'] = []
        out = compute(source)
        self.assertEqual(out['packet_status'], 'hold-for-approval')
        self.assertFalse(vo(out, source))

    def test_results_independent_comparisons_and_one_baseline(self):
        _, compute, _, source, _ = self.bundle(RESULTS)
        out = compute(source)
        self.assertEqual(out['metric_findings'][0]['surprise_pct'], 0.029412)
        self.assertEqual(out['metric_findings'][3]['classification'], 'Beat')
        self.assertEqual(out['guidance_findings'][0]['prior_mid'], 21250)
        self.assertEqual(out['guidance_findings'][0]['new_mid'], 20750)
        self.assertEqual(out['guidance_findings'][0]['classification'], 'Lowered')
        self.assertEqual(out['overall_result'], 'Mixed')
        self.assertIn('one supplied baseline', out['baseline_scope'])
        source['metrics'].append(copy.deepcopy(source['metrics'][0]))
        self.assert_rejected_input(RESULTS, source)

    def test_results_missing_baseline_preserves_guidance(self):
        _, compute, vo, source, _ = self.bundle(RESULTS)
        for m in source['metrics']:
            m['estimate_ref'] = None
        out = compute(source)
        self.assertTrue(all(not f['evaluable'] for f in out['metric_findings']))
        self.assertEqual(len(out['guidance_findings']), 2)
        self.assertEqual(out['overall_result'], 'Undetermined')
        self.assertNotIn('estimate:None', json.dumps(out))
        self.assertFalse(vo(out, source))
        source['guidance'][0]['source_ref'] = None
        out = compute(source)
        self.assertEqual(len(out['guidance_findings']), 1)
        self.assertNotIn('guidance:None', json.dumps(out))

    def test_results_vintage_basis_and_numeric_range(self):
        _, _, _, source, _ = self.bundle(RESULTS)
        for key, value in (('estimate_known_at', '2026-07-17T20:01:00Z'),
                           ('actual_known_at', '2026-07-18T00:00:00Z'),
                           ('estimate_accounting_basis', 'different-basis'),
                           ('estimate_currency', 'EUR')):
            changed = copy.deepcopy(source); changed['metrics'][0][key] = value
            self.assert_rejected_input(RESULTS, changed)
        changed = copy.deepcopy(source); changed['config']['beat_tol'] = -1
        self.assert_rejected_input(RESULTS, changed)
        changed = copy.deepcopy(source); changed['guidance'][0].update(new_low=9, new_high=1)
        self.assert_rejected_input(RESULTS, changed)

    def test_publication_unknowns_are_gaps_and_no_clearance(self):
        _, compute, vo, source, _ = self.bundle(PUB)
        out = compute(source)
        self.assertEqual(out['suggested_disposition'], 'gaps-for-review')
        self.assertTrue(any(g['check'] == 'rights' for g in out['gaps']))
        source.pop('context')
        source['restricted_list'] = []; source['restricted_list_checked'] = False
        out = compute(source)
        self.assertIsNone(out['checks']['restricted'])
        self.assertTrue(any(g['check'] == 'restricted_list_coverage' for g in out['gaps']))
        self.assertFalse(vo(out, source))

    def test_publication_unrated_and_restricted(self):
        _, compute, vo, source, _ = self.bundle(PUB)
        source['note'].update(rating=None, prior_rating=None, target_price=None, prior_target=None,
                              rating_applicable=False, target_applicable=False)
        source['rating_scale'] = []
        out = compute(source)
        self.assertEqual(out['checks']['rating_status'], 'not-applicable')
        self.assertFalse(any(f['check'] == 'rating_validity' for f in out['flags']))
        self.assertFalse(vo(out, source))
        source['restricted_list'] = [source['note']['ticker']]
        out = compute(source)
        self.assertTrue(out['checks']['restricted'])
        self.assertTrue(any(f.get('hard_stop') for f in out['flags']))
        self.assertEqual(out['suggested_disposition'], 'gaps-for-review')

    def test_publication_fabricated_clean_status_rejected(self):
        _, compute, vo, source, _ = self.bundle(PUB)
        out = compute(source)
        out.update(gaps=[], flags=[], gap_count=0, flag_count=0,
                   suggested_disposition='ready-for-compliance-review')
        self.assertTrue(vo(out, source))


if __name__ == '__main__':
    unittest.main(verbosity=2)
