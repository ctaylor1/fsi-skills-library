#!/usr/bin/env python3
"""Render IR discovery from the reviewed registry; --check is read-only."""
import argparse, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def render():
    doc=json.loads((ROOT/'catalog/investment-research-capabilities.json').read_text())
    caps=doc['capabilities']
    implemented=sum(r['support_status']!='planned' for r in caps)
    planned=len(caps)-implemented
    legacy=len(doc['retained_legacy'])
    phase=doc.get('phase','phase1').replace('phase','Phase ')
    note=f' {legacy} legacy method(s) remain installed.' if legacy else ' The legacy model auditor resolves to the reviewed model-reviewer continuity mode after parity checks.'
    rows=['# Investment Research support matrix','',f'Generated from catalog/investment-research-capabilities.json. The 42-capability target has {implemented} bounded native methods and {planned} planned methods.'+note+' Planned methods are not installed packages. All methods remain draft-only; professional acceptance is not established.','','| ID | Method | Support | Phase for expanded scope | Bounded scope / planned job |','|---|---|---|---|---|']
    for r in caps:
        label=r['name'] if r['support_status']=='planned' else f"[{r['name']}](../../{r['path']}/SKILL.md)"
        rows.append(f"| {r['id']} | {label} | {r['support_status']} | {r['roadmap_phase']} | {r['implementation_scope']} |")
    rows += ['','Native support is not a governed cross-skill adapter or deployment acceptance. Financial-institution DCF/three-statement/surveillance methods are not implemented. The router returns an explicit profile gap.','','Shared owners: '+', '.join(r['name'] for r in doc['shared_owners'])+'.','']
    readme=['# Investment Research','',f'{phase}: {implemented+legacy} installed packages ({implemented} target methods and {legacy} retained legacy methods). The broader architecture contains 42 target capabilities; planned methods are listed separately and are not installed.','','[Architecture and controls](../../docs/investment-research/README.md) · [Support matrix](../../docs/investment-research/support-matrix.md) · [Migration](../../docs/investment-research/migration.md)','','| Installed package | Current role |','|---|---|']
    for r in caps+doc['retained_legacy']:
        if r['support_status']!='planned': readme.append(f"| [{r['name']}]({r['name']}/SKILL.md) | {r.get('implementation_scope',r.get('reason'))} |")
    readme += ['','Use the router to select explicit intents, methods, owner and installation status. Keep the original supplied input for every output validation. No source authentication, publication or execution authority is provided.','']
    return {'docs/investment-research/support-matrix.md':'\n'.join(rows),'skills/investment-research/README.md':'\n'.join(readme)}

def run(check=False):
    errors=[]
    for rel,value in render().items():
        p=ROOT/rel
        if check:
            if not p.exists() or p.read_text()!=value: errors.append(rel+' differs')
        else: p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value)
    return errors

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    errors=run(parser.parse_args().check)
    for e in errors: print(e)
    print('Investment Research index: '+('FAIL' if errors else 'PASS'))
    raise SystemExit(bool(errors))
