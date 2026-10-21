#!/usr/bin/env python3
"""Bundle pinned investment resources and portable package manifests.

Use --update-lock deliberately after reviewing canonical changes; --check writes nothing.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
LOCK=REPO/'catalog/investment-resource-lock.json'
SOURCES={
 'specialist-contract':('shared/asset-management/specialist_contract.py','1.0'),
 'specialist-engine-contract':('shared/asset-management/specialist-engine-contract.md','1.0'),
 'native-integrity':('shared/investment-data/native_integrity.py','1.0.0'),
 'research-runtime':('shared/investment-research/research_runtime.py','1.1.0'),
 'research-analysis-contract':('shared/investment-research/analysis_contract.py','2.0.0'),
 'research-reviewed-handoffs':('shared/investment-research/reviewed_handoffs.py','1.3.0'),
 'research-handoff-cli':('tools/review_ir_handoff.py','1.3.0'),
 'research-evidence-standard':('shared/investment-research/evidence-standard.md','1.2.0'),
 'research-records-schema':('shared/investment-research/research-records.schema.json','1.0.0'),
 'investment-contract':('shared/asset-management/investment_contract.py','1.0'),
 'workflow-contract':('shared/workflow-review/workflow_contract.py','1.0'),
 'insurance-legacy-contract':('shared/insurance/insurance_contract.py','1.0'),
 'engine-contract':('shared/investment-analytics/engine-contract.md','1.0'),
 'foundation-contract':('shared/asset-management/foundation_contract.py','1.0'),
 'portfolio-math':('shared/investment-analytics/portfolio_math.py','1.0'),
 'performance-math':('shared/investment-analytics/performance_math.py','1.0'),
 'business-evidence':('shared/asset-management/business_evidence.py','1.0'),
 'modernization-contract':('shared/asset-management/modernization_contract.py','1.0'),
 'licensed-data-connector':('shared/asset-management/licensed_data_connector.py','1.0'),
 'gateway-contract':('shared/asset-management/gateway-contract.md','1.0'),
 'workflow-foundation':('shared/workflow-review/workflow_foundation.py','1.0'),
 'design-support':('shared/workflow-review/design_support.py','1.0'),
 'shared-architecture':('skills/enterprise-functions-technology/solution-architecture-planner/scripts/domain.py','0.1.0'),
 'shared-data-value':('skills/data-ai-model-governance/data-product-value-evaluator/scripts/domain.py','0.1.0'),
 'shared-operations':('skills/finance-operations/operations-performance-analyzer/scripts/domain.py','0.1.0'),
 'shared-automation':('skills/enterprise-functions-technology/workflow-automation-assessor/scripts/domain.py','0.1.0'),
}

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def encoded(value):return json.dumps(value,indent=2,ensure_ascii=False)+'\n'

def run(check=False,update_lock=False):
    expected={'schema_version':'investment-resource-lock/1.0','resources':{
        key:{'source':path,'version':version,'sha256':digest(REPO/path),'license':'MIT'}
        for key,(path,version) in SOURCES.items()}}
    if update_lock:
        if check:raise ValueError('--check cannot update the lock')
        LOCK.write_text(encoded(expected))
    if not LOCK.exists() or json.loads(LOCK.read_text())!=expected:
        raise ValueError('canonical resource differs from reviewed lock; review and use --update-lock')
    migrations=json.loads((REPO/'catalog/asset-management-migrations.json').read_text())['migrations']
    phase2=json.loads((REPO/'catalog/asset-management-phase2-capabilities.json').read_text())
    foundation_names=set(phase2['new_packages'])|set(phase2['expanded_packages'])
    phase3=json.loads((REPO/'catalog/asset-management-phase3-capabilities.json').read_text())
    modernization_names=set(phase3['new_packages'])
    phase4=json.loads((REPO/'catalog/asset-management-phase4-capabilities.json').read_text())
    specialist_names=set(phase4['new_packages'])|set(phase4['expanded_packages'])
    foundation_names |= modernization_names | specialist_names
    foundation_paths={'skills/asset-management/'+name for name in foundation_names}
    paths=sorted({r['new_path'] for r in migrations}|foundation_paths|{'skills/asset-management/asset-management-router'})
    ir=json.loads((REPO/'catalog/investment-research-capabilities.json').read_text())
    ir_paths={r['path'] for r in ir['capabilities'] if r['support_status']!='planned'}
    ir_paths |= {r['path'] for r in ir['retained_legacy']+ir['shared_owners']}
    paths=sorted(set(paths)|ir_paths)
    adapter_path=REPO/'catalog/investment-research-adapters.json'
    if ir.get('phase') in {'phase2','phase3','phase4'}:
        routes_path=REPO/'catalog/investment-research-routes.json'
        routes=json.loads(routes_path.read_text())
        declared=json.loads(adapter_path.read_text())['adapters']
        if routes.get('reviewed_adapters')!=declared:
            if check:raise ValueError('route adapter projection differs from reviewed registry')
            routes['reviewed_adapters']=declared;routes_path.write_text(encoded(routes))
    am_paths={r['new_path'] for r in migrations if r['old_path'].startswith('skills/asset-management/')}
    errors=[]
    for rel in paths:
        package=REPO/rel
        if not (package/'SKILL.md').exists():
            errors.append('missing migrated package: '+rel);continue
        bundles={}
        if rel in am_paths or rel in foundation_paths or package.name=='asset-management-router':
            bundles={'scripts/native_integrity.py':'native-integrity','references/engine-contract.md':'engine-contract'}
        if rel in ir_paths:
            bundles.update({'scripts/native_integrity.py':'native-integrity',
                            'references/evidence-standard.md':'research-evidence-standard'})
        if rel in ir_paths and ((package/'scripts/phase2_domain.py').exists() or package.name in {r['name'] for r in ir['capabilities'] if r['support_status']!='planned' and r['roadmap_phase'] in {2,3,4}}):
            bundles.update({'scripts/analysis_contract.py':'research-analysis-contract',
                            'scripts/research_runtime.py':'research-runtime'})
        if package.name in {'investment-research-router','research-evidence-dossier-builder'}:
            bundles.update({'scripts/research_runtime.py':'research-runtime',
                            'references/research-records.schema.json':'research-records-schema'})
            if package.name=='investment-research-router':
                if ir.get('phase') in {'phase2','phase3','phase4'}:
                    bundles.update({'scripts/analysis_contract.py':'research-analysis-contract',
                                    'scripts/reviewed_handoffs.py':'research-reviewed-handoffs',
                                    'scripts/review_handoff.py':'research-handoff-cli'})
                copies=[('investment-research-capabilities.json','capabilities.json'),('investment-research-routes.json','routes.json')]
                if ir.get('phase') in {'phase2','phase3','phase4'}:copies.append(('investment-research-adapters.json','adapters.json'))
                for src,dst in copies:
                    target=package/'references'/dst
                    if check:
                        if not target.exists() or target.read_bytes()!=(REPO/'catalog'/src).read_bytes(): errors.append(rel+'/'+dst+' differs')
                    else: target.write_bytes((REPO/'catalog'/src).read_bytes())
        if rel in foundation_paths:
            bundles['scripts/foundation_contract.py']='foundation-contract'
        if package.name in specialist_names:
            bundles['scripts/specialist_contract.py']='specialist-contract'
        if package.name in {'portfolio-hedge-reviewer','portfolio-performance-attributor','etf-operations-reviewer'}:
            bundles.update({'scripts/specialist_contract.py':'specialist-contract','references/specialist-engine-contract.md':'specialist-engine-contract'})
        if package.name in modernization_names:
            bundles.update({'scripts/modernization_contract.py':'modernization-contract',
                            'scripts/workflow_contract.py':'workflow-contract',
                            'scripts/workflow_foundation.py':'workflow-foundation',
                            'scripts/design_support.py':'design-support',
                            'scripts/insurance_contract.py':'insurance-legacy-contract',
                            'references/gateway-contract.md':'gateway-contract'})
            owners={'solution-architecture-planner':'architecture','data-product-value-evaluator':'data-value',
                    'operations-performance-analyzer':'operations','workflow-automation-assessor':'automation'}
            for owner in phase3['new_packages'][package.name]['shared_owners']:
                key=owners[owner]
                bundles['scripts/shared_'+key.replace('-','_')+'.py']='shared-'+key
            if package.name=='investment-data-architecture-planner':
                bundles['scripts/licensed_data_connector.py']='licensed-data-connector'
        if package.name in {'asset-allocation-planner','portfolio-construction-analyzer'}:
            bundles['scripts/portfolio_math.py']='portfolio-math'
        if package.name in {'portfolio-performance-measurer','private-fund-performance-analyzer'}:
            bundles['scripts/performance_math.py']='performance-math'
        if package.name in {'asset-manager-economics-analyzer','investment-product-lifecycle-planner','investment-distribution-planner','investment-client-service-preparer','investment-investor-report-builder','institutional-proposal-responder','investment-manager-due-diligence-reviewer','investment-committee-memo-builder'}:
            bundles['scripts/business_evidence.py']='business-evidence'
        if package.name=='asset-management-router':
            bundles.update({'scripts/investment_contract.py':'investment-contract',
                            'scripts/workflow_contract.py':'workflow-contract',
                            'scripts/insurance_contract.py':'insurance-legacy-contract'})
        for dst,key in bundles.items():
            source=REPO/SOURCES[key][0];target=package/dst
            if check:
                if not target.exists() or target.read_bytes()!=source.read_bytes(): errors.append(rel+'/'+dst+' differs from canonical source')
            else:
                target.parent.mkdir(exist_ok=True);target.write_bytes(source.read_bytes())
        manifest=package/'references/package-manifest.json'
        files={str(p.relative_to(package)):digest(p) for p in sorted(package.rglob('*'))
               if p.is_file() and p!=manifest and '__pycache__' not in p.parts and p.name!='.DS_Store' and p.suffix!='.pyc'}
        data={'schema_version':'portable-skill-package/1.0','skill':package.name,
              'runtime':{'python':'3.10+','local_mode':'offline supplied JSON','source_authentication':False},
              'bundled_resources':{dst:expected['resources'][key] for dst,key in bundles.items()},
              'dependencies':{'other_skills':'Declared handoffs; separately installed, never launched by this manifest',
                              'enterprise_services':'Deployment-specific source/engine/approval services; no live connectors bundled'},
              'acceptance':'Package integrity and portability only; not professional acceptance','files':files}
        if package.name=='investment-data-architecture-planner':
            data['runtime']['optional_gateway_mode']='Explicit CLI read against an independently approved/provisioned HTTPS gateway; credential supplied only through environment'
            data['dependencies']['enterprise_services']='Institution-provisioned investment-data-gateway/1.0 service; identity, entitlement and license policy independently administered; no vendor credentials or live gateway bundled'
        if check:
            if not manifest.exists() or manifest.read_text()!=encoded(data):errors.append(rel+' package manifest differs')
        else:
            manifest.parent.mkdir(exist_ok=True);manifest.write_text(encoded(data))
    router=REPO/'skills/asset-management/asset-management-router/references'
    for source,name in [('catalog/asset-management-capabilities.json','capabilities.json'),('catalog/asset-management-migrations.json','migrations.json')]:
        target=router/name
        if check:
            if target.read_bytes()!=(REPO/source).read_bytes():errors.append(name+' differs from catalog')
        elif target.read_bytes()!=(REPO/source).read_bytes():
            target.write_bytes((REPO/source).read_bytes())
            # Manifest changes on a subsequent deterministic pass.
            return run(check=False,update_lock=False)
    return errors

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');parser.add_argument('--update-lock',action='store_true');args=parser.parse_args()
    try: errors=run(args.check,args.update_lock)
    except (ValueError,OSError) as exc: errors=[str(exc)]
    for error in errors:print(error)
    print('Investment resources: '+('FAIL' if errors else 'PASS'))
    raise SystemExit(bool(errors))
