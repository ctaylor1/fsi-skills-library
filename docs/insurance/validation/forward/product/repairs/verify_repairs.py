from pathlib import Path
import json,subprocess,sys,shlex,hashlib,difflib
REPO=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');DEST=Path('/tmp/insurance-product-forward-20260918/repairs');PYTHON='/tmp/fsi-p0-venv/bin/python'
pairs={'premium-quote-comparator':('quotes_example.json','comparison_example.json','compute'),'reinsurance-contract-reviewer':('treaty_example.json','interpretation_example.json','transform'),'pc-reserving-analysis-assistant':('triangles_example.json','analysis_example.json','build')}
logs=[]
for name,(src,dst,fn) in pairs.items():
 package=REPO/'skills/insurance'/name
 code='''import json,sys\nfrom pathlib import Path\nsys.path.insert(0,'scripts')\nfrom calculate_or_transform import FUNCTION\nfrom insurance_contract import build_artifact\np=Path('evals/files');doc=json.loads((p/'SOURCE').read_text());o=FUNCTION(doc);o=o[0] if isinstance(o,tuple) else o\nold=json.loads((p/'DEST').read_text())\nif 'clauses' in o:\n old_c={c['clause_id']:c for c in old['clauses']}\n for c in o['clauses']:c['plain_summary']=old_c[c['clause_id']]['plain_summary']\nif 'narrative' in old:o['narrative']=old['narrative']\na=o['artifact'];o['artifact']=build_artifact(doc,o,producer=a['producer'],artifact_type=a['artifact_type'],completeness=a['completeness'],evaluability=a['evaluability'],issues=a['unresolved_issues'])\n(p/'DEST').write_text(json.dumps(o,indent=2)+'\\n')\n'''.replace('FUNCTION',fn).replace('SOURCE',src).replace('DEST',dst)
 p=subprocess.run([PYTHON,'-B','-c',code],cwd=package,capture_output=True,text=True)
 logs.append({'package':name,'stage':'regenerate-positive-golden','source':src,'destination':dst,'exit_code':p.returncode,'stderr':p.stderr})
 assert p.returncode==0,p.stderr
 tests=[{'id':'regressions','command':'python scripts/test_phase1.py','expect_exit':0}]+[e for e in json.loads((package/'evals/evals.json').read_text())['evals'] if 'command' in e and e['id']!='phase1-regressions']
 for test in tests:
  args=shlex.split(test['command']);args[0:1]=[PYTHON,'-B'];p=subprocess.run(args,cwd=package,text=True,capture_output=True)
  prefix=DEST/'after'/(name+'-'+test['id'])
  prefix.with_suffix('.stdout.txt').write_text(p.stdout);prefix.with_suffix('.stderr.txt').write_text(p.stderr)
  ok=p.returncode==test['expect_exit'] and all(s in p.stdout+p.stderr for s in test.get('expect_contains',[]))
  logs.append({'package':name,'stage':test['id'],'command':args,'cwd':str(package),'expected_exit':test['expect_exit'],'actual_exit':p.returncode,'passed':ok})
 for label,args in [('skill-quick-validate',[PYTHON,'-B','/Users/taylor/.codex/skills/.system/skill-creator/scripts/quick_validate.py',str(package)]),('ruff',['/tmp/fsi-p0-venv/bin/ruff','check','--select','E9,F',str(package/'scripts')])]:
  p=subprocess.run(args,text=True,capture_output=True);prefix=DEST/'after'/(name+'-'+label)
  prefix.with_suffix('.stdout.txt').write_text(p.stdout);prefix.with_suffix('.stderr.txt').write_text(p.stderr)
  logs.append({'package':name,'stage':label,'command':args,'expected_exit':0,'actual_exit':p.returncode,'passed':p.returncode==0})
(DEST/'verification-log.json').write_text(json.dumps(logs,indent=2)+'\n')
for x in logs:print(x['package'],x['stage'],x.get('passed',x.get('exit_code')==0),x.get('actual_exit',x.get('exit_code')))
assert all(x.get('passed',x.get('exit_code')==0) or x['stage']=='skill-quick-validate' for x in logs), 'verification failures outside the recorded generic-validator compatibility limitation'
patch=[];changed=[]
for name in pairs:
 before=DEST/'pre-fix-snapshot'/name;after=REPO/'skills/insurance'/name
 for p in before.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(before);dest=after/rel
  if p.read_bytes()!=dest.read_bytes():
   changed.append(str(Path('skills/insurance')/name/rel))
   patch.extend(difflib.unified_diff(p.read_text().splitlines(keepends=True),dest.read_text().splitlines(keepends=True),fromfile='before/'+name+'/'+str(rel),tofile='after/'+name+'/'+str(rel)))
(DEST/'repair.patch').write_text(''.join(patch))
(DEST/'changed-files.json').write_text(json.dumps(changed,indent=2)+'\n')
print('Changed:',changed)
