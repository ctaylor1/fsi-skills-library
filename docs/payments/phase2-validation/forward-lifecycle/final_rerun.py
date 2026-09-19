import json,os,subprocess,hashlib
from pathlib import Path
R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/payments');O=Path('/tmp/payments-phase2-forward-lifecycle');P='/tmp/fsi-p0-venv/bin/python';ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
skills=['bank-payment-workflow-designer','payment-initiation-control-reviewer','payment-servicing-planner','payment-lifecycle-diagnoser','card-program-designer','card-lifecycle-operations-assistant']
def save(n,v):p=O/(n+'.json');p.write_text(json.dumps(v,indent=2)+'\n');return p
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes():return {str(p.relative_to(R)):sha(p) for s in skills for p in (R/s).rglob('*') if p.is_file() and p.suffix in ['.py','.md','.json'] and '/evals/' not in str(p) and p.name!='regression_tests.py'}
refs=[]
for name in ['command-results-bank','command-results-card']:
 for row in json.loads((O/(name+'.json')).read_text()):refs.append((row['scenario'],row['skill']))
refs.extend([('b15-exact-individual1250','payment-initiation-control-reviewer'),('b16-policy-expires-before-execution','payment-initiation-control-reviewer')])
input_hashes={n:sha(O/(n+'-input.json')) for n,s in refs}
before=hashes();save('source-hashes-final-before',before)
entries=[];summary=[]
for n,s in refs:
 inp=O/(n+'-input.json');entry={'scenario':n,'skill':s,'input_sha256':sha(inp),'commands':[]}
 result=None
 for mode in ['validate_input','calculate_or_transform','validate_output']:
  args=[P,'-B',str(R/s/'scripts'/(mode+'.py')),str(inp if mode!='validate_output' else O/('final-'+n+'-output.json'))]
  if mode=='validate_output' and s!='payment-lifecycle-diagnoser':args+=['--input',str(inp)]
  p=subprocess.run(args,env=ENV,cwd=O,text=True,capture_output=True)
  (O/('final-'+n+'-'+mode+'.stdout')).write_text(p.stdout);(O/('final-'+n+'-'+mode+'.stderr')).write_text(p.stderr)
  entry['commands'].append({'command':args,'exit_code':p.returncode,'stdout_file':'final-'+n+'-'+mode+'.stdout','stderr':p.stderr})
  if mode=='calculate_or_transform' and p.returncode==0:
   result=json.loads(p.stdout);save('final-'+n+'-output',result)
  if p.returncode!=0:break
 entries.append(entry)
 if result:summary.append({'scenario':n,'status':result.get('status'),'review':result.get('result',{}).get('review'),'findings':[f['code'] for f in result.get('findings',[])],'all_clis_pass':len(entry['commands'])==3 and all(c['exit_code']==0 for c in entry['commands'])})
 else:summary.append({'scenario':n,'calculation_failed':True,'commands':entry['commands']})
after=hashes();save('source-hashes-final-after',after);save('final-command-results',entries);save('final-result-summary',summary)
assert input_hashes=={n:sha(O/(n+'-input.json')) for n,s in refs},'input changed'
save('final-input-hashes',input_hashes)
print(json.dumps({'scenarios':len(refs),'native_cli_calls':sum(len(x['commands']) for x in entries),'source_changes':[k for k in set(before)|set(after) if before.get(k)!=after.get(k)],'summary':summary},indent=2))
