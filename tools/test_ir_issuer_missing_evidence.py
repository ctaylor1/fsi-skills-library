#!/usr/bin/env python3
"""Missing issuer evidence must be partial, calculable and original-bound."""
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
FIELDS = ('ebitda', 'gross_debt', 'unrestricted_cash', 'interest_expense',
          'operating_cash_flow', 'capex', 'funds_from_operations')


def fixture():
    return json.loads((PACKAGE / 'evals/files/input.json').read_text())


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


def missing(row, key, omit):
    if omit:
        row.pop(key)
    else:
        row[key] = None


def run_cli(script, *args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH', None)
    return subprocess.run([sys.executable, '-B', 'scripts/' + script + '.py', *map(str, args)],
                          cwd=PACKAGE, capture_output=True, text=True, env=env)


class IssuerMissingEvidence(unittest.TestCase):
    def result(self, doc):
        original = copy.deepcopy(doc)
        self.assertEqual(call('validate_input', 'validate', doc)[0], [])
        out = call('domain', 'compute', doc)
        self.assertEqual(call('validate_output', 'validate', out, original)[0], [])
        self.assertEqual(doc, original, 'calculation must not fill in original evidence')
        return out

    def partial(self, doc, fragment):
        out = self.result(doc)
        self.assertEqual(out['status'], 'partial')
        self.assertTrue(any(fragment in issue for issue in out['unresolved_issues']), out['unresolved_issues'])
        return out

    def test_each_nullable_financial_amount_has_equivalent_omitted_and_null_results(self):
        for key in FIELDS:
            with self.subTest(field=key):
                outputs = []
                for omit in (False, True):
                    doc = fixture()
                    missing(doc['financials'], key, omit)
                    outputs.append(self.partial(doc, 'financials.' + key + ': missing evidence'))
                self.assertNotEqual(outputs[0]['input_hash'], outputs[1]['input_hash'])
                outputs[0].pop('input_hash')
                outputs[1].pop('input_hash')
                self.assertEqual(outputs[0], outputs[1])

    def test_missing_cash_flow_inputs_withhold_only_affected_measures(self):
        for key in ('operating_cash_flow', 'capex', 'funds_from_operations'):
            with self.subTest(field=key):
                doc = fixture()
                doc['financials'][key] = None
                result = self.partial(doc, key)['results']
                self.assertEqual(result['credit_metrics']['reported_ebitda'], {
                    'ebitda': 100, 'gross_leverage_x': 4, 'net_leverage_x': 3.5, 'interest_coverage_x': 5})
                self.assertAlmostEqual(result['credit_metrics']['analyst_adjusted_ebitda']['gross_leverage_x'], 40 / 11)
                if key == 'funds_from_operations':
                    self.assertEqual(result['cash_flow']['free_cash_flow'], 50)
                    self.assertIsNone(result['cash_flow']['ffo_to_debt'])
                else:
                    self.assertIsNone(result['cash_flow']['free_cash_flow'])
                    self.assertAlmostEqual(result['cash_flow']['ffo_to_debt'], 7 / 40)

    def test_all_nullable_financial_amounts_can_be_unknown(self):
        for omit in (False, True):
            doc = fixture()
            for key in FIELDS:
                missing(doc['financials'], key, omit)
            out = self.partial(doc, 'missing evidence')
            for key in FIELDS:
                self.assertTrue(any('financials.' + key + ':' in issue for issue in out['unresolved_issues']))
            for metrics in out['results']['credit_metrics'].values():
                self.assertTrue(all(value is None for value in metrics.values()))
            self.assertEqual(out['results']['cash_flow'], {'free_cash_flow': None, 'ffo_to_debt': None})

    def test_missing_ebitda_retains_independent_cash_flow(self):
        doc = fixture()
        doc['financials'].pop('ebitda')
        result = self.partial(doc, 'financials.ebitda')['results']
        self.assertEqual(result['cash_flow'], {'free_cash_flow': 50, 'ffo_to_debt': 0.175})
        self.assertTrue(all(value is None for row in result['credit_metrics'].values() for value in row.values()))

    def test_missing_cash_and_interest_retain_supported_credit_metrics(self):
        for key, unavailable, retained, expected in (
                ('unrestricted_cash', 'net_leverage_x', 'interest_coverage_x', 5),
                ('interest_expense', 'interest_coverage_x', 'net_leverage_x', 3.5)):
            doc = fixture()
            doc['financials'].pop(key)
            result = self.partial(doc, 'financials.' + key)['results']
            reported = result['credit_metrics']['reported_ebitda']
            self.assertEqual(reported['gross_leverage_x'], 4)
            self.assertIsNone(reported[unavailable])
            self.assertEqual(reported[retained], expected)
            self.assertEqual(result['cash_flow']['free_cash_flow'], 50)

    def test_zero_cash_flow_amounts_are_known_and_complete(self):
        doc = fixture()
        for key in ('operating_cash_flow', 'capex', 'funds_from_operations'):
            doc['financials'][key] = 0
        out = self.result(doc)
        self.assertEqual(out['status'], 'complete-for-supplied-scope')
        self.assertEqual(out['unresolved_issues'], [])
        self.assertEqual(out['results']['cash_flow'], {'free_cash_flow': 0, 'ffo_to_debt': 0})

    def test_zero_capex_and_cash_are_valid(self):
        doc = fixture()
        doc['financials'].update(capex=0, unrestricted_cash=0)
        out = self.result(doc)
        self.assertEqual(out['status'], 'complete-for-supplied-scope')
        self.assertEqual(out['results']['cash_flow']['free_cash_flow'], 80)
        self.assertEqual(out['results']['credit_metrics']['reported_ebitda']['net_leverage_x'], 4)

    def test_zero_ebitda_withholds_leverage_and_keeps_supported_adjusted_metrics(self):
        doc = fixture()
        doc['financials']['ebitda'] = 0
        out = self.partial(doc, 'reported_ebitda')
        reported = out['results']['credit_metrics']['reported_ebitda']
        self.assertEqual(reported['ebitda'], 0)
        self.assertIsNone(reported['gross_leverage_x'])
        self.assertIsNone(reported['net_leverage_x'])
        self.assertEqual(reported['interest_coverage_x'], 0)
        self.assertEqual(out['results']['credit_metrics']['analyst_adjusted_ebitda']['gross_leverage_x'], 40)
        self.assertFalse(any('missing evidence' in issue for issue in out['unresolved_issues']))

    def test_zero_interest_withholds_coverage_without_discarding_leverage(self):
        doc = fixture()
        doc['financials']['interest_expense'] = 0
        out = self.partial(doc, 'reported_ebitda')
        self.assertIsNone(out['results']['credit_metrics']['reported_ebitda']['interest_coverage_x'])
        self.assertEqual(out['results']['credit_metrics']['reported_ebitda']['gross_leverage_x'], 4)
        self.assertEqual(out['results']['cash_flow']['free_cash_flow'], 50)
        self.assertFalse(any('missing evidence' in issue for issue in out['unresolved_issues']))

    def test_reconciled_zero_debt_is_known_but_cannot_be_an_ffo_denominator(self):
        doc = fixture()
        doc['financials'].update(gross_debt=0, unrestricted_cash=0, funds_from_operations=0)
        doc['instruments'][0]['principal'] = 0
        out = self.partial(doc, 'cash_flow.ffo_to_debt')
        result = out['results']
        self.assertEqual(result['evidence_reconciliation']['debt_inventory']['status'], 'reconciled')
        self.assertEqual(result['credit_metrics']['reported_ebitda']['gross_leverage_x'], 0)
        self.assertEqual(result['credit_metrics']['reported_ebitda']['net_leverage_x'], 0)
        self.assertIsNone(result['cash_flow']['ffo_to_debt'])
        self.assertFalse(any('missing evidence' in issue for issue in out['unresolved_issues']))

    def test_supported_signed_cash_flows_remain_usable(self):
        doc = fixture()
        doc['financials'].update(operating_cash_flow=-12, capex=3, funds_from_operations=-8)
        out = self.result(doc)
        self.assertEqual(out['status'], 'complete-for-supplied-scope')
        self.assertEqual(out['results']['cash_flow'], {'free_cash_flow': -15, 'ffo_to_debt': -0.02})

    def test_negative_ebitda_retains_signed_coverage_and_withholds_leverage(self):
        doc = fixture()
        doc['financials']['ebitda'] = -20
        out = self.partial(doc, 'reported_ebitda')
        for name, coverage in [('reported_ebitda', -1), ('analyst_adjusted_ebitda', -0.5)]:
            metrics = out['results']['credit_metrics'][name]
            self.assertIsNone(metrics['gross_leverage_x'])
            self.assertIsNone(metrics['net_leverage_x'])
            self.assertEqual(metrics['interest_coverage_x'], coverage)

    def test_omitted_and_null_debt_reconciliation_are_equivalent_partial_results(self):
        outputs = []
        for omit in (False, True):
            doc = fixture()
            missing(doc, 'debt_reconciliation', omit)
            out = self.partial(doc, 'debt inventory lacks source-bound coverage')
            self.assertEqual(out['calculation_lineage'][0]['bridge_ids'], [])
            result = out['results']
            self.assertIsNone(result['cash_flow']['ffo_to_debt'])
            self.assertEqual(result['cash_flow']['free_cash_flow'], 50)
            self.assertEqual(result['credit_metrics']['reported_ebitda']['interest_coverage_x'], 5)
            for row in result['credit_metrics'].values():
                self.assertIsNone(row['gross_leverage_x'])
                self.assertIsNone(row['net_leverage_x'])
            outputs.append(out)
        self.assertNotEqual(outputs[0].pop('input_hash'), outputs[1].pop('input_hash'))
        self.assertEqual(outputs[0], outputs[1])

    def test_omitted_and_null_instrument_inclusion_withhold_debt_dependent_measures(self):
        for omit in (False, True):
            doc = fixture()
            missing(doc['instruments'][0], 'debt_inclusion', omit)
            result = self.partial(doc, 'explicit debt inclusion/exclusion is missing')['results']
            self.assertIsNone(result['credit_metrics']['reported_ebitda']['gross_leverage_x'])
            self.assertIsNone(result['cash_flow']['ffo_to_debt'])
            self.assertEqual(result['cash_flow']['free_cash_flow'], 50)
            self.assertEqual(result['credit_metrics']['reported_ebitda']['interest_coverage_x'], 5)

    def test_omitted_and_null_included_principal_are_unavailable_not_zero(self):
        for omit in (False, True):
            doc = fixture()
            missing(doc['instruments'][0], 'principal', omit)
            result = self.partial(doc, 'included principal is missing')['results']
            self.assertIsNone(result['credit_metrics']['reported_ebitda']['gross_leverage_x'])
            self.assertIsNone(result['cash_flow']['ffo_to_debt'])
            self.assertEqual(result['cash_flow']['free_cash_flow'], 50)

    def test_unknown_excluded_principal_does_not_invalidate_supported_inventory(self):
        for omit in (False, True):
            doc = fixture()
            instrument = copy.deepcopy(doc['instruments'][0])
            instrument.update(instrument_id='SUB-1', issuer_id='SUB-ISSUER', estate_id='SUB-ESTATE')
            instrument['debt_inclusion'].update(treatment='excluded', reason='Separate unconsolidated structural obligation')
            missing(instrument, 'principal', omit)
            doc['instruments'].append(instrument)
            out = self.result(doc)
            self.assertEqual(out['status'], 'complete-for-supplied-scope')
            self.assertEqual(out['results']['credit_metrics']['reported_ebitda']['gross_leverage_x'], 4)
            self.assertEqual(out['results']['evidence_reconciliation']['debt_inventory']['excluded_instrument_ids'], ['SUB-1'])
            self.assertEqual(out['results']['structural_risks'][0]['instrument_id'], 'SUB-1')

    def test_malformed_amounts_and_object_evidence_still_reject_at_intake(self):
        for field in FIELDS:
            for value in (False, '', [], {}):
                doc = fixture()
                doc['financials'][field] = value
                self.assertTrue(call('validate_input', 'validate', doc)[0])
        for field in ('debt_reconciliation', 'debt_inclusion'):
            for value in (False, '', [], 0):
                doc = fixture()
                target = doc if field == 'debt_reconciliation' else doc['instruments'][0]
                target[field] = value
                self.assertTrue(call('validate_input', 'validate', doc)[0])

    def test_output_cannot_hide_missingness_or_invent_zero(self):
        doc = fixture()
        doc['financials'].pop('operating_cash_flow')
        valid = self.result(doc)
        for change in ('complete', 'clear-issues', 'zero-result'):
            out = copy.deepcopy(valid)
            if change == 'complete':
                out['status'] = 'complete-for-supplied-scope'
            elif change == 'clear-issues':
                out['unresolved_issues'] = []
            else:
                out['results']['cash_flow']['free_cash_flow'] = 0
            self.assertTrue(call('validate_output', 'validate', out, doc)[0])

    def test_original_binding_distinguishes_omitted_from_explicit_null(self):
        doc = fixture()
        doc['financials'].pop('funds_from_operations')
        out = self.result(doc)
        changed = copy.deepcopy(doc)
        changed['financials']['funds_from_operations'] = None
        self.assertTrue(any('input_hash' in issue for issue in call('validate_output', 'validate', out, changed)[0]))

    def test_public_commands_accept_all_missing_variants_and_reject_output_mutations(self):
        cases = []
        for key in FIELDS:
            for omit in (False, True):
                doc = fixture()
                missing(doc['financials'], key, omit)
                cases.append(doc)
        for key in ('debt_reconciliation', 'debt_inclusion'):
            for omit in (False, True):
                doc = fixture()
                target = doc if key == 'debt_reconciliation' else doc['instruments'][0]
                missing(target, key, omit)
                cases.append(doc)
        with tempfile.TemporaryDirectory(prefix='ir-issuer-missing-') as temp:
            for index, doc in enumerate(cases):
                with self.subTest(case=index):
                    source = Path(temp) / (str(index) + '-input.json')
                    source.write_text(json.dumps(doc))
                    output = Path(temp) / (str(index) + '-output.json')
                    checked = run_cli('validate_input', source)
                    self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
                    computed = run_cli('calculate_or_transform', source)
                    self.assertEqual(computed.returncode, 0, computed.stdout + computed.stderr)
                    result = json.loads(computed.stdout)
                    self.assertEqual(result['status'], 'partial')
                    output.write_text(computed.stdout)
                    checked = run_cli('validate_output', output, '--input', source)
                    self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
                    result['status'] = 'complete-for-supplied-scope'
                    output.write_text(json.dumps(result))
                    tampered = run_cli('validate_output', output, '--input', source)
                    self.assertEqual(tampered.returncode, 1)
                    self.assertNotIn('Traceback', tampered.stderr)


if __name__ == '__main__':
    unittest.main()
