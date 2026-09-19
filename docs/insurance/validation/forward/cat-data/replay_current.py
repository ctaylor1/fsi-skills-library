from pathlib import Path
import hashlib,json,shlex,shutil,subprocess
ROOT=Path('/tmp/insurance-cat-data-forward-20260918')
REPO=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
PYTHON='/tmp/fsi-p0-venv/bin/python'
AFTER=ROOT/'after';AFTER.mkdir(exist_ok=True)
def save(p,doc):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(doc,indent=2)+'\n')
def run(argv,cwd=None):
 p=subprocess.run(argv,cwd=cwd,text=True,capture_output=True)
 return {'argv':argv,'cwd':str(cwd) if cwd else None,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
records=[]
for original in sorted((ROOT/'runs').iterdir()):
 package='catastrophe-exposure-monitor' if original.name.startswith('cat_') else 'insurance-data-reconciler'
 scripts=REPO/'skills/insurance'/package/'scripts'
 folder=AFTER/'runs'/original.name;folder.mkdir(parents=True,exist_ok=True)
 for name in ['input.json','raw-request.txt']:shutil.copyfile(original/name,folder/name)
 assert (original/'input.json').read_bytes()==(folder/'input.json').read_bytes()
 stages=[]
 for script,file in [('validate_input.py','input.json'),('calculate_or_transform.py','input.json'),('validate_output.py','output.json')]:
  result=run([PYTHON,str(scripts/script),str(folder/file)])
  save(folder/(script+'.result.json'),result);stages.append(result['exit_code'])
  if script=='calculate_or_transform.py' and result['exit_code']==0:(folder/'output.json').write_text(result['stdout'])
 argv=[PYTHON,'-c','import json,sys; from validate_output import validate; p=json.load(open(sys.argv[1])); d=json.load(open(sys.argv[2])); errors=validate(p,d); print(json.dumps({"errors":errors})); raise SystemExit(bool(errors))',str(folder/'output.json'),str(folder/'input.json')]
 result=run(argv,cwd=scripts);save(folder/'validate_with_original_input.result.json',result);stages.append(result['exit_code'])
 output=json.loads((folder/'output.json').read_text())
 before=json.loads((original/'output.json').read_text())
 fields=['completeness','evaluability','confidence','dedup','overall_severity','break_counts','checks','unresolved_issues']
 records.append({'name':original.name,'input_sha256':hashlib.sha256((folder/'input.json').read_bytes()).hexdigest(),'input_unchanged':True,'validation_exit_codes':stages,'before':{k:before[k] for k in fields if k in before},'after':{k:output[k] for k in fields if k in output}})
save(AFTER/'summary.json',records)
assert all(r['validation_exit_codes']==[0,0,0,0] for r in records)
manifest=[]
for name in ['catastrophe-exposure-monitor','insurance-data-reconciler']:
 package=REPO/'skills/insurance'/name
 for item in json.loads((package/'evals/evals.json').read_text())['evals']:
  if 'command' not in item:continue
  argv=shlex.split(item['command']);argv[0]=PYTHON
  result=run(argv,cwd=package)
  result.update(package=name,id=item['id'],expected_exit=item['expect_exit'])
  result['passed']=result['exit_code']==item['expect_exit'] and all(part in result['stdout']+result['stderr'] for part in item.get('expect_contains',[]))
  manifest.append(result)
save(AFTER/'package-evaluations.json',manifest)
assert all(r['passed'] for r in manifest)
hashes={}
for name in ['catastrophe-exposure-monitor','insurance-data-reconciler']:
 for p in (REPO/'skills/insurance'/name).rglob('*'):
  if p.is_file() and p.suffix in {'.py','.md','.json'}:hashes[str(p.relative_to(REPO))]=hashlib.sha256(p.read_bytes()).hexdigest()
save(AFTER/'current-package-hashes.json',hashes)
print(json.dumps({'forward_cases':len(records),'forward_command_stages':sum(len(r['validation_exit_codes']) for r in records),'unchanged_input_files':len(records),'package_command_evaluations':len(manifest),'all_passed':True},indent=2))
