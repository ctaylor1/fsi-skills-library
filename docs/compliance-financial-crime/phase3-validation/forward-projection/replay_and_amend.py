from pathlib import Path
import copy,json,subprocess,sys,hashlib
ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');OUT=Path('/tmp/cfc-phase3-forward-projection');ROUTER=ROOT/'skills/compliance-financial-crime/compliance-financial-crime-router'
sys.path.insert(0,str(ROUTER/'scripts'));sys.path.insert(0,str(ROOT/'shared/compliance-financial-crime'))
from native_runner import native_validate
from cfc_contract import build_packet
from native_integrity import canonical_hash
from review_projection import build_review_projection,validate_review_projection,expected_basis

def package(name):return ROOT/'skills/compliance-financial-crime'/name

def read(p):return json.loads(p.read_text())

def set_claim(doc,c,value):
 c['value']=copy.deepcopy(value)
 for s in doc['sources']:
  for f in s['facts']:
   if f['fact_id'] in c['fact_ids']:f['value']=copy.deepcopy(value);f['excerpt']='Synthetic separately amended forward linkage fact: '+json.dumps(value)

def load_case(folder):
 c={k:read(folder/(k+'.json')) for k in ['source_input','source_output','source_packet','target_input','mappings','projection_basis','supplemental']}
 c['producer']=c['source_packet']['producer'];c['receiver']='transaction-monitoring-effectiveness-reviewer' if c['producer']=='transaction-monitoring-scenario-designer' else 'financial-crime-case-quality-reviewer'
 return c

def kwargs(c):return dict(producer=c['producer'],target_skill=c['receiver'],producer_validator=lambda out,doc:native_validate(package(c['producer']),out,doc),receiver_validator=lambda doc:native_validate(package(c['receiver']),doc),supplemental_inputs=c['supplemental'])

def attempt(c):
 try:
  p=build_review_projection(c['source_packet'],c['source_input'],c['target_input'],mappings=c['mappings'],projection_basis=c['projection_basis'],**kwargs(c))
  return {'accepted':True,'projection':p,'reconstruction_errors':validate_review_projection(p,c['source_input'],**kwargs(c))}
 except ValueError as exc:return {'accepted':False,'error':str(exc)}

original=read(OUT/'results.json');replay=[]
for old in original['results']:
 folder=OUT/old['id'];result=attempt(load_case(folder));result.pop('projection',None)
 replay.append({'id':old['id'],'original_expected_acceptance':old['expected_acceptance'],'original_observed_acceptance':old['accepted'],'current_observed_acceptance':result['accepted'],'matches_original_expectation':result['accepted']==old['expected_acceptance'],**{k:v for k,v in result.items() if k!='accepted'}})
(OUT/'original-raw-replay-results.json').write_text(json.dumps({'original_inputs_unchanged':True,'note':'Original normal cases lack newly explicit namespace or upstream-version/basis requirements and are now rejected; original expected outcomes are retained without relabeling. Former cross-subject failures now reject.','results':replay},indent=2)+'\n')

amended=[]
for i in [1,2]:
 c=load_case(OUT/('pair'+str(i)+'-same-subject'));t=c['target_input'];s=c['source_input']
 if i==1:
  mapping=[('scenario_id','scenario_id'),('design_version','scenario_version'),('engine_id','engine_id'),('engine_version','engine_version'),('population_id','population_id'),('population_unit','population_unit'),('mapping_dataset_id','mapping_dataset_id'),('identifier_namespace','identifier_namespace'),('entity_mapping_ref','entity_mapping_ref'),('entity_mapping_version','entity_mapping_version'),('graph_reference','graph_reference'),('graph_version','graph_version')]
  for old,new in mapping:set_claim(t,t['data']['scope'][new],s['data']['scenario'][old]['value'])
 else:
  # Separate amended valid-link case: QA claims were received Oct 4, so review
  # cutoff and actual producer output must be refreshed, not silently backdated.
  s['knowledge_cutoff']='2026-10-04';t['knowledge_cutoff']='2026-10-04'
  amended_input=OUT/'amended-pair2-producer-input.json';amended_input.write_text(json.dumps(s))
  computed=subprocess.run([sys.executable,'-B',str(package(c['producer'])/'scripts/calculate_or_transform.py'),str(amended_input)],capture_output=True,text=True,timeout=30)
  if computed.returncode:raise ValueError(computed.stdout+computed.stderr)
  c['source_output']=json.loads(computed.stdout)
  c['source_packet']=build_packet(s,c['source_output'],producer=c['producer'],native_validator=lambda out,doc:native_validate(package(c['producer']),out,doc))
  set_claim(t,t['data']['cases'][0]['upstream_native_version'],canonical_hash(s))
 # Exact new linkage basis is sourced in its independent registry record.
 c['projection_basis']['value']=expected_basis(c['source_packet'],s,t,c['producer'],c['receiver'])
 for record in t['sources']:
  for fact in record['facts']:
   if fact['fact_id'] in c['projection_basis']['fact_ids']:fact['value']=copy.deepcopy(c['projection_basis']['value']);fact['excerpt']='Synthetic independently amended new underlying-subject linkage basis; semantic adequacy and authority unverified'
 c['supplemental']={'detached_receiver':copy.deepcopy(t)}
 stem=OUT/('amended-pair'+str(i));stem.mkdir(exist_ok=True)
 for k in ['source_input','source_output','source_packet','target_input','mappings','projection_basis','supplemental']:(stem/(k+'.json')).write_text(json.dumps(c[k],indent=2)+'\n')
 outcome=attempt(c);projection=outcome.pop('projection',None)
 if projection:(stem/'projection.json').write_text(json.dumps(projection,indent=2)+'\n')
 amended.append({'id':'amended-pair'+str(i)+'-valid-link','expected_acceptance':True,'passed':outcome['accepted'] and not outcome.get('reconstruction_errors'),**outcome})
 for mutation in ['native-subject','version','label-fact','dropped-source','authority-tamper']:
  changed=copy.deepcopy(c);target=changed['target_input']
  if mutation=='native-subject':
   if i==1:
    set_claim(target,target['data']['scope']['scenario_id'],'UNRELATED-FW-2')
    for row in target['data']['observations']:set_claim(target,row['scenario_id'],'UNRELATED-FW-2')
    set_claim(target,target['data']['operations']['scenario_id'],'UNRELATED-FW-2')
   else:
    for section,rows in target['data'].items():
     if isinstance(rows,list):
      for row in rows:
       if 'case_id' in row:set_claim(target,row['case_id'],'UNRELATED-FW-2')
       if 'native_case_id' in row:row['native_case_id']='UNRELATED-FW-2'
    for field in ['population_case_ids','selected_case_ids']:set_claim(target,target['data']['mandate'][field],['UNRELATED-FW-2'])
  if mutation=='version':
   claim=target['data']['scope']['scenario_version'] if i==1 else target['data']['cases'][0]['upstream_native_version'];set_claim(target,claim,'UNRELATED-VERSION')
  if mutation=='label-fact':
   if i==1:target['data']['scope']['scenario_id']['fact_ids']=['INVENTED-LINKAGE-FACT']
   else:target['data']['cases'][0]['case_id']['fact_ids']=['INVENTED-LINKAGE-FACT']
  if mutation=='dropped-source':target['sources']=[a for a in target['sources'] if a['source_ref'] not in {r['source_ref'] for r in s['sources']}]
  changed['supplemental']={'detached_receiver':copy.deepcopy(target)}
  if mutation=='authority-tamper':
   forged=copy.deepcopy(projection);forged['authority_granted']=True
   errors=validate_review_projection(forged,s,**kwargs(c));outcome={'accepted':not bool(errors),'error':'; '.join(errors)}
  else:outcome=attempt(changed);outcome.pop('projection',None)
  amended.append({'id':'amended-pair'+str(i)+'-'+mutation,'expected_acceptance':False,'passed':not outcome['accepted'],**outcome})
 # Actual CLI builds, verifies and checks detached input tamper and strict JSON.
 command=[sys.executable,'-B',str(ROUTER/'scripts/project_review.py'),'--source-package',str(package(c['producer'])),'--receiver-package',str(package(c['receiver']))]
 for arg,key in [('source-input','source_input'),('source-packet','source_packet'),('target-input','target_input'),('mappings','mappings'),('projection-basis','projection_basis'),('supplemental','supplemental')]:command+=['--'+arg,str(stem/(key+'.json'))]
 built=subprocess.run(command,capture_output=True,text=True,timeout=60);(stem/'cli-projection.json').write_text(built.stdout)
 verified=subprocess.run(command+['--verify',str(stem/'cli-projection.json')],capture_output=True,text=True,timeout=60)
 amended.append({'id':'amended-pair'+str(i)+'-cli-build-verify','expected_exit':0,'build_exit':built.returncode,'verify_exit':verified.returncode,'passed':built.returncode==0 and verified.returncode==0,'verify_output':verified.stdout+verified.stderr})
 forged=read(stem/'cli-projection.json');forged['target_input']['request_id']='FABRICATED-REQUEST';(stem/'cli-tamper.json').write_text(json.dumps(forged))
 rejected=subprocess.run(command+['--verify',str(stem/'cli-tamper.json')],capture_output=True,text=True,timeout=60)
 amended.append({'id':'amended-pair'+str(i)+'-cli-detached-tamper','expected_rejection':True,'exit':rejected.returncode,'passed':rejected.returncode!=0,'output':rejected.stdout+rejected.stderr})
 original_mapping=(stem/'mappings.json').read_text();(stem/'mappings.json').write_text('{"double":1,"double":2}')
 rejected=subprocess.run(command,capture_output=True,text=True,timeout=60);(stem/'mappings.json').write_text(original_mapping)
 amended.append({'id':'amended-pair'+str(i)+'-cli-duplicate-key','expected_rejection':True,'exit':rejected.returncode,'passed':rejected.returncode!=0 and 'duplicate JSON' in rejected.stdout,'output':rejected.stdout+rejected.stderr})
report={'scope':'Independent explicitly amended linkage cases with actual installed validators; no source/professional acceptance','passed':all(r['passed'] for r in amended),'checks':len(amended),'results':amended}
(OUT/'amended-results.json').write_text(json.dumps(report,indent=2)+'\n')
print('Frozen raw replay: former unrelated-subject accepted cases are now rejected; original baselines also reject because they predate the explicit native linkage contract')
print('Amended valid-link replay:',report['checks'],'checks','PASS' if report['passed'] else 'FAIL')
for result in amended:
 if not result['passed']:print(json.dumps(result))
