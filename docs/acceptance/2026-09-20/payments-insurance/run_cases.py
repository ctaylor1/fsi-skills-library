from pathlib import Path
import json, subprocess, os
root=Path.cwd(); out=Path('/tmp/fsi-final-existing-acceptance'); results=[]
py='/tmp/fsi-p0-venv/bin/python'
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
for case,package in [('payment-earlier-shortfall','payments/payment-liquidity-and-funding-analyzer'),('claim-settled-versus-repeat','insurance/claim-payment-closure-reviewer'),('capital-invalid-stress-denominator','insurance/insurance-capital-solvency-analyzer')]:
 inp=out/'cases'/f'{case}.json'; output=out/f'{case}.output.json'; prefix=root/'skills'/package/'scripts'
 for kind in ['validate_input','calculate_or_transform','validate_output']:
  argv=[py,'-B',str(prefix/f'{kind}.py'),str(output if kind=='validate_output' else inp)]
  if kind=='validate_output' and package.startswith('payments/'): argv+=['--input',str(inp)]
  p=subprocess.run(argv,capture_output=True,text=True,cwd=root,env=env)
  results.append({'case':case,'kind':kind,'argv':argv,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
  if kind=='calculate_or_transform':output.write_text(p.stdout)
  print(case,kind,p.returncode,p.stdout[:250].replace('\n',' '),p.stderr[:250].replace('\n',' '))
(out/'commands.json').write_text(json.dumps(results,indent=2)+'\n')
