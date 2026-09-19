import json, os, subprocess, copy, hashlib
from pathlib import Path
ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/payments')
OUT=Path('/tmp/payments-forward-money')
PY='/tmp/fsi-p0-venv/bin/python'
ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
checks=json.loads((OUT/'command-results.json').read_text())
def save(name,obj):
 p=OUT/(name+'.json');p.write_text(json.dumps(obj,indent=2)+'\n');return p
def call(name,skill,script,*args):
 cmd=[PY,'-B',str(ROOT/skill/'scripts'/script),*map(str,args)]
 p=subprocess.run(cmd,text=True,capture_output=True,env=ENV,cwd=OUT)
 (OUT/(name+'.stdout')).write_text(p.stdout);(OUT/(name+'.stderr')).write_text(p.stderr)
 checks.append({'name':name,'command':cmd,'exit_code':p.returncode,'stdout':p.stdout if len(p.stdout)<4000 else f'see {name}.stdout','stderr':p.stderr})
 return p
def sequence(name,skill,doc):
 inp=save(name+'-input',doc);call(name+'-validate-input',skill,'validate_input.py',inp)
 calc=call(name+'-calculate',skill,'calculate_or_transform.py',inp);result=json.loads(calc.stdout)
 out=save(name+'-output',result)
 args=[out]+(['--input',inp] if skill=='payment-transaction-reconciler' else [])
 call(name+'-validate-output',skill,'validate_output.py',*args);return result
identity=json.loads((OUT/'s4-reused-source-identity-input.json').read_text())
for rec in identity['records']:rec['amount']='100.00'
result=sequence('s4-reused-identity-all-equal','payment-transaction-reconciler',identity)
print('reused identity all equal:',result['summary'],result['partition_totals'])
# User supplied a revised independent value check and a new scoped screening disposition.
repair=json.loads((OUT/'s2-changed-value-stale-screening-input.json').read_text())
repair['evidence']['verification_source']='synthetic:authorized-analyst-verification:new-beneficiary-BIC-COBADEFF'
repair['screening']['disposition_id']='SYNTH-SCR-4472'
repair['screening']['source_ref']='synthetic:screening:SYNTH-SCR-4472'
repair['screening']['screened_at']='2026-07-16T14:50:00Z'
save('s2-refreshed-binding-candidate',repair)
cmd=[PY,'-B','-c',"import sys,json;sys.path.insert(0,sys.argv[1]);from validate_input import repair_binding;print(repair_binding(json.load(open(sys.argv[2]))))",str(ROOT/'payment-repair-planner/scripts'),str(OUT/'s2-refreshed-binding-candidate.json')]
repair['screening']['repair_binding']=subprocess.check_output(cmd,text=True,env=ENV,cwd=OUT).strip()
newplan=sequence('s2-new-value-fresh-scope','payment-repair-planner',repair)
oldplan=json.loads((OUT/'s2-scoped-repair-output.json').read_text())
print('revised plan:',{k:newplan[k] for k in ['plan_id','status','approval','execution','exact_change']})
assert newplan['plan_hash']!=oldplan['plan_hash'] and newplan['plan_id']!=oldplan['plan_id']
# Final current-source validation of every produced output, including bad mutations.
for output in sorted(OUT.glob('*-output.json')):
 name=output.name.removesuffix('-output.json')
 skill='payment-lifecycle-diagnoser' if name.startswith('s1') else 'payment-repair-planner' if name.startswith('s2') else 'payment-settlement-reconciler' if name.startswith('s3') else 'payment-transaction-reconciler'
 args=[output]+(['--input',OUT/(name+'-input.json')] if name.startswith(('s3','s4')) else [])
 p=call(name+'-final-validate-output',skill,'validate_output.py',*args)
 print(name,'final native output validation',p.returncode)
skills=['payment-lifecycle-diagnoser','payment-repair-planner','payment-settlement-reconciler','payment-transaction-reconciler']
after={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for s in skills for p in (ROOT/s).rglob('*') if p.is_file() and p.suffix in ('.py','.md')}
before=json.loads((OUT/'source-hashes-before.json').read_text())
changed=[k for k in set(before)|set(after) if before.get(k)!=after.get(k)]
save('source-hashes-final',after);save('command-results',checks)
print('source files changed since run:',changed)
