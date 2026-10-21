#!/usr/bin/env python3
"""Check ownership, routing and approved migrations and Phase 2 foundations without changing files."""
import argparse
import json
from pathlib import Path
from resolve_skill import resolve

ROOT=Path(__file__).resolve().parents[1]

def check(scope_only=False):
    errors=[]
    catalog=json.loads((ROOT/'catalog/skills-catalog.json').read_text())['skills']
    names={r['name'] for r in catalog}
    categories={r['name']:r['category'] for r in catalog}
    packages={p.parent.name:p.parent for p in (ROOT/'skills').glob('*/*/SKILL.md')}
    if scope_only:
        # Explicit domain-only check for independent work in a shared checkout.
        # Default/release validation below still requires the whole-library bijection.
        installed_am={name for name,path in packages.items() if path.parent==ROOT/'skills/asset-management'}
        catalog_am={name for name,category in categories.items() if category=='Asset Management'}
        if installed_am!=catalog_am:errors.append('AM installed package/catalog mismatch')
    elif len(packages)!=len(names) or set(packages)!=names: errors.append('installed package/catalog mismatch')
    if len(names)!=len(catalog): errors.append('duplicate catalog names')
    moves=json.loads((ROOT/'catalog/asset-management-migrations.json').read_text())['migrations']
    originals=[r for r in moves if r['old_path'].startswith('skills/asset-management/')]
    if len(originals)!=30 or len({r['old_name'] for r in originals})!=30: errors.append('original AM inventory must contain30 distinct packages')
    for row in moves:
        if row['new_name'] not in names or not (ROOT/row['new_path']/'SKILL.md').is_file(): errors.append('missing migration target: '+row['new_name'])
        if categories.get(row['new_name'])!=row['category']: errors.append('category drift: '+row['new_name'])
        if row['old_path']!=row['new_path'] and (ROOT/row['old_path']/'SKILL.md').exists(): errors.append('old package still active: '+row['old_path'])
        for identifier in (row['old_name'],row['old_path']):
            result=resolve(identifier)
            if (result['name'],result['path'],result['mode'])!=(row['new_name'],row['new_path'],row['mode']): errors.append('alias drift: '+identifier)
    caps=json.loads((ROOT/'catalog/asset-management-capabilities.json').read_text())['capabilities']
    am=[r for r in caps if r['category']=='Asset Management']
    if len(am)!=64: errors.append('approved AM roadmap must retain64 capabilities')
    for row in caps:
        implemented=row['support_status']!='planned'
        if implemented!=(row['name'] in packages): errors.append('support status/package mismatch: '+row['name'])
        if row['professional_acceptance']!='not-established' or row['authority']!='draft-only': errors.append('unsupported acceptance claim: '+row['name'])
    phase2=json.loads((ROOT/'catalog/asset-management-phase2-capabilities.json').read_text())
    if len(phase2['new_packages'])!=29 or len(phase2['expanded_packages'])!=3:errors.append('Phase2 requires29 new and3 expanded packages')
    phase3=json.loads((ROOT/'catalog/asset-management-phase3-capabilities.json').read_text())
    phase4=json.loads((ROOT/'catalog/asset-management-phase4-capabilities.json').read_text())
    if {r['id'] for r in am if r['support_status']=='planned'}!=set(phase4['remaining_planned_ids']):errors.append('later-phase scope drift')
    if set(phase3['remaining_planned_ids']) != {v['id'] for v in phase4['new_packages'].values()}:errors.append('Phase4 must preserve Phase3 roadmap')
    if len(phase4['new_packages'])!=6 or len(phase4['expanded_packages'])!=6:errors.append('Phase4 scope requires six new and six extended packages')
    if set(phase2['remaining_planned_ids']) != set(phase3['remaining_planned_ids']) | {r['id'] for r in phase3['new_packages'].values()}:errors.append('Phase3 must preserve the Phase2 roadmap')
    if len([r for r in am if r['support_status']!='planned'])!=64:errors.append('Phase4 must retain64 implemented AM packages')
    byname={r['name']:r for r in caps}
    for name,spec in phase2['new_packages'].items():
        if name not in packages or byname.get(name,{}).get('support_status')!='bounded-native':errors.append('missing Phase2 native package: '+name)
        if byname.get(name,{}).get('id')!=spec['id'] or byname.get(name,{}).get('path')!=spec['path']:errors.append('Phase2 identity drift: '+name)
    if {r['id'] for r in phase3['new_packages'].values()} != {'T03','T04','T05','T06'}:errors.append('Phase3 scope must be T03-T06')
    for name,spec in phase3['new_packages'].items():
        if name not in packages or byname.get(name,{}).get('support_status')!='bounded-native':errors.append('missing Phase3 native package: '+name)
        if byname.get(name,{}).get('id')!=spec['id'] or byname.get(name,{}).get('path')!=spec['path']:errors.append('Phase3 identity drift: '+name)
        if any(owner not in names for owner in spec['shared_owners']):errors.append('missing Phase3 shared owner: '+name)
    for name,spec in phase4['new_packages'].items():
        if name not in packages or byname.get(name,{}).get('support_status')!='bounded-native':errors.append('missing Phase4 native package: '+name)
        if byname.get(name,{}).get('id')!=spec['id'] or byname.get(name,{}).get('path')!=spec['path']:errors.append('Phase4 identity drift: '+name)
    router=ROOT/'skills/asset-management/asset-management-router/references'
    for row in json.loads((router/'routes.json').read_text())['routes']:
        for target in ([row['primary']] if row['primary'] else [])+row['supporting']:
            if target['support_status']!='planned' and target['name'] not in names: errors.append('unavailable route: '+target['name'])
            if target['support_status']=='planned' and target['name'] in names: errors.append('stale planned route: '+target['name'])
    return errors

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--scope-only",action="store_true",help="Validate AM inventory and approved migrations; whole-library inventory remains a separate release check")
    args=parser.parse_args();errors=check(args.scope_only)
    for error in errors:print(error)
    print(f'Asset management ownership/routing ({"AM scope" if args.scope_only else "whole-library inventory"}): {len(errors)} error(s)')
    raise SystemExit(bool(errors))
