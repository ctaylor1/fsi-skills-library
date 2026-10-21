#!/usr/bin/env python3
"""Independent arithmetic and adverse checks for the bounded structured-credit profile."""
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
PACKAGE = ROOT / 'skills/investment-research/structured-credit-researcher'


def fixture():
    return json.loads((PACKAGE / 'evals/files/input.json').read_text())


def call(module, method, *args):
    sys.path.insert(0, str(PACKAGE / 'scripts'))
    try:
        for key in ('domain', 'analysis_contract', 'research_runtime', 'native_integrity', 'validate_input', 'validate_output', 'calculate_or_transform'):
            sys.modules.pop(key, None)
        spec = importlib.util.spec_from_file_location(module, PACKAGE / 'scripts' / (module + '.py'))
        mod = importlib.util.module_from_spec(spec); sys.modules[module] = mod; spec.loader.exec_module(mod)
        return getattr(mod, method)(*args)
    finally:
        sys.path.pop(0)


def compute(doc=None):
    return call('calculate_or_transform', 'compute', fixture() if doc is None else doc)


def flat_scenario(doc, default=0, recovery=0, prepay=0, scheduled=0):
    for a in doc['scenario']['assumptions']:
        a.update(default_fraction=default, recovery_fraction=recovery, prepay_fraction=prepay, scheduled_principal=scheduled)
    return doc


class StructuredCreditPhase4(unittest.TestCase):
    def test_saved_downside_independent_arithmetic(self):
        d = fixture(); out = compute(d); r = out['results']; w = r['waterfall']; notes = r['tranche_results']
        # 20 defaults, 8 recoveries, 5 scheduled and 5 prepaid => 18 cash, 70 remaining collateral, 12 loss.
        self.assertEqual(r['collateral_review']['opening_principal'], 100)
        self.assertEqual(r['collateral_review']['ending_performing_principal'], 70)
        self.assertEqual(w['principal_collections'], 18)
        self.assertEqual(r['loss_allocation']['scenario_collateral_loss'], 12)
        self.assertEqual(r['loss_allocation']['equity_cushion_absorbed'], 10)
        self.assertEqual(notes[0]['principal_write_down'], 0)
        self.assertEqual(notes[1]['principal_write_down'], 2)
        self.assertEqual(notes[0]['interest_due'], .875)
        self.assertEqual(notes[1]['interest_due'], .4)
        self.assertAlmostEqual(w['excess_interest_diverted'], 1.725)
        self.assertAlmostEqual(notes[0]['ending_principal'], 50.275)
        self.assertEqual(notes[1]['ending_principal'], 18)
        self.assertEqual(r['conservation']['cash_sources'], 27)
        self.assertEqual(r['conservation']['cash_uses'], 27)
        self.assertEqual(out, json.loads((PACKAGE / 'evals/files/valid.json').read_text()))
        self.assertFalse(call('validate_input', 'validate', d)[0])
        self.assertFalse(call('validate_output', 'validate', out, d)[0])

    def test_recovery_counted_once_cash_not_reinstated_collateral(self):
        d = flat_scenario(fixture(), default=.5, recovery=.4)
        r = compute(d)['results']; c = r['collateral_review']; loss = r['loss_allocation']; w = r['waterfall']
        self.assertEqual(c['ending_performing_principal'], 50)
        self.assertEqual(w['principal_collections'], 20)
        self.assertEqual(loss['scenario_collateral_loss'], 30)
        self.assertEqual(loss['equity_cushion_absorbed'], 10)
        self.assertEqual(loss['note_principal_write_downs'], 20)
        self.assertEqual(r['tranche_results'][1]['ending_principal'], 0)
        self.assertAlmostEqual(r['tranche_results'][0]['ending_principal'], 48.275)

    def test_severe_loss_junior_then_senior_after_cushion(self):
        d = flat_scenario(fixture(), default=.6)
        r = compute(d)['results']; notes = r['tranche_results']
        self.assertEqual(r['loss_allocation']['scenario_collateral_loss'], 60)
        self.assertEqual(notes[1]['principal_write_down'], 20)
        self.assertEqual(notes[0]['principal_write_down'], 30)
        self.assertEqual(r['loss_allocation']['unallocated_loss'], 0)

    def test_full_loss_zero_denominator_no_fake_coverage_ratio(self):
        d = flat_scenario(fixture(), default=1)
        r = compute(d)['results']; trigger = r['trigger_result']
        self.assertTrue(trigger['denominator_zero']); self.assertIsNone(trigger['observed_ratio'])
        self.assertFalse(trigger['breached']); self.assertEqual(r['loss_allocation']['note_principal_write_downs'], 90)
        self.assertEqual(r['waterfall']['note_principal_paid'], 0)
        self.assertAlmostEqual(r['waterfall']['residual_interest_cash'], 1.725)

    def test_prepayment_applies_only_after_defaults_and_scheduled(self):
        d = flat_scenario(fixture(), default=.2, recovery=0, prepay=.5, scheduled=2)
        r = compute(d)['results']; assets = r['collateral_review']['assets']
        # 60 asset: 12 defaults then 2 scheduled, so prepay 23. 40 asset: 8 defaults,2 scheduled, prepay15.
        self.assertEqual(assets[0]['prepaid_principal'], 23)
        self.assertEqual(assets[1]['prepaid_principal'], 15)
        self.assertEqual(r['waterfall']['principal_collections'], 42)
        self.assertEqual(r['collateral_review']['ending_performing_principal'], 38)

    def test_all_prepay_excess_principal_is_residual_and_reserve_stays_separate(self):
        d = flat_scenario(fixture(), prepay=1)
        r = compute(d)['results']; w = r['waterfall']
        self.assertEqual(r['collateral_review']['ending_performing_principal'], 0)
        self.assertEqual(w['note_principal_paid'], 90)
        self.assertAlmostEqual(w['residual_principal_cash'], 11.725)
        self.assertEqual(w['ending_reserve'], 5)
        self.assertEqual(r['conservation']['cash_sources'], r['conservation']['cash_uses'])

    def test_disabled_trigger_keeps_excess_interest_separate(self):
        d = fixture(); d['reviewed_terms']['trigger'].update(enabled=False, minimum_ratio=None)
        r = compute(d)['results']; w = r['waterfall']
        self.assertFalse(r['trigger_result']['breached']); self.assertEqual(w['excess_interest_diverted'], 0)
        self.assertAlmostEqual(w['residual_interest_cash'], 1.725)
        self.assertEqual(w['note_principal_paid'], 18)
        self.assertEqual(r['tranche_results'][0]['ending_principal'], 52)

    def test_trigger_equality_is_not_a_breach(self):
        d = fixture(); d['reviewed_terms']['trigger']['minimum_ratio'] = 70 / 88
        r = compute(d)['results']; self.assertFalse(r['trigger_result']['breached'])
        self.assertEqual(r['waterfall']['note_principal_paid'], 18)
        d['reviewed_terms']['trigger']['minimum_ratio'] += .0001
        self.assertTrue(compute(d)['results']['trigger_result']['breached'])

    def test_exact_decimal_trigger_equality_and_strict_neighbors(self):
        d = fixture()
        d['pool']['assets'] = [d['pool']['assets'][0]]
        d['pool']['assets'][0]['balance'] = .3
        d['tranches']['notes'] = [d['tranches']['notes'][0]]
        d['tranches']['notes'][0].update(opening_principal=.25, annual_coupon=0)
        d['scenario']['assumptions'] = [d['scenario']['assumptions'][0]]
        a = d['scenario']['assumptions'][0]
        a.update(default_fraction=0, recovery_fraction=0, scheduled_principal=.1, prepay_fraction=0)
        d['scenario'].update(interest_collections=1, fees_due=0)
        d['reviewed_terms']['opening_reserve'] = 0
        trigger = d['reviewed_terms']['trigger']; trigger['minimum_ratio'] = .8
        # Declared decimal (.3-.1)/.25 is exactly .8; binary .3-.1 must not divert cash.
        r = compute(d)['results']; self.assertFalse(r['trigger_result']['breached'])
        self.assertEqual(r['waterfall']['excess_interest_diverted'], 0)
        self.assertEqual(r['waterfall']['residual_interest_cash'], 1)
        self.assertEqual(r['trigger_result']['comparison_numerator_rational'], '1/5')
        self.assertEqual(r['trigger_result']['comparison_denominator_rational'], '1/4')
        for threshold, expected in [(.8000000000000001, True), (.7999999999999999, False)]:
            trigger['minimum_ratio'] = threshold
            self.assertEqual(compute(d)['results']['trigger_result']['breached'], expected)
        trigger['minimum_ratio'] = .8
        for scheduled, expected in [(.10000000000000002, True), (.09999999999999999, False)]:
            a['scheduled_principal'] = scheduled
            self.assertEqual(compute(d)['results']['trigger_result']['breached'], expected)

    def test_exact_trigger_reconstructs_post_loss_note_denominator(self):
        d = fixture(); d['pool']['assets'] = [d['pool']['assets'][0]]
        d['pool']['assets'][0]['balance'] = .3
        d['tranches']['notes'] = [d['tranches']['notes'][0]]
        d['tranches']['notes'][0].update(opening_principal=.25, annual_coupon=0)
        d['scenario']['assumptions'] = [d['scenario']['assumptions'][0]]
        d['scenario']['assumptions'][0].update(default_fraction=.2, recovery_fraction=0, scheduled_principal=.048, prepay_fraction=0)
        d['reviewed_terms']['trigger']['minimum_ratio'] = .8
        # .06 loss less .05 cushion writes down .01 notes => .24 denominator;
        # .3-.06-.048=.192 ending collateral, exactly .8 of .24.
        r = compute(d)['results']['trigger_result']
        self.assertFalse(r['breached']); self.assertEqual(r['comparison_numerator_rational'], '24/125')
        self.assertEqual(r['comparison_denominator_rational'], '6/25')
        self.assertEqual(r['observed_ratio'], .8)

    def test_trigger_order_excludes_collected_principal_and_reserve(self):
        r = compute()['results']['trigger_result']
        self.assertEqual(r['numerator'], 70); self.assertEqual(r['denominator_post_loss_notes'], 88)
        self.assertAlmostEqual(r['observed_ratio'], 70 / 88)
        self.assertNotEqual(r['observed_ratio'], (70 + 18 + 5) / 88)

    def test_reserve_covers_fees_then_opening_basis_senior_interest(self):
        d = fixture(); d['scenario'].update(interest_collections=0, fees_due=1)
        d['reviewed_terms']['opening_reserve'] = 2
        r = compute(d)['results']; w = r['waterfall']; notes = r['tranche_results']
        self.assertEqual(w['fees_paid'], 1); self.assertEqual(w['ending_reserve'], 0)
        self.assertEqual(notes[0]['interest_paid'], .875)
        self.assertEqual(notes[1]['interest_paid'], .125)
        self.assertAlmostEqual(notes[1]['unpaid_interest'], .275)
        self.assertEqual(w['note_principal_paid'], 18)  # principal never pays interest.
        self.assertEqual(w['reserve_draw_for_fees_and_interest'], 2)

    def test_unpaid_fee_uses_all_interest_and_reserve_before_any_note_interest(self):
        d = fixture(); d['scenario'].update(interest_collections=1, fees_due=5); d['reviewed_terms']['opening_reserve'] = 1
        r = compute(d)['results']; self.assertEqual(r['waterfall']['fees_unpaid'], 3)
        self.assertEqual(r['waterfall']['interest_paid'], 0)
        self.assertTrue(any('fees unpaid' in s for s in compute(d)['unresolved_issues']))

    def test_concentration_aggregates_same_obligor_across_assets(self):
        d = fixture(); d['pool']['assets'][1]['obligor_id'] = 'O1'
        r = compute(d)['results']['collateral_review']
        self.assertEqual(r['largest_obligor_fraction'], 1)
        self.assertEqual(len(r['concentrations']['obligor_id']), 1)
        self.assertEqual(len(r['concentrations']['vintage']), 2)

    def test_ineligible_asset_not_dropped_from_economics(self):
        d = fixture(); d['pool']['assets'][1].update(eligible=False, eligibility_reason='synthetic eligibility breach')
        out = compute(d); r = out['results']['collateral_review']
        self.assertEqual(r['supplied_eligible_principal'], 60)
        self.assertEqual(r['opening_principal'], 100)
        self.assertEqual(r['ending_performing_principal'], 70)
        self.assertFalse(r['eligibility_independently_verified'])
        self.assertTrue(any('supplied-ineligible' in x for x in out['unresolved_issues']))

    def test_requested_coverage_missing_and_gap_remain_partial(self):
        d = fixture(); d['research_review']['assessments'] = []
        out = compute(d); rows = out['results']['research_review']['requested_coverage']
        self.assertEqual(len(rows), 5); self.assertTrue(all(r['status'] == 'not-supplied' for r in rows))
        self.assertEqual(out['status'], 'partial')
        d = fixture(); d['research_review']['assessments'][0]['status'] = 'gap'
        self.assertTrue(any('remains gap' in x for x in compute(d)['unresolved_issues']))

    def test_rank_order_not_input_array_order(self):
        d = fixture(); d['tranches']['notes'].reverse()
        r = compute(d)['results']; self.assertEqual(r, compute()['results'])

    def test_inventory_identity_and_unsupported_term_rejections(self):
        cases = []
        d = fixture(); d['pool']['inventory_complete'] = False; cases.append(d)
        d = fixture(); d['tranches']['inventory_complete'] = False; cases.append(d)
        d = fixture(); d['pool']['issuer_id'] = 'OTHER'; cases.append(d)
        d = fixture(); d['subject']['id'] = 'ABS-Z'; cases.append(d)
        d = fixture(); d['tranches']['notes'][1]['seniority'] = 1; cases.append(d)
        d = fixture(); d['tranches']['notes'][1]['opening_interest_arrears'] = 1; cases.append(d)
        d = fixture(); d['tranches']['notes'][0]['opening_principal'] = 90; cases.append(d)
        d = fixture(); d['reviewed_terms']['profile'] = 'universal-clo'; cases.append(d)
        d = fixture(); d['reviewed_terms']['reserve_use'] = 'principal-and-interest'; cases.append(d)
        d = fixture(); d['scenario']['recovery_timing'] = 'one-year-lag'; cases.append(d)
        d = fixture(); d['scenario']['kind'] = 'actuals'; cases.append(d)
        d = fixture(); d['reviewed_terms']['reinvestment'] = True; cases.append(d)
        d = fixture(); d['reviewed_terms']['trigger']['test_basis'] = 'after-distribution'; cases.append(d)
        for d in cases:
            with self.subTest(d=d): self.assertTrue(call('validate_input', 'validate', d)[0])

    def test_missing_or_duplicate_asset_assumption_rejections(self):
        cases = []
        d = fixture(); d['scenario']['assumptions'].pop(); cases.append(d)
        d = fixture(); d['scenario']['assumptions'].append(copy.deepcopy(d['scenario']['assumptions'][0])); cases.append(d)
        d = fixture(); d['pool']['assets'][1]['asset_id'] = 'L1'; cases.append(d)
        d = fixture(); d['scenario']['assumptions'][0]['scheduled_principal'] = 49; cases.append(d)
        for d in cases: self.assertTrue(call('validate_input', 'validate', d)[0])

    def test_missing_negative_boolean_nonfinite_and_fraction_rejections(self):
        for field, value in [('default_fraction', None), ('default_fraction', True), ('default_fraction', -.01), ('default_fraction', 1.01), ('recovery_fraction', float('nan')), ('prepay_fraction', 2), ('scheduled_principal', -1)]:
            d = fixture(); d['scenario']['assumptions'][0][field] = value
            with self.subTest(field=field, value=value): self.assertTrue(call('validate_input', 'validate', d)[0])
        d = fixture(); del d['scenario']['fees_due']; self.assertTrue(call('validate_input', 'validate', d)[0])
        d = fixture(); d['financial_basis']['currency'] = ' Unknown '; self.assertTrue(call('validate_input', 'validate', d)[0])

    def test_time_vintage_and_undeclared_citation_rejections(self):
        cases = []
        d = fixture(); d['pool']['snapshot_date'] = '2026-10-19'; cases.append(d)
        d = fixture(); d['scenario']['period_start'] = '2026-10-21'; cases.append(d)
        d = fixture(); d['scenario']['period_end'] = d['scenario']['period_start']; cases.append(d)
        d = fixture(); d['scenario']['known_at'] = '2026-10-21T12:00:00Z'; cases.append(d)
        d = fixture(); d['pool']['assets'][0]['known_at'] = '2026-10-20'; cases.append(d)
        d = fixture(); d['pool']['evidence_refs'] = [{'source_id': 'synthetic-trust', 'locator': 'undeclared annex'}]; cases.append(d)
        for d in cases: self.assertTrue(call('validate_input', 'validate', d)[0])

    def test_multi_year_horizon_rejected_despite_small_supplied_accrual_fraction(self):
        d = fixture(); d['scenario']['period_end'] = '2046-10-20'
        self.assertTrue(call('validate_input', 'validate', d)[0])
        with self.assertRaises(ValueError): compute(d)

    def test_source_rights_identity_barrier_and_expiry_withhold(self):
        for key, value in [('permission_status', 'denied'), ('classification', 'restricted'), ('subject_ids', ['OTHER']), ('expires_on', '2026-10-19')]:
            d = fixture(); d['sources'][0][key] = value
            out = compute(d)
            with self.subTest(key=key):
                self.assertIsNone(out['results']); self.assertEqual(out['calculation_lineage'], [])
                self.assertEqual(out['evidence_refs'], []); self.assertEqual(out['source_register'], [])
                self.assertEqual(out['status'], 'partial')

    def test_inherited_issues_and_no_authority_preserved(self):
        d = fixture(); d['unresolved_issues'] = ['trustee restatement remains unadjudicated']
        out = compute(d); self.assertIn(d['unresolved_issues'][0], out['unresolved_issues'])
        self.assertFalse(out['authority_granted']); self.assertFalse(out['action_taken'])
        self.assertEqual(out['approval'], 'not_requested'); self.assertEqual(out['execution'], 'not_performed')
        self.assertEqual(out['professional_acceptance'], 'not-established')
        self.assertFalse(out['results']['legal_terms_verified']); self.assertFalse(out['results']['agency_rating_assigned'])
        self.assertFalse(out['results']['tranche_price_estimated'])

    def test_original_bound_reconstruction_and_tamper_deletion_rejected(self):
        d = fixture(); out = compute(d)
        self.assertTrue(call('validate_output', 'validate', out, None)[0])
        for mutate in ('change-result', 'delete-conservation', 'delete-issue', 'add-field', 'change-identity', 'embed-source'):
            altered = copy.deepcopy(out)
            if mutate == 'change-result': altered['results']['tranche_results'][0]['ending_principal'] += 1
            elif mutate == 'delete-conservation': del altered['results']['conservation']
            elif mutate == 'delete-issue': altered['unresolved_issues'] = []
            elif mutate == 'add-field': altered['approved'] = True
            elif mutate == 'change-identity': altered['subject']['issuer_id'] = 'OTHER'
            else: altered['source_input'] = d
            with self.subTest(mutate=mutate): self.assertTrue(call('validate_output', 'validate', altered, d)[0])
        original = copy.deepcopy(d); original['scenario']['interest_collections'] = 5
        self.assertTrue(call('validate_output', 'validate', out, original)[0])

    def test_public_readers_reject_duplicate_keys_and_nonfinite_constants(self):
        env = dict(os.environ); env.pop('PYTHONPATH', None); env.pop('PYTHONHOME', None)
        raw = json.dumps(fixture())
        bads = [raw.replace('"fees_due": 1', '"fees_due": 1, "fees_due": 0'), raw.replace('"fees_due": 1', '"fees_due": NaN')]
        for script in ('validate_input.py', 'calculate_or_transform.py'):
            for payload in bads:
                p = subprocess.run([sys.executable, '-B', str(PACKAGE / 'scripts' / script)], input=payload, text=True, capture_output=True, env=env)
                self.assertNotEqual(p.returncode, 0); self.assertIn('ERROR:', p.stdout); self.assertNotIn('Traceback', p.stderr)
        with tempfile.TemporaryDirectory(prefix='ir-structured-phase4-') as tmp:
            original = Path(tmp) / 'input.json'; original.write_text(raw)
            output = json.dumps(compute()).replace('"authority_granted": false', '"authority_granted": false, "authority_granted": true')
            p = subprocess.run([sys.executable, '-B', str(PACKAGE / 'scripts/validate_output.py'), '--input', str(original)], input=output, text=True, capture_output=True, env=env)
            self.assertNotEqual(p.returncode, 0); self.assertIn('duplicate JSON', p.stdout)


if __name__ == '__main__': unittest.main()
