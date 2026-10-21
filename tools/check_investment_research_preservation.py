#!/usr/bin/env python3
"""Compare pre-edit source hashes; never treat the dirty Git diff as this task's patch."""
import argparse, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GLOBAL={
 'catalog/approved-overrides.json','catalog/provisional-additions.json',
 'catalog/skills-catalog.json','catalog/skills-catalog.csv',
 'catalog/asset-management-capabilities.json','catalog/asset-management-migrations.json',
 'catalog/investment-resource-lock.json','tools/resolve_skill.py',
 'tools/sync_investment_resources.py','tools/build_catalog_from_xlsx.py',
 'tools/build_asset_management_index.py','docs/asset-management/DISPOSITION.md',
 'tools/test_asset_management_research_phase1.py',
 'docs/asset-management/SUPPORT-MATRIX.md','README.md','STATUS.md',
 'skills/asset-management/asset-management-router/references/capabilities.json',
 'skills/asset-management/asset-management-router/references/migrations.json',
 'skills/asset-management/asset-management-router/references/package-manifest.json',
 'skills/investment-banking/financing-alternatives-calculator/SKILL.md',
 'skills/investment-banking/financing-alternatives-calculator/references/handoffs.md',
 'skills/investment-banking/financing-alternatives-calculator/references/package-manifest.json',
 'skills/investment-banking/market-window-readiness-pack/SKILL.md',
 'skills/investment-banking/market-window-readiness-pack/references/handoffs.md',
 'skills/investment-banking/market-window-readiness-pack/references/package-manifest.json',
}
OWNED=('skills/investment-research/','skills/data-ai-model-governance/document-version-comparator/',
       'skills/finance-operations/financials-normalizer/','shared/investment-research/',
       'docs/investment-research/')
def permitted(rel):
    return rel in GLOBAL or rel.startswith(OWNED) or rel.startswith('catalog/investment-research-') or rel.startswith('tools/test_ir_') or rel in {
        'tools/build_investment_research_index.py','tools/check_investment_research.py',
        'tools/check_investment_research_preservation.py','tools/run_investment_research_portable.py'}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(baseline):
    changed=[]; unchanged=0
    for rel,old in baseline['files'].items():
        p=ROOT/rel
        if p.is_file() and digest(p)==old: unchanged+=1
        else:changed.append({'path':rel,'state':'changed' if p.is_file() else 'removed','permitted':permitted(rel)})
    raw=subprocess.run(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT,capture_output=True,check=True).stdout.decode().split('\0')
    new=sorted({rel for rel in raw if rel and rel not in baseline['files'] and (ROOT/rel).is_file()})
    entries=[{'path':rel,'state':'new','permitted':permitted(rel)} for rel in new]
    unexpected=[r for r in changed+entries if not r['permitted']]
    return {'schema_version':'ir-preservation-evidence/1.0','baseline_head':baseline['head'],
        'baseline_files':len(baseline['files']),'unchanged_baseline_files':unchanged,
        'changed_baseline_files':changed,'new_files':entries,'unexpected_changes':unexpected,
        'passed':not unexpected,'scope':'Source bytes outside declared Phase 1 ownership; not attribution of pre-existing Git changes or professional acceptance'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('--report',type=Path);a=p.parse_args()
    report=audit(json.loads(a.baseline.read_text()))
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'changed_baseline_files','new_files'}},indent=2))
    raise SystemExit(not report['passed'])
