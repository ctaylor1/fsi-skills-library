import json,pathlib,subprocess,os,hashlib,datetime
D=pathlib.Path('/private/tmp/ir-remaining-findings-independent');R=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/investment-research');P='/Users/taylor/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};rows=[]
for case in sorted(D.iterdir()):
 if not case.is_dir() or not (case/'request.json').exists():continue
 pkg='issuer-credit-researcher' if case.name.startswith('issuer_') else 'issuer-credit-surveillance-reviewer';scripts=R/pkg/'scripts';row={'case':case.name,'package':pkg,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'steps':[]}
 for label,script,args in [('input','validate_input.py',[str(case/'request.json')]),('calculate','calculate_or_transform.py',[str(case/'request.json')])]:
  argv=[P,'-B',str(scripts/script),*args];p=subprocess.run(argv,env=env,capture_output=True,text=True);(case/(label+'.stdout')).write_text(p.stdout);(case/(label+'.stderr')).write_text(p.stderr);row['steps'].append({'step':label,'argv':argv,'exit_code':p.returncode})
  if label=='calculate' and p.returncode==0:
   try:output=json.loads(p.stdout);(case/'output.json').write_text(p.stdout)
   except ValueError:continue
   argv=[P,'-B',str(scripts/'validate_output.py'),str(case/'output.json'),'--input',str(case/'original.json')];q=subprocess.run(argv,env=env,capture_output=True,text=True);(case/'output-check.stdout').write_text(q.stdout);(case/'output-check.stderr').write_text(q.stderr);row['steps'].append({'step':'output-check','argv':argv,'exit_code':q.returncode})
   row['status']=output.get('status');row['results']=output.get('results');row['issues']=output.get('unresolved_issues')
 rows.append(row)
(D/'execution-results.json').write_text(json.dumps(rows,indent=2)+'\n')
after={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for name in ['issuer-credit-researcher','issuer-credit-surveillance-reviewer'] for p in sorted((R/name).rglob('*')) if p.is_file() and '__pycache__' not in p.parts};(D/'package-hashes-after.json').write_text(json.dumps(after,indent=2)+'\n');before=json.loads((D/'package-hashes-before.json').read_text());diff={'before_count':len(before),'after_count':len(after),'changed':[k for k in before if before.get(k)!=after.get(k)],'added':sorted(set(after)-set(before)),'removed':sorted(set(before)-set(after))};(D/'package-hash-comparison.json').write_text(json.dumps(diff,indent=2)+'\n')
print(json.dumps({'runs':[{'case':r['case'],'status':r.get('status'),'steps':r['steps'],'issues':r.get('issues')} for r in rows],'package_hash_comparison':diff},indent=2))
