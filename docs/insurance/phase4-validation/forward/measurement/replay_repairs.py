from pathlib import Path
import subprocess,json,shlex,shutil
P=Path('/tmp/insurance-p4-forward-measurement');Q=P/'repairs';Q.mkdir(exist_ok=True);R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills');py='/tmp/fsi-p0-venv/bin/python'
paths={'architecture':'enterprise-functions-technology/solution-architecture-planner','automation':'enterprise-functions-technology/workflow-automation-assessor','data':'data-ai-model-governance/data-product-value-evaluator','operations':'finance-operations/operations-performance-analyzer'};log=[];comp=[]
for inp in sorted(P.glob('*-input.json')):
 stem=inp.name.removesuffix('-input.json');kind=stem.split('-')[0];shutil.copy2(inp,Q/inp.name)
 for script,arg,suffix in [('validate_input.py',Q/inp.name,'input-validation'),('calculate_or_transform.py',Q/inp.name,'output'),('validate_output.py',Q/(stem+'-output.json'),'output-validation')]:
  cmd=[py,str(R/paths[kind]/'scripts'/script),str(arg)];r=subprocess.run(cmd,capture_output=True,text=True);(Q/(stem+'-'+suffix+'.json')).write_text(r.stdout);(Q/(stem+'-'+suffix+'.stderr')).write_text(r.stderr);log.append(dict(command=shlex.join(cmd),exit_code=r.returncode))
 old=json.loads((P/(stem+'-output.json')).read_text());new=json.loads((Q/(stem+'-output.json')).read_text());comp.append(dict(case=stem,input_unchanged=inp.read_bytes()==(Q/inp.name).read_bytes(),before_status=old['status'],after_status=new['status'],before_results=old['results'],after_results=new['results'],before_findings=old['findings'],after_findings=new['findings']))
(Q/'commands.json').write_text(json.dumps(log,indent=2)+'\n');(Q/'comparison.json').write_text(json.dumps(comp,indent=2)+'\n')
for c in comp:print(c['case'],c['before_status'],'->',c['after_status'],'results changed:',c['before_results']!=c['after_results'])
print('commands',len(log),'nonzero',sum(x['exit_code']!=0 for x in log))
