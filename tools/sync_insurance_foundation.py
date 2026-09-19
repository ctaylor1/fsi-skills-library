#!/usr/bin/env python3
"""Bundle the native workflow helper into approved Phase 2/3 packages."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = {'insurance_foundation.py': 'scripts/insurance_foundation.py',
             'insurance-foundation.md': 'references/insurance-foundation.md'}


def packages():
    names = []
    for phase in (2, 3):
        path = ROOT / f'catalog/insurance-phase{phase}-capabilities.json'
        if path.exists():
            names.extend(json.loads(path.read_text())['packages'])
    return names


def check():
    errors = []
    for source, destination in RESOURCES.items():
        expected = (ROOT / 'shared/insurance' / source).read_bytes()
        for name in packages():
            path = ROOT / 'skills/insurance' / name / destination
            if not path.is_file() or path.read_bytes() != expected:
                errors.append(f'{name}/{destination}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if not args.check:
        for source, destination in RESOURCES.items():
            contents = (ROOT / 'shared/insurance' / source).read_bytes()
            for name in packages():
                path = ROOT / 'skills/insurance' / name / destination
                if path.parent.is_dir():
                    path.write_bytes(contents)
    errors = check()
    print(f'Insurance foundation: {len(packages())} expected bundles; {len(errors)} missing/drifted')
    for name in errors:
        print(name)
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
