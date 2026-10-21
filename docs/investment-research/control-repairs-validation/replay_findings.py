"""Replay the reported failures through public commands; write fresh evidence only."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEST = Path(__file__).resolve().parent / 'after-repair'
ENV = {key: value for key, value in os.environ.items() if key not in ('PYTHONPATH', 'PYTHONHOME')}
ENV['PYTHONDONTWRITEBYTECODE'] = '1'


def fixture(skill, name='input.json'):
    return json.loads((ROOT / 'skills/investment-research' / skill / 'evals/files' / name).read_text())


def run(skill, label, doc, expected_exit):
    folder = DEST / label
    folder.mkdir(parents=True, exist_ok=True)
    original = folder / 'input.json'
    original.write_text(json.dumps(doc, indent=2) + '\n')
    package = ROOT / 'skills/investment-research' / skill
    commands = []
    for script in ('validate_input.py', 'calculate_or_transform.py'):
        command = [sys.executable, '-B', 'scripts/' + script, str(original)]
        result = subprocess.run(command, cwd=package, env=ENV, capture_output=True, text=True)
        (folder / (script + '.stdout')).write_text(result.stdout)
        (folder / (script + '.stderr')).write_text(result.stderr)
        assert result.returncode == expected_exit, (label, script, result.stdout, result.stderr)
        assert 'Traceback' not in result.stdout + result.stderr
        commands.append({'command': command, 'exit': result.returncode})
    summary = {'skill': skill, 'case': label, 'commands': commands, 'expected_exit': expected_exit}
    if expected_exit == 0:
        output = json.loads(result.stdout)
        saved = folder / 'output.json'
        saved.write_text(result.stdout)
        command = [sys.executable, '-B', 'scripts/validate_output.py', str(saved), '--input', str(original)]
        checked = subprocess.run(command, cwd=package, env=ENV, capture_output=True, text=True)
        (folder / 'validate_output.py.stdout').write_text(checked.stdout)
        (folder / 'validate_output.py.stderr').write_text(checked.stderr)
        assert checked.returncode == 0, checked.stdout + checked.stderr
        commands.append({'command': command, 'exit': checked.returncode})
        summary['status'] = output['status'] if 'status' in output else output['routes'][0]['status']
        if skill == 'issuer-credit-surveillance-reviewer':
            assert output['results']['spread_change_bps'] is None
            assert 'spread widened beyond supplied threshold' not in output['results']['alerts']
            assert output['status'] == 'partial' and output['unresolved_issues']
            summary['spread_change_bps'] = None
            summary['alerts'] = output['results']['alerts']
            summary['unresolved_issues'] = output['unresolved_issues']
        else:
            status = output['routes'][0]['status']
            assert status == ('unsupported-method-profile' if label == 'corporate-profile-gap' else 'routed-native-only'), output
            summary['route_status'] = status
    return summary


if __name__ == '__main__':
    reports = []
    skill = 'issuer-credit-researcher'
    future = fixture(skill)
    future['financials']['period'].update(start='2027-01-01', end='2027-09-30')
    reports.append(run(skill, 'future-issuer-period', future, 1))
    duplicate = fixture(skill)
    duplicate['ebitda_adjustments'].append(copy.deepcopy(duplicate['ebitda_adjustments'][0]))
    reports.append(run(skill, 'duplicate-adjustment', duplicate, 1))
    skill = 'issuer-credit-surveillance-reviewer'
    future = fixture(skill, 'phase2_input.json')
    future['prior']['period'].update(start='2027-01-01', end='2027-09-30')
    future['current']['period'].update(start='2028-01-01', end='2028-09-30')
    reports.append(run(skill, 'future-surveillance-periods', future, 1))
    for label, name in (('undated-spreads', 'phase2_undated_spread_input.json'),
                        ('stale-spreads', 'phase2_stale_spread_input.json')):
        reports.append(run(skill, label, fixture(skill, name), 0))
    skill = 'investment-research-router'
    for label, name in (('quality-economy', 'quality-economy-route.json'),
                        ('corporate-profile-gap', 'corporate-profile-gap-route.json')):
        reports.append(run(skill, label, fixture(skill, name), 0))
    target = DEST / 'report.json'
    target.write_text(json.dumps({'passed': True, 'cases': reports}, indent=2) + '\n')
    assert json.loads(target.read_text())['passed']
    print(json.dumps({'cases': len(reports), 'passed': True, 'report': str(target)}))
