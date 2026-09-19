import json,pathlib,hashlib,subprocess,datetime
R=pathlib.Path('/tmp/insurance-p2-forward-operations'); A=R/'after-repair';repo=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library'); py='/tmp/fsi-p0-venv/bin/python'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
original_manifest=json.loads((R/'evidence-manifest.json').read_text())
assert all(sha(R/p)==h for p,h in original_manifest.items()),'Original evidence changed before replay'
summary=[]; identities=[]
for key,name in json.loads((R/'cases.json').read_text()).items():
 case=R/key;new=A/key;new.mkdir(exist_ok=True); package=repo/'skills/insurance'/name; inp=case/'native-input.json'
 before=sha(inp);expected=original_manifest[f'{key}/native-input.json']
 assert before==expected
 # Snapshot actual reviewed interfaces and documentation only. No tests or eval fixtures read.
 files=[f for f in package.rglob('*') if f.is_file() and f.suffix in ['.py','.md'] and not any(x in str(f.relative_to(package)) for x in ['evals/','test_','__pycache__'])]
 hashes={str(f.relative_to(package)):sha(f) for f in files};dump(new/'package-source-hashes.json',hashes)
 commands=[]
 for mode,source,out in [('validate_input',inp,'input-validation.json'),('calculate_or_transform',inp,'native-output.json'),('validate_output',new/'native-output.json','output-validation.json')]:
  command=[py,str(package/'scripts'/f'{mode}.py'),str(source)];start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(command,text=True,capture_output=True)
  (new/out).write_text(p.stdout);(new/(out+'.stderr')).write_text(p.stderr)
  commands.append(dict(command=command,started_utc=start,returncode=p.returncode,stdout=str(new/out),stderr=str(new/(out+'.stderr'))))
 dump(new/'commands-status.json',commands)
 assert all(sha(package/f)==h for f,h in hashes.items()),'Package changed during replay'
 after=sha(inp);identities.append(dict(case=key,input_path=str(inp),original_manifest_sha256=expected,before_replay_sha256=before,after_replay_sha256=after,unchanged=expected==before==after))
 output=json.loads((new/'native-output.json').read_text());previous=json.loads((case/'native-output.json').read_text());summary.append(dict(case=key,skill=name,exit_codes=[x['returncode'] for x in commands],previous_status=previous.get('status'),status=output.get('status'),findings=output.get('findings'),results=output.get('results'),identical_result_to_original=output.get('results')==previous.get('results')))
assert all(sha(R/p)==h for p,h in original_manifest.items()),'Original evidence changed after replay'
dump(A/'unchanged-input-evidence.json',identities);dump(A/'run-summary.json',summary);dump(A/'original-evidence-verification.json',dict(original_manifest_sha256=sha(R/'evidence-manifest.json'),original_files_verified=len(original_manifest),all_originals_unchanged=True))
print(json.dumps(summary,indent=2))
