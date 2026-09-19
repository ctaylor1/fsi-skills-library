from pathlib import Path
import hashlib,json,subprocess
P=Path('/tmp/insurance-p2-forward-life/life-annuity-contract-service-reviewer');R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance/life-annuity-contract-service-reviewer');PY='/tmp/fsi-p0-venv/bin/python'
raw='''# Synthetic valuation supplement SV-22-V2, version 1; dated 2026-09-18
## valuation-confirmation
For separate forward-evaluation variant only: carrier valuation extract confirms contract AN-22 USD account value 180,000 at 2026-09-18. Original source packet remains unchanged. All other original contract identities, request, deductions and consent inventory remain as originally supplied.
'''
(P/'same-day-source.md').write_text(raw)
d=json.loads((P/'input.json').read_text());d['case_id']='SV-22-SAME-DAY';ref='same-day-source.md#valuation-confirmation';d['sources'].append(dict(source_ref=ref,version='1',as_of='2026-09-18',sha256=hashlib.sha256(raw.encode()).hexdigest()));d['data']['contract']['value_date']='2026-09-18';d['data']['contract']['source_ref']=ref
(P/'same-day-input.json').write_text(json.dumps(d,indent=2)+'\n')
commands=[]
for script,inp,out in [('validate_input.py','same-day-input.json','same-day-input-validation.json'),('calculate_or_transform.py','same-day-input.json','same-day-actual-output.json'),('validate_output.py','same-day-actual-output.json','same-day-output-validation.json')]:
 cmd=[PY,str(R/'scripts'/script),str(P/inp)];cp=subprocess.run(cmd,text=True,capture_output=True,cwd=R)
 (P/out).write_text(cp.stdout);(P/(out+'.stderr')).write_text(cp.stderr);commands.append(dict(command=cmd,returncode=cp.returncode,stdout_file=out,stderr_file=out+'.stderr'))
(P/'same-day-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
print(json.dumps(json.loads((P/'same-day-actual-output.json').read_text())['results'],indent=2))
