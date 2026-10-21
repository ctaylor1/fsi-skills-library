import json,pathlib,copy,subprocess,shlex
p=pathlib.Path('/tmp/insurance-p4-forward-design');repo=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance');py='/tmp/fsi-p0-venv/bin/python';rows=json.loads((p/'commands.json').read_text())
# Retain original runs; repair unsupported affirmative assumptions, not raw sources.
a=json.loads((p/'data-early.input.json').read_text());a['case_id']='CH-DATA-SOURCE-AUDITED';a['data']['sample_inventory_complete']=None;a['data']['fields'][0]['purpose_reviewed']=None;a['unresolved_issues']=['Raw DICT-2 states intended purpose but does not explicitly affirm purpose review or sample inventory completeness.'];
b=json.loads((p/'core-rehearsal.input.json').read_text());b['case_id']='CH-CORE-SOURCE-AUDITED';b['data']['inventory_complete']=None
for o in b['data']['options']:o['cost_inventory_complete']=None
b['unresolved_issues']=['CORE-5 lists options, costs and requirements but does not explicitly affirm complete cost/requirement inventories. Initial normalization wrongly assumed completeness.']
for stem,pkg,obj in [('data-source-audited','insurance-data-product-designer',a),('core-source-audited','insurance-core-modernization-planner',b)]:
 inp=p/(stem+'.input.json');inp.write_text(json.dumps(obj,indent=2)+'\n');out=p/(stem+'.output.json')
 for script,target,dest in [('validate_input.py',inp,p/(stem+'.input-validation.json')),('calculate_or_transform.py',inp,out),('validate_output.py',out,p/(stem+'.output-validation.json'))]:
  cmd=[py,str(repo/pkg/'scripts'/script),str(target)];r=subprocess.run(cmd,capture_output=True,text=True);dest.write_text(r.stdout);err=p/(stem+'.'+script+'.stderr.txt');err.write_text(r.stderr);rows.append({'command':shlex.join(cmd),'stdout':str(dest),'stderr':str(err),'exit_code':r.returncode})
(p/'commands.json').write_text(json.dumps(rows,indent=2)+'\n')
