#!/usr/bin/env python3
"""Resolve registered IDs/paths to a terminal package without launching it."""
from __future__ import annotations
import argparse, json
from pathlib import Path, PurePosixPath

REPO=Path(__file__).resolve().parents[1]
REGISTRIES=('asset-management-migrations.json','compliance-financial-crime-migrations.json','investment-research-migrations.json')

def safe_path(value):
    p=PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or not value.startswith('skills/'):
        raise ValueError('unsafe migration path: '+value)
    return value

def resolve(identifier, repo=REPO):
    repo=Path(repo)
    normalized=identifier.rstrip('/').removesuffix('/SKILL.md')
    try: normalized=str(Path(normalized).relative_to(repo))
    except ValueError: pass
    edges={}; modes={}
    def add(key,target,mode=None):
        if key==target: return
        if key in edges and edges[key]!=target:
            raise ValueError('conflicting migration alias: '+key)
        if key in modes and modes[key]!=mode:
            raise ValueError('conflicting migration mode: '+key)
        edges[key]=target; modes[key]=mode
    records=[]
    for registry in REGISTRIES:
        path=repo/'catalog'/registry
        if path.exists(): records.extend(json.loads(path.read_text())['migrations'])
    for row in records:
        old=safe_path(row['old_path']); new=safe_path(row['new_path'])
        if PurePosixPath(new).name!=row['new_name']:
            raise ValueError('migration name/path mismatch: '+new)
        add(old,new,row.get('mode'))
        if row['old_name']!=row['new_name'] or row.get('mode'):
            add(row['old_name'],row['new_name'],row.get('mode'))
    overrides=json.loads((repo/'catalog/approved-overrides.json').read_text()).get('renames',{})
    for old,new in overrides.items(): add(old,new,modes.get(old))
    def terminal(key):
        seen=set(); mode=None
        while key in edges:
            if key in seen: raise ValueError('migration alias cycle: '+key)
            seen.add(key)
            next_mode=modes.get(key)
            if next_mode:
                if mode and mode!=next_mode: raise ValueError('incompatible migration modes')
                mode=next_mode
            key=edges[key]
        return key,mode
    for key in edges: terminal(key)
    target,mode=terminal(normalized)
    matches=[p.parent for p in (repo/'skills').rglob('SKILL.md')
             if p.parent.name==target or str(p.parent.relative_to(repo))==target]
    if len(matches)!=1: raise ValueError('unknown or ambiguous skill identifier: '+identifier)
    p=matches[0]
    if not p.resolve().is_relative_to(repo.resolve()): raise ValueError('package escapes repository')
    return {'name':p.name,'path':str(p.relative_to(repo)), 'mode':mode,'installed':True,
            'legacy_identifier':identifier if normalized!=target or normalized!=identifier else None,
            'authority_granted':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('identifier');args=parser.parse_args()
    try: print(json.dumps(resolve(args.identifier),indent=2))
    except (ValueError,OSError,KeyError) as exc: parser.exit(1,str(exc)+'\\n')
