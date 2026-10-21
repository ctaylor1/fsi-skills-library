from pathlib import Path
import copy,json,subprocess,sys
ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
OUT=Path('/tmp/cfc-phase3-forward-projection')
ROUTER=ROOT/'skills/compliance-financial-crime/compliance-financial-crime-router'
sys.path.insert(0,str(ROUTER/'scripts'))
sys.path.insert(0,str(ROOT/'shared/compliance-financial-crime'))
from native_runner import native_validate
from cfc_contract import build_packet
from native_integrity import canonical_hash
from review_projection import build_review_projection,validate_review_projection,expected_basis

def package(name):return ROOT/'skills/compliance-financial-crime'/name

def fixture(name):
 p=package(name)/'evals/files'
 file='phase2_input.json' if name=='financial-crime-case-investigator' else 'input_complete.json'
 return json.loads((p/file).read_text())

def calculate(name,doc):
 p=OUT/(name+'-compute-input.json');p.write_text(json.dumps(doc))
 r=subprocess.run([sys.executable,'-B',str(package(name)/'scripts/calculate_or_transform.py'),str(p)],capture_output=True,text=True,timeout=30)
 if r.returncode:raise ValueError(r.stdout+r.stderr)
 return json.loads(r.stdout)

def set_claim(doc,c,value):
 c['value']=value
 for s in doc['sources']:
  for f in s['facts']:
   if f['fact_id'] in c['fact_ids']:f['value']=copy.deepcopy(value);f['excerpt']='Synthetic forward-test amended fact: '+json.dumps(value)

def distinct_registry(doc):
 def walk(value):
  if isinstance(value,dict):
   for k,v in value.items():
    if k in {'source_ref','fact_id'} and isinstance(v,str):value[k]='FW-RECEIVER-'+v
    elif k in {'source_refs','fact_ids'} and isinstance(v,list):value[k]=['FW-RECEIVER-'+a for a in v]
    else:walk(v)
  elif isinstance(value,list):
   for v in value:walk(v)
 walk(doc)
 return doc

def prepare(pair):
 producer,receiver=pair;source=fixture(producer)
 source['as_of']='2026-10-04';source['workflow']['as_of']='2026-10-04'
 if producer.endswith('scenario-designer'):
  source['object_id']='SCENARIO-FORWARD-41';source['workflow']['context']['object_id']=source['object_id']
  set_claim(source,source['data']['scenario']['scenario_id'],source['object_id'])
  set_claim(source,source['data']['engine_observations'][0]['scenario_id'],source['object_id'])
 out=calculate(producer,source)
 packet=build_packet(source,out,producer=producer,native_validator=lambda o,d:native_validate(package(producer),o,d))
 target=distinct_registry(fixture(receiver))
 for k,v in source['workflow']['context'].items():
  if k not in {'object_type','capacity','purpose'}:target['workflow']['context'][k]=v
 target['object_id']=source['object_id'];target['as_of']=source['as_of'];target['knowledge_cutoff']=source['knowledge_cutoff'];target['workflow']['as_of']=source['as_of']
 for k in ['classification','audience','allowed_audiences']:target['workflow'][k]=copy.deepcopy(source['workflow'][k])
 for s in target['sources']:s['classification']=target['workflow']['classification'];s['permitted_audiences']=copy.deepcopy(target['workflow']['allowed_audiences'])
 if receiver.endswith('effectiveness-reviewer'):
  set_claim(target,target['data']['scope']['review_id'],source['object_id'])
  set_claim(target,target['data']['scope']['scenario_id'],source['object_id'])
  for r in target['data']['observations']:set_claim(target,r['scenario_id'],source['object_id'])
  set_claim(target,target['data']['operations']['scenario_id'],source['object_id'])
 else:
  # Fresh single-case receiver based on one supplied workpaper row only.
  for collection,rows in target['data'].items():
   if isinstance(rows,list) and rows:
    target['data'][collection]=[r for r in rows if 'case_id' not in r or r['case_id']['value']=='CASE-A']
  for collection,rows in target['data'].items():
   if not isinstance(rows,list):continue
   for r in rows:
    if 'native_case_id' in r:r['native_case_id']=source['object_id']
    if 'case_id' in r:set_claim(target,r['case_id'],source['object_id'])
    if 'upstream_native_id' in r:set_claim(target,r['upstream_native_id'],source['object_id'])
    if 'applicable_case_ids' in r:set_claim(target,r['applicable_case_ids'],[source['object_id']])
    for field in ['institution_id','legal_entity_id','jurisdiction']:
     if field in r:set_claim(target,r[field],source['workflow']['context'][field])
  for field in ['population_case_ids','selected_case_ids']:set_claim(target,target['data']['mandate'][field],[source['object_id']])
 target['sources']+=copy.deepcopy(source['sources'])
 target['workflow']['unresolved_issues']=copy.deepcopy(packet['unresolved_issues'])
 return {'pair':pair,'source':source,'output':out,'packet':packet,'target':target}

def finalize(case):
 target=case['target'];producer,receiver=case['pair']
 target['sources']=[s for s in target['sources'] if s['source_ref']!='FW-BASIS']
 basis={'value':expected_basis(case['packet'],case['source'],target,producer,receiver),'source_refs':['FW-BASIS'],'fact_ids':['FW-BASIS-FACT']}
 target['sources'].append({'source_ref':'FW-BASIS','version':'forward/v1','publication_date':target['knowledge_cutoff'],'received_at':target['knowledge_cutoff'],'classification':target['workflow']['classification'],'permitted_audiences':copy.deepcopy(target['workflow']['allowed_audiences']),'facts':[{'fact_id':'FW-BASIS-FACT','value':copy.deepcopy(basis['value']),'excerpt':'Synthetic forward review-scope basis, not authenticated approval'}]})
 target['workflow']['sources']=[{'source_ref':s['source_ref'],'version':s['version']} for s in target['sources']]
 mappings=[{'target_field':k,'source':'supplemental','source_pointer':'/detached_receiver/'+k,'basis':'Synthetic retained independent receiver evidence','reviewed_by':'FORWARD-REVIEWER','source_refs':[s['source_ref'] for s in target['sources']]} for k in target]
 next(m for m in mappings if m['target_field']=='object_id').update(source='source_input',source_pointer='/object_id')
 kwargs={'producer':producer,'target_skill':receiver,'producer_validator':lambda o,d:native_validate(package(producer),o,d),'receiver_validator':lambda d:native_validate(package(receiver),d),'supplemental_inputs':{'detached_receiver':copy.deepcopy(target)}}
 return mappings,basis,kwargs

def run(case,label,expected):
 mappings,basis,kwargs=finalize(case)
 stem=OUT/label;stem.mkdir(exist_ok=True)
 for name,value in [('source_input',case['source']),('source_output',case['output']),('source_packet',case['packet']),('target_input',case['target']),('mappings',mappings),('projection_basis',basis),('supplemental',kwargs['supplemental_inputs'])]:(stem/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
 try:
  projection=build_review_projection(case['packet'],case['source'],case['target'],mappings=mappings,projection_basis=basis,**kwargs)
  receiver_result=calculate(kwargs['target_skill'],case['target'])
  errors=validate_review_projection(projection,case['source'],**kwargs)
  (stem/'projection.json').write_text(json.dumps(projection,indent=2)+'\n')
  (stem/'receiver_result.json').write_text(json.dumps(receiver_result,indent=2)+'\n')
  accepted=not errors;detail={'validation_errors':errors,'source_object_id':case['source']['object_id'],'target_object_id':case['target']['object_id'],'authority_granted':projection['authority_granted'],'semantic_evidence_sufficiency':projection['semantic_evidence_sufficiency']}
 except ValueError as exc:accepted=False;detail={'error':str(exc)}
 result={'id':label,'expected_acceptance':expected,'accepted':accepted,'passed':accepted==expected,**detail}
 print(json.dumps(result));return result

pairs=[('transaction-monitoring-scenario-designer','transaction-monitoring-effectiveness-reviewer'),('financial-crime-case-investigator','financial-crime-case-quality-reviewer')]
results=[]
for i,pair in enumerate(pairs,1):
 base=prepare(pair);results.append(run(copy.deepcopy(base),'pair'+str(i)+'-same-subject',True))
 case=copy.deepcopy(base)
 if i==1:
  set_claim(case['target'],case['target']['data']['scope']['scenario_id'],'SCENARIO-UNRELATED-99')
  for row in case['target']['data']['observations']:set_claim(case['target'],row['scenario_id'],'SCENARIO-UNRELATED-99')
  set_claim(case['target'],case['target']['data']['operations']['scenario_id'],'SCENARIO-UNRELATED-99')
 else:
  for collection,rows in case['target']['data'].items():
   if isinstance(rows,list):
    for row in rows:
     if 'native_case_id' in row:row['native_case_id']='CASE-UNRELATED-99'
     if 'case_id' in row:set_claim(case['target'],row['case_id'],'CASE-UNRELATED-99')
     if 'upstream_native_id' in row:set_claim(case['target'],row['upstream_native_id'],'NATIVE-UNRELATED-99')
     if 'applicable_case_ids' in row:set_claim(case['target'],row['applicable_case_ids'],['CASE-UNRELATED-99'])
  for field in ['population_case_ids','selected_case_ids']:set_claim(case['target'],case['target']['data']['mandate'][field],['CASE-UNRELATED-99'])
 results.append(run(case,'pair'+str(i)+'-embedded-unrelated-subject',False))
 for mutation in ['cutoff','audience','source-facts','inherited-issues']:
  case=copy.deepcopy(base)
  if mutation=='cutoff':case['target']['knowledge_cutoff']='2026-10-02'
  if mutation=='audience':case['target']['workflow']['audience']='OUTSIDE';case['target']['workflow']['allowed_audiences'].append('OUTSIDE')
  if mutation=='source-facts':case['target']['sources'][-1]['facts'][0]['value']='ALTERED'
  if mutation=='inherited-issues':case['target']['workflow']['unresolved_issues']=[]
  results.append(run(case,'pair'+str(i)+'-'+mutation,False))
(OUT/'results.json').write_text(json.dumps({'scope':'Independent actual native validators; synthetic source/professional truth unverified','results':results,'passed':all(r['passed'] for r in results)},indent=2)+'\n')
