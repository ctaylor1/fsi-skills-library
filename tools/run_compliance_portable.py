#!/usr/bin/env python3
"""Run installed CFC executable checks from isolated single-package installations."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def check_package(relative):
    results = []
    with tempfile.TemporaryDirectory(prefix='fsi-cfc-portable-') as directory:
        package = Path(directory) / Path(relative).name
        shutil.copytree(ROOT / relative, package, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        cases = json.loads((package / 'evals/evals.json').read_text())['evals']
        checks = [dict(case) for case in cases if case.get('command') and 'expect_exit' in case]
        for suite in sorted((package / 'scripts').glob('test_phase*.py')):
            relative_suite = suite.relative_to(package).as_posix()
            if not any(relative_suite in str(case.get('command', case.get('argv', ''))) for case in checks):
                checks.append({'id': 'focused-' + suite.stem, 'argv': [sys.executable, '-B', relative_suite], 'expect_exit': 0})
        for case in checks:
            try:
                command = case.get('argv') or case['command']
                run = subprocess.run(command, shell=not isinstance(command, list), cwd=package,
                                     env=env, capture_output=True, text=True, timeout=60)
                output = run.stdout + run.stderr
                passed = run.returncode == case['expect_exit'] and all(t in output for t in case.get('expect_contains', []))
                result = {'id': case['id'], 'passed': passed, 'exit': run.returncode,
                          'expected_exit': case['expect_exit'], 'output': output[-16000:]}
            except subprocess.TimeoutExpired:
                result = {'id': case['id'], 'passed': False, 'error': 'command timeout'}
            results.append(result)
    return {'package': relative, 'checks': results, 'passed': bool(results) and all(r['passed'] for r in results)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    caps = json.loads((ROOT / 'catalog/compliance-financial-crime-capabilities.json').read_text())['capabilities']
    paths = sorted(c['path'] for c in caps if c['support_status'] != 'planned')
    phase2 = json.loads((ROOT / 'catalog/compliance-financial-crime-phase2-capabilities.json').read_text())
    retained = phase2['promotion_migration']['retained_owner']
    retained_paths = list((ROOT / 'skills').glob('*/' + retained + '/SKILL.md'))
    if len(retained_paths) != 1:
        raise ValueError('retained promotion specialist must be an actual installed package')
    paths = sorted(set(paths) | {str(retained_paths[0].parent.relative_to(ROOT))})
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check_package, paths))
    report = {'scope': 'Isolated offline software checks; source, legal and institutional acceptance unestablished',
              'packages': len(results), 'checks': sum(len(r['checks']) for r in results),
              'passed': all(r['passed'] for r in results), 'results': results}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    for result in results:
        if not result['passed']:
            print(json.dumps(result, indent=2))
    print(f"Portable compliance packages: {report['packages']} packages, {report['checks']} command checks, " + ('PASS' if report['passed'] else 'FAIL'))
    return int(not report['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
