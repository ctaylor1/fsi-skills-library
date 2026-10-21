#!/usr/bin/env python3
"""Check the repair scope against pre-edit bytes, including all four phase records."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    'issuer-credit-researcher', 'issuer-credit-surveillance-reviewer',
    'investment-research-router',
}
FILES = {
    'catalog/investment-research-capabilities.json',
    'catalog/investment-research-routes.json',
    'catalog/approved-overrides.json', 'catalog/provisional-additions.json',
    'catalog/skills-catalog.json', 'catalog/skills-catalog.csv',
    'tools/check_investment_research.py',
    'tools/check_ir_control_repairs_preservation.py',
    'tools/test_ir_issuer_control_repairs.py',
    'tools/test_ir_surveillance_control_repairs.py',
    'tools/test_ir_route_contract_parity.py',
    'tools/test_ir_specialist_integration_phase4.py',
    'docs/investment-research/README.md',
    'docs/investment-research/migration.md',
    'docs/investment-research/support-matrix.md',
    'docs/investment-research/control-repairs-implementation.md',
    'skills/investment-research/README.md',
}
HISTORY = tuple('docs/investment-research/phase' + str(n) + '-'
                for n in range(1, 5))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def permitted(rel):
    return (rel in FILES or rel.startswith('docs/investment-research/control-repairs-validation/')
            or any(rel.startswith('skills/investment-research/' + name + '/')
                   for name in PACKAGES))


def audit(baseline):
    changes = []
    unchanged = 0
    for rel, expected in baseline['files'].items():
        path = ROOT / rel
        if path.is_file() and digest(path) == expected:
            unchanged += 1
        else:
            changes.append({'path': rel, 'state': 'changed' if path.is_file() else 'removed',
                            'permitted': permitted(rel)})
    current = subprocess.check_output(
        ['git', 'ls-files', '-co', '--exclude-standard', '-z'], cwd=ROOT
    ).decode().split('\0')
    added = [{'path': rel, 'permitted': permitted(rel)} for rel in sorted(set(current))
             if rel and rel not in baseline['files'] and (ROOT / rel).is_file()]
    unexpected = [row for row in changes + added if not row['permitted']]
    history = [rel for rel in baseline['files'] if rel.startswith(HISTORY)]
    history_changes = [row for row in changes + added if row['path'].startswith(HISTORY)]
    return {
        'schema_version': 'ir-control-repairs-preservation/1.0',
        'baseline_head': baseline['head'], 'baseline_files': len(baseline['files']),
        'unchanged_baseline_files': unchanged, 'changes': changes, 'new_files': added,
        'unexpected_changes': unexpected,
        'prior_phase_evidence_files': len(history),
        'prior_phase_evidence_changes': history_changes,
        'prior_phase_evidence_untouched': not history_changes,
        'passed': not unexpected and not history_changes,
        'scope': 'Pre-edit byte comparison; preserves existing dirty-checkout work and all Phase 1-4 records. No professional acceptance claim.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.baseline.read_text()))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in {'changes', 'new_files'}}, indent=2))
    raise SystemExit(not result['passed'])
