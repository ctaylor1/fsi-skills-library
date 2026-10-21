import copy,json,hashlib,subprocess,sys,shutil,os
from pathlib import Path
ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');OUT=Path(__file__).resolve().parent
h=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
base=json.loads((OUT/'base-input.json').read_text());context={k:copy.deepcopy(base[k]) for k in ('request_id','purpose','audience','subject','as_of','use_on','knowledge_cutoff','information_barrier','sources','evidence_refs','unresolved_issues')}
context['sources']=[context['sources'][0]];context['evidence_refs']=[context['evidence_refs'][0]]

def compute(name,doc,root=ROOT):
 p=subprocess.run([sys.executable,'-B',str(root/'skills/investment-research'/name/'scripts/calculate_or_transform.py')],input=json.dumps(doc),text=True,capture_output=True)
 if p.returncode:raise ValueError(p.stdout+p.stderr)
 return json.loads(p.stdout)

def updater(kind):
 original=json.loads((ROOT/'skills/investment-research'/kind/'evals/files/phase2-input.json').read_text());original.update(copy.deepcopy(context));original['request_id']='fresh-'+kind+'-original'
 if kind=='three-statement-model-builder':
  m=original['model_input'];m['company_id']=context['subject']['id'];m['company']='Fresh Operating Company';m['ticker']='FRESH';m['as_of']=context['as_of']
  for record in ('income_statement','balance_sheet'):
   for key in m['historical'][record]:m['historical'][record][key]*=2
  for name,driver in m['drivers'].items():driver['source']='synthetic:release-v2#'+name
  path='/model_input/drivers/revenue_growth/value';prior=.1;replacement=.09
 else:
  original['forecast_rows']=[]
  for year,revenue,ebit,depreciation,capex,nwc in [(2026,500,60,10,15,5),(2027,550,75,12,18,7)]:
   nopat=ebit*.75;original['forecast_rows'].append({'year':year,'period_start':str(year)+'-01-01','period_end':str(year)+'-12-31','revenue':revenue,'ebit':ebit,'depreciation':depreciation,'capex':capex,'delta_nwc':nwc,'tax_rate':.25,'nopat':nopat,'ufcf':nopat+depreciation-capex-nwc,'currency':original['currency'],'units':original['units'],'accounting_basis':original['accounting_basis'],'consolidation_scope':original['consolidation_scope']})
  original['diluted_shares']=20;original['bridge']={'total_debt':80,'cash_and_equivalents':30,'minority_interest':0,'preferred_equity':0,'investments_associates':0};original['discounting']='end_year';original['valuation_subject']={'security_id':'FRESH-A','share_class':'A','share_count_basis':'fully-diluted-A'}
  path='/wacc';prior=.1;replacement=.13
 dates={k:context[k] for k in ('as_of','knowledge_cutoff','use_on')}
 doc=copy.deepcopy(context);doc.update({k:original[k] for k in ('currency','units','accounting_basis','consolidation_scope')})
 doc.update(schema_version='ir-phase3/1.0',model_kind=kind,model_id='FRESH-MODEL',base_version='v8',proposed_version='v9',original_model=original,original_model_hash=h(original),observed_current={'version':'v8','input_hash':h(original)},context_transition={'mode':'same-snapshot','from':dates,'to':copy.deepcopy(dates),'rationale':'Fresh scenario input revision before internal review','evidence_refs':copy.deepcopy(context['evidence_refs'])},required_update_paths=[path],patches=[{'patch_id':'fresh-parameter','path':path,'before_hash':h(prior),'value':replacement,'rationale':'Explicit supplied scenario assumption','evidence_refs':copy.deepcopy(context['evidence_refs'])}])
 output=compute('financial-model-update-preparer',doc)
 return {'adapter_id':'model-update-to-'+('dcf' if kind=='dcf-modeler' else 'three-statement'),'producer_input':doc,'producer_output':output,'receiver_input':copy.deepcopy(output['results']['candidate_input'])}

def event():
 doc=copy.deepcopy(context);doc.update(schema_version='ir-phase3-event/1.0',valuation_subject={'security_id':'FRESH-A','share_class':'A','share_count_basis':'fully-diluted-A'},financial_basis={'currency':'USD','units':'millions','share_units':'millions','accounting_basis':'IFRS','consolidation_scope':'consolidated'},baseline={'balance_date':'2026-09-30','known_at':'2026-10-20T13:00:00Z','cash':125,'debt':210,'shares':25,'evidence_refs':copy.deepcopy(context['evidence_refs'])},event={'event_id':'FRESH-EQUITY-RAISE','type':'equity-raise','status':'announced','announcement_date':'2026-10-20','effective_date':'2026-11-15','known_at':'2026-10-20T13:00:00Z','scenario_label':'Conditional funding closes on announced terms','evidence_refs':copy.deepcopy(context['evidence_refs']),'terms':{'shares_issued':3,'issue_price':18,'fees':2}})
 target=copy.deepcopy(context);target.update(review_scope={'required_checks':['sections','claim_evidence','arithmetic','contradictions','comparability','risks','disclosures'],'required_sections':['event-bridge'],'required_claim_ids':['event-'+state+'-'+component for state in ('before','change','after') for component in ('cash','debt','net_debt','shares')],'required_arithmetic_ids':['event-'+state+'-net-debt' for state in ('before','change','after')],'required_risks':['event-funding'],'required_disclosures':['event-conditionality'],'inventory_complete':True},packet={})
 return {'adapter_id':'event-impact-to-quality','producer_input':doc,'producer_output':compute('corporate-event-impact-reviewer',doc),'receiver_input':target}

requests={'fresh-three-statement':updater('three-statement-model-builder'),'fresh-dcf':updater('dcf-modeler'),'fresh-event-quality':event()}
bad=copy.deepcopy(requests['fresh-dcf']);bad['receiver_input']['wacc']=.14;requests['candidate-conflict']=bad
bad=copy.deepcopy(requests['fresh-three-statement']);bad['producer_output']['results']['patch_ledger']=[];requests['producer-ledger-tamper']=bad
bad=copy.deepcopy(requests['fresh-event-quality']);bad['receiver_input']['review_scope']['required_risks']=[];requests['event-risk-coverage-omitted']=bad
bad=copy.deepcopy(requests['fresh-event-quality']);bad['producer_input']['unresolved_issues']=['Source authenticity remains unverified beyond metadata'];bad['producer_output']=compute('corporate-event-impact-reviewer',bad['producer_input']);requests['event-inherited-issue']=bad
results=[]
def invoke(name,doc,entry=ROOT/'tools/review_ir_handoff.py',library=ROOT):
 ip=OUT/(name+'-request.json');ip.write_text(json.dumps(doc,indent=2)+'\n')
 p=subprocess.run([sys.executable,'-B',str(entry),str(ip),'--library-root',str(library)],capture_output=True,text=True,env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}})
 op=OUT/(name+'-handoff.json' if not p.returncode else name+'-error.txt');op.write_text(p.stdout+p.stderr)
 row={'case':name,'exit_code':p.returncode,'request_hash':h(doc),'entrypoint':str(entry),'library':str(library),'output_sha256':hashlib.sha256(op.read_bytes()).hexdigest()}
 if not p.returncode:
  out=json.loads(p.stdout);row.update(package_manifest_hashes=out['package_manifest_hashes'],adapter_hash=out['adapter_implementation_hash'],registry_hash=out['registry_hash'],status=out['status'],receiver_results=out['receiver_output']['results'],unresolved_issues=out['unresolved_issues'])
  v=subprocess.run([sys.executable,'-B',str(entry),str(op),'--library-root',str(library),'--input',str(ip)],capture_output=True,text=True);row['reconstruction_exit']=v.returncode
 else:row['error']=p.stdout+p.stderr
 results.append(row);return row
for name,doc in requests.items():invoke(name,doc)
# Copy only declared local package dependencies; router entrypoint must work from its bundled helpers.
lib=OUT/'isolated-library';(lib/'catalog').mkdir(parents=True,exist_ok=True)
for name in ('investment-research-capabilities.json','investment-research-adapters.json'):shutil.copy2(ROOT/'catalog'/name,lib/'catalog'/name)
for name in ('investment-research-router','financial-model-update-preparer','three-statement-model-builder','dcf-modeler','corporate-event-impact-reviewer','research-quality-reviewer'):
 shutil.copytree(ROOT/'skills/investment-research'/name,lib/'skills/investment-research'/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
entry=lib/'skills/investment-research/investment-research-router/scripts/review_handoff.py'
invoke('isolated-router-dcf',requests['fresh-dcf'],entry,lib)
# An added unpinned file and a changed pinned file must both be rejected.
package=lib/'skills/investment-research/research-quality-reviewer';extra=package/'scripts/undeclared.py';extra.write_text('raise RuntimeError("should never run")\n');invoke('isolated-extra-unpinned',requests['fresh-event-quality'],entry,lib);extra.unlink()
script=package/'scripts/domain.py';script.write_text(script.read_text()+'\n# unexpected local drift\n');invoke('isolated-modified-pinned',requests['fresh-event-quality'],entry,lib)
(OUT/'adapters-run.json').write_text(json.dumps({'results':results},indent=2)+'\n')
for row in results:
 r=row.get('receiver_results') or {};summary={k:row[k] for k in ('case','exit_code')};summary.update(error=row.get('error'),reconstruction=row.get('reconstruction_exit'),readiness=r.get('readiness'))
 if row['case'] in {'fresh-dcf','isolated-router-dcf'}:
  expected=35/1.13+43.25/(1.13**2)+(43.25*1.02/(.13-.02))/(1.13**2)
  assert abs(r['enterprise_value']-expected)<1e-8;assert abs(r['value_per_share']-(expected-50)/20)<1e-8;summary['independent_enterprise_value']=expected
 if row['case']=='fresh-three-statement':assert abs(r['forecast_rows'][0]['revenue']-2180)<1e-8;assert abs(r['forecast_rows'][1]['revenue']-2376.2)<1e-8
 if row['case']=='fresh-event-quality' and row['exit_code']==0:
  handoff=json.loads((OUT/(row['case']+'-handoff.json')).read_text());claims={c['claim_id']:c for c in handoff['receiver_input']['packet']['claims']};assert claims['event-after-cash']['value']==177;assert claims['event-after-net_debt']['value']==33;assert claims['event-after-shares']['value']==28;assert len(r['arithmetic_results'])==3;assert r['readiness']=='review-required'
 print(json.dumps(summary))
(OUT/'adapters-run.json').write_text(json.dumps({'results':results},indent=2)+'\n')
