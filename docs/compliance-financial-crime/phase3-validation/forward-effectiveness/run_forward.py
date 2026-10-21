from pathlib import Path
import json,subprocess,sys
base=Path('/tmp/cfc-phase3-forward-effectiveness')
root=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime')
commands=[]
for path in sorted(base.glob('M2-*.json'))+sorted(base.glob('T2-*.json')):
 package='transaction-monitoring-effectiveness-reviewer' if path.name.startswith('M2') else 'financial-crime-case-quality-reviewer'
 command=[sys.executable,'-B',str(root/package/'scripts/calculate_or_transform.py'),str(path)]
 proc=subprocess.run(command,capture_output=True,text=True,cwd=base)
 output=base/(path.stem+'-result.json')
 if proc.returncode==0:output.write_text(proc.stdout)
 (base/(path.stem+'-stderr.txt')).write_text(proc.stderr)
 entry={'input':path.name,'package':package,'command':command,'actual_exit':proc.returncode}
 if proc.returncode==0:
  valid_command=[sys.executable,'-B',str(root/package/'scripts/validate_output.py'),str(output),'--input',str(path)]
  valid=subprocess.run(valid_command,capture_output=True,text=True,cwd=base)
  (base/(path.stem+'-validation.json')).write_text(valid.stdout)
  entry.update(validation_command=valid_command,validation_exit=valid.returncode)
 commands.append(entry)
(base/'commands-and-exits.json').write_text(json.dumps(commands,indent=2)+'\n')
for name in ['M2-original','T2-original']:
 output=base/(name+'-result.json')
 if output.exists():
  result=json.loads(output.read_text())
  print(name,json.dumps({'results':{k:v for k,v in result['results'].items() if not isinstance(v,list) and k not in ['scope','selection','criteria','operations','mandate']},'issues':result['unresolved_issues']},indent=2))
 else:print(name,(base/(name+'-stderr.txt')).read_text())
print('exits',json.dumps([{k:v for k,v in e.items() if k in ['input','actual_exit','validation_exit']} for e in commands]))
