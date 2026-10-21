import pathlib,json,subprocess
O=pathlib.Path('/tmp/fsi-final-wealth-acceptance');R=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');P='/tmp/fsi-p0-venv/bin/python'
d=json.loads((O/'planning-request.json').read_text()); monetary={'balance','reserved_amount','target_amount','monthly_contribution','amount','monthly_reserve_contribution','monthly_amount','minimum_monthly_payment','additional_monthly_payment'}
def convert(x):
 if isinstance(x,dict): return {k:int(float(v)) if k in monetary and isinstance(v,str) else convert(v) for k,v in x.items()}
 if isinstance(x,list): return [convert(v) for v in x]
 return x
d=convert(d);(O/'planning-request.json').write_text(json.dumps(d,indent=2)+'\n')
log=json.loads((O/'invocations.json').read_text())
for script,inp,out in [('validate_input.py','planning-request.json','planning-input-validation.json'),('calculate_or_transform.py','planning-request.json','planning-output.json'),('validate_output.py','planning-output.json','planning-output-validation.json')]:
 cmd=[P,'-B',str(R/'skills/wealth-management/household-financial-planning-assistant/scripts'/script),str(O/inp)];p=subprocess.run(cmd,capture_output=True,text=True);(O/out).write_text(p.stdout);(O/(out+'.stderr')).write_text(p.stderr);log.append({'argv':cmd,'exit_code':p.returncode,'stdout_file':out,'stderr_file':out+'.stderr'});(O/'invocations.json').write_text(json.dumps(log,indent=2)+'\n')
 if p.returncode: raise SystemExit(p.stdout+p.stderr)
p=json.loads((O/'planning-output.json').read_text());print(json.dumps({k:v for k,v in p.items() if k not in ['input_snapshot','sources']},indent=2))
