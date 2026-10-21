import json,pathlib,subprocess,shlex
P=pathlib.Path('/tmp/insurance-p4-forward-measurement');R=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills');py='/tmp/fsi-p0-venv/bin/python';log=[]
for stem,path in [('data-unknown-projection','data-ai-model-governance/data-product-value-evaluator'),('operations-unknown-open-cost','finance-operations/operations-performance-analyzer')]:
 for script,arg,suffix in [('validate_input.py',P/(stem+'-input.json'),'input-validation'),('calculate_or_transform.py',P/(stem+'-input.json'),'output'),('validate_output.py',P/(stem+'-output.json'),'output-validation')]:
  cmd=[py,str(R/path/'scripts'/script),str(arg)];r=subprocess.run(cmd,text=True,capture_output=True);(P/(stem+'-'+suffix+'.json')).write_text(r.stdout);(P/(stem+'-'+suffix+'.stderr')).write_text(r.stderr);log.append(dict(command=shlex.join(cmd),exit_code=r.returncode))
(P/'probe-commands.json').write_text(json.dumps(log,indent=2)+'\n')
for stem in ['data-unknown-projection','operations-unknown-open-cost']:
 d=json.loads((P/(stem+'-output.json')).read_text());print(stem,json.dumps({'status':d['status'],'findings':d['findings'],'results':d['results']},indent=2))
