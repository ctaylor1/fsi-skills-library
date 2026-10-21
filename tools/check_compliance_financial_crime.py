#!/usr/bin/env python3
"""Check compliance ownership, migrations, support scope and declared routes."""
import json
from pathlib import Path
from resolve_skill import resolve

ROOT = Path(__file__).resolve().parents[1]


def check():
    errors = []
    catalog = json.loads((ROOT / 'catalog/skills-catalog.json').read_text())['skills']
    names = {x['name']: x for x in catalog}
    paths = {p.parent.name: str(p.parent.relative_to(ROOT)) for p in (ROOT / 'skills').glob('*/*/SKILL.md')}
    if len(names) != len(catalog):
        errors.append('duplicate catalog identifiers')
    if set(names) != set(paths):
        errors.append('catalog/installed package mismatch')
    migrations = json.loads((ROOT / 'catalog/compliance-financial-crime-migrations.json').read_text())['migrations']
    if len(migrations) != 15 or len({m['old_name'] for m in migrations}) != 15:
        errors.append('all 15 original packages need one migration record')
    for m in migrations:
        if paths.get(m['new_name']) != m['new_path']:
            errors.append('missing/wrong migration target ' + m['new_name'])
        if names.get(m['new_name'], {}).get('category') != m['category']:
            errors.append('category mismatch ' + m['new_name'])
        if m['old_path'] != m['new_path'] and (ROOT / m['old_path'] / 'SKILL.md').exists():
            errors.append('legacy package still active ' + m['old_path'])
        for identifier in (m['old_name'], m['old_path'], str(ROOT / m['old_path'] / 'SKILL.md')):
            try:
                r = resolve(identifier)
                if r['path'] != m['new_path'] or r['authority_granted'] is not False:
                    errors.append('alias mismatch ' + identifier)
            except ValueError as exc:
                errors.append(str(exc))
    caps = json.loads((ROOT / 'catalog/compliance-financial-crime-capabilities.json').read_text())['capabilities']
    if sum(c['target_workflow'] for c in caps) != 36:
        errors.append('target workflow roadmap count drifted')
    for c in caps:
        installed = c['name'] in paths
        if (c['support_status'] != 'planned') != installed:
            errors.append('support/installation mismatch ' + c['name'])
        if c['professional_acceptance'] != 'not-established' or c['authority'] != 'draft-only':
            errors.append('unsupported acceptance/authority ' + c['name'])
    phase2 = json.loads((ROOT / 'catalog/compliance-financial-crime-phase2-capabilities.json').read_text())
    by_name = {c['name']: c for c in caps}
    if len(phase2['new_packages']) != 19 or len(phase2['expanded_packages']) != 2:
        errors.append('Phase2 requires 19 distinct new packages and two expanded native modes')
    for name in set(phase2['new_packages']) | set(phase2['expanded_packages']):
        capability = by_name.get(name, {})
        if capability.get('support_status') != 'bounded-native' or capability.get('implementation_phase') != 2:
            errors.append('Phase2 native scope missing: ' + name)
        if not (ROOT / paths.get(name, 'missing') / 'scripts/test_phase2.py').exists():
            errors.append('Phase2 domain regressions missing: ' + name)
    phase3 = json.loads((ROOT / 'catalog/compliance-financial-crime-phase3-capabilities.json').read_text())
    if {p['id'] for p in phase3['new_packages'].values()} != set(phase2['remaining_phase3_ids']):
        errors.append('Phase3 implementation differs from four historical Phase2 gaps')
    if any(c['target_workflow'] and c['support_status'] == 'planned' for c in caps):
        errors.append('Phase3 target workflow remains planned')
    for name in phase3['new_packages']:
        capability = by_name.get(name, {})
        if capability.get('support_status') != 'bounded-native' or capability.get('implementation_phase') != 3:
            errors.append('Phase3 native scope missing: ' + name)
        if not (ROOT / paths.get(name, 'missing') / 'scripts/test_phase3.py').exists():
            errors.append('Phase3 domain regressions missing: ' + name)
    for name in phase3['adjacent_composition_owners']:
        if name not in paths or name in phase3['new_packages']:
            errors.append('Phase3 adjacent owner missing or duplicated: ' + name)
    migration_doc = json.loads((ROOT / 'catalog/compliance-financial-crime-migrations.json').read_text())
    scope_migrations = migration_doc.get('phase2_scope_migrations', [])
    if len(scope_migrations) != 1 or scope_migrations[0].get('new_primary') != 'financial-promotion-reviewer' or migration_doc.get('pending_migrations'):
        errors.append('external promotion ownership migration missing')
    routes = json.loads((ROOT / 'skills/compliance-financial-crime/compliance-financial-crime-router/references/routes.json').read_text())['routes']
    expected_routes = 27 + len(phase2['additional_router_intents']) + len(phase3['additional_router_intents'])
    if len(routes) != expected_routes or len({r['id'] for r in routes}) != expected_routes:
        errors.append('27 original routes plus distinct Phase2/Phase3 direct intents required')
    if not set(phase2['additional_router_intents']).issubset({r['id'] for r in routes}):
        errors.append('Phase2 direct workflow intents missing')
    if not (set(phase2['new_packages']) | set(phase2['expanded_packages'])).issubset({r['primary']['name'] for r in routes}):
        errors.append('Phase2 native package lacks a direct primary-owner route')
    if not set(phase3['additional_router_intents']).issubset({r['id'] for r in routes}):
        errors.append('Phase3 direct workflow intents missing')
    if not set(phase3['new_packages']).issubset({r['primary']['name'] for r in routes}):
        errors.append('Phase3 native package lacks a direct primary-owner route')
    for route in routes:
        for target in [route['primary']] + route['supporting']:
            if target['name'] in by_name and any(target.get(k) != by_name[target['name']][k] for k in ('path', 'support_status', 'implementation_scope')):
                errors.append('route capability scope drift: ' + target['name'])
            if target['support_status'] != 'planned' and paths.get(target['name']) != target['path']:
                errors.append('unavailable route target ' + target['name'])
            if target['support_status'] == 'planned' and target['name'] in paths:
                errors.append('planned status drift ' + target['name'])
    return errors


if __name__ == '__main__':
    errors = check()
    for error in errors:
        print(error)
    print(f'Compliance ownership/routing: {len(errors)} error(s)')
    raise SystemExit(bool(errors))
