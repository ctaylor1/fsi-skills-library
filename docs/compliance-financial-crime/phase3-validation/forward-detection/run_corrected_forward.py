from pathlib import Path
import json,subprocess,sys,hashlib
ROOT=Path('/tmp/cfc-phase3-forward-detection');REPO=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');cases=json.loads((ROOT/'before-corrected-run-expectations.json').read_text())['cases'];results=[]
packages={c['skill']:REPO/'skills/compliance-financial-crime'/c['skill'] for c in cases}
def hashes():return {str(f):hashlib.sha256(f.read_bytes()).hexdigest() for p in packages.values() for f in p.rglob('*') if f.is_file()}
before=hashes();(ROOT/'packages-corrected-before-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
for case in cases:
 package=packages[case['skill']];input_path=ROOT/case['input'];args=[sys.executable,'-B',str(package/'scripts/calculate_or_transform.py'),str(input_path)]
 run=subprocess.run(args,cwd=ROOT,capture_output=True,text=True);(ROOT/(case['id']+'.stdout')).write_text(run.stdout);(ROOT/(case['id']+'.stderr')).write_text(run.stderr)
 item={'id':case['id'],'expectation':case['independent_expectation'],'command':args,'cwd':str(ROOT),'exit_code':run.returncode,'stderr':run.stderr,'output_file':case['id']+'.stdout'}
 if run.returncode==0:
  output=json.loads(run.stdout);result=output['results'];item['status']=output['status'];item['result_keys']=list(result);item['issues']=output['unresolved_issues'];output_path=ROOT/(case['id']+'.output.json');output_path.write_text(json.dumps(output,indent=2)+'\n')
  checkargs=[sys.executable,'-B',str(package/'scripts/validate_output.py'),str(output_path),'--input',str(input_path)];check=subprocess.run(checkargs,cwd=ROOT,capture_output=True,text=True);item['detached_validation']={'command':checkargs,'exit_code':check.returncode,'output':check.stdout+check.stderr}
  if case['id'].startswith('s3'):
   item['summary']={k:v for k,v in result.items() if k in ('within_supplied_review_criteria','measured_sample_confusion_counts','measured_confusion_counts','false_positive_rate','false_negative_rate','operational_effectiveness','match_identity_disposition','independent_assurance') or ('count' in k and 'test' not in k)}
   item['overall_comparison']=result.get('within_supplied_review_criteria')
  else:
   item['summary']={k:result.get(k) for k in ('proposal_prerequisites_consistent','proposed_engine_configuration','material_blockers','activation','identity_resolution','backtest_executed','holdout_executed')}
   item['overall_comparison']=result.get('proposal_prerequisites_consistent')
  item['action_controls']={k:output.get(k) for k in ('draft','human_review_required','action_taken','approval','execution','source_truth')}
  expect=case['independent_expectation']
  item['expectation_matched']= (expect=='measured-subset-and-no-professional-acceptance' and item['overall_comparison'] is True) or (expect=='proposal-draft-no-execution' and item['overall_comparison'] is True) or (expect in ('overall-withheld','proposal-withheld') and item['overall_comparison'] is None if case['id'].startswith('s3') else expect=='proposal-withheld' and result.get('proposed_engine_configuration') is None) or (expect=='criterion-false' and item['overall_comparison'] is False) or (expect=='overall-withheld-or-false' and item['overall_comparison'] is not True)
  if expect=='intake-stops':item['expectation_matched']=False
  item['expectation_matched']=bool(item['expectation_matched']) and check.returncode==0 and output['action_taken'] is False and output['human_review_required'] is True
 else:item['expectation_matched']=case['independent_expectation']=='intake-stops'
 results.append(item)
 print(case['id'],run.returncode,item.get('overall_comparison'),'matched' if item['expectation_matched'] else 'REVIEW')
after=hashes();changed=[f for f in set(before)|set(after) if before.get(f)!=after.get(f)]
(ROOT/'corrected-result.json').write_text(json.dumps({'evaluations':results,'total':len(results),'matched':sum(r['expectation_matched'] for r in results),'changed_reviewed_package_files':changed,'limits':'Independent synthetic forward scenarios only; not practitioner acceptance or source authentication'},indent=2)+'\n')
