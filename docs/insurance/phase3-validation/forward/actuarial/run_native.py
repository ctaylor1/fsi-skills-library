import json,subprocess,os,datetime,hashlib
from pathlib import Path
ROOT=Path('/tmp/insurance-p3-forward-actuarial');REPO=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');PY='/tmp/fsi-p0-venv/bin/python'
idx=json.loads((ROOT/'case_index.json').read_text()); summary={}
for slug,o in idx.items():
 folder=Path(o['folder']);cwd=REPO/'skills/insurance'/o['skill'];input_path=folder/'native_input.json'; commands=[]
 for step,script,arg in [('validate_input','validate_input.py',input_path),('calculate','calculate_or_transform.py',input_path),('validate_output','validate_output.py',folder/'output.json')]:
  cmd=[PY,str(cwd/'scripts'/script),str(arg)];start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  (folder/(step+'.stdout.txt')).write_text(p.stdout);(folder/(step+'.stderr.txt')).write_text(p.stderr)
  if step=='calculate':(folder/'output.json').write_text(p.stdout)
  commands.append({'command':cmd,'cwd':str(cwd),'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'started_utc':start,'exit_code':p.returncode,'stdout_path':str(folder/(step+'.stdout.txt')),'stderr_path':str(folder/(step+'.stderr.txt'))})
 (folder/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 try:
  output=json.loads((folder/'output.json').read_text());summary[slug]={'exits':[x['exit_code'] for x in commands],'status':output.get('status'),'findings':output.get('findings'),'results':output.get('results')}
 except Exception:summary[slug]={'exits':[x['exit_code'] for x in commands],'calculate_stderr':(folder/'calculate.stderr.txt').read_text(),'validate_input_stdout':(folder/'validate_input.stdout.txt').read_text()}
(ROOT/'initial_run_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
