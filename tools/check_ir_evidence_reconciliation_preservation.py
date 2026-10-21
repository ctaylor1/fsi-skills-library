#!/usr/bin/env python3
"""Verify reconciliation ownership and preserve all prior phase/repair evidence."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {'issuer-credit-researcher', 'issuer-credit-surveillance-reviewer'}
FILES = {
    'catalog/approved-overrides.json', 'catalog/provisional-additions.json',
    'catalog/skills-catalog.json', 'catalog/skills-catalog.csv',
    'tools/check_ir_evidence_reconciliation_preservation.py',
    'tools/test_ir_issuer_evidence_reconciliation.py',
    'tools/test_ir_surveillance_evidence_reconciliation.py',
    'tools/test_ir_credit_phase2.py', 'tools/test_ir_issuer_control_repairs.py',
    'tools/test_ir_surveillance_control_repairs.py', 'tools/test_ir_route_contract_parity.py',
    'docs/investment-research/README.md', 'docs/investment-research/migration.md',
    'docs/investment-research/evidence-reconciliation-implementation.md',
}
PHASES = tuple('docs/investment-research/phase' + str(n) + '-' for n in range(1, 5))
REPAIRS = 'docs/investment-research/control-repairs-'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def permitted(rel):
    return (rel in FILES or rel.startswith('docs/investment-research/evidence-reconciliation-validation/')
            or any(rel.startswith('skills/investment-research/' + name + '/') for name in PACKAGES))


def audit(baseline):
    changes = []
    unchanged = 0
    for rel, digest in baseline['files'].items():
        path = ROOT / rel
        if path.is_file() and sha(path) == digest:
            unchanged += 1
        else:
            changes.append({'path': rel, 'state': 'changed' if path.is_file() else 'removed',
                            'permitted': permitted(rel)})
    inventory = subprocess.check_output(
        ['git', 'ls-files', '-co', '--exclude-standard', '-z'], cwd=ROOT
    ).decode().split('\0')
    added = [{'path': rel, 'permitted': permitted(rel)} for rel in sorted(set(inventory))
             if rel and rel not in baseline['files'] and (ROOT / rel).is_file()]
    unexpected = [row for row in changes + added if not row['permitted']]
    protected_changes = [row for row in changes + added
                         if row['path'].startswith(PHASES) or row['path'].startswith(REPAIRS)]
    return {
        'schema_version': 'ir-evidence-reconciliation-preservation/1.0',
        'baseline_head': baseline['head'], 'baseline_files': len(baseline['files']),
        'unchanged_baseline_files': unchanged, 'changes': changes, 'new_files': added,
        'unexpected_changes': unexpected,
        'earlier_phase_evidence_files': sum(rel.startswith(PHASES) for rel in baseline['files']),
        'earlier_repair_evidence_files': sum(rel.startswith(REPAIRS) for rel in baseline['files']),
        'protected_evidence_changes': protected_changes,
        'earlier_phase_and_repair_evidence_untouched': not protected_changes,
        'passed': not unexpected and not protected_changes,
        'scope': 'Byte comparison to the pre-edit dirty-checkout baseline; all earlier phase and repair records protected.',
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
