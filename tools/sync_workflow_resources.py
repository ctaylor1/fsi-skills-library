#!/usr/bin/env python3
"""Bundle portable Phase 4 resources without modifying earlier insurance runtimes."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pairs():
    manifest = json.loads((ROOT / 'catalog/insurance-phase4-capabilities.json').read_text())
    for path in manifest['all_native_packages'].values():
        for name in ('workflow_contract.py', 'workflow_foundation.py', 'design_support.py'):
            yield ROOT / 'shared/workflow-review' / name, ROOT / path / 'scripts' / name
        for name in ('workflow-contract.md', 'workflow-foundation.md'):
            yield ROOT / 'shared/workflow-review' / name, ROOT / path / 'references' / name
        yield ROOT / 'shared/insurance/insurance_contract.py', ROOT / path / 'scripts/insurance_contract.py'
    router = ROOT / 'skills/insurance/insurance-router'
    yield ROOT / 'shared/workflow-review/workflow_contract.py', router / 'scripts/workflow_contract.py'
    yield ROOT / 'shared/workflow-review/workflow-contract.md', router / 'references/workflow-contract.md'


def check():
    return [str(target.relative_to(ROOT)) for source, target in pairs()
            if not target.is_file() or source.read_bytes() != target.read_bytes()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if not args.check:
        for source, target in pairs():
            target.write_bytes(source.read_bytes())
    errors = check()
    print(f'Workflow resources: {len(list(pairs()))} bundles; {len(errors)} missing/drifted')
    for error in errors:
        print(error)
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
