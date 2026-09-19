import hashlib,json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('/tmp/insurance-p3-forward-claims-risk'); REPO=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
manifest=json.loads((ROOT/(sys.argv[2] if len(sys.argv)>2 else 'freeze-manifest.json')).read_text())
label=sys.argv[1] if len(sys.argv)>1 else 'original'
summary=[]
for case in manifest['cases']:
    folder=ROOT/case['skill']/case['key']; run=folder/label; run.mkdir(exist_ok=True)
    source=REPO/'skills/insurance'/case['skill']/'scripts'
    hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in source.glob('*.py') if not f.name.startswith('test')}
    (run/'runtime-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    records=[]
    input_path=folder/case.get('input_filename','input.json')
    for script,inp,out in [('validate_input.py',input_path,'input-validation'),('calculate_or_transform.py',input_path,'output'),('validate_output.py',run/'output.json','output-validation')]:
        command=[sys.executable,str(source/script),str(inp)]
        result=subprocess.run(command,capture_output=True,text=True,cwd=ROOT)
        (run/(out+'.stdout')).write_text(result.stdout)
        (run/(out+'.stderr')).write_text(result.stderr)
        records.append(dict(command=command,exit_code=result.returncode,at=datetime.now(timezone.utc).isoformat(),input_sha256=hashlib.sha256(inp.read_bytes()).hexdigest() if inp.exists() else None))
        if out=='output':
            try:
                parsed=json.loads(result.stdout); (run/'output.json').write_text(result.stdout)
            except json.JSONDecodeError: pass
    (run/'command-log.json').write_text(json.dumps(records,indent=2)+'\n')
    doc=json.loads((run/'output.json').read_text()) if (run/'output.json').exists() else {}
    summary.append(dict(**case,exit_codes=[r['exit_code'] for r in records],status=doc.get('status'),findings=doc.get('findings'),results=doc.get('results')))
(ROOT/(label+'-summary.json')).write_text(json.dumps(summary,indent=2)+'\n')
for s in summary:
    print(s['key'],s['exit_codes'],s['status'])
