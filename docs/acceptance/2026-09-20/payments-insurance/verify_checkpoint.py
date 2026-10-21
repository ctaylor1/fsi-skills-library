import os,json,subprocess
from pathlib import Path
out=Path('/tmp/fsi-final-existing-acceptance'); root=Path.cwd(); py='/tmp/fsi-p0-venv/bin/python'; env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH='tools')
commands=[['git','branch','--show-current'],[py,'-B','tools/sync_payment_contract.py','--check'],[py,'-B','tools/sync_payment_foundation.py','--check'],[py,'-B','-m','unittest','tools.test_insurance_phase1.InsuranceIntegration.test_spec_cards_reproduce_insurance_metadata','-v'],[py,'-B','tools/run_insurance_phase2_forward.py','--output',str(out/'insurance-phase2-replay')]]
results=[]
for argv in commands:
 p=subprocess.run(argv,capture_output=True,text=True,cwd=root,env=env);results.append({'argv':argv,'cwd':str(root),'env_overrides':{'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':'tools'},'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}); print(argv[-1],p.returncode,p.stdout[:500],p.stderr[:500])
(out/'checkpoint-commands.json').write_text(json.dumps(results,indent=2)+'\n')
