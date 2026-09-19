import json, subprocess, os
from pathlib import Path
root=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');out=root/'docs/payments/phase3-validation';python='/tmp/fsi-p0-venv/bin/python'
commands={
'payments_structure':[python,'-B','tools/validate_skills.py','skills/payments','skills/cybersecurity-operational-resilience/pci-dss-evidence-assistant'],
'repository_structure':[python,'-B','tools/validate_skills.py'],
'payments_handoffs':[python,'-B','tools/check_handoffs.py','skills/payments','skills/cybersecurity-operational-resilience/pci-dss-evidence-assistant'],
'repository_handoffs':[python,'-B','tools/check_handoffs.py'],
'payments_routes_migrations':[python,'-B','tools/check_payment_handoffs.py'],
'contract_sync':[python,'-B','tools/sync_payment_contract.py','--check'],
'foundation_sync':[python,'-B','tools/sync_payment_foundation.py','--check'],
'whitespace':['git','diff','--check'],
}
results={}
for name,cmd in commands.items():
 r=subprocess.run(cmd,cwd=root,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 results[name]={'command':cmd,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 print(name,r.returncode,r.stdout[-450:],r.stderr[-450:])
(out/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
