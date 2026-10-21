from pathlib import Path
import copy,json,subprocess,sys
base=Path('/tmp/cfc-phase3-forward-effectiveness');root=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime')
def change(doc,collection,index,field,value):
 row=doc['data'][collection] if index is None else doc['data'][collection][index]
 claim=row[field];claim['value']=copy.deepcopy(value)
 for source in doc['sources']:
  for fact in source['facts']:
   if fact['fact_id'] in claim['fact_ids']:fact['value']=copy.deepcopy(value)
def save(name,data):(base/name).write_text(json.dumps(data,indent=2)+'\n')
doc=json.loads((base/'T2-complete-original.json').read_text())
for i,row in enumerate(doc['data']['observations']):
 case=row['case_id']['value'];change(doc,'observations',i,'exhibit_ids',['ex-'+case,'counter-'+case])
variants={'original':lambda d:None,'chronology-reversal':lambda d:change(d,'events',0,'occurred_on','2026-09-24'),
'counterevidence-omitted':lambda d:change(d,'reasoning',0,'considered_counterevidence_ids',[]),
'partial-selected-case':lambda d:change(d,'reasoning',1,'human_judgement',None),
'exhibit-missing':lambda d:change(d,'exhibits',0,'available',False),
'tool-source-conflict':lambda d:change(d,'tool_outputs',0,'proposed_facts',[{'source_ref':'case-record','fact_id':'T2:case-A.underlying_amount','value':'999.999'}]),
'future-observation':lambda d:change(d,'observations',0,'tested_on','2026-10-05'),
'role-label-independent':lambda d:change(d,'mandate',None,'mandate_type','statutory-independent-testing'),
'unknown-authority':lambda d:change(d,'mandate',None,'authority_reviewed',None),
'context-change':lambda d:change(d,'cases',0,'legal_entity_id','another-entity'),
'access-denied':lambda d:d['sources'][0].update(permitted_audiences=['external'])}
for name,mutate in variants.items():
 raw=copy.deepcopy(doc);mutate(raw);save('T2-scoped-'+name+'.json',raw)
save('before-run-scoped-expectations.json',{'basis':'Written before calculations of scoped intakes: prior added counterevidence exhibits also require linking them to each performed observation. Prior inputs/outputs/expectations preserved; native unknowns accurately exposed both incomplete workpaper conditions.','original':'pass10/fail0/unknown0;2completecases;exception0/2;threshold true;case-Cpopulation untested.','chronology-reversal':'Known predecessor exception retained despite supplied pass.','counterevidence-omitted':'Known reasoning/disposition inventory exception retained.','partial-selected-case':'Case-B excluded from complete-case denominator; threshold null.','exhibit-missing':'Known evidence exception, no favorable comparison.','tool-source-conflict':'Known exact fact mismatch; source-faithfulness fail, no favorable comparison.','future-observation':'Unknown future observation; threshold null.','role-label-independent':'Unsupported mandate; threshold null, no assurance.','unknown-authority':'Unknown authority;threshold null.','context-change':'intake rejection','access-denied':'intake rejection'})
commands=[]
for name in variants:
 path=base/('T2-scoped-'+name+'.json');pkg=root/'financial-crime-case-quality-reviewer'
 command=[sys.executable,'-B',str(pkg/'scripts/calculate_or_transform.py'),str(path)]
 proc=subprocess.run(command,capture_output=True,text=True,cwd=base)
 (base/(path.stem+'-stderr.txt')).write_text(proc.stderr)
 entry={'input':path.name,'command':command,'actual_exit':proc.returncode}
 if proc.returncode==0:
  output=base/(path.stem+'-result.json');output.write_text(proc.stdout)
  vcmd=[sys.executable,'-B',str(pkg/'scripts/validate_output.py'),str(output),'--input',str(path)]
  valid=subprocess.run(vcmd,capture_output=True,text=True,cwd=base);(base/(path.stem+'-validation.json')).write_text(valid.stdout)
  entry.update(validation_command=vcmd,validation_exit=valid.returncode)
 commands.append(entry)
save('scoped-commands-and-exits.json',commands)
for name in variants:
 path=base/('T2-scoped-'+name+'-result.json')
 if path.exists():
  out=json.loads(path.read_text());r=out['results']
  print(name,json.dumps({key:r[key] for key in ['observed_criterion_counts','coverage','observed_case_exception_proportion','within_supplied_exception_threshold']}))
 else:print(name,'rejected')
