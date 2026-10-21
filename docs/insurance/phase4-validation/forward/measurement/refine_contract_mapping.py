import pathlib,json,copy,shutil
P=pathlib.Path('/tmp/insurance-p4-forward-measurement');A=P/'initial-run';A.mkdir(exist_ok=True)
for f in list(P.glob('*-input.json'))+list(P.glob('*-output*'))+list(P.glob('*-input-validation*'))+[P/'commands.json']:
 shutil.copy2(f,A/f.name)
supp={'fictional':True,'source':'SUP-1','version':'1','date':'2026-09-19','owner':'Elena Moss','scope':'Newly supplied fictional sandbox evidence for contract-disambiguation rerun, not a correction of the initial raw packet','operations_accruals':{'E2':{'cost':8,'human_minutes':10},'E5':{'cost':4,'human_minutes':5}},'automation_controls':[
 ['human-review','Elena Moss','Require examiner acceptance before transfer','4/4 drafts waited for examiner; no adjudication performed','passed'],
 ['privacy','Jo Lane','Inspect all supplied packet fields','4/4 deidentified; no production records','passed'],
 ['permission-scope','Noah Vale','Attempt access outside sandbox draft scope','0/3 out-of-scope writes permitted','passed'],
 ['failure-recovery','Noah Vale','Interrupt after request before receipt; reconcile token before replay','One retained draft; manual route visible for every interrupted case','passed'],
 ['auditability','Mira Chen','Join request, response and examiner receipt by token','4/4 have complete trace','passed'],
 ['evaluation-quality','Ada Soto','Independent review of all eight paired outputs','All four paired error labels reconciled; fixed replay order documented','passed']],
 'design_proposal':{'owner':'Mira Chen','version':'1','date':'2026-09-19','scope':'Proposed interface contracts only; purpose reviewed for fictional sandbox; no deployment authorized','payload':'token, captured_at, supplied_fields, missing_fields; deidentified only','auth':'Mutual service identity; sandbox draft-create only','transport':'TLS and managed at-rest encryption','timeout_seconds':5,'max_attempts':3,'delivery':'at-least-once','idempotency_key':'intake-token','receipt':'one draft ID matching token','failure':'Stop producer on unknown receipt; examiner reconciles before replay','approval_owner':'Elena Moss'}}
(P/'supplemental-evidence.json').write_text(json.dumps(supp,indent=2)+'\n')
src={'source_ref':'SUP-1','version':'1','as_of':'2026-09-19','locator':'supplemental-evidence.json','owner':'Elena Moss'}
for kind in ['architecture','automation','data','operations']:
 for variant in ['complete','imperfect']:
  f=P/f'{kind}-{variant}-input.json';q=json.loads(f.read_text());q['data']['profile']=q.pop('profile');d=q['data']
  if kind in ['architecture','automation','operations']:q['sources'].append(src)
  if kind=='architecture':
   for interface in d['interfaces']:interface['operation']='proposed-write';interface['source_refs']=['SUP-1']
   for c in d['components']:c['source_refs'].append('SUP-1')
  if kind=='automation':
   d['requested_mode']='assist'
   d['controls'] += [dict(control_id=cid,owner=owner,test=test,actual=actual,status=status,source_refs=['SUP-1']) for cid,owner,test,actual,status in supp['automation_controls']]
  if kind=='data':
   if variant=='complete':(P/'data-unknown-projection-input.json').write_text(json.dumps(q,indent=2)+'\n')
   d['projection']=None
  if kind=='operations':
   if variant=='complete':(P/'operations-unknown-open-cost-input.json').write_text(json.dumps(q,indent=2)+'\n')
   for e in d['episodes']:
    if e['episode_id'] in supp['operations_accruals']:
     e.update(supp['operations_accruals'][e['episode_id']]);e['source_refs'].append('SUP-1')
  f.write_text(json.dumps(q,indent=2)+'\n')
