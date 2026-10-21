#!/usr/bin/env python3
"""Replay frozen Phase 4 diagnostic inputs without rewriting historical evidence."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/insurance/phase4-validation'


def replay(destination):
    packages = json.loads((ROOT / 'catalog/insurance-phase4-capabilities.json').read_text())['all_native_packages']
    cases = json.loads((EVIDENCE / 'replay-cases.json').read_text())['cases']
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ValueError('Replay destination must be empty; historical outputs are never overwritten')
    results = []
    for index, case in enumerate(cases):
        folder = destination / f'{index+1:02d}'
        folder.mkdir()
        source = EVIDENCE / case['input']
        target = folder / 'input.json'
        shutil.copy2(source, target)
        output = folder / 'output.json'
        calls = []
        for script, data in [('validate_input', target), ('calculate_or_transform', target), ('validate_output', output)]:
            cmd = [sys.executable, '-B', str(ROOT / packages[case['skill']] / 'scripts' / (script+'.py')), str(data)]
            proc = subprocess.run(cmd, text=True, capture_output=True, timeout=30)
            (folder / (script+'.stdout.txt')).write_text(proc.stdout)
            (folder / (script+'.stderr.txt')).write_text(proc.stderr)
            calls.append({'command':cmd,'exit_code':proc.returncode})
            if script == 'calculate_or_transform':
                output.write_text(proc.stdout)
        try:
            exact = json.loads(output.read_text()) == json.loads((EVIDENCE / case['expected']).read_text())
        except (ValueError, OSError):
            exact = False
        result = {'case':case['case'],'calls':calls,'source_bytes_unchanged':source.read_bytes()==target.read_bytes(),
                  'matches_reviewed_output':exact,'passed':exact and all(c['exit_code']==0 for c in calls)}
        results.append(result)
        print(('PASS ' if result['passed'] else 'FAIL ') + case['case'])
    report = {'cases':results,'passed':sum(c['passed'] for c in results),'failed':sum(not c['passed'] for c in results),
              'native_commands':sum(len(c['calls']) for c in results),
              'limitation':'Output identity and validator success do not establish source truth or professional acceptance.'}
    (destination / 'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"Phase 4 replay: {report['passed']}/{len(results)} cases; {report['native_commands']} native commands")
    return bool(report['failed'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New empty evidence directory; defaults to a temporary directory')
    args = parser.parse_args()
    if args.output:
        return replay(args.output.resolve())
    with tempfile.TemporaryDirectory(prefix='insurance-phase4-replay-') as temp:
        return replay(Path(temp))


if __name__ == '__main__':
    raise SystemExit(main())
