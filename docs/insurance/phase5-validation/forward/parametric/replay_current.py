import json,subprocess,os
from pathlib import Path
r=Path('/tmp/insurance-p5-forward/parametric')
pkg=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance/parametric-trigger-reviewer')
cases=[('06-clarified-text-revisions','10-current-normal'),('07-preliminary-old-final-text-revisions','11-current-old-final'),('08-preliminary-terminal-text-revisions','12-current-preliminary-terminal'),('09-fallback-clarified-text-revisions','13-current-fallback-conflict')]
log=[]
for src,name in cases:
 x=json.loads((r/(src+'.input.json')).read_text());x['case_id']=name;x['context']['capacity']='parametric-claims-review'
 inp=r/(name+'.input.json');inp.write_text(json.dumps(x,indent=2)+'\n')
 rec={'case':name,'replayed_from':src,'capacity_mapping':'parametric-claims-review'}
 for stage,script,arg in [('input-validation','validate_input.py',inp),('native-output','calculate_or_transform.py',inp),('output-validation','validate_output.py',r/(name+'.native-output.json'))]:
  p=subprocess.run(['python3',str(pkg/'scripts'/script),str(arg)],text=True,capture_output=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  (r/(name+'.'+stage+'.json')).write_text(p.stdout);(r/(name+'.'+stage+'.stderr.txt')).write_text(p.stderr)
  rec[stage]={'exit_code':p.returncode,'result':json.loads(p.stdout)}
 log.append(rec)
(r/'current-runtime-replay-log.json').write_text(json.dumps(log,indent=2)+'\n')
for rec in log:
 for stage in ['input-validation','native-output','output-validation']:assert rec[stage]['exit_code']==0
 for stage in ['input-validation','output-validation']:assert rec[stage]['result']['valid'] is True
 x=rec['native-output']['result']
 print(json.dumps({'case':rec['case'],'status':x['status'],'findings':x['findings'],'results':x['results']}))
 if rec['case']=='10-current-normal':
  assert x['status']=='ready-for-review' and x['results']['provisional_unpaid_scenario']=='30000'
 else:
  assert x['status']=='needs-data'
  assert all(x['results'][k] is None for k in ['index_value','matched_tier_id','gross_event_scenario','current_event_recorded_paid','aggregate_remaining','provisional_unpaid_scenario'])
 assert x['action_taken'] is False and x['human_review_required'] is True and x['results']['payment_authorized'] is False
