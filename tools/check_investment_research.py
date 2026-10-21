#!/usr/bin/env python3
"""Read-only structural, ownership and completeness guards for delivered IR phases."""
import json
import re
from pathlib import Path
from resolve_skill import resolve
from build_investment_research_index import run as check_index
from test_ir_route_contract_parity import contract_parity_errors
from validate_skills import split_frontmatter
ROOT=Path(__file__).resolve().parents[1]

# Installed native packages use stable major.minor.patch release identifiers.
PACKAGE_VERSION = re.compile(r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z')


def capability_version_errors(root=ROOT):
    """Check current discovery metadata against the actual installed packages.

    Historical phase inventories are intentionally excluded. Equal canonical and
    bundled values alone are insufficient: both can retain the same stale value.
    """
    import yaml

    root = Path(root)
    errors = []
    registries = {}
    paths = {
        'canonical': root / 'catalog/investment-research-capabilities.json',
        'bundled': root / 'skills/investment-research/investment-research-router/references/capabilities.json',
    }
    for label, path in paths.items():
        try:
            doc = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(doc, dict) or not isinstance(doc.get('capabilities'), list):
                raise ValueError('capabilities must be an array')
            installed = {}
            for row in doc['capabilities']:
                if not isinstance(row, dict) or not isinstance(row.get('name'), str) or not row['name']:
                    raise ValueError('every capability must have a name')
                if row.get('support_status') == 'planned':
                    continue
                name = row['name']
                if name in installed:
                    errors.append(f'{label} capability version: duplicate installed name {name}')
                installed[name] = row
                version = row.get('package_version')
                if not isinstance(version, str) or not PACKAGE_VERSION.fullmatch(version):
                    errors.append(f'{label} capability version: {name} requires a major.minor.patch package_version')
            registries[label] = installed
        except (OSError, ValueError) as exc:
            errors.append(f'{label} capability version registry: {exc}')
    if set(registries) != set(paths):
        return errors

    canonical, bundled = registries['canonical'], registries['bundled']
    if set(canonical) != set(bundled):
        errors.append('capability version: canonical/bundled installed capability inventory differs')
    for name, row in canonical.items():
        try:
            path = row.get('path')
            if not isinstance(path, str) or not path:
                raise ValueError('missing package path')
            raw, _ = split_frontmatter((root / path / 'SKILL.md').read_text(encoding='utf-8'))
            if raw is None:
                raise ValueError('missing YAML frontmatter')
            frontmatter = yaml.safe_load(raw)
            metadata = frontmatter.get('metadata') if isinstance(frontmatter, dict) else None
            version = metadata.get('aws-fsi-version') if isinstance(metadata, dict) else None
            if not isinstance(version, str) or not PACKAGE_VERSION.fullmatch(version):
                raise ValueError('requires a major.minor.patch aws-fsi-version')
            for label, registered in (('canonical', row), ('bundled', bundled.get(name))):
                if registered is not None and registered.get('package_version') != version:
                    errors.append(f'{label} capability version: {name} is {registered.get("package_version")!r}; installed package is {version}')
            if name in bundled and bundled[name].get('path') != path:
                errors.append(f'capability version: canonical/bundled package path differs for {name}')
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f'installed capability version: {name}: {exc}')
    return errors

def check():
    errors=[]
    def expect(ok,message):
        if not ok: errors.append(message)
    doc=json.loads((ROOT/'catalog/investment-research-capabilities.json').read_text()); caps=doc['capabilities']
    catalog=json.loads((ROOT/'catalog/skills-catalog.json').read_text())['skills']
    packages=list((ROOT/'skills').glob('*/*/SKILL.md')); names=[p.parent.name for p in packages]
    expect(len(names)==len(set(names)),'duplicate installed package names')
    expect(len(catalog)==len({r['name'] for r in catalog}),'duplicate catalog names')
    expect(set(names)=={r['name'] for r in catalog},'global installed/catalog mismatch')
    expect(len(caps)==42 and len({r['id'] for r in caps})==42 and len({r['name'] for r in caps})==42,'target registry must contain 42 distinct capabilities')
    installed=[r for r in caps if r['support_status']!='planned']
    expected_count={'phase1':18,'phase2':34,'phase3':37,'phase4':42}.get(doc.get('phase'))
    expect(len(installed)==expected_count,'implemented target count inconsistent with delivered phase')
    for row in caps:
        exists=(ROOT/row['path']/'SKILL.md').is_file()
        expect(exists==(row['support_status']!='planned'),'support/path mismatch: '+row['name'])
        expect(row['professional_acceptance']=='not-established' and row['authority']=='draft-only','unsupported authority/acceptance: '+row['name'])
        if exists: expect(any(c['name']==row['name'] and c['category']=='Investment Research' for c in catalog),'catalog ownership mismatch: '+row['name'])
    expected={r['name'] for r in installed+doc['retained_legacy']}
    actual={p.parent.name for p in packages if p.parent.parent.name=='investment-research'}
    expect(actual==expected,'IR package inventory mismatch')
    for row in installed+doc['retained_legacy']+doc['shared_owners']:
        p=ROOT/row['path']; ef=p/'evals/evals.json'
        expect(ef.is_file(),'missing evals: '+row['name'])
        if ef.exists():
            checks=[r for r in json.loads(ef.read_text()).get('evals',[]) if r.get('command') and 'expect_exit' in r]
            expect(any(r['expect_exit']==0 for r in checks) and any(r['expect_exit']!=0 for r in checks),'missing positive/negative executable evidence: '+row['name'])
    routes=json.loads((ROOT/'catalog/investment-research-routes.json').read_text())['routes']
    expect(len({r['intent'] for r in routes})==len(routes),'duplicate route intent')
    for row in routes:
        expect(row['target'] in {r['name'] for r in caps} or row['target'] in names,'unknown route target: '+row['target'])
    migrations=json.loads((ROOT/'catalog/investment-research-migrations.json').read_text())['migrations']
    for row in migrations:
        expect(not (ROOT/row['old_path']/'SKILL.md').exists(),'old duplicate remains: '+row['old_path'])
        for identifier in [row['old_name'],row['old_path']]:
            resolved=resolve(identifier)
            expect(resolved['path']==row['new_path'] and resolved['name']==row['new_name'],'alias drift: '+identifier)
    for row in doc['shared_owners']:
        expect((ROOT/row['path']/'SKILL.md').is_file(),'missing shared owner: '+row['name'])
    if doc.get('phase') in {'phase2','phase3','phase4'}:
        phase=json.loads((ROOT/'catalog/investment-research-phase2-capabilities.json').read_text())
        expect(len(phase['new_packages'])==16 and len(phase['expanded_packages'])==16,'Phase 2 must account for sixteen new and sixteen expanded methods')
        adapters=json.loads((ROOT/'catalog/investment-research-adapters.json').read_text())['adapters']
        phase3=json.loads((ROOT/'catalog/investment-research-phase3-capabilities.json').read_text()) if doc.get('phase') in {'phase3','phase4'} else None
        phase4=json.loads((ROOT/'catalog/investment-research-phase4-capabilities.json').read_text()) if doc.get('phase')=='phase4' else None
        expected_adapters=set(phase['reviewed_adapters']) | (set(phase3['reviewed_adapters']) if phase3 else set())
        if phase4:expected_adapters.update(phase4['reviewed_adapters'])
        expect(len(adapters)==len(expected_adapters) and {r['id'] for r in adapters}==expected_adapters,'reviewed adapter inventory drift')
        if phase3:
            expect(set(phase3['new_packages'])=={r['name'] for r in installed if r['roadmap_phase']==3},'Phase 3 package inventory drift')
        if phase4:
            expect(set(phase4['new_packages'])=={r['name'] for r in installed if r['roadmap_phase']==4},'Phase 4 package inventory drift')
            expect(len(phase4['new_packages'])==5,'Phase 4 must implement five specialist methods')
        for adapter in adapters:
            expect(adapter['producer'] in expected and adapter['receiver'] in expected,'adapter dependency missing')
        expect(json.loads((ROOT/'catalog/investment-research-routes.json').read_text()).get('reviewed_adapters')==adapters,'router reviewed-adapter projection drift')
        retired=resolve('model-roll-forward-auditor')
        expect(retired['name']=='research-financial-model-reviewer' and retired['mode']=='legacy-roll-forward','legacy parity mode missing')
        expect((ROOT/'docs/investment-research/phase2-validation/legacy-auditor/SKILL.md').exists(),'legacy source archive missing')
    errors.extend(check_index(check=True))
    errors.extend(contract_parity_errors(ROOT))
    errors.extend(capability_version_errors(ROOT))
    return errors

if __name__=='__main__':
    try: errors=check()
    except (ValueError,OSError,KeyError) as exc: errors=[str(exc)]
    for e in errors: print(e)
    print('Investment Research structure: '+('FAIL' if errors else 'PASS'))
    raise SystemExit(bool(errors))
