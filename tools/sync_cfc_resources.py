#!/usr/bin/env python3
"""Bundle reviewed portable compliance resources; --check never writes."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'catalog/compliance-resource-lock.json'
SOURCES = {
    'native-integrity': ('shared/investment-data/native_integrity.py', '1.0.0'),
    'workflow-contract': ('shared/workflow-review/workflow_contract.py', '1.0'),
    'insurance-legacy-contract': ('shared/insurance/insurance_contract.py', '1.0'),
    'cfc-contract': ('shared/compliance-financial-crime/cfc_contract.py', '1.2'),
    'review-projection': ('shared/compliance-financial-crime/review_projection.py', '1.0'),
    'foundation-contract': ('shared/compliance-financial-crime/foundation_contract.py', '2.0'),
    'foundation-reference': ('shared/compliance-financial-crime/foundation-contract.md', '2.0'),
    'native-runner': ('shared/compliance-financial-crime/native_runner.py', '1.0'),
    'scenario-replay': ('shared/compliance-financial-crime/scenario_replay.py', '1.0'),
    'policy-contract': ('shared/compliance-financial-crime/policy_contract.py', '1.0'),
    'evidence-contract': ('shared/compliance-financial-crime/evidence-contract.md', '1.1'),
    'source-governance': ('shared/compliance-financial-crime/source-governance.md', '1.0'),
    'source-catalog': ('shared/compliance-financial-crime/source-catalog.json', '1.2'),
}


def encoded(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + '\n'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(check=False, update_lock=False):
    if check and update_lock:
        raise ValueError('--check cannot update lock')
    expected = {'schema_version': 'compliance-resource-lock/1.0', 'resources': {
        key: {'source': path, 'version': version, 'sha256': digest(ROOT / path), 'license': 'MIT'}
        for key, (path, version) in SOURCES.items()}}
    if update_lock:
        LOCK.write_text(encoded(expected))
    if not LOCK.exists() or json.loads(LOCK.read_text()) != expected:
        raise ValueError('canonical resource differs from reviewed lock; review then --update-lock')
    caps = json.loads((ROOT / 'catalog/compliance-financial-crime-capabilities.json').read_text())['capabilities']
    paths = [c['path'] for c in caps if c['support_status'] != 'planned']
    phase2 = json.loads((ROOT / 'catalog/compliance-financial-crime-phase2-capabilities.json').read_text())
    phase3 = json.loads((ROOT / 'catalog/compliance-financial-crime-phase3-capabilities.json').read_text())
    foundation_packages = set(phase2['new_packages']) | set(phase2['expanded_packages']) | set(phase3['new_packages']) | {'compliance-financial-crime-router'}
    errors = []
    for rel in paths:
        package = ROOT / rel
        if not (package / 'SKILL.md').exists():
            errors.append('missing package: ' + rel); continue
        bundles = {'scripts/native_integrity.py': 'native-integrity',
                   'references/evidence-contract.md': 'evidence-contract',
                   'references/source-governance.md': 'source-governance'}
        if package.name in foundation_packages:
            bundles['scripts/foundation_contract.py'] = 'foundation-contract'
            bundles['references/foundation-contract.md'] = 'foundation-reference'
        if package.name in {'customer-due-diligence-reviewer', 'beneficial-ownership-analyzer',
                            'customer-risk-rating-reviewer', 'enhanced-due-diligence-assessor',
                            'adverse-media-investigator'}:
            bundles['scripts/policy_contract.py'] = 'policy-contract'
        if package.name == 'transaction-monitoring-scenario-evaluator':
            bundles['scripts/scenario_replay.py'] = 'scenario-replay'
        if package.name == 'compliance-financial-crime-router':
            bundles.update({'scripts/workflow_contract.py': 'workflow-contract',
                            'scripts/insurance_contract.py': 'insurance-legacy-contract',
                            'scripts/cfc_contract.py': 'cfc-contract',
                            'scripts/review_projection.py': 'review-projection',
                            'scripts/native_runner.py': 'native-runner',
                            'references/source-catalog.json': 'source-catalog'})
        for destination, key in bundles.items():
            source = ROOT / SOURCES[key][0]; target = package / destination
            if check:
                if not target.exists() or target.read_bytes() != source.read_bytes():
                    errors.append(str(target.relative_to(ROOT)) + ' drifted')
            else:
                target.parent.mkdir(exist_ok=True); target.write_bytes(source.read_bytes())
        if package.name == 'compliance-financial-crime-router':
            for catalog, target in [('compliance-financial-crime-capabilities.json', 'capabilities.json'),
                                    ('compliance-financial-crime-migrations.json', 'migrations.json')]:
                source = ROOT / 'catalog' / catalog; destination = package / 'references' / target
                if check:
                    if not destination.exists() or destination.read_bytes() != source.read_bytes():
                        errors.append(target + ' differs from catalog')
                else:
                    destination.write_bytes(source.read_bytes())
        manifest = package / 'references/package-manifest.json'
        data = {'schema_version': 'portable-skill-package/1.0', 'skill': package.name,
                'runtime': {'python': '3.10+', 'mode': 'offline supplied JSON', 'source_authentication': False},
                'bundled_resources': {dst: expected['resources'][key] for dst, key in bundles.items()},
                'dependencies': {'other_skills': 'Separately installed; no runtime sibling imports',
                                 'enterprise': 'Institution sources, engines and authority services are unverified deployment dependencies'},
                'acceptance': 'Integrity and bounded method checks only; no professional or operational acceptance',
                'files': {str(p.relative_to(package)): digest(p) for p in sorted(package.rglob('*'))
                          if p.is_file() and p != manifest and '__pycache__' not in p.parts and p.name != '.DS_Store' and p.suffix != '.pyc'}}
        if check:
            if not manifest.exists() or manifest.read_text() != encoded(data):
                errors.append(rel + ' manifest drifted')
        else:
            manifest.write_text(encoded(data))
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true'); parser.add_argument('--update-lock', action='store_true')
    args = parser.parse_args()
    try:
        errors = run(args.check, args.update_lock)
    except (ValueError, OSError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(error)
    print('Compliance resources: ' + ('FAIL' if errors else 'PASS'))
    raise SystemExit(bool(errors))
