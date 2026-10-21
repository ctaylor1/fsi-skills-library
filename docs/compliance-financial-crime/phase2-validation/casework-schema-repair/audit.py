from pathlib import Path
import json, sys, subprocess, hashlib, importlib.metadata, copy
from jsonschema import Draft202012Validator, FormatChecker
R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library'); B=R/'skills/compliance-financial-crime'; D=R/'docs/compliance-financial-crime/phase2-validation'; T=D/'casework-schema-repair/native-artifacts'; T.mkdir(parents=True,exist_ok=True)
skills=['financial-crime-case-investigator','sanctions-exposure-reviewer','financial-crime-information-sharing-reviewer','financial-crime-reporting-reviewer','compliance-regulatory-notification-reviewer','customer-due-diligence-reviewer','enhanced-due-diligence-assessor']; records=[]; negatives=[]; validators={}
for skill in skills:
 validators[skill]={}
 for kind in ('input','output'):
  p=B/skill/'references'/f'{kind}-schema.json'; s=json.loads(p.read_text()); Draft202012Validator.check_schema(s); validators[skill][kind]=Draft202012Validator(s,format_checker=FormatChecker())
def test(skill,kind,path,label):
 obj=json.loads(path.read_text()); errors=[{'path':'/'+ '/'.join(str(x) for x in e.absolute_path),'message':e.message} for e in validators[skill][kind].iter_errors(obj)]; records.append({'skill':skill,'kind':kind,'label':label,'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'execution_context_present':('execution_context' in obj) if kind=='input' else None,'valid':not errors,'errors':errors}); return obj

def cli(skill,inp,out):
 p=subprocess.run([sys.executable,'-B',str(B/skill/'scripts/calculate_or_transform.py'),str(inp)],capture_output=True,text=True)
 if p.returncode: raise RuntimeError(skill+' calculation failed '+p.stdout+p.stderr)
 out.write_text(p.stdout)
 p=subprocess.run([sys.executable,'-B',str(B/skill/'scripts/validate_output.py'),str(out),'--input',str(inp)],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(skill+' detached failed '+p.stdout+p.stderr)
for skill in skills:
 fixture=B/skill/'evals/files'; test(skill,'input',fixture/'phase2_input.json','happy-intake'); good=test(skill,'output',fixture/'phase2_golden.json','happy-golden')
 # Native needs-evidence branches caused by an absent registry, preserving structurally valid claims.
 partial=json.loads((fixture/'phase2_input.json').read_text()); partial['sources']=[]; partial['workflow']['sources']=[]
 ip=T/(skill+'-partial-input.json'); op=T/(skill+'-partial-output.json'); ip.write_text(json.dumps(partial,indent=2)+'\n'); cli(skill,ip,op); test(skill,'input',ip,'partial-intake'); test(skill,'output',op,'partial-native-output')
 for field,value in [('action_taken',True),('human_review_required',False),('approval','approved'),('execution','performed'),('skill','other-skill'),('object_type','other-type'),('source_truth','verified'),('audience','')]:
  bad=copy.deepcopy(good);bad[field]=value; rejected=not validators[skill]['output'].is_valid(bad); negatives.append({'skill':skill,'alteration':field,'rejected':rejected})
 bad=copy.deepcopy(good); del bad['context']['institution_id']; negatives.append({'skill':skill,'alteration':'missing context institution','rejected':not validators[skill]['output'].is_valid(bad)})
 bad=copy.deepcopy(good);bad['classification']='sar_restricted';bad['audience']='authorized_analyst';negatives.append({'skill':skill,'alteration':'restricted SAR wrong audience','rejected':not validators[skill]['output'].is_valid(bad)})
# Derived quantities retain their normal types even though source observations may vary.
computed_paths={
'financial-crime-case-investigator':['results','flow_links',0,'amount'],
'sanctions-exposure-reviewer':['results','direct_blocked_ownership_pct'],
'financial-crime-information-sharing-reviewer':['results','send_authorized'],
'financial-crime-reporting-reviewer':['results','obligation_reviews',0,'amount'],
'compliance-regulatory-notification-reviewer':['results','notification_reviews',0,'applicable'],
'customer-due-diligence-reviewer':['results','observed_activity_total'],
'enhanced-due-diligence-assessor':['results','wealth_funds_assessments',0,'corroborated_amount']}
for skill,path in computed_paths.items():
 bad=json.loads((B/skill/'evals/files/phase2_golden.json').read_text());v=bad
 for key in path[:-1]:v=v[key]
 v[path[-1]]='true' if isinstance(v[path[-1]],bool) else 100.5
 negatives.append({'skill':skill,'alteration':'derived quantity wrong JSON type','rejected':not validators[skill]['output'].is_valid(bad)})
# Three explicit EDD identities regressions.
edd='enhanced-due-diligence-assessor'
for stem in ('economic_event_duplicate','economic_event_equal_distinct','economic_event_missing_identity'):
 test(edd,'input',B/edd/'evals/files'/f'{stem}_input.json',stem+'-intake'); test(edd,'output',B/edd/'evals/files'/f'{stem}_golden.json',stem+'-golden')
# Additional unresolved economic-event branches retain typed withheld fields.
def sourced(d,value):
 fid='schema-event-fact-'+str(len(d['sources'][0]['facts'])+1)
 d['sources'][0]['facts'].append({'fact_id':fid,'value':copy.deepcopy(value),'excerpt':'Synthetic schema branch exact value: '+json.dumps(value)})
 return {'value':copy.deepcopy(value),'source_refs':[d['sources'][0]['source_ref']],'fact_ids':[fid]}
for stem in ('conflicting-economic-event','missing-additivity'):
 d=json.loads((B/edd/'evals/files/phase2_input.json').read_text());r=d['data']['wealth_funds_claims'][0]
 if stem=='missing-additivity':r.pop('additivity')
 else:
  c=copy.deepcopy(r['corroboration'][0]);c['evidence_id']='SECOND-SOURCE-DOCUMENT'
  for key in ('amount','date','currency_evidence','description'):c[key]=sourced(d,c[key]['value'])
  c['amount']=sourced(d,'101.10');v=copy.deepcopy(c['economic_event']['value']);v['amount']='101.10';c['economic_event']=sourced(d,v);r['corroboration'].append(c)
 ip=T/(stem+'-input.json');op=T/(stem+'-output.json');ip.write_text(json.dumps(d,indent=2)+'\n');cli(edd,ip,op);test(edd,'input',ip,stem+'-intake');test(edd,'output',op,stem+'-native-output')
# Original raw forward inputs run through current calculators into separate outputs. Originals remain untouched.
for ip in sorted((D/'forward').glob('*/input.initial.json')):
 obj=json.loads(ip.read_text()); skill=obj.get('skill')
 if skill not in skills:
  lookup={'customer':'customer-due-diligence-reviewer' if obj.get('mode')=='lifecycle' else 'enhanced-due-diligence-assessor','financial_crime_case':'financial-crime-case-investigator'}
  skill=lookup.get(obj.get('object_type'))
 if skill not in skills: continue
 op=T/(ip.parent.name+'-current-output.json'); test(skill,'input',ip,'raw-forward-original-intake')
 try: cli(skill,ip,op)
 except RuntimeError as e:
  if ip.parent.name not in ('cdd-duplicate-receipt','mule-duplicate-identity'): raise
  records[-1]['native_outcome']='rejected duplicated monetary provenance; no native output generated'; continue
 test(skill,'output',op,'raw-forward-current-output')
f=D/'forward/edd-duplicated-economic-event'
for iname,oname,label in [('input.initial.json','output.repaired-original.json','original-withheld-replay'),('input.amended-event-identity.json','output.amended-event-identity.json','amended-event-replay')]:
 test(edd,'input',f/iname,label+'-intake');test(edd,'output',f/oname,label+'-output')
audit=json.loads((D/'forward-governance/post-repair-replay/schema-compatibility-audit.json').read_text())
for row in audit['cases']:
 for kind in ('input','output'):test(row['skill'],kind,R/row[kind]['artifact'],'independent-governance-'+row['case_id'])
i2=json.loads((B/'financial-crime-case-investigator/evals/files/phase2_input.json').read_text());i2['execution_context']=None
input_type_negative={'case_investigator_execution_context_null_rejected_when_supplied':not validators['financial-crime-case-investigator']['input'].is_valid(i2)}
summary={'input_type_negative':input_type_negative,'validator':'jsonschema.Draft202012Validator with FormatChecker','jsonschema_version':importlib.metadata.version('jsonschema'),'standards_schemas_checked':14,'schema_hashes':{skill:{kind:hashlib.sha256((B/skill/'references'/f'{kind}-schema.json').read_bytes()).hexdigest() for kind in ('input','output')} for skill in skills},'input_count':sum(r['kind']=='input' for r in records),'output_count':sum(r['kind']=='output' for r in records),'passed':sum(r['valid'] for r in records),'total':len(records),'authority_negative_checks':negatives,'authority_negative_passed':sum(r['rejected'] for r in negatives if r['alteration']!='derived quantity wrong JSON type'),'derived_type_negative_passed':sum(r['rejected'] for r in negatives if r['alteration']=='derived quantity wrong JSON type'),'records':records}
(D/'casework-schema-repair-audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:summary[k] for k in ('validator','jsonschema_version','standards_schemas_checked','input_count','output_count','passed','total','authority_negative_passed','derived_type_negative_passed')},indent=2))
for row in records:
 if not row['valid']:print(row['skill'],row['label'],json.dumps(row['errors'],indent=2))
if not all(input_type_negative.values()) or any(not r['valid'] for r in records) or any(not r['rejected'] for r in negatives):sys.exit(1)
