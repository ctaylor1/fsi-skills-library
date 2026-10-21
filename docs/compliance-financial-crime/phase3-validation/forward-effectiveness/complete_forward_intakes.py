from pathlib import Path
import copy,json
base=Path('/tmp/cfc-phase3-forward-effectiveness')
def save(name,data):(base/name).write_text(json.dumps(data,indent=2)+'\n')
def change(doc,collection,index,field,value):
 row=doc['data'][collection] if index is None else doc['data'][collection][index]
 claim=row[field];claim['value']=copy.deepcopy(value)
 for source in doc['sources']:
  for fact in source['facts']:
   if fact['fact_id'] in claim['fact_ids']:fact['value']=copy.deepcopy(value)
def claim(doc,value,name):
 source=next(s for s in doc['sources'] if s['source_ref']=='case-record')
 fid='T2-forward-counter:'+name
 source['facts'].append({'fact_id':fid,'value':copy.deepcopy(value),'excerpt':'Independent supplied counterevidence exhibit '+name})
 return {'value':copy.deepcopy(value),'source_refs':['case-record'],'fact_ids':[fid]}
t2=json.loads((base/'T2-original.json').read_text())
for i,case in enumerate(['case-A','case-B']):
 underlying=claim(t2,'Counterevidence context requires specialist review',case+'.countercontext')
 values={'case_id':case,'version':'counter-v1','evidence_source_ref':'case-record','evidence_fact_ids':underlying['fact_ids'],'available':True,'captured_on':'2026-10-01'}
 t2['data']['exhibits'].append({'exhibit_id':'counter-'+case,**{k:claim(t2,v,case+'.'+k) for k,v in values.items()}})
 change(t2,'cases',i,'required_exhibit_ids',['ex-'+case,'counter-'+case])
 change(t2,'reasoning',i,'exhibit_ids',['ex-'+case,'counter-'+case])
save('T2-complete-original.json',t2)
for name,mut in [
 ('chronology-reversal',lambda d:change(d,'events',0,'occurred_on','2026-09-24')),
 ('counterevidence-omitted',lambda d:change(d,'reasoning',0,'considered_counterevidence_ids',[])),
 ('partial-selected-case',lambda d:change(d,'reasoning',1,'human_judgement',None)),
 ('exhibit-missing',lambda d:change(d,'exhibits',0,'available',False)),
 ('tool-source-conflict',lambda d:change(d,'tool_outputs',0,'proposed_facts',[{'source_ref':'case-record','fact_id':'T2:case-A.underlying_amount','value':'999.999'}])),
 ('future-observation',lambda d:change(d,'observations',0,'tested_on','2026-10-05')),
 ('role-label-independent',lambda d:change(d,'mandate',None,'mandate_type','statutory-independent-testing')),
 ('unknown-authority',lambda d:change(d,'mandate',None,'authority_reviewed',None)),
 ('context-change',lambda d:change(d,'cases',0,'legal_entity_id','another-entity')),
 ('access-denied',lambda d:d['sources'][0].update(permitted_audiences=['external']))]:
 d=copy.deepcopy(t2);mut(d);save('T2-complete-'+name+'.json',d)
m2=json.loads((base/'M2-original.json').read_text())
change(m2,'operations',None,'total_cost','120.5');change(m2,'operations',None,'analyst_minutes',None)
save('M2-cost-supported-time-unknown.json',m2)
save('before-run-additional-expectations.json',{'basis':'Amendment before new calculations: initial T2 raw workpapers had counterevidence IDs but missing actual counterevidence exhibit records. Initial unknowns were correct. New original adds source-bound counterevidence exhibit records, preserving initial artifacts and expectations. No package tests inspected.',
'T2-complete-original':'Two selected cases/five criteria each are fully supplied; all10pass, completecase0/2, threshold0favorable, population thirdcase remains untested.',
'T2-complete-variants':'Independent original scenario expectations apply; known chronology/tool/counterevidence exceptions cannot be overridden by observationpass; unknown reviewer/authority/future evidence withholds dependent comparison; mismatched context/access rejects.',
'M2-cost-supported-time-unknown':'Completed4 totalcost120.5 USD gross allows exact costpercompletedreview30.125; missinganalystminutes withholds only time measure. Supported sample metrics remain1/2.'})
print('12 further raw intakes and expectations frozen before execution')
