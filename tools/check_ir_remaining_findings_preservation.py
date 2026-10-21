#!/usr/bin/env python3
"""Check repair ownership against the dirty-checkout baseline; preserve older evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = 'docs/investment-research/remaining-findings-repairs-validation/'
PACKAGES = ('issuer-credit-researcher', 'issuer-credit-surveillance-reviewer',
            'investment-research-router')
FILES = {
    'tools/check_ir_remaining_findings_preservation.py',
    'tools/check_investment_research.py',
    'tools/test_ir_issuer_missing_evidence.py',
    'tools/test_ir_surveillance_legacy_gate.py',
    'tools/test_ir_capability_versions.py',
    'tools/test_ir_credit_phase1.py',
    'tools/test_asset_management_research_phase1.py',
    'catalog/investment-research-capabilities.json',
    'catalog/approved-overrides.json', 'catalog/provisional-additions.json',
    'catalog/skills-catalog.json', 'catalog/skills-catalog.csv',
    'docs/investment-research/README.md', 'docs/investment-research/migration.md',
    'docs/investment-research/remaining-findings-repairs-implementation.md',
}
PROTECTED = tuple('docs/investment-research/' + name for name in (
    'phase1-', 'phase2-', 'phase3-', 'phase4-', 'control-repairs-',
    'evidence-reconciliation-'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def permitted(path):
    return (path in FILES or path.startswith(CHECKPOINT)
            or any(path.startswith('skills/investment-research/' + name + '/')
                   for name in PACKAGES))


def audit(baseline):
    changed = [{'path': path, 'state': 'changed' if (ROOT / path).is_file() else 'removed',
                'permitted': permitted(path)}
               for path, digest in baseline['files'].items()
               if not (ROOT / path).is_file() or sha(ROOT / path) != digest]
    inventory = set(subprocess.check_output(
        ['git', 'ls-files', '-co', '--exclude-standard', '-z'], cwd=ROOT
    ).decode().split('\0'))
    added = [{'path': path, 'state': 'added', 'permitted': permitted(path)}
             for path in sorted(inventory - set(baseline['files']))
             if path and (ROOT / path).is_file()]
    violations = [row for row in changed + added if not row['permitted']]
    protected_changes = [row for row in changed + added if row['path'].startswith(PROTECTED)]
    return {
        'schema_version': 'ir-remaining-findings-preservation/1.0',
        'baseline_head': baseline['head'], 'baseline_files': len(baseline['files']),
        'unchanged_baseline_files': len(baseline['files']) - len(changed),
        'changes': changed, 'new_files': added, 'unexpected_changes': violations,
        'protected_evidence_files': sum(path.startswith(PROTECTED) for path in baseline['files']),
        'protected_evidence_changes': protected_changes,
        'all_earlier_phase_and_repair_evidence_untouched': not protected_changes,
        'passed': not violations and not protected_changes,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = audit(json.loads(args.baseline.read_text()))
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('changes', 'new_files')}, indent=2))
    raise SystemExit(not report['passed'])
