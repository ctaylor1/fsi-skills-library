import subprocess,pathlib,json,shlex
P=pathlib.Path('/tmp/insurance-p4-forward-measurement');R=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');py='/tmp/fsi-p0-venv/bin/python'
paths={'architecture':'enterprise-functions-technology/solution-architecture-planner','automation':'enterprise-functions-technology/workflow-automation-assessor','data':'data-ai-model-governance/data-product-value-evaluator','operations':'finance-operations/operations-performance-analyzer'}
log=[]
for kind,path in paths.items():
 for variant in ['complete','imperfect']:
  stem=f'{kind}-{variant}';inp=P/(stem+'-input.json');out=P/(stem+'-output.json')
  for script,arg,suffix in [('validate_input.py',inp,'input-validation'),('calculate_or_transform.py',inp,'output'),('validate_output.py',out,'output-validation')]:
   cmd=[py,str(R/'skills'/path/'scripts'/script),str(arg)];p=subprocess.run(cmd,text=True,capture_output=True)
   (P/(stem+'-'+suffix+'.json')).write_text(p.stdout);(P/(stem+'-'+suffix+'.stderr')).write_text(p.stderr)
   log.append({'command':shlex.join(cmd),'exit_code':p.returncode,'stdout':stem+'-'+suffix+'.json','stderr':stem+'-'+suffix+'.stderr'})
(P/'commands.json').write_text(json.dumps(log,indent=2)+'\n')
print(json.dumps(log,indent=2))
