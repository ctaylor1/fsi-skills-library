#!/usr/bin/env python3
"""Replay the retained Phase 2 synthetic inputs; not an independent model benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/insurance/phase2-validation'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New directory for replay evidence; originals are never replaced')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output directory already exists; choose a new replay location')
    args.output.mkdir(parents=True)
    cases = json.loads((EVIDENCE / 'forward-cases.json').read_text())['cases']
    records, failures = [], []
    for case in cases:
        source = EVIDENCE / case['input']
        if digest(source) != case['input_sha256']:
            failures.append(f'{case["case_id"]}: retained input hash differs')
            continue
        package = ROOT / 'skills/insurance' / case['skill']
        target = args.output / case['case_id']
        target.mkdir()
        logs = []
        output = target / 'output.json'
        for script, input_path, result_name in (
            ('validate_input.py', source, 'input-validation.json'),
            ('calculate_or_transform.py', source, 'output.json'),
            ('validate_output.py', output, 'output-validation.json'),
        ):
            command = [sys.executable, '-B', str(package / 'scripts' / script), str(input_path.resolve())]
            run = subprocess.run(command, cwd=package, text=True, capture_output=True)
            (target / result_name).write_text(run.stdout)
            (target / (result_name + '.stderr')).write_text(run.stderr)
            logs.append({'command': command, 'exit': run.returncode, 'stdout': result_name, 'stderr': result_name + '.stderr'})
            if run.returncode:
                failures.append(f'{case["case_id"]}: {script} exited {run.returncode}')
        try:
            data = json.loads(output.read_text())
            if data.get('action_taken') is not False or data.get('execution') != 'not_performed' or data.get('approval') != 'not_requested':
                failures.append(f'{case["case_id"]}: action boundary differs')
        except (ValueError, OSError):
            failures.append(f'{case["case_id"]}: output unavailable')
        hashes = {str(p.relative_to(ROOT)): digest(p) for p in sorted(package.rglob('*'))
                  if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
        record = {**case, 'input_unchanged': digest(source) == case['input_sha256'], 'commands': logs,
                  'output_sha256': digest(output), 'package_hashes': hashes}
        (target / 'execution.json').write_text(json.dumps(record, indent=2) + '\n')
        records.append(record)
    summary = {'cases': len(cases), 'commands': sum(len(r['commands']) for r in records),
               'failures': failures, 'input_hashes_unchanged': all(r['input_unchanged'] for r in records),
               'note': 'Native reproducibility and no-action checks only. Independent domain expectations and practitioner narratives are separate retained evidence.',
               'records': records}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'records'}, indent=2))
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
