from pathlib import Path
import json,hashlib,datetime,subprocess,shlex
ROOT=Path('/tmp/insurance-p3-forward-analytics'); REPO=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library'); PY='/tmp/fsi-p0-venv/bin/python'
runlabel='initial'; rec=[];hashes={}
for p in sorted(ROOT.glob('insurance-*')):
 if not p.is_dir():continue
 skill=REPO/'skills/insurance'/p.name
 for f in sorted(skill.rglob('*')):
  if f.is_file() and 'evals' not in f.parts and not f.name.startswith('test_') and '__pycache__' not in f.parts:hashes[str(f.relative_to(REPO))]=hashlib.sha256(f.read_bytes()).hexdigest()
 rd=p/runlabel;rd.mkdir(exist_ok=True)
 for phase,script,inputfile in [('input','validate_input.py',p/'native-input.json'),('calculate','calculate_or_transform.py',p/'native-input.json'),('output','validate_output.py',rd/'result.json')]:
  argv=[PY,str(skill/'scripts'/script),str(inputfile)]; start=datetime.datetime.now(datetime.timezone.utc).isoformat();x=subprocess.run(argv,capture_output=True,text=True,cwd=REPO)
  (rd/f'{phase}.stdout').write_text(x.stdout);(rd/f'{phase}.stderr').write_text(x.stderr)
  rec.append({'skill':p.name,'phase':phase,'command':shlex.join(argv),'argv':argv,'cwd':str(REPO),'started_at_utc':start,'exit':x.returncode,'stdout':str(rd/f'{phase}.stdout'),'stderr':str(rd/f'{phase}.stderr')})
  if phase=='calculate' and x.returncode==0:(rd/'result.json').write_text(x.stdout)
  print(p.name,phase,'exit',x.returncode)
  if x.returncode!=0:print(x.stdout[:3000],x.stderr[:3000]);break
(ROOT/'initial-executions.json').write_text(json.dumps(rec,indent=2)+'\n');(ROOT/'initial-exact-commands.txt').write_text('\n'.join(a['command']+'\nexit='+str(a['exit']) for a in rec)+'\n');(ROOT/'initial-source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
