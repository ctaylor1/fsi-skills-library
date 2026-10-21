#!/usr/bin/env python3
"""Audit Phase 3 against its original source-byte baseline and exact write scope."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NEW_PACKAGES={'financial-model-update-preparer','corporate-event-impact-reviewer','research-quality-reviewer'}
GLOBALS={
 'README.md','STATUS.md','catalog/approved-overrides.json','catalog/provisional-additions.json',
 'catalog/skills-catalog.json','catalog/skills-catalog.csv','catalog/investment-resource-lock.json',
 'catalog/investment-research-capabilities.json','catalog/investment-research-phase3-capabilities.json',
 'catalog/investment-research-routes.json','catalog/investment-research-adapters.json',
 'shared/investment-research/reviewed_handoffs.py','shared/investment-research/evidence-standard.md','tools/review_ir_handoff.py',
 'tools/check_investment_research.py','tools/sync_investment_resources.py','tools/check_ir_phase3_preservation.py',
 'tools/test_ir_phase1.py','tools/test_ir_model_updates_phase3.py','tools/test_ir_corporate_events_phase3.py',
 'tools/test_ir_research_quality_phase3.py','tools/test_ir_adapters_phase3.py',
 'docs/investment-research/README.md','docs/investment-research/migration.md',
 'docs/investment-research/support-matrix.md','docs/investment-research/phase3-implementation.md',
 'skills/investment-research/README.md'}
# Existing methods receive only the canonical evidence reference and its pin.
# Their computation code, fixtures and prior validation evidence are outside scope.
_catalog=json.loads((ROOT/'catalog/investment-research-capabilities.json').read_text())
for _row in _catalog['capabilities']+_catalog['shared_owners']:
    if _row.get('support_status')!='planned':
        GLOBALS.update({_row['path']+'/references/'+name for name in ('evidence-standard.md','package-manifest.json')})
def permitted(rel):
    return rel in GLOBALS or rel.startswith('docs/investment-research/phase3-validation/') or any(
        rel.startswith('skills/investment-research/'+name+'/') for name in NEW_PACKAGES|{'investment-research-router'})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(baseline):
    changes=[];same=0
    for rel,digest in baseline['files'].items():
        p=ROOT/rel
        if p.is_file() and sha(p)==digest:same+=1
        else:changes.append({'path':rel,'state':'changed' if p.is_file() else 'removed','permitted':permitted(rel)})
    current=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    new=[{'path':p,'permitted':permitted(p)} for p in sorted(set(current)) if p and p not in baseline['files'] and (ROOT/p).is_file()]
    unexpected=[r for r in changes+new if not r['permitted']]
    evidence_unchanged=not any(r['path'].startswith(('docs/investment-research/phase1-','docs/investment-research/phase2-')) for r in changes)
    return {'schema_version':'ir-phase3-preservation/1.0','baseline_head':baseline['head'],'baseline_files':len(baseline['files']),
      'unchanged_baseline_files':same,'changes':changes,'new_files':new,'unexpected_changes':unexpected,
      'prior_phase_evidence_untouched':evidence_unchanged,'passed':not unexpected and evidence_unchanged,
      'scope':'Source bytes outside explicitly declared Phase 3 ownership; pre-existing Git changes are not attributed to this phase'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('--report',type=Path);a=p.parse_args();r=audit(json.loads(a.baseline.read_text()))
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ('changes','new_files')},indent=2));raise SystemExit(not r['passed'])
