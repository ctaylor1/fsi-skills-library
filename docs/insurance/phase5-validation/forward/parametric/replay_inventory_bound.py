import json,subprocess,os
from pathlib import Path
r=Path('/tmp/insurance-p5-forward/parametric')
pkg=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance/parametric-trigger-reviewer')
cases=[('10-current-normal','14-inventory-bound-normal'),('11-current-old-final','15-inventory-bound-old-final'),('12-current-preliminary-terminal','16-inventory-bound-preliminary-terminal'),('13-current-fallback-conflict','17-inventory-bound-fallback-conflict')]
log=[]
for src,name in cases:
 x=json.loads((r/(src+'.input.json')).read_text());x['case_id']=name
 x['data']['inventory']={
  'contract_id':'P-77','event_id':'E-77','aggregate_period_id':'A26',
  'reading_statement':'Complete reading inventory.',
  'ledger_statement':'Complete reconciled annual paid ledger: older event15000 asofSep30, E77 paid10000 asofOct3, same contract/currency/A26.',
  'locator':'fictional signed packet — review-packet v2 dated Oct3; explicit complete reading inventory and complete reconciled annual paid ledger statements from supplied exercise',
  'source_refs':['review-packet']}
 inp=r/(name+'.input.json');inp.write_text(json.dumps(x,indent=2)+'\n')
 rec={'case':name,'replayed_from':src,'inventory_mapping':'Verbatim supplied completeness statements; source-bound P-77/E-77/A26 object.'}
 for stage,script,arg in [('input-validation','validate_input.py',inp),('native-output','calculate_or_transform.py',inp),('output-validation','validate_output.py',r/(name+'.native-output.json'))]:
  p=subprocess.run(['python3',str(pkg/'scripts'/script),str(arg)],text=True,capture_output=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  (r/(name+'.'+stage+'.json')).write_text(p.stdout);(r/(name+'.'+stage+'.stderr.txt')).write_text(p.stderr)
  rec[stage]={'exit_code':p.returncode,'result':json.loads(p.stdout)}
 log.append(rec)
(r/'inventory-bound-replay-log.json').write_text(json.dumps(log,indent=2)+'\n')
for rec in log:
 for stage in ['input-validation','native-output','output-validation']:assert rec[stage]['exit_code']==0
 for stage in ['input-validation','output-validation']:assert rec[stage]['result']['valid'] is True
 x=rec['native-output']['result']
 print(json.dumps({'case':rec['case'],'status':x['status'],'findings':x['findings'],'results':x['results']}))
 if rec['case']=='14-inventory-bound-normal':
  assert x['status']=='ready-for-review' and not x['findings']
  assert x['results']['index_value']=='110'
  assert x['results']['gross_event_scenario']=='40000'
  assert x['results']['current_event_recorded_paid']=='10000'
  assert x['results']['aggregate_remaining']=='75000'
  assert x['results']['provisional_unpaid_scenario']=='30000'
 else:
  code={'15-inventory-bound-old-final':'terminal-reading','16-inventory-bound-preliminary-terminal':'finality','17-inventory-bound-fallback-conflict':'contrary-primary'}[rec['case']]
  assert x['status']=='needs-data' and [f['code'] for f in x['findings']]==[code]
  assert all(x['results'][k] is None for k in ['index_value','matched_tier_id','gross_event_scenario','current_event_recorded_paid','aggregate_remaining','provisional_unpaid_scenario'])
 assert x['action_taken'] is False and x['human_review_required'] is True and x['results']['payment_authorized'] is False
 assert x['approval']=='not_requested' and x['execution']=='not_performed'
 assert x['results']['verifier_authenticated'] is False and x['results']['physical_loss_estimated'] is False
 assert x['results']['coverage_determination']=='not_performed'
 assert x['source_document']['data']['inventory']['contract_id']=='P-77'
 assert x['source_document']['data']['inventory']['event_id']=='E-77'
 assert x['source_document']['data']['inventory']['aggregate_period_id']=='A26'
