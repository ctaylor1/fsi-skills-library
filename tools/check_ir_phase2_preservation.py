#!/usr/bin/env python3
"""Audit Phase 2 against its pre-edit source baseline; preserve Phase 1 evidence."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GLOBALS={
 'README.md','STATUS.md','catalog/approved-overrides.json','catalog/provisional-additions.json',
 'catalog/skills-catalog.json','catalog/skills-catalog.csv','catalog/investment-resource-lock.json',
 'catalog/asset-management-capabilities.json','catalog/asset-management-migrations.json',
 'docs/asset-management/DISPOSITION.md','docs/asset-management/SUPPORT-MATRIX.md',
 'tools/build_investment_research_index.py','tools/check_investment_research.py','tools/sync_investment_resources.py',
 'tools/review_ir_handoff.py','tools/check_ir_phase2_preservation.py',
 'docs/investment-research/README.md','docs/investment-research/migration.md','docs/investment-research/support-matrix.md',
 'skills/asset-management/asset-management-router/references/capabilities.json',
 'skills/asset-management/asset-management-router/references/migrations.json',
 'skills/asset-management/asset-management-router/references/package-manifest.json',
 'skills/data-ai-model-governance/document-version-comparator/references/evidence-standard.md',
 'skills/data-ai-model-governance/document-version-comparator/references/package-manifest.json',
 'skills/finance-operations/financials-normalizer/references/evidence-standard.md',
 'skills/finance-operations/financials-normalizer/references/package-manifest.json'}
def permitted(rel):
    return rel in GLOBALS or rel.startswith(('skills/investment-research/','shared/investment-research/',
       'catalog/investment-research-','tools/test_ir_','docs/investment-research/phase2-'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(baseline):
    changes=[];same=0;archive=[]
    oldprefix='skills/investment-research/model-roll-forward-auditor/'
    for rel,digest in baseline['files'].items():
        p=ROOT/rel
        if p.is_file() and sha(p)==digest:same+=1
        else:changes.append({'path':rel,'state':'changed' if p.is_file() else 'removed','permitted':permitted(rel)})
        if rel.startswith(oldprefix):
            saved=ROOT/'docs/investment-research/phase2-validation/legacy-auditor'/rel[len(oldprefix):]
            archive.append({'path':rel,'preserved_in_archive':saved.is_file() and sha(saved)==digest})
    current=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    new=[{'path':p,'permitted':permitted(p)} for p in sorted(set(current)) if p and p not in baseline['files'] and (ROOT/p).is_file()]
    unexpected=[r for r in changes+new if not r['permitted']]
    badarchive=[r for r in archive if not r['preserved_in_archive']]
    return {'schema_version':'ir-phase2-preservation/1.0','baseline_head':baseline['head'],'baseline_files':len(baseline['files']),
      'unchanged_baseline_files':same,'changes':changes,'new_files':new,'unexpected_changes':unexpected,
      'retired_source_archive':archive,'archive_failures':badarchive,'phase1_evidence_untouched':not any(r['path'].startswith('docs/investment-research/phase1-') for r in changes),
      'passed':not unexpected and not badarchive,'scope':'Source-byte preservation outside explicit Phase 2 ownership; no attribution of pre-existing Git changes or professional acceptance'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('--report',type=Path);a=p.parse_args();r=audit(json.loads(a.baseline.read_text()))
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ('changes','new_files','retired_source_archive')},indent=2));raise SystemExit(not r['passed'])
