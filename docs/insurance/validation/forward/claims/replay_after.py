import collections, copy, hashlib, json, os, pathlib, subprocess, sys
ROOT=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
BASE=pathlib.Path('/tmp/insurance-claims-forward-20260918'); OUT=BASE/'after';OUT.mkdir(exist_ok=True)
PY='/tmp/fsi-p0-venv/bin/python'; ENV={**os.environ,'PATH':'/tmp/fsi-p0-venv/bin:'+os.environ['PATH'],'PYTHONDONTWRITEBYTECODE':'1'}
manifest=[]
def write(name,text): (OUT/name).write_text(json.dumps(text,indent=2)+'\n' if not isinstance(text,str) else text)
def run(label,cmd,stdout,cwd=ROOT):
 p=subprocess.run(cmd,capture_output=True,text=True,cwd=cwd,env=ENV)
 write(stdout,p.stdout);write(stdout+'.stderr.txt',p.stderr)
 manifest.append({'label':label,'command':cmd,'cwd':str(cwd),'exit_code':p.returncode,'stdout':stdout,'stderr':stdout+'.stderr.txt'})
 return p
# Golden refresh is confined to the two owned packages and their existing valid outputs.
for pkg,inp,out in [('claims-triage-assistant','claims_example.json','triage_example.json'),('claims-triage-assistant','claims_nondefault_config.json','triage_nondefault_config.json'),('subrogation-opportunity-screener','claim_example.json','screening_example.json')]:
 scripts=ROOT/'skills/insurance'/pkg/'scripts'; fixtures=scripts.parent/'evals/files'
 p=run('regenerate owned golden '+pkg+'/'+out,[PY,str(scripts/'calculate_or_transform.py'),str(fixtures/inp)],'golden-'+out)
 if p.returncode:raise RuntimeError(p.stderr)
 (fixtures/out).write_text(p.stdout)
for cid,pkg in [('01-urgent-unknown-liability','claims-triage-assistant'),('02-quoted-contrary-evidence','liability-evidence-matrix-builder'),('03-unknown-waiver-economics','subrogation-opportunity-screener'),('03b-explicit-null-amounts','subrogation-opportunity-screener'),('04-receipt-incomplete-package','claim-intake-preparer')]:
 src=BASE/(cid+'.native.json');scripts=ROOT/'skills/insurance'/pkg/'scripts'
 run(cid+' input validation',[PY,str(scripts/'validate_input.py'),str(src)],cid+'.input-validation.txt')
 result=run(cid+' calculation',[PY,str(scripts/'calculate_or_transform.py'),str(src)],cid+'.output.json')
 if result.returncode==0:
  run(cid+' output validation',[PY,str(scripts/'validate_output.py'),str(OUT/(cid+'.output.json'))],cid+'.output-validation.txt')
  code='import json,sys;sys.path.insert(0,sys.argv[1]);from insurance_contract import validate_artifact;d=json.load(open(sys.argv[2]));o=json.load(open(sys.argv[3]));errors=validate_artifact(o["artifact"],input_doc=d,output=o);print(json.dumps(errors));sys.exit(bool(errors))'
  run(cid+' source-bound artifact validation',[PY,'-c',code,str(scripts),str(src),str(OUT/(cid+'.output.json'))],cid+'.source-bound-validation.txt')
for pkg in ('claims-triage-assistant','subrogation-opportunity-screener'):
 run(pkg+' focused regression',[PY,str(ROOT/'skills/insurance'/pkg/'scripts/test_phase1.py')],pkg+'.regressions.txt')
 run(pkg+' generic skill structure',[PY,'/Users/taylor/.codex/skills/.system/skill-creator/scripts/quick_validate.py',str(ROOT/'skills/insurance'/pkg)],pkg+'.generic-structure.txt')
run('owned repository structural validation',[PY,str(ROOT/'tools/validate_skills.py'),'skills/insurance/claims-triage-assistant','skills/insurance/subrogation-opportunity-screener'],'owned-structural.txt')
run('owned executable evaluations',[PY,str(ROOT/'tools/run_selftests.py'),'skills/insurance/claims-triage-assistant','skills/insurance/subrogation-opportunity-screener'],'owned-executable-evals.txt')
run('owned defect-focused lint',['/tmp/fsi-p0-venv/bin/ruff','check','--select','F,E9','skills/insurance/claims-triage-assistant/scripts','skills/insurance/subrogation-opportunity-screener/scripts'],'owned-lint-defects.txt')
# Measure strict lint against saved source, without changing inherited diagnostics.
current=run('strict lint current',['/tmp/fsi-p0-venv/bin/ruff','check','--output-format','json','skills/insurance/claims-triage-assistant/scripts','skills/insurance/subrogation-opportunity-screener/scripts'],'strict-lint-current.json')
before=run('strict lint before',['/tmp/fsi-p0-venv/bin/ruff','check','--config',str(ROOT/'ruff.toml'),'--output-format','json',str(BASE/'source-before/claims-triage-assistant/scripts'),str(BASE/'source-before/subrogation-opportunity-screener/scripts')],'strict-lint-before.json')
def key(v):
 parts=pathlib.Path(v['filename']).parts
 return ('/'.join(parts[-3:]),v['code'],v['message'])
old=collections.Counter(key(d) for d in json.loads(before.stdout));new=collections.Counter(key(d) for d in json.loads(current.stdout))
write('strict-lint-delta.json',{'before_count':sum(old.values()),'after_count':sum(new.values()),'introduced':[{'diagnostic':k,'count':v} for k,v in (new-old).items()]})
# Replay unchanged installed-inventory requests saved before repair, plus rederive inventory.
installed=sorted(p.parent.name for p in (ROOT/'skills/insurance').glob('*/SKILL.md'));write('installed-insurance-inventory.json',installed)
for p in sorted((BASE/'router-after').glob('*.request.json')):
 req=json.loads(p.read_text());assert req['available_skills']==installed
 cid=p.name.removesuffix('.request.json')
 run('final route replay '+cid,[PY,str(ROOT/'skills/insurance/insurance-router/scripts/route.py'),str(p)],cid+'.route.json')
 run('final route validation '+cid,[PY,str(ROOT/'skills/insurance/insurance-router/scripts/route.py'),'--validate',str(OUT/(cid+'.route.json'))],cid+'.route-validation.txt')
write('native-input-hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(BASE.glob('*.native.json'))})
write('source-hashes-after.json',{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for pkg in ['claims-triage-assistant','subrogation-opportunity-screener','liability-evidence-matrix-builder','claim-intake-preparer','insurance-router'] for p in sorted((ROOT/'skills/insurance'/pkg).rglob('*')) if p.is_file() and '__pycache__' not in p.parts})
write('execution-manifest.json',manifest)
print(json.dumps([{'label':m['label'],'exit_code':m['exit_code']} for m in manifest],indent=2))
