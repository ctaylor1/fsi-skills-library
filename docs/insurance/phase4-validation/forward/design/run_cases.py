import json,pathlib,subprocess,shlex
p=pathlib.Path('/tmp/insurance-p4-forward-design'); repo=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');py='/tmp/fsi-p0-venv/bin/python'
rows=[]
for f in sorted(p.glob('*.input.json')):
 package={'workflow':'insurance-workflow-designer','data':'insurance-data-product-designer','core':'insurance-core-modernization-planner'}[f.name.split('-')[0]]
 root=repo/'skills/insurance'/package/'scripts';stem=f.name.removesuffix('.input.json');out=p/(stem+'.output.json')
 for script,inp,stdout in [('validate_input.py',f,p/(stem+'.input-validation.json')),('calculate_or_transform.py',f,out),('validate_output.py',out,p/(stem+'.output-validation.json'))]:
  cmd=[py,str(root/script),str(inp)];r=subprocess.run(cmd,capture_output=True,text=True);stdout.write_text(r.stdout);(p/(stem+'.'+script+'.stderr.txt')).write_text(r.stderr);rows.append({'command':shlex.join(cmd),'stdout':str(stdout),'stderr':str(p/(stem+'.'+script+'.stderr.txt')),'exit_code':r.returncode})
(p/'commands.json').write_text(json.dumps(rows,indent=2)+'\n')
for f in sorted(p.glob('*.output.json')):
 d=json.loads(f.read_text());print(f.name,d.get('status'),[x['code'] for x in d.get('findings',[])],json.dumps(d.get('results',{}))[:700])
