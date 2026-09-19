import json,pathlib,subprocess,hashlib,datetime
root=pathlib.Path('/tmp/insurance-p2-forward-operations'); repo=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library'); py='/tmp/fsi-p0-venv/bin/python'
summary=[]
for key,name in json.loads((root/'cases.json').read_text()).items():
 case=root/key; package=repo/'skills/insurance'/name
 hashes={str(f.relative_to(package)):hashlib.sha256(f.read_bytes()).hexdigest() for f in package.rglob('*') if f.is_file() and f.suffix in ['.py','.md'] and not any(x in str(f.relative_to(package)) for x in ['evals/','test_','__pycache__'])}
 (case/'package-source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
 records=[]
 for mode,file,out in [('validate_input','native-input.json','input-validation.json'),('calculate_or_transform','native-input.json','native-output.json'),('validate_output','native-output.json','output-validation.json')]:
  cmd=[py,str(package/'scripts'/f'{mode}.py'),str(case/file)]
  proc=subprocess.run(cmd,text=True,capture_output=True)
  (case/out).write_text(proc.stdout);(case/(out+'.stderr')).write_text(proc.stderr)
  records.append(dict(command=cmd,returncode=proc.returncode,stdout=out,stderr=out+'.stderr'))
 (case/'commands-status.json').write_text(json.dumps(records,indent=2)+'\n')
 output=json.loads((case/'native-output.json').read_text())
 summary.append(dict(case=key,skill=name,exit_codes=[x['returncode'] for x in records],status=output.get('status'),findings=output.get('findings'),results=output.get('results')))
(root/'run-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
