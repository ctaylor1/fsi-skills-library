#!/usr/bin/env python3
"""Record a fresh repair validation run; never write older checkpoint evidence."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def run(suite):
    commands = [('whole-library-tests', ['-m', 'unittest', 'discover', '-s', 'tools', '-p', 'test_*.py'])]
    if suite == 'focused':
        commands = [
            ('focused-tests', ['-m', 'unittest', 'discover', '-s', 'tools', '-p', 'test_ir_*.py']),
            ('portable', ['tools/run_investment_research_portable.py', '--report', str(HERE / 'portable.json')]),
            ('skills', ['tools/validate_skills.py']),
            ('structure', ['tools/check_investment_research.py']),
            ('resources', ['tools/sync_investment_resources.py', '--check']),
            ('index', ['tools/build_investment_research_index.py', '--check']),
        ]
    records = []
    for name, args in commands:
        command = [sys.executable, '-B', *args]
        start = time.monotonic()
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                timeout=900, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        output = result.stdout + result.stderr
        (HERE / (name + '.log')).write_text(output)
        record = {'name': name, 'command': command, 'exit': result.returncode,
                  'seconds': round(time.monotonic() - start, 3), 'log': name + '.log'}
        match = re.search(r'Ran (\d+) tests in ([\d.]+)s', output)
        if match:
            record.update(tests=int(match[1]), reported_seconds=float(match[2]))
        records.append(record)
        print(json.dumps(record), flush=True)
    (HERE / (suite + '-commands.json')).write_text(json.dumps(records, indent=2) + '\n')
    return int(any(row['exit'] != 0 for row in records))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', choices=('whole', 'focused'))
    raise SystemExit(run(parser.parse_args().suite))
