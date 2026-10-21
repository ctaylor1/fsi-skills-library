import pathlib,json,copy,subprocess,shlex
p=pathlib.Path('/tmp/insurance-p4-forward-design');repo=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance');py='/tmp/fsi-p0-venv/bin/python';rows=json.loads((p/'commands.json').read_text())
def run(name,pkg,script,obj):
 inp=p/(name+'.json');inp.write_text(json.dumps(obj,indent=2)+'\n');cmd=[py,str(repo/pkg/'scripts'/script),str(inp)];r=subprocess.run(cmd,capture_output=True,text=True);out=p/(name+'.validation.json');out.write_text(r.stdout);err=p/(name+'.stderr.txt');err.write_text(r.stderr);rows.append({'command':shlex.join(cmd),'stdout':str(out),'stderr':str(err),'exit_code':r.returncode});print(name,r.returncode,r.stdout)
a=json.loads((p/'workflow-complete.output.json').read_text());a['results']['weighted_minutes']['target']['human_minutes']='0';run('tampered-workflow-output','insurance-workflow-designer','validate_output.py',a)
a=json.loads((p/'workflow-complete.input.json').read_text());a['data']['steps'][2]['max_attempts']=True;run('invalid-boolean-retries','insurance-workflow-designer','validate_input.py',a)
# Raw evidence fidelity sentinel: a deliberately wrong mapper changes a source value.
# This is an evaluation probe, not an approved mapping or practitioner fact.
a=json.loads((p/'core-rehearsal.input.json').read_text());a['case_id']='CH-INTENTIONALLY-WRONG-MAPPING';a['data']['options'][0]['costs'][0]['amount']=1;run('unsupported-mapped-cost','insurance-core-modernization-planner','calculate_or_transform.py',a)
out=json.loads((p/'unsupported-mapped-cost.validation.json').read_text());run('unsupported-mapped-cost-output','insurance-core-modernization-planner','validate_output.py',out)
(p/'commands.json').write_text(json.dumps(rows,indent=2)+'\n')
