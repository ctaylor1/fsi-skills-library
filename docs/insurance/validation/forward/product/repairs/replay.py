from pathlib import Path
import sys,json,subprocess,hashlib
ROOT=Path('/tmp/insurance-product-forward-20260918');REPO=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');PYTHON='/tmp/fsi-p0-venv/bin/python'
phase=sys.argv[1];results=[]
for case,pkg in [('05-unavailable-quote-limits','premium-quote-comparator'),('06-zero-premium-reinstatement','reinsurance-contract-reviewer'),('07-no-large-loss-schedule','pc-reserving-analysis-assistant')]:
 d=ROOT/'repairs'/phase/case;d.mkdir(parents=True,exist_ok=True)
 src=ROOT/'cases'/case/'input.json';copy=d/'input.json';copy.write_bytes(src.read_bytes())
 (d/'raw-request.md').write_bytes((ROOT/'cases'/case/'raw-request.md').read_bytes())
 logs=[]
 for stage,script in [('input-validation','validate_input.py'),('calculation','calculate_or_transform.py')]:
  cmd=[PYTHON,'-B',str(REPO/'skills/insurance'/pkg/'scripts'/script),str(copy)];p=subprocess.run(cmd,text=True,capture_output=True)
  (d/(stage+'.stdout.txt')).write_text(p.stdout);(d/(stage+'.stderr.txt')).write_text(p.stderr);logs.append({'stage':stage,'command':cmd,'exit_code':p.returncode})
  if stage=='calculation':
   out=json.JSONDecoder().raw_decode(p.stdout)[0];(d/'native-output.json').write_text(json.dumps(out,indent=2)+'\n')
 final_code='''import json,sys\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\nfrom insurance_contract import build_artifact\np=Path(sys.argv[2]);out=json.loads((p/'native-output.json').read_text())\nif 'clauses' in out:\n for clause in out['clauses']:clause['plain_summary']='The supplied wording states: '+clause['source_text']\nout['narrative']='Synthetic replay for review of the documented calculation and missing-data behavior.'\na=out['artifact'];out['artifact']=build_artifact(out['calculation_inputs'],out,producer=a['producer'],artifact_type=a['artifact_type'],completeness=a['completeness'],evaluability=a['evaluability'],issues=a['unresolved_issues'])\n(p/'final-output.json').write_text(json.dumps(out,indent=2)+'\\n')\n'''
 subprocess.run([PYTHON,'-B','-c',final_code,str(REPO/'skills/insurance'/pkg/'scripts'),str(d)],check=True)
 cmd=[PYTHON,'-B',str(REPO/'skills/insurance'/pkg/'scripts/validate_output.py'),str(d/'final-output.json')];p=subprocess.run(cmd,text=True,capture_output=True)
 (d/'output-validation.stdout.txt').write_text(p.stdout);(d/'output-validation.stderr.txt').write_text(p.stderr);logs.append({'stage':'output-validation','command':cmd,'exit_code':p.returncode})
 (d/'run-log.json').write_text(json.dumps(logs,indent=2)+'\n')
 if case.startswith('05'):observed={k:out[k] for k in ('cost_comparison_status','lowest_annualized_total_cost_quote_id','cost_spread','comparability_flags')}
 elif case.startswith('06'):observed=out['recovery_illustration']['occurrences'][0]
 else:observed=out['segments'][0]['large_loss']
 results.append({'case':case,'package':pkg,'unchanged_input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'same_input_bytes':src.read_bytes()==copy.read_bytes(),'observed':observed,'artifact_completeness':out['artifact']['completeness'],'exit_codes':[x['exit_code'] for x in logs]})
(ROOT/'repairs'/phase/'summary.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
