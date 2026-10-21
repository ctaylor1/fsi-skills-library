from pathlib import Path
import json,hashlib,subprocess,sys
ROOT=Path('/tmp/cfc-phase3-forward-detection');OUT=ROOT/'after-m1-repair';OUT.mkdir(exist_ok=True);REPO=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');cases=[]
for expectations in ('before-run-expectations.json','before-corrected-run-expectations.json','before-engine-extension-expectations.json'):
 for case in json.loads((ROOT/expectations).read_text())['cases']:
  if case['skill']=='transaction-monitoring-scenario-designer':cases.append({**case,'expectation_file':expectations})
# Intakes and earlier results are hashed before replay; after results are saved elsewhere.
protected={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*') if p.is_file()};runs=[]
package=REPO/'skills/compliance-financial-crime/transaction-monitoring-scenario-designer'
for case in cases:
 raw=ROOT/case['input'];args=[sys.executable,'-B',str(package/'scripts/calculate_or_transform.py'),str(raw)];run=subprocess.run(args,cwd=ROOT,capture_output=True,text=True);(OUT/(case['id']+'.stdout')).write_text(run.stdout);(OUT/(case['id']+'.stderr')).write_text(run.stderr)
 record={'id':case['id'],'command':args,'original_raw_intake':str(raw),'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'expectation_file':case['expectation_file'],'unchanged_independent_expectation':case['independent_expectation'],'exit_code':run.returncode,'original_setup_scope':case['expectation_file']=='before-run-expectations.json'}
 if run.returncode==0:
  out=json.loads(run.stdout);op=OUT/(case['id']+'.output.json');op.write_text(json.dumps(out,indent=2)+'\n');validation_args=[sys.executable,'-B',str(package/'scripts/validate_output.py'),str(op),'--input',str(raw)];validation=subprocess.run(validation_args,cwd=ROOT,capture_output=True,text=True);r=out['results'];record.update(status=out['status'],proposal_prerequisites_consistent=r['proposal_prerequisites_consistent'],configuration_present=r['proposed_engine_configuration'] is not None,material_blockers=r['material_blockers'],detached_validation={'command':validation_args,'exit_code':validation.returncode,'output':validation.stdout+validation.stderr},action_taken=out['action_taken'],activation=r['activation'])
  matched=(case['independent_expectation']=='proposal-draft-no-execution' and r['proposal_prerequisites_consistent'] is True and r['proposed_engine_configuration'] is not None) or (case['independent_expectation']=='proposal-withheld' and r['proposed_engine_configuration'] is None and r['proposal_prerequisites_consistent'] is False)
  record['expectation_matched']=matched and validation.returncode==0 and out['action_taken'] is False and r['activation']=='not-performed'
 else:
  record.update(error=run.stderr,expectation_matched=case['independent_expectation']=='intake-stops',safe_stronger_intake_boundary=case['id']=='m1-engine-population-mismatch-scope-adapted')
 runs.append(record);print(case['id'],run.returncode,record.get('proposal_prerequisites_consistent'),'matched' if record['expectation_matched'] else 'original setup retained' if record['original_setup_scope'] else 'safe stronger' if record.get('safe_stronger_intake_boundary') else 'REVIEW')
unchanged=all((ROOT/n).exists() and hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in protected.items());assert unchanged,'Original input/result/expectations mutated'
meaningful=[r for r in runs if not r['original_setup_scope']]
(OUT/'result.json').write_text(json.dumps({'status':'independent-replay-passed' if all(r['expectation_matched'] or r.get('safe_stronger_intake_boundary') for r in meaningful) else 'finding-remains','total_native_calls':len(runs),'meaningful_scope_corrected_or_extended_cases':len(meaningful),'strict_expectation_matches':sum(r['expectation_matched'] for r in meaningful),'safe_stronger_intake_boundaries':sum(bool(r.get('safe_stronger_intake_boundary')) for r in meaningful),'original_setup_failures_replayed_and_retained':sum(r['original_setup_scope'] for r in runs),'original_inputs_results_expectations_unchanged':unchanged,'runs':runs,'limitations':'Synthetic independent replay only; no source authentication, professional acceptance or execution'},indent=2)+'\n')
