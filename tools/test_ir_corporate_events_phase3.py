#!/usr/bin/env python3
"""Independent financial identities and adverse tests for Phase 3 event mechanics."""
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
PACKAGE = ROOT / 'skills/investment-research/corporate-event-impact-reviewer'


def fixture():
    return json.loads((PACKAGE / 'evals/files/input.json').read_text())


def call(module, method, *args):
    sys.path.insert(0, str(PACKAGE / 'scripts'))
    try:
        for key in ('domain', 'analysis_contract', 'research_runtime', 'native_integrity',
                    'validate_input', 'validate_output', 'calculate_or_transform'):
            sys.modules.pop(key, None)
        spec = importlib.util.spec_from_file_location(module, PACKAGE / 'scripts' / (module + '.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module] = mod
        spec.loader.exec_module(mod)
        return getattr(mod, method)(*args)
    finally:
        sys.path.pop(0)


def compute(doc=None):
    return call('calculate_or_transform', 'compute', fixture() if doc is None else doc)


def event(kind, terms):
    doc = fixture()
    doc['event'].update(type=kind, terms=terms)
    return doc


class CorporateEventsPhase3(unittest.TestCase):
    def test_saved_acquisition_independent_arithmetic(self):
        d = fixture(); out = compute(d); r = out['results']; bridge = r['financial_bridge']
        # Price 150 is equity consideration. Assumed debt 30 and acquired cash 10 imply EV 170.
        self.assertEqual(bridge['before'], {'cash': 80, 'debt': 200, 'shares': 40, 'net_debt': 120})
        self.assertEqual(bridge['after'], {'cash': 65, 'debt': 310, 'shares': 45, 'net_debt': 245})
        self.assertEqual(bridge['change'], {'cash': -15, 'debt': 110, 'shares': 5, 'net_debt': 125})
        self.assertEqual(r['event_metrics']['implied_acquired_enterprise_value'], 170)
        self.assertEqual(r['funding_reconciliation']['sources'], 155)
        self.assertEqual(r['funding_reconciliation']['uses'], 155)
        self.assertAlmostEqual(r['event_metrics']['new_shares_fraction_of_post_event_shares'], 5 / 45)
        self.assertEqual(out, json.loads((PACKAGE / 'evals/files/valid.json').read_text()))
        self.assertFalse(call('validate_input', 'validate', d)[0])
        self.assertFalse(call('validate_output', 'validate', out, d)[0])

    def test_primary_issuance_share_scale_and_net_proceeds(self):
        d = event('equity-raise', {'shares_issued': 2, 'issue_price': 15, 'fees': 3})
        r = compute(d)['results']; b = r['financial_bridge']
        self.assertEqual(b['after']['cash'], 107); self.assertEqual(b['after']['shares'], 42)
        self.assertEqual(b['after']['debt'], 200); self.assertEqual(b['after']['net_debt'], 93)
        self.assertEqual(r['event_metrics']['gross_primary_equity_proceeds'], 30)
        self.assertAlmostEqual(r['event_metrics']['new_shares_fraction_of_post_event_shares'], 2 / 42)

    def test_repurchase_fees_do_not_reduce_additional_shares(self):
        d = event('share-repurchase', {'cash_spend': 60, 'repurchase_price': 20, 'fees': 2, 'cash_funding': 22, 'debt_funding': 40})
        r = compute(d)['results']; b = r['financial_bridge']
        self.assertEqual(b['after'], {'cash': 58, 'debt': 240, 'shares': 37, 'net_debt': 182})
        self.assertEqual(r['event_metrics']['shares_reduced'], 3)
        self.assertEqual(r['event_metrics']['fraction_of_opening_shares_reduced'], .075)
        self.assertEqual(r['event_metrics']['new_shares_fraction_of_post_event_shares'], 0)

    def test_refinancing_cash_retained_fees_and_annual_interest(self):
        d = event('refinancing', {'principal_repaid': 100, 'new_debt_proceeds': 120, 'fees': 5, 'cash_funding': 0, 'cash_retained': 15, 'old_annual_rate': .08, 'new_annual_rate': .06})
        r = compute(d)['results']; b = r['financial_bridge']
        self.assertEqual(b['after'], {'cash': 95, 'debt': 220, 'shares': 40, 'net_debt': 125})
        self.assertEqual(r['event_metrics']['old_tranche_annual_interest'], 8)
        self.assertAlmostEqual(r['event_metrics']['new_tranche_annual_interest'], 7.2)
        self.assertAlmostEqual(r['event_metrics']['annual_interest_change'], -.8)

    def test_disposal_cash_leaving_fees_taxes_and_debt_transfer(self):
        d = event('asset-disposal', {'sale_cash_proceeds': 50, 'debt_transferred': 20, 'cash_disposed': 5, 'fees': 2, 'taxes': 3})
        r = compute(d)['results']; b = r['financial_bridge']
        self.assertEqual(b['after'], {'cash': 120, 'debt': 180, 'shares': 40, 'net_debt': 60})
        self.assertEqual(r['event_metrics']['net_sale_cash_after_fees_tax'], 45)
        self.assertNotIn('book_gain', r['event_metrics'])

    def test_funding_gap_is_retained_not_silently_financed(self):
        d = event('share-repurchase', {'cash_spend': 100, 'repurchase_price': 20, 'fees': 2, 'cash_funding': 102, 'debt_funding': 0})
        out = compute(d); r = out['results']
        self.assertEqual(r['financial_bridge']['after']['cash'], -22)
        self.assertFalse(r['funding_reconciliation']['cash_feasible_for_supplied_bridge'])
        self.assertEqual(r['funding_reconciliation']['additional_cash_required'], 22)
        self.assertEqual(out['status'], 'partial'); self.assertTrue(out['unresolved_issues'])

    def test_no_stock_acquisition_requires_no_unused_price(self):
        d = fixture(); d['event']['terms'].update(equity_funding_shares=0, issue_price=0, cash_funding=75)
        r = compute(d)['results']; self.assertEqual(r['financial_bridge']['after']['shares'], 40)
        self.assertEqual(r['event_metrics']['new_shares_fraction_of_post_event_shares'], 0)
        d['event']['terms']['issue_price'] = 10
        self.assertTrue(call('validate_input', 'validate', d)[0])

    def test_acquisition_closing_cash_does_not_finance_upfront_cash_leg(self):
        d = fixture(); d['event']['terms'].update(cash_funding=90, debt_funding=15, acquired_cash=10)
        out = compute(d); r = out['results']; funding = r['funding_reconciliation']
        # 90 cash + 15 debt + 50 stock = 150 price + 5 fees. Acquired cash
        # arrives after the 90 cash-funded leg against only 80 opening cash.
        self.assertEqual(funding['sources'], 155); self.assertEqual(funding['uses'], 155)
        self.assertEqual(r['financial_bridge']['after']['cash'], 0)
        self.assertEqual(funding['ending_cash_shortfall'], 0)
        self.assertEqual(funding['upfront_cash_required'], 90)
        self.assertEqual(funding['upfront_cash_available_from_baseline'], 80)
        self.assertEqual(funding['upfront_cash_shortfall'], 10)
        self.assertEqual(funding['additional_cash_required'], 10)
        self.assertFalse(funding['cash_feasible_for_supplied_bridge'])
        self.assertEqual(out['status'], 'partial')
        self.assertTrue(any('upfront cash funding' in x for x in out['unresolved_issues']))
        self.assertFalse(call('validate_output', 'validate', out, d)[0])

    def test_refinancing_retained_cash_cannot_mask_prior_cash_requirement(self):
        d = event('refinancing', {'principal_repaid': 100, 'new_debt_proceeds': 120, 'fees': 5, 'cash_funding': 90, 'cash_retained': 105, 'old_annual_rate': .08, 'new_annual_rate': .06})
        out = compute(d); r = out['results']; funding = r['funding_reconciliation']
        # 120 new debt + 90 cash = 100 principal + 5 fees + 105 retained.
        # Closing cash 95 does not establish the earlier 90 cash leg.
        self.assertEqual(funding['sources'], 210); self.assertEqual(funding['uses'], 210)
        self.assertEqual(r['financial_bridge']['after']['cash'], 95)
        self.assertEqual(funding['ending_cash_shortfall'], 0)
        self.assertEqual(funding['upfront_cash_required'], 90)
        self.assertEqual(funding['upfront_cash_shortfall'], 10)
        self.assertEqual(funding['additional_cash_required'], 10)
        self.assertFalse(funding['cash_feasible_for_supplied_bridge'])
        self.assertEqual(out['status'], 'partial')
        self.assertTrue(any('upfront cash funding' in x for x in out['unresolved_issues']))

    def test_overlapping_upfront_and_closing_gaps_are_not_double_counted(self):
        d = event('share-repurchase', {'cash_spend': 100, 'repurchase_price': 20, 'fees': 2, 'cash_funding': 102, 'debt_funding': 0})
        f = compute(d)['results']['funding_reconciliation']
        self.assertEqual(f['upfront_cash_shortfall'], 22)
        self.assertEqual(f['ending_cash_shortfall'], 22)
        self.assertEqual(f['additional_cash_required'], 22)

    def test_funding_mismatches_and_unmodeled_terms_rejected(self):
        for kind, terms in [
            ('acquisition', dict(fixture()['event']['terms'], cash_funding=20)),
            ('share-repurchase', {'cash_spend': 60, 'repurchase_price': 20, 'fees': 2, 'cash_funding': 20, 'debt_funding': 40}),
            ('refinancing', {'principal_repaid': 100, 'new_debt_proceeds': 120, 'fees': 5, 'cash_funding': 0, 'cash_retained': 20, 'old_annual_rate': .08, 'new_annual_rate': .06}),
        ]:
            d = event(kind, terms)
            self.assertTrue(call('validate_input', 'validate', d)[0])
            with self.assertRaises(ValueError): compute(d)
        d = fixture(); d['event']['terms']['contingent_earnout'] = 5
        self.assertTrue(call('validate_input', 'validate', d)[0])

    def test_announced_proposed_completed_status_preserved(self):
        d = fixture(); self.assertEqual(compute(d)['results']['effect_basis'], 'conditional-on-supplied-terms')
        d['event'].update(status='proposed', announcement_date=None, scenario_label='analyst hypothetical')
        self.assertEqual(compute(d)['results']['event_summary']['status'], 'proposed')
        d['event'].update(status='completed', announcement_date='2026-10-01', effective_date='2026-10-18', scenario_label=None)
        r = compute(d)['results']; self.assertEqual(r['effect_basis'], 'supplied-completed-terms')
        self.assertFalse(r['legal_completion_verified']); self.assertFalse(r['market_reaction_predicted'])

    def test_status_inconsistency_and_double_counting_rejected(self):
        cases = []
        d = fixture(); d['event'].update(status='completed', scenario_label=None); cases.append(d)
        d = fixture(); d['event']['scenario_label'] = None; cases.append(d)
        d = fixture(); d['event']['status'] = 'proposed'; cases.append(d)
        d = fixture(); d['event']['announcement_date'] = '2026-10-20'; cases.append(d)
        d = fixture(); d['event']['effective_date'] = d['baseline']['balance_date']; cases.append(d)
        d = fixture(); d['event']['type'] = 'spin-off'; cases.append(d)
        for d in cases:
            with self.subTest(event=d['event']): self.assertTrue(call('validate_input', 'validate', d)[0])

    def test_elapsed_effective_date_does_not_auto_complete(self):
        d = fixture(); d['event']['effective_date'] = '2026-10-20'
        out = compute(d); self.assertEqual(out['results']['event_summary']['status'], 'announced')
        self.assertEqual(out['status'], 'partial'); self.assertTrue(any('elapsed' in issue for issue in out['unresolved_issues']))

    def test_basis_identity_and_missingness_rejected(self):
        cases = []
        for key, value in [('cash', None), ('debt', None), ('shares', None), ('cash', True), ('shares', 0)]:
            d = fixture(); d['baseline'][key] = value; cases.append(d)
        d = fixture(); d['financial_basis']['share_units'] = 'ones'; cases.append(d)
        d = fixture(); d['financial_basis']['currency'] = 'unknown'; cases.append(d)
        d = fixture(); d['financial_basis']['accounting_basis'] = ' unknown '; cases.append(d)
        d = fixture(); d['subject'] = {'type': 'security', 'id': 'OTHER-SECURITY', 'issuer_id': d['subject']['id']}; cases.append(d)
        d = fixture(); del d['event']['terms']['fees']; cases.append(d)
        for d in cases:
            self.assertTrue(call('validate_input', 'validate', d)[0])

    def test_economic_inventory_bounds(self):
        examples = [
            event('share-repurchase', {'cash_spend': 800, 'repurchase_price': 20, 'fees': 0, 'cash_funding': 800, 'debt_funding': 0}),
            event('refinancing', {'principal_repaid': 201, 'new_debt_proceeds': 201, 'fees': 0, 'cash_funding': 0, 'cash_retained': 0, 'old_annual_rate': .05, 'new_annual_rate': .05}),
            event('refinancing', {'principal_repaid': 100, 'new_debt_proceeds': 100, 'fees': 0, 'cash_funding': 0, 'cash_retained': 0, 'old_annual_rate': 8, 'new_annual_rate': 6}),
            event('equity-raise', {'shares_issued': 1, 'issue_price': 2, 'fees': 3}),
            event('asset-disposal', {'sale_cash_proceeds': 50, 'debt_transferred': 201, 'cash_disposed': 0, 'fees': 0, 'taxes': 0}),
            event('asset-disposal', {'sale_cash_proceeds': 50, 'debt_transferred': 0, 'cash_disposed': 81, 'fees': 0, 'taxes': 0}),
        ]
        for d in examples: self.assertTrue(call('validate_input', 'validate', d)[0])

    def test_known_times_citation_vintage_and_precision(self):
        for target, key, value in [
            ('event', 'known_at', '2026-10-21T16:00:00Z'),
            ('event', 'known_at', '2026-10-19'),
            ('baseline', 'known_at', '2026-10-18T16:00:00Z'),
            ('source', 'known_at', '2026-10-19T16:00:01Z'),
            ('source', 'known_at', '2026-10-19'),
            ('baseline', 'balance_date', '2026-10-20'),
        ]:
            d = fixture(); row = d['sources'][0] if target == 'source' else d[target]; row[key] = value
            self.assertTrue(call('validate_input', 'validate', d)[0])
        d = fixture(); d['knowledge_cutoff'] = '2026-10-20'
        for row in (d['sources'][0], d['baseline'], d['event']): row['known_at'] = '2026-10-19'
        self.assertEqual(compute(d)['status'], 'complete-for-supplied-scope')

    def test_source_rights_subjects_and_references_gate_projection(self):
        for key, value in [('permission_status', 'denied'), ('classification', 'restricted'), ('subject_ids', ['UNRELATED-ISSUER']), ('expires_on', '2026-10-19')]:
            d = fixture(); d['sources'][0][key] = value; out = compute(d)
            self.assertIsNone(out['results']); self.assertEqual(out['status'], 'partial')
            self.assertEqual(out['calculation_lineage'], []); self.assertEqual(out['source_register'], [])
        for row_name in ('event', 'baseline'):
            d = fixture(); d[row_name]['evidence_refs'] = []
            self.assertTrue(call('validate_input', 'validate', d)[0])
        d = fixture(); d['event']['evidence_refs'][0]['locator'] = 'undeclared citation'
        self.assertTrue(call('validate_input', 'validate', d)[0])

    def test_preserves_issues_and_never_grants_action(self):
        d = fixture(); d['unresolved_issues'] = ['Baseline independently unreconciled']
        out = compute(d)
        self.assertEqual(out['status'], 'partial'); self.assertIn(d['unresolved_issues'][0], out['unresolved_issues'])
        self.assertFalse(out['authority_granted']); self.assertFalse(out['action_taken'])
        self.assertEqual(out['approval'], 'not_requested'); self.assertEqual(out['execution'], 'not_performed')
        self.assertEqual(out['source_truth'], 'unverified'); self.assertNotIn('source_input', out)

    def test_full_original_binding_tamper_deletion_and_extra_fields(self):
        d = fixture(); out = compute(d)
        self.assertTrue(call('validate_output', 'validate', out, None)[0])
        changed = copy.deepcopy(d); changed['unrelated_metadata'] = 'changed original'
        self.assertTrue(call('validate_output', 'validate', out, changed)[0])
        for field in out:
            candidate = copy.deepcopy(out); del candidate[field]
            self.assertTrue(call('validate_output', 'validate', candidate, d)[0], field)
        for mutate in ('authority', 'number', 'extra', 'source'):
            candidate = copy.deepcopy(out)
            if mutate == 'authority': candidate['authority_granted'] = True
            elif mutate == 'number': candidate['results']['financial_bridge']['after']['cash'] += 1
            elif mutate == 'extra': candidate['unchecked_claim'] = 'approved'
            else: candidate['source_input'] = d
            self.assertTrue(call('validate_output', 'validate', candidate, d)[0])

    def test_actual_cli_source_binding_and_duplicate_nonfinite_rejection(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        with tempfile.TemporaryDirectory(prefix='ir-events-phase3-') as temp:
            source = PACKAGE / 'evals/files/input.json'; target = Path(temp) / 'output.json'
            proc = subprocess.run([sys.executable, '-B', 'scripts/calculate_or_transform.py', str(source)], cwd=PACKAGE, env=env, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr); json.loads(proc.stdout); target.write_text(proc.stdout)
            proc = subprocess.run([sys.executable, '-B', 'scripts/validate_output.py', str(target), '--input', str(source)], cwd=PACKAGE, env=env, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            for raw in ('{"request_id":"one","request_id":"two"}', '{"number":NaN}', '{"number":Infinity}'):
                bad = Path(temp) / 'bad.json'; bad.write_text(raw)
                for script in ('validate_input.py', 'calculate_or_transform.py', 'validate_output.py'):
                    args = [sys.executable, '-B', 'scripts/' + script, str(bad)]
                    if script == 'validate_output.py': args += ['--input', str(source)]
                    proc = subprocess.run(args, cwd=PACKAGE, env=env, capture_output=True, text=True)
                    self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                    self.assertIn('ERROR:', proc.stdout); self.assertNotIn('Traceback', proc.stdout + proc.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
