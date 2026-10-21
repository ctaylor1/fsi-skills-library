import os, subprocess, json
from pathlib import Path
root=Path('/tmp/insurance-p5-forward/parametric')
pkg=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance/parametric-trigger-reviewer')
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
summary=[]
for inp in sorted(root.glob('*.input.json')):
 name=inp.name.removesuffix('.input.json')
 record={'case':name}
 for stage,script,arg in [('input-validation','validate_input.py',inp),('native-output','calculate_or_transform.py',inp),('output-validation','validate_output.py',root/(name+'.native-output.json'))]:
  proc=subprocess.run(['python3',str(pkg/'scripts'/script),str(arg)],text=True,capture_output=True,env=env)
  (root/(name+'.'+stage+'.json')).write_text(proc.stdout)
  (root/(name+'.'+stage+'.stderr.txt')).write_text(proc.stderr)
  record[stage]={'exit_code':proc.returncode,'stdout_chars':len(proc.stdout),'stderr_chars':len(proc.stderr)}
  try: record[stage]['result']=json.loads(proc.stdout)
  except ValueError: record[stage]['stdout']=proc.stdout
 summary.append(record)
(root/'native-run-log.json').write_text(json.dumps(summary,indent=2)+'\n')
for rec in summary:
 print(json.dumps(rec))
