#!/usr/bin/env python3
"""Check insurance routes, migration records and bundle/catalog integrity."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check():
    errors = []
    catalog = json.loads((ROOT / 'catalog/skills-catalog.json').read_text())['skills']
    names = {row['name'] for row in catalog}
    packages = {p.parent.name: p.parent for p in (ROOT / 'skills').glob('*/*/SKILL.md')}
    router = ROOT / 'skills/insurance/insurance-router/references'
    routes = json.loads((router / 'routes.json').read_text())['intents']
    migrations = json.loads((ROOT / 'catalog/insurance-phase1-migrations.json').read_text())
    if migrations != json.loads((router / 'migrations.json').read_text()):
        errors.append('router migration bundle drift')

    def visit(intent, row):
        if 'variants' in row:
            for variant, child in row['variants'].items():
                visit(intent + '/' + variant, child)
            return
        if row.get('planned') and row.get('target'):
            errors.append(f'{intent}: planned capability masquerades as installed route')
        if not row.get('planned') and not row.get('target'):
            errors.append(f'{intent}: missing target or explicit capability gap')
        targets = ([row['target']] if row.get('target') else []) + row.get('support', []) + row.get('evidence_options', [])
        for target in targets:
            if target not in names or target not in packages:
                errors.append(f'{intent}: unavailable catalog/package target {target}')

    for intent, row in routes.items():
        visit(intent, row)
    for old, change in migrations['aliases'].items():
        if old in names or old in packages:
            errors.append(f'retired insurance name remains active: {old}')
        if change['target'] not in names or change['target'] not in packages:
            errors.append(f'missing migration target: {change["target"]}')
        for intent in change['intents']:
            if intent not in routes:
                errors.append(f'alias {old}: missing intent {intent}')
    accounted = set(migrations['aliases']) | set(migrations['retained_with_revisions'])
    if len(accounted) != 24:
        errors.append('migration must account for all 24 original insurance packages')
    expected = {v['target'] for v in migrations['aliases'].values()} | set(migrations['retained_with_revisions']) | {'insurance-router'}
    for phase in (2, 3, 4, 5):
        manifest = ROOT / f'catalog/insurance-phase{phase}-capabilities.json'
        if manifest.exists():
            expected |= set(json.loads(manifest.read_text())['packages'])
    actual = {name for name, package in packages.items() if package.parent.name == 'insurance'}
    if actual != expected:
        errors.append('insurance portfolio differs from approved phase dispositions')
    for name, package in packages.items():
        if package.parent.name == 'insurance':
            if name not in names:
                errors.append(f'{name}: absent from catalog')
            if not (package / 'references/insurance-contract.md').is_file():
                errors.append(f'{name}: missing common reference')
    if len(names) != len(catalog):
        errors.append('duplicate catalog names')
    # No direct instruction may send treaty interpretation back to policy wording.
    treaty = ROOT / 'skills/insurance/reinsurance-contract-reviewer/references/handoffs.md'
    if treaty.exists() and 'route to `policy-wording-comparator`' in treaty.read_text().lower():
        errors.append('treaty-to-policy routing loop remains')
    return errors


if __name__ == '__main__':
    findings = check()
    for finding in findings:
        print('ERROR', finding)
    print(f'Insurance route/migration checks: {len(findings)} error(s)')
    raise SystemExit(bool(findings))
