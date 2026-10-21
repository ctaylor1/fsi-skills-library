from pathlib import Path
import json,copy
root=Path('/tmp/cfc-phase3-forward-detection');base=json.loads((root/'m1-new-complete-proposal-scope-adapted.json').read_text())
def mutate(d,c,v):
 c['value']=v
 for s in d['sources']:
  for f in s['facts']:
   if f['fact_id'] in c['fact_ids']:f['value']=v;f['excerpt']='Extended synthetic engine evidence: '+json.dumps(v)
cases=[]
for name,field,value,reason in [('future-engine-workpaper','observed_on','2026-10-05','An unobservable post-cutoff engine workpaper cannot support this engine configuration proposal.'),('unknown-engine-workpaper','observation',None,'Unknown substantive engine evidence must not be replaced by benchmark references or a role/source label.'),('unknown-engine-version','engine_version',None,'Unknown version in engine workpaper cannot establish configuration/version support.')]:
 d=copy.deepcopy(base);mutate(d,d['data']['engine_observations'][0][field],value);filename='m1-'+name+'.json';(root/filename).write_text(json.dumps(d,indent=2)+'\n');cases.append({'id':'m1-'+name,'skill':'transaction-monitoring-scenario-designer','input':filename,'independent_expectation':'proposal-withheld','reason_before_run':reason})
d=copy.deepcopy(base);d['data']['engine_observations'][0]['observation']['fact_ids']=['NO-STATED-FACT'];filename='m1-unsupported-engine-fact.json';(root/filename).write_text(json.dumps(d,indent=2)+'\n');cases.append({'id':'m1-unsupported-engine-fact','skill':'transaction-monitoring-scenario-designer','input':filename,'independent_expectation':'proposal-withheld','reason_before_run':'A present source registry does not support an engine observation with an absent exact fact locator.'})
(root/'before-engine-extension-expectations.json').write_text(json.dumps({'created_before_native_runs':True,'original_expectations_unchanged':True,'cases':cases},indent=2)+'\n')
s=(root/'run_forward.py').read_text().replace('before-run-expectations.json','before-engine-extension-expectations.json').replace('packages-before-hashes.json','packages-engine-extension-before-hashes.json').replace("ROOT/'result.json'","ROOT/'engine-extension-result.json'")
(root/'run_engine_extensions.py').write_text(s)
