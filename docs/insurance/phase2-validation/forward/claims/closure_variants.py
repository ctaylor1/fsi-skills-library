from pathlib import Path
import json, hashlib, subprocess, shlex, copy, os

OUT=Path('/tmp/insurance-p2-forward-claims')
CASE=OUT/'claim-payment-closure-reviewer'
BASE=json.loads((CASE/'input.json').read_text())
PYTHON='/tmp/fsi-p0-venv/bin/python'
variants=[
 ('complete_reopening','Closure worksheet addendum v2: the new concealed water damage trigger is assigned to the Property Claims Reopening Team. Route the evidence to internal claim queue PROPERTY-REOPEN, with the claim ID. All original obligations, payment reconciliation and zero-reserve statements remain unchanged.',[{'trigger':'New concealed water damage evidence','owner':'Property Claims Reopening Team','routing':'Internal queue PROPERTY-REOPEN with claim ID','source_refs':['CLOSURE-V2']}],[], 'ready_for_authorized_review'),
 ('blank_reopening','Closure worksheet addendum v2: migration left the reopening entry blank. No trigger, owner or routing is supplied. All original obligations, payment reconciliation and zero-reserve statements remain unchanged.',[''],['Reopening trigger, owner and routing unavailable after migration.'],'blocked')]
summary=[]
for name,raw,triggers,issues,expected in variants:
    dest=CASE/'variants'/name;dest.mkdir(parents=True,exist_ok=True)
    p=dest/'CLOSURE-V2.md';p.write_text('# SYNTHETIC SOURCE\n\n'+raw+'\n')
    d=copy.deepcopy(BASE);d['case_id']+='-'+name;d['unresolved_issues']=issues
    d['sources'].append({'source_ref':'CLOSURE-V2','version':'2','as_of':'2026-09-18','path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    d['data']['closure']['reopen_triggers']=triggers;d['data']['closure']['source_refs']=['CLOSURE','CLOSURE-V2']
    (dest/'input.json').write_text(json.dumps(d,indent=2)+'\n')
    (dest/'request.md').write_text('Replay the same closure review with this one documented reopening-evidence variation. All other raw source facts remain unchanged. Expected closure readiness independently judged from the documented ownership requirement: '+expected+'.\n')
    (dest/'mapping.md').write_text('Original source packet preserved. CLOSURE-V2 supersedes only reopening information. Native reopen_triggers and unresolved_issues reflect that explicit update; all amount, identity, scope and settlement fields unchanged. Variants execute the frozen pre-repair native implementation.\n')
    logs=[]
    for script,src,out in [('validate_input.py','input.json','validate_input.json'),('calculate_or_transform.py','input.json','output.json'),('validate_output.py','output.json','validate_output.json')]:
        cmd=[PYTHON,str(CASE/'snapshot/scripts'/script),str(dest/src)]
        r=subprocess.run(cmd,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        (dest/out).write_text(r.stdout)
        logs.append({'command':shlex.join(cmd),'env_override':{'PYTHONDONTWRITEBYTECODE':'1'},'exit_code':r.returncode,'stdout_path':str(dest/out),'stderr':r.stderr})
    (dest/'execution-log.json').write_text(json.dumps(logs,indent=2)+'\n')
    output=json.loads((dest/'output.json').read_text())
    summary.append({'variant':name,'expected_closure':expected,'native_closure':output['results']['closure_review_status'],'all_native_checks_pass':all(x['exit_code']==0 for x in logs),'accepted_but_wrong':all(x['exit_code']==0 for x in logs) and expected!=output['results']['closure_review_status']})
(CASE/'variants/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
