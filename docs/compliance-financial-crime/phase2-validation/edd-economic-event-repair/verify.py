from pathlib import Path
import json,hashlib,subprocess,sys,shlex,time
R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library'); P=R/'skills/compliance-financial-crime/enhanced-due-diligence-assessor'; F=R/'docs/compliance-financial-crime/phase2-validation/forward/edd-duplicated-economic-event'; evidence={'evals':[],'replays':[]}; logs=[]
for ev in json.loads((P/'evals/evals.json').read_text())['evals']:
 if 'command' not in ev: continue
 start=time.monotonic(); result=subprocess.run(shlex.split(ev['command']),cwd=P,capture_output=True,text=True,timeout=30); joined=result.stdout+result.stderr; good=result.returncode==ev.get('expect_exit',0) and all(x in joined for x in ev.get('expect_contains',[])); evidence['evals'].append({'id':ev['id'],'command':ev['command'],'expected_exit':ev.get('expect_exit',0),'actual_exit':result.returncode,'passed':good,'elapsed_seconds':round(time.monotonic()-start,4)}); logs.append(ev['id']+'\n'+joined)
 if not good: print(ev['id'],joined);raise SystemExit(1)
for stem,inputname,outputname in [('original-withheld','input.initial.json','output.repaired-original.json'),('amended-events','input.amended-event-identity.json','output.amended-event-identity.json')]:
 for name,cmd in [('validate_input',[sys.executable,'-B',str(P/'scripts/validate_input.py'),str(F/inputname)]),('validate_output',[sys.executable,'-B',str(P/'scripts/validate_output.py'),str(F/outputname),'--input',str(F/inputname)])]:
  result=subprocess.run(cmd,capture_output=True,text=True,timeout=30); evidence['replays'].append({'case':stem,'step':name,'exit':result.returncode});logs.append(stem+' '+name+'\n'+result.stdout+result.stderr)
  if result.returncode: print(result.stdout,result.stderr);raise SystemExit(1)
 original=json.loads((F/inputname).read_text()); output=json.loads((F/outputname).read_text()); reviews=output['results']['wealth_funds_assessments']
 if stem=='original-withheld':
  assert all(r['corroborated_amount'] is None and r['difference'] is None for r in reviews)
 else:
  assert reviews[0]['corroborated_amount']=='375000.00' and reviews[0]['difference']=='0.00'
  assert reviews[0]['economic_event_aggregation']['unique_event_count']==2
  assert reviews[0]['corroboration'][2]['counting_status']=='duplicate-document-not-additional-funds'
  assert reviews[1]['corroborated_amount']=='900000.00' and reviews[1]['difference']=='300000.00'
 assert output['results']['residual_risk']['band']=='Unknown'; assert not output['action_taken']; assert output['execution']=='not_performed'
oldout=subprocess.run([sys.executable,'-B',str(P/'scripts/validate_output.py'),str(F/'output.initial.json'),'--input',str(F/'input.initial.json')],capture_output=True,text=True);assert oldout.returncode==1;evidence['old_initial_output_rejected_by_repaired_method']=True;logs.append('frozen old output rejection\n'+oldout.stdout+oldout.stderr)
frozen=json.loads((R/'docs/compliance-financial-crime/phase2-validation/edd-economic-event-repair/initial-forward-hashes.json').read_text()); mismatches=[name for name,sha in frozen.items() if hashlib.sha256((R/name).read_bytes()).hexdigest()!=sha];assert not mismatches;evidence['frozen_original_artifacts_unchanged']=len(frozen)
archive=R/'docs/compliance-financial-crime/phase2-validation/initial-implementation/enhanced-due-diligence-assessor';manifest=json.loads((archive/'sha256-manifest.json').read_text());assert all(hashlib.sha256((archive/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in manifest['files']);ash=json.loads((archive/'archive-sha256.json').read_text());assert hashlib.sha256((R/ash['archive']).read_bytes()).hexdigest()==ash['sha256'];evidence['initial_archive_sha256']=ash['sha256']
skills=['financial-crime-case-investigator','sanctions-exposure-reviewer','financial-crime-information-sharing-reviewer','financial-crime-reporting-reviewer','compliance-regulatory-notification-reviewer','customer-due-diligence-reviewer','enhanced-due-diligence-assessor'];evidence['schema_hashes']={s:hashlib.sha256((R/'skills/compliance-financial-crime'/s/'references/input-schema.json').read_bytes()).hexdigest() for s in skills}
Path('/tmp/edd-repair-verification.json').write_text(json.dumps(evidence,indent=2)+'\n');Path('/tmp/edd-repair-verification.log').write_text('\n'.join(logs));print(json.dumps({'edd_executable_evals':len(evidence['evals']),'passed':sum(r['passed'] for r in evidence['evals']),'old_output_rejected':True,'frozen_artifacts_unchanged':len(frozen),'replay_assertions':'original totals withheld; amended375000 plus900000 wealth, no extra completion proceeds, residualUnknown'},indent=2))
