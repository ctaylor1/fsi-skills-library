#!/usr/bin/env python3
"""Replay identical review cases against frozen prior or current public commands."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ISSUER = 'issuer-credit-researcher'
SURVEILLANCE = 'issuer-credit-surveillance-reviewer'


def encoded(value):
    return json.dumps(value, indent=2, allow_nan=False) + '\n'


def cases():
    base = HERE / 'pre-edit/skills/investment-research'
    issuer = json.loads((base / ISSUER / 'evals/files/input.json').read_text())
    old = json.loads((base / SURVEILLANCE / 'evals/files/surveillance_request_example.json').read_text())
    current = json.loads((base / SURVEILLANCE / 'evals/files/phase2_input.json').read_text())
    output = []
    def add(name, package, doc, behavior):
        output.append((name, package, doc, behavior))
    add('issuer-supported', ISSUER, issuer, 'complete')
    add('surveillance-supported', SURVEILLANCE, current, 'complete')
    add('legacy-undated-quotes', SURVEILLANCE, old, 'legacy')
    doc = copy.deepcopy(old)
    doc['financials']['period'] = 'LTM-2030-06-30'
    doc['prior_financials']['period'] = 'LTM-2029-06-30'
    add('legacy-future-reported-periods', SURVEILLANCE, doc, 'legacy')
    doc = copy.deepcopy(old)
    doc['spreads']['instrument_id'] = 'OTHER-ISSUER-BOND'
    add('legacy-unmapped-security', SURVEILLANCE, doc, 'legacy')
    doc = copy.deepcopy(old)
    for source in doc['sources']:
        if source['source_id'] == doc['spreads']['source_id']:
            source['known_at'] = '2020-01-02T12:00:00Z'
    doc['spreads'].update(prior_observed_at='2019-01-01T12:00:00Z', current_observed_at='2020-01-01T12:00:00Z')
    doc['spread_freshness_policy'] = {'max_current_age_hours': 24}
    add('legacy-stale-quotes', SURVEILLANCE, doc, 'legacy')
    for field in ('operating_cash_flow', 'capex', 'funds_from_operations'):
        for mode in ('null', 'omitted'):
            doc = copy.deepcopy(issuer)
            if mode == 'null':
                doc['financials'][field] = None
            else:
                del doc['financials'][field]
            add('issuer-' + field + '-' + mode, ISSUER, doc, mode)
    doc = copy.deepcopy(issuer)
    doc['debt_reconciliation'] = None
    add('issuer-null-debt-reconciliation', ISSUER, doc, 'omitted')
    doc = copy.deepcopy(issuer)
    for field in ('operating_cash_flow', 'capex', 'funds_from_operations'):
        doc['financials'][field] = 0
    add('issuer-genuine-zero', ISSUER, doc, 'zero')
    return output


def run(stage, destination):
    library = HERE / 'pre-edit' if stage == 'before' else ROOT
    records = []
    for name, package, doc, behavior in cases():
        folder = destination / name
        folder.mkdir(parents=True, exist_ok=True)
        original = folder / 'original.json'
        original.write_text(encoded(doc))
        original_digest = hashlib.sha256(original.read_bytes()).hexdigest()
        before = HERE / 'before-repair' / name
        if stage == 'after':
            assert original.read_bytes() == (before / 'original.json').read_bytes(), name
        scripts = library / 'skills/investment-research' / package / 'scripts'
        commands = []
        def command(script, *args):
            cmd = [sys.executable, '-B', str(scripts / (script + '.py')), *map(str, args)]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                                  env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            (folder / (script + '.stdout')).write_text(proc.stdout)
            (folder / (script + '.stderr')).write_text(proc.stderr)
            assert 'Traceback (most recent call last)' not in proc.stdout + proc.stderr, name
            commands.append({'command': cmd, 'exit': proc.returncode})
            return proc
        intake = command('validate_input', original)
        calculation = command('calculate_or_transform', original)
        output = None
        if calculation.returncode == 0:
            output = json.loads(calculation.stdout)
            result_path = folder / 'output.json'
            result_path.write_text(calculation.stdout)
            validation = command('validate_output', result_path, '--input', original)
            assert validation.returncode == 0, name
        elif stage == 'after' and behavior == 'legacy':
            validation = command('validate_output', before / 'output.json', '--input', original)
            assert validation.returncode == 1, name
        if stage == 'before':
            assert intake.returncode == 0, name
            assert calculation.returncode == (1 if behavior == 'omitted' else 0), name
            if behavior == 'legacy':
                assert output['support_status'] == 'SUPPLIED_INPUT_REVIEW' and not output['unresolved'], name
                assert output['changes']['spread_delta_bps'] == 60, name
            elif output:
                assert output['status'] == 'complete-for-supplied-scope' and not output['unresolved_issues'], name
        elif behavior == 'legacy':
            assert intake.returncode == calculation.returncode == 1, name
            assert 'migration' in (intake.stdout + intake.stderr + calculation.stdout + calculation.stderr).lower(), name
        else:
            assert intake.returncode == calculation.returncode == 0, name
            expected = 'complete-for-supplied-scope' if behavior in ('complete', 'zero') else 'partial'
            assert output['status'] == expected, name
            if expected == 'partial':
                assert output['unresolved_issues'], name
            if package == ISSUER:
                cash = output['results']['cash_flow']
                if 'operating_cash_flow-' in name or 'capex-' in name:
                    assert cash['free_cash_flow'] is None and cash['ffo_to_debt'] == 0.175, name
                if 'funds_from_operations-' in name:
                    assert cash['free_cash_flow'] == 50 and cash['ffo_to_debt'] is None, name
                if behavior == 'zero':
                    assert cash == {'free_cash_flow': 0, 'ffo_to_debt': 0}, name
                if name == 'issuer-null-debt-reconciliation':
                    assert cash['free_cash_flow'] == 50 and cash['ffo_to_debt'] is None, name
                    for metrics in output['results']['credit_metrics'].values():
                        assert metrics['gross_leverage_x'] is None and metrics['net_leverage_x'] is None, name
        assert hashlib.sha256(original.read_bytes()).hexdigest() == original_digest
        records.append({'case': name, 'behavior': behavior, 'package': package,
                        'original_sha256': original_digest, 'commands': commands, 'passed': True})
    report = {'stage': stage, 'cases': len(records), 'passed': True, 'records': records}
    (destination / 'report.json').write_text(encoded(report))
    print(json.dumps({'stage': stage, 'cases': len(records), 'passed': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('before', 'after'), required=True)
    args = parser.parse_args()
    run(args.stage, HERE / (args.stage + '-repair'))
