import json,hashlib,datetime,subprocess,os
from pathlib import Path
root=Path('/tmp/insurance-p3-forward-actuarial');repo=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');idx=json.loads((root/'case_index.json').read_text());summary={}
for slug in ['experience','reinsurance','close']:
 base=root/slug;f=base/'mapped_v2';f.mkdir(exist_ok=True);d=json.loads((base/'native_input.json').read_text())
 if slug=='experience':
  for r in d['data']['exposures']:
   if r['exit_reason']=='death':r['exit_reason']='event'
  changes=['exposures R1/R4 exit_reason death -> event; event_type remains death. Source dates/counts unchanged.']
 elif slug=='reinsurance':
  d['context']['capacity']='assuming_reinsurer';d['data']['terms'].update(trigger_basis='losses_occurring',loss_measure='ultimate_loss_including_lae',inuring_basis='net_of_scheduled_inuring')
  for s in d['data']['scenarios']:
   for r in s['events']:r.update(loss_measure='ultimate_loss_including_lae',inuring_basis='net_of_scheduled_inuring')
  changes=['capacity semantic alias mapped to assuming_reinsurer; public hyphenated labels mapped to executable underscore enums. No business terms/numbers changed.']
 else:d['data']['profile']['sign_convention']='debit-positive';changes=['Duplicate existing PROFILE raw debit-positive assertion into data.profile.sign_convention, which executable requires but public native-schema omits.']
 (f/'native_input.json').write_text(json.dumps(d,indent=2)+'\n');(f/'mapping_change.json').write_text(json.dumps({'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'changes':changes,'unchanged_raw_sha256':hashlib.sha256((base/'raw_sources.json').read_bytes()).hexdigest(),'new_native_sha256':hashlib.sha256((f/'native_input.json').read_bytes()).hexdigest(),'initial_native_unchanged_sha256':hashlib.sha256((base/'native_input.json').read_bytes()).hexdigest(),'implementation_inspected':'Only enum/support guard snippets in domain.py after original freeze and first run.'},indent=2)+'\n')
 cwd=repo/'skills/insurance'/idx[slug]['skill'];commands=[]
 for step,script,arg in [('validate_input','validate_input.py',f/'native_input.json'),('calculate','calculate_or_transform.py',f/'native_input.json'),('validate_output','validate_output.py',f/'output.json')]:
  cmd=['/tmp/fsi-p0-venv/bin/python',str(cwd/'scripts'/script),str(arg)];p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'});(f/(step+'.stdout.txt')).write_text(p.stdout);(f/(step+'.stderr.txt')).write_text(p.stderr)
  if step=='calculate':(f/'output.json').write_text(p.stdout)
  commands.append({'command':cmd,'cwd':str(cwd),'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'exit_code':p.returncode,'stdout_path':str(f/(step+'.stdout.txt')),'stderr_path':str(f/(step+'.stderr.txt'))})
 (f/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');out=json.loads((f/'output.json').read_text());summary[slug]={'exits':[r['exit_code'] for r in commands],'status':out['status'],'findings':out['findings'],'results':out['results']}
(root/'mapped_run_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
