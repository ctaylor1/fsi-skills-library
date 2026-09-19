#!/usr/bin/env python3
"""Replay frozen Phase 3 cases; native reproducibility is not professional acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/insurance/phase3-validation'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='New directory; retained evidence is never overwritten')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output directory already exists; choose a new location')
    args.output.mkdir(parents=True)
    cases = json.loads((EVIDENCE / 'forward-cases.json').read_text())['cases']
    records, failures = [], []
    for case in cases:
        source = EVIDENCE / case['input']
        if not source.is_file() or digest(source) != case['input_sha256']:
            failures.append(f'{case["case_id"]}: retained input missing or hash differs')
            continue
        package = ROOT / 'skills/insurance' / case['skill']
        target = args.output / case['case_id']
        target.mkdir()
        output = target / 'output.json'
        commands = []
        for script, input_path, result_name in (
            ('validate_input.py', source, 'input-validation.json'),
            ('calculate_or_transform.py', source, 'output.json'),
            ('validate_output.py', output, 'output-validation.json'),
        ):
            command = [sys.executable, '-B', str(package / 'scripts' / script), str(input_path.resolve())]
            run = subprocess.run(command, cwd=package, text=True, capture_output=True)
            (target / result_name).write_text(run.stdout)
            (target / (result_name + '.stderr')).write_text(run.stderr)
            expected_exit = case.get('expected_exits', {}).get(script, 0)
            commands.append({'command': command, 'exit': run.returncode, 'expected_exit': expected_exit,
                             'stdout': result_name, 'stderr': result_name + '.stderr'})
            if run.returncode != expected_exit:
                failures.append(f'{case["case_id"]}: {script} exited {run.returncode}, expected {expected_exit}')
        matches_reviewed = None
        try:
            data = json.loads(output.read_text())
            rejected_input = case.get('expected_exits', {}).get('calculate_or_transform.py', 0) != 0
            if rejected_input:
                if 'artifact' in data:
                    failures.append(f'{case["case_id"]}: rejected input produced a native artifact')
            elif (data.get('action_taken') is not False or data.get('execution') != 'not_performed'
                  or data.get('approval') != 'not_requested'):
                failures.append(f'{case["case_id"]}: action boundary differs')
            if case.get('reviewed_output'):
                reviewed = EVIDENCE / case['reviewed_output']
                if digest(reviewed) != case['reviewed_output_sha256']:
                    failures.append(f'{case["case_id"]}: reviewed output hash differs')
                matches_reviewed = data == json.loads(reviewed.read_text())
                if not matches_reviewed:
                    failures.append(f'{case["case_id"]}: result differs from independently reviewed output')
        except (ValueError, OSError):
            failures.append(f'{case["case_id"]}: output or reviewed result unavailable')
        hashes = {str(p.relative_to(ROOT)): digest(p) for p in sorted(package.rglob('*'))
                  if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
        record = {**case, 'input_unchanged': digest(source) == case['input_sha256'],
                  'commands': commands, 'output_sha256': digest(output),
                  'matches_reviewed_output': matches_reviewed, 'package_hashes': hashes}
        (target / 'execution.json').write_text(json.dumps(record, indent=2) + '\n')
        records.append(record)
    summary = {'cases': len(cases), 'commands': sum(len(r['commands']) for r in records),
               'failures': failures,
               'input_hashes_unchanged': len(records) == len(cases) and all(r['input_unchanged'] for r in records),
               'reviewed_outputs_equal': sum(r['matches_reviewed_output'] is True for r in records),
               'note': 'Reproducibility and no-action checks; separate synthetic practitioner reviews are not a model benchmark, source authentication or professional acceptance.',
               'records': records}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'records'}, indent=2))
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
