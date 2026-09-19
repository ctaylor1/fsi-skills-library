from pathlib import Path
import json, subprocess, shlex, hashlib, os, datetime

ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
CASE=Path('/tmp/insurance-p2-forward-claims/claim-payment-closure-reviewer')
PKG=ROOT/'skills/insurance/claim-payment-closure-reviewer'
PYTHON='/tmp/fsi-p0-venv/bin/python'
targets=[('baseline',CASE,'blocked'),('complete_reopening',CASE/'variants/complete_reopening','ready_for_authorized_review'),('blank_reopening',CASE/'variants/blank_reopening','blocked')]
summary=[]
for name,src,expect in targets:
    dest=CASE/'after-repair'/name;dest.mkdir(parents=True,exist_ok=True)
    log=[]
    original_input=src/'input.json'
    input_hash=hashlib.sha256(original_input.read_bytes()).hexdigest()
    for script,infile,outfile in [('validate_input.py',original_input,'validate_input.json'),('calculate_or_transform.py',original_input,'output.json'),('validate_output.py',dest/'output.json','validate_output.json')]:
        cmd=[PYTHON,str(PKG/'scripts'/script),str(infile)]
        proc=subprocess.run(cmd,capture_output=True,text=True,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        (dest/outfile).write_text(proc.stdout)
        log.append({'command':shlex.join(cmd),'cwd':str(ROOT),'env_override':{'PYTHONDONTWRITEBYTECODE':'1'},'exit_code':proc.returncode,'stdout_file':str(dest/outfile),'stderr':proc.stderr})
    (dest/'execution-log.json').write_text(json.dumps(log,indent=2)+'\n')
    before=json.loads((src/'output.json').read_text())
    after=json.loads((dest/'output.json').read_text())
    results=after.get('results',{})
    item={'case':name,'source_input':str(original_input),'input_sha256_before':input_hash,'input_sha256_after':hashlib.sha256(original_input.read_bytes()).hexdigest(),'expected_closure':expect,'before_closure':before['results']['closure_review_status'],'after_closure':results.get('closure_review_status'),'after_findings':after.get('findings'),'exit_codes':[x['exit_code'] for x in log],'assessment_matches':results.get('closure_review_status')==expect,'payment_status':results.get('payment_review_status'),'no_action':after.get('action_taken') is False}
    summary.append(item)
hashes={str(p.relative_to(PKG)):hashlib.sha256(p.read_bytes()).hexdigest() for p in PKG.rglob('*') if p.is_file() and 'evals' not in p.parts and '__pycache__' not in p.parts and p.name!='test_phase2.py'}
(CASE/'after-repair/source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
(CASE/'after-repair/replay-summary.json').write_text(json.dumps({'replayed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':summary},indent=2)+'\n')
print(json.dumps(summary,indent=2))
