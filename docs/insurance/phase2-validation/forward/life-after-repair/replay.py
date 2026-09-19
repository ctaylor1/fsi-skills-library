from pathlib import Path
import json,hashlib,shutil,subprocess,os
BASE=Path('/tmp/insurance-p2-forward-life');P=Path('/tmp/insurance-p2-forward-life-after-repair');R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance');PY='/tmp/fsi-p0-venv/bin/python'
SKILLS=['life-underwriting-reviewer','life-annuity-contract-service-reviewer','life-benefit-claim-reviewer','reinsurance-program-analyzer','reinsurance-contract-administration-reviewer']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
def snapshot():
 return {str(f):sha(f) for s in SKILLS for f in sorted((R/s).rglob('*')) if f.is_file() and (f.name=='SKILL.md' or f.parent.name in ('references','assets') or (f.parent.name=='scripts' and f.suffix=='.py' and not f.name.startswith('test')))}
pre=snapshot();write(P/'package-hashes-before.json',pre)
all_commands=[];copies=[];comparisons=[]
for s in SKILLS:
 dst=P/s;src=BASE/s;dst.mkdir(exist_ok=True)
 for n in ['request.md','raw-source.md','input.json','design-status.json','mapping-notes.json','same-day-input.json','same-day-source.md']:
  if (src/n).exists():
   shutil.copyfile(src/n,dst/n);copies.append(dict(source=str(src/n),destination=str(dst/n),sha256=sha(src/n),unchanged=sha(src/n)==sha(dst/n)))
 variants=['']+(['same-day-'] if s=='life-annuity-contract-service-reviewer' else [])
 for v in variants:
  logs=[]
  for script,inp,out in [('validate_input.py',v+'input.json',v+'input-validation.json'),('calculate_or_transform.py',v+'input.json',v+'actual-output.json'),('validate_output.py',v+'actual-output.json',v+'output-validation.json')]:
   cmd=[PY,str(R/s/'scripts'/script),str(dst/inp)];cp=subprocess.run(cmd,text=True,capture_output=True,cwd=R/s,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
   (dst/out).write_text(cp.stdout);(dst/(out+'.stderr')).write_text(cp.stderr)
   logs.append(dict(command=cmd,returncode=cp.returncode,stdout_file=str(dst/out),stderr_file=str(dst/(out+'.stderr'))))
   assert cp.returncode==0,(cmd,cp.stdout,cp.stderr)
  write(dst/(v+'commands.json'),logs);all_commands.extend(logs)
  old=json.loads((src/(v+'actual-output.json')).read_text());new=json.loads((dst/(v+'actual-output.json')).read_text());inp=json.loads((dst/(v+'input.json')).read_text())
  assert new['source_document']==inp
  changed=[k for k in sorted(set(old)|set(new)) if old.get(k)!=new.get(k)]
  newcodes=[f['code'] for f in new['findings'] if f not in old['findings']]
  row=dict(package=s,variant='original' if not v else 'same-day',status=new['status'],unchanged_input_retained=True,changed_top_level_fields=changed,changed_findings=newcodes,results_unchanged=old['results']==new['results'])
  assert row['results_unchanged']
  if s=='life-annuity-contract-service-reviewer' and not v:
   dates=[f for f in new['findings'] if f['code']=='valuation_date_stale'];assert len(dates)==1
   assert '2026-09-17' in dates[0]['message'] and '2026-09-18' in dates[0]['message']
   assert new['results']['value_scenario'] is None
   assert inp['data']['contract']['value_date']=='2026-09-17'
   row['valuation_date_finding']=dates[0]
   assert newcodes==['valuation_date_stale'],newcodes
  else:assert not changed,(s,v,changed)
  comparisons.append(row)
post=snapshot();write(P/'package-hashes-after.json',post);assert pre==post,'Package source drifted during replay'
write(P/'unchanged-input-hashes.json',copies);assert all(x['unchanged'] for x in copies)
# Copy independent arithmetic code, changing only its evidence directory.
checker=(BASE/'check_arithmetic.py').read_text(); adapted=checker.replace("P=Path('/tmp/insurance-p2-forward-life')","P=Path('/tmp/insurance-p2-forward-life-after-repair')");assert adapted!=checker
(P/'check_arithmetic.py').write_text(adapted)
cp=subprocess.run([PY,str(P/'check_arithmetic.py')],capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'));assert cp.returncode==0,cp.stdout+cp.stderr
write(P/'arithmetic-command.json',dict(command=[PY,str(P/'check_arithmetic.py')],returncode=cp.returncode,stdout=cp.stdout,stderr=cp.stderr,baseline_checker_sha256=sha(BASE/'check_arithmetic.py'),replay_checker_sha256=sha(P/'check_arithmetic.py'),change='only P evidence-root path; independent arithmetic unchanged'))
arithmetic=[r for s in SKILLS for r in json.loads((P/s/'independent-arithmetic.json').read_text())];assert len(arithmetic)==26 and all(x['passed'] for x in arithmetic)
summary=dict(status='PASS',original_cases=5,separately_sourced_variants=1,native_cli_checks=len(all_commands),native_cli_checks_passed=len(all_commands),independent_arithmetic_checks=len(arithmetic),independent_arithmetic_checks_passed=len(arithmetic),all_original_sources_and_inputs_unchanged=True,package_source_stable_during_replay=True,documentation_readback='same-day requirement is now explicit in SKILL.md, references/source-map.md and references/domain-rules.md',comparisons=comparisons,no_repo_edits=True,no_external_actions=True,no_professional_acceptance_claimed=True)
write(P/'summary.json',summary)
write(P/'artifact-hashes.json',{str(f):sha(f) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='artifact-hashes.json'})
for path,h in json.loads((P/'artifact-hashes.json').read_text()).items():assert sha(Path(path))==h,path
print(json.dumps(summary,indent=2))
