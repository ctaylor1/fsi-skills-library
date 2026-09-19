import json, copy, os, subprocess, hashlib
from pathlib import Path
R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/payments');O=Path('/tmp/payments-phase2-forward-lifecycle');P='/tmp/fsi-p0-venv/bin/python';ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
RUNS=[]
def save(n,v):
 p=O/(n+'.json');p.write_text(json.dumps(v,indent=2)+'\n');return p
def run(n,skill,d,phase1=False):
 inp=save(n+'-input',d);entry={'scenario':n,'skill':skill,'input_sha256':hashlib.sha256(inp.read_bytes()).hexdigest(),'commands':[]}
 result=None
 for mode in ['validate_input','calculate_or_transform','validate_output']:
  if mode=='validate_output' and result is None:continue
  args=[P,'-B',str(R/skill/'scripts'/(mode+'.py')),str(inp if mode!='validate_output' else O/(n+'-output.json'))]
  if mode=='validate_output' and not phase1:args+=['--input',str(inp)]
  p=subprocess.run(args,env=ENV,cwd=O,text=True,capture_output=True)
  (O/(n+'-'+mode+'.stdout')).write_text(p.stdout);(O/(n+'-'+mode+'.stderr')).write_text(p.stderr)
  entry['commands'].append({'command':args,'exit_code':p.returncode,'stdout_file':n+'-'+mode+'.stdout','stderr':p.stderr})
  if mode=='calculate_or_transform':
   try:result=json.loads(p.stdout)
   except ValueError:continue
   if p.returncode==0:save(n+'-output',result)
   else:result=None
 RUNS.append(entry)
 if result:print(n, 'STATUS',result.get('status'), 'FINDINGS',[f['code'] for f in result.get('findings',[])], 'REVIEW',result.get('result',{}).get('review'))
 else:print(n,'CLI FAILURE',entry)
 return result
def env(n,data,j='US',participant='bank'):
 ids=['requirements','access','timing','funding','costs','instruction','intent','screen','account','policy','batch','auth','mandate','delegation','outcome','history','service','card-profile']
 return {'schema_version':'1.0','request_id':n,'as_of':'2026-09-18','jurisdiction':j,'participant':participant,'requested_action':'draft','sources':[{'source_id':i,'reference':'synthetic:'+n+':'+i,'as_of':'2026-09-18','review_due':'2026-10-01'} for i in ids],'upstream_issues':[],'data':data}
def active(s):return {'effective_from':'2026-09-01','effective_until':'2026-09-30','revoked':False,'source_ids':[s]}
