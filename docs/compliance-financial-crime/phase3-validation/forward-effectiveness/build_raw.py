from pathlib import Path
import copy,json
base=Path('/tmp/cfc-phase3-forward-effectiveness')
def save(name,value): (base/name).write_text(json.dumps(value,indent=2)+'\n')
class Raw:
 def __init__(self,name,objtype,sources):
  self.name=name; self.sources=[{'source_ref':s,'version':'independent-forward-1','publication_date':'2026-10-01','received_at':'2026-10-04','classification':'compliance_confidential','permitted_audiences':['internal_compliance'],'facts':[]} for s in sources]
  self.index={s['source_ref']:s for s in self.sources}
  self.doc={'request_id':'forward-'+name,'object_id':'review-'+name,'object_type':objtype,'as_of':'2026-10-04','knowledge_cutoff':'2026-10-04','workflow':{'context':{'institution_id':'Example-FI','legal_entity_id':'Example-Entity','capacity':'second line compliance','represented_party':'Example-FI','object_id':'review-'+name,'object_type':objtype,'jurisdiction':'US-reviewed-profile','line_of_business':'corporate payments','purpose':'bounded professional review of supplied evidence'},'as_of':'2026-10-04','role':'oversight','classification':'compliance_confidential','audience':'internal_compliance','allowed_audiences':['internal_compliance'],'unresolved_issues':['Professional source authenticity remains unverified'],'sources':[{'source_ref':s,'version':'independent-forward-1'} for s in sources]},'sources':self.sources,'data':{}}
 def c(self,value,name,source):
  fid=self.name+':'+name
  self.index[source]['facts'].append({'fact_id':fid,'value':copy.deepcopy(value),'excerpt':'Independent synthetic raw evidence for '+name})
  return {'value':copy.deepcopy(value),'source_refs':[source],'fact_ids':[fid]}
 def obj(self,values,name,source): return {k:self.c(v,name+'.'+k,source) for k,v in values.items()}
 def row(self,key,name,values,source): return {key:name,**self.obj(values,name,source)}
def change(doc,collection,index,field,value):
 row=doc['data'][collection] if index is None else doc['data'][collection][index]
 claim=row[field];claim['value']=copy.deepcopy(value)
 for source in doc['sources']:
  for fact in source['facts']:
   if fact['fact_id'] in claim['fact_ids']:fact['value']=copy.deepcopy(value)

m=Raw('M2','transaction_monitoring_effectiveness_review',['scope-record','reference-labels','engine-record','technology-record','operations-record','benchmark-record'])
pop=['txn-1','txn-2','txn-3','txn-4','txn-5','txn-6'];sample=pop[:4]
m.doc['data']['scope']=m.obj({'review_id':'review-M2','scenario_id':'cross-border-velocity','scenario_version':'v7','engine_id':'monitor-engine','engine_version':'build-19','population_id':'September-FI-payments','population_unit':'transaction','population_definition':'Distinct settled September corporate-payment transaction IDs','population_ids':pop,'window_from':'2026-09-01','window_to':'2026-09-30','cohort':'corporate-USD','expected_count':6,'received_count':6,'extract_complete':True,'reconciliation_reference':'reconcile-September-v2','data_available_through':'2026-09-30','freshness_criterion':'All September settled transaction events available for review by October 1','freshness_met':True,'mapping_dataset_id':'party-crosswalk','identifier_namespace':'FI-payment-id','entity_mapping_ref':'mapping-review-7','entity_mapping_version':'map-v7','ambiguous_link_count':0,'conflicting_link_count':0,'graph_reference':'reviewed-linkage-graph','graph_version':'graph-v3','identity_limitations':'Mapped identifiers are supplied, without identity authentication'},'scope','scope-record')
m.doc['data']['selection']=m.obj({'sample_ids':sample,'sampling_method':'Targeted non-probability holdout challenge sample','selection_frame_reference':'reviewed-independent-selection-frame','selection_limitations':'Four selected challenge transactions do not establish population prevalence','label_definition':'Accepted target-pattern reference, not crime or SAR disposition','label_reference_domain':'FI-reviewed-target-pattern','label_reference_version':'reference-v2','label_acceptance_reference':'signed-review-record','label_owner':'Reference review committee','label_limitations':'Reference classifications remain supplied and unverified','independent_assessment':True,'operational_involvement':False,'conflict_review':True,'reporting_line_review':True,'independence_review_reference':'reviewer-independence-record','leakage_assessed':True,'leakage_free':True,'training_item_ids':[]},'selection','reference-labels')
m.doc['data']['criteria']=m.obj({'minimum_precision':'0.5','minimum_recall':'0.5','unit':'fraction','owner':'Effectiveness review committee','review_reference':'criteria-record-v2','basis':'Bounded selected-sample comparison'},'criteria','reference-labels')
m.doc['data']['operations']=m.obj({'scenario_id':'cross-border-velocity','scenario_version':'v7','population_id':'September-FI-payments','cohort':'corporate-USD','window_from':'2026-09-01','window_to':'2026-09-30','completed_reviews':4,'analyst_minutes':'240','total_cost':None,'currency':'USD','cost_accounting':'gross','outcomes_reference':'analyst-completion-record','cost_limitations':'Cost ledger unavailable; do not infer zero cost'},'operations','operations-record')
m.doc['data']['observations']=[]
for i,(detected,label) in enumerate([(True,'positive'),(True,'negative'),(False,'positive'),(False,'negative'),(None,None),(False,None)],1):
 row=m.row('observation_id','obs-'+str(i),{'item_id':'txn-'+str(i),'scenario_id':'cross-border-velocity','scenario_version':'v7','engine_id':'monitor-engine','engine_version':'build-19','population_id':'September-FI-payments','cohort':'corporate-USD','event_on':'2026-09-29','observed_on':'2026-10-01','detected':detected,'engine_observation_reference':'engine-observation-'+str(i),'label':label,'label_reference_domain':'FI-reviewed-target-pattern','label_reference_version':'reference-v2','label_record_reference':'adjudication-'+str(i) if label else None,'label_reviewed':True if label else None},'engine-record')
 for key in ['label','label_reference_domain','label_reference_version','label_record_reference','label_reviewed']:
  old=row[key];m.index['engine-record']['facts']=[f for f in m.index['engine-record']['facts'] if f['fact_id']!=old['fact_ids'][0]]
  row[key]=m.c(old['value'],'labels-'+str(i)+'.'+key,'reference-labels')
 m.doc['data']['observations'].append(row)
m.doc['data']['benchmark_references']=[m.row('benchmark_reference_id','bench-1',{'reference_domain':'external challenge study','reference_version':'study-v3','context':'Different synthetic cohort and engine; context only','claim':'Published study states precision 0.99','limitation':'Not an institutional observation or acceptance threshold'},'benchmark-record')]
m.doc['data']['technology_requirements']=[m.row('technology_requirement_id','tech-1',{'kind':'model','profile_id':'reviewed-monitoring-model-controls','profile_version':'profile-v2','requirement':'Same-version holdout and provenance review recorded','owner':'Model controls owner','review_reference':'model-control-record','requirement_supported':True,'limitation':'Supplied evidence only; no model validation opinion'},'technology-record')]
save('M2-original.json',m.doc)
for name,mut in [
 ('M2-unknown-selected-label',lambda d:change(d,'observations',2,'label',None)),
 ('M2-late-observation',lambda d:change(d,'observations',0,'observed_on','2026-10-05')),
 ('M2-version-mismatch',lambda d:change(d,'observations',0,'engine_version','other-build')),
 ('M2-training-overlap',lambda d:change(d,'selection',None,'training_item_ids',['txn-1'])),
 ('M2-control-unknown',lambda d:change(d,'technology_requirements',0,'requirement_supported',None)),
 ('M2-exact-threshold',lambda d:change(d,'criteria',None,'minimum_recall','0.50000000000000000000000000000000001')),
 ('M2-access-denied',lambda d:d['sources'][0].update(permitted_audiences=['external-distributor'])),
 ('M2-source-conflict',lambda d:d['data']['observations'][0]['detected'].update(value=False)),
 ('M2-role-label-only',lambda d:change(d,'selection',None,'independence_review_reference',None))]:
 d=copy.deepcopy(m.doc);mut(d);save(name+'.json',d)

q=Raw('T2','financial_crime_case_quality_review',['mandate-record','case-record','qa-record','tool-record'])
pop=['case-A','case-B','case-C'];sel=pop[:2]
criteria=['exhibit','chronology','reasoning','disposition','tool-faithfulness']
q.doc['data']['mandate']=q.obj({'mandate_id':'case-quality-mandate','mandate_type':'operational-qa','mandate_owner':'Case quality lead','reviewer_id':'reviewer-Q','legal_profile_id':'reviewed-FI-case-QA','legal_profile_version':'v2','legal_profile_reviewed':True,'authority_reviewed':True,'authority_scope':'Internal QA only, no closure or SAR decision','independence_owner_assessment':True,'operational_involvement':False,'reporting_line_review':True,'conflict_review':True,'competence_review':True,'period_from':'2026-09-01','period_to':'2026-10-04','population_case_ids':pop,'selected_case_ids':sel,'sampling_method':'Targeted non-probability QA sample','sampling_rationale':'Two selected cases reviewed; third case remains untested','criteria_ids':criteria,'maximum_exception_proportion':'0'},'mandate','mandate-record')
for key in ['cases','exhibits','events','reasoning','criteria','observations','tool_outputs']:q.doc['data'][key]=[]
for case in sel:
 exhibit='ex-'+case; reason='reason-'+case
 underlying=q.c('1000.253',case+'.underlying_amount','case-record');fid=underlying['fact_ids'][0]
 q.doc['data']['cases'].append(q.row('native_case_id',case,{'case_id':case,'institution_id':'Example-FI','legal_entity_id':'Example-Entity','jurisdiction':'US-reviewed-profile','upstream_native_id':'investigation-'+case,'upstream_native_version':'v5','period_from':'2026-09-01','period_to':'2026-10-04','required_exhibit_ids':[exhibit],'concern_ids':['concern-'+case],'contradiction_ids':[],'counterevidence_ids':['counter-'+case],'disposition_reasoning_id':reason,'proposed_disposition':'Further specialist review proposed','disposition_on':'2026-09-30'},'case-record'))
 q.doc['data']['exhibits'].append(q.row('exhibit_id',exhibit,{'case_id':case,'version':'ex-v1','evidence_source_ref':'case-record','evidence_fact_ids':[fid],'available':True,'captured_on':'2026-10-01'},'case-record'))
 for number,when,kind,predecessors in [(1,'2026-09-20','activity',[]),(2,'2026-09-23','analysis',['event-1-'+case])]:
  q.doc['data']['events'].append(q.row('event_id','event-'+str(number)+'-'+case,{'case_id':case,'occurred_on':when,'predecessor_event_ids':predecessors,'exhibit_ids':[exhibit],'event_kind':kind,'statement':'Supplied case chronology event '+str(number)},'case-record'))
 q.doc['data']['reasoning'].append(q.row('reasoning_id',reason,{'case_id':case,'concern_ids':['concern-'+case],'considered_counterevidence_ids':['counter-'+case],'addressed_contradiction_ids':[],'exhibit_ids':[exhibit],'rationale':'The reviewer evaluated the documented activity and counterevidence and proposes specialist review; evidence is limited to this case.','proposed_disposition':'Further specialist review proposed','human_review_complete':True,'reviewer_id':'reviewer-Q','human_judgement':'pass'},'qa-record'))
 q.doc['data']['tool_outputs'].append(q.row('output_id','tool-'+case,{'case_id':case,'tool_name':'Case summary copilot','tool_version':'v1','model_id':'supplied-model','model_version':'m5','prompt_version':'p8','output_version':'o3','generated_on':'2026-10-01','purpose':'case-evidence-summary','proposed_facts':[{'source_ref':'case-record','fact_id':fid,'value':'1000.253'}],'exhibit_ids':[exhibit],'human_review_complete':True,'human_reviewer_id':'reviewer-Q'},'tool-record'))
for identity,kind in zip(criteria,['evidence-completeness','chronology-consistency','reasoning-traceability','disposition-traceability','tool-source-faithfulness']):
 q.doc['data']['criteria'].append(q.row('criterion_id',identity,{'kind':kind,'version':'criterion-v1','procedure':'Case-specific '+kind+' QA procedure','requirement':'Reviewed '+kind+' workpaper evidence','legal_profile_id':'reviewed-FI-case-QA','legal_profile_version':'v2','applicable_case_ids':sel},'mandate-record'))
 for case in sel:
  q.doc['data']['observations'].append(q.row('observation_id','observation-'+identity+'-'+case,{'case_id':case,'criterion_id':identity,'criterion_version':'criterion-v1','tested_on':'2026-10-03','observed_outcome':'pass','rationale':'Named reviewer applied the scoped criterion to the exact case workpaper.','exhibit_ids':['ex-'+case],'reasoning_ids':['reason-'+case],'human_reviewer_id':'reviewer-Q','human_review_complete':True},'qa-record'))
save('T2-original.json',q.doc)
for name,mut in [
 ('T2-chronology-reversal',lambda d:change(d,'events',0,'occurred_on','2026-09-24')),
 ('T2-counterevidence-omitted',lambda d:change(d,'reasoning',0,'considered_counterevidence_ids',[])),
 ('T2-partial-selected-case',lambda d:change(d,'reasoning',1,'human_judgement',None)),
 ('T2-exhibit-missing',lambda d:change(d,'exhibits',0,'available',False)),
 ('T2-tool-source-conflict',lambda d:change(d,'tool_outputs',0,'proposed_facts',[{'source_ref':'case-record','fact_id':'T2:case-A.underlying_amount','value':'999.999'}])),
 ('T2-future-observation',lambda d:change(d,'observations',0,'tested_on','2026-10-05')),
 ('T2-role-label-independent',lambda d:change(d,'mandate',None,'mandate_type','statutory-independent-testing')),
 ('T2-unknown-authority',lambda d:change(d,'mandate',None,'authority_reviewed',None)),
 ('T2-context-change',lambda d:change(d,'cases',0,'legal_entity_id','another-entity')),
 ('T2-access-denied',lambda d:d['sources'][0].update(permitted_audiences=['external']))]:
 d=copy.deepcopy(q.doc);mut(d);save(name+'.json',d)
expectations={
 'basis':'Independent expectations written before any package calculation; schemas/docs read, unit tests and expected fixture outputs not inspected. Inputs authored from raw synthetic evidence.',
 'M2-original':'Known engine observations 5: detected2/not-detected3, unknown/absent1. Population observation coverage5/6. Accepted selected sample TP1 FP1 FN1 TN1; precision/recall1/2. Optional total cost unknown must not erase those supported sample metrics; minutes per completed review60. Separate benchmark precision0.99 must not replace observations/threshold. No crime/SAR/assurance/action determination.',
 'M2-unknown-selected-label':'Selected sample unknown1; precision/recall withheld; known engine observations preserved.',
 'M2-late-observation':'Future observation is ineligible, detection denominator4, selected unknown1, sample metrics withheld.',
 'M2-version-mismatch':'Known changed engine scope rejected at intake.',
 'M2-training-overlap':'Adverse leakage withholds selected sample metrics and criteria, retaining engine observations.',
 'M2-control-unknown':'Material unknown technology control withholds favorable criteria, with source-supported sample metrics retained.',
 'M2-exact-threshold':'Exact recall0.5 fails threshold just above0.5 despite floating-point rounding.',
 'M2-access-denied':'Source access mismatch rejected at intake.',
 'M2-source-conflict':'Unsupported detected claim becomes unknown, with selected metrics withheld.',
 'M2-role-label-only':'Missing actual independence review record withholds label method even though role/boolean assertions exist.',
 'T2-original':'Two selected cases have five supported criteria each; pass10, complete-case proportion0/2, third population case untested; maximum0 comparison favorable. No closure/SAR/assurance/actions.',
 'T2-chronology-reversal':'Mechanical predecessor reversal produces known chronology exception despite supplied observation pass.',
 'T2-counterevidence-omitted':'Mechanical omission creates reasoning/disposition exceptions; observation pass cannot override.',
 'T2-partial-selected-case':'Case-B reasoning/disposition unknown; case-B outside complete-case proportion denominator; overall threshold comparison withheld.',
 'T2-exhibit-missing':'Known absent required exhibit produces exception, not hidden by supplied pass.',
 'T2-tool-source-conflict':'Known tool factual-value conflict produces source-faithfulness exception, while source truth remains unverified.',
 'T2-future-observation':'Future observation unknown and dependent threshold comparison withheld.',
 'T2-role-label-independent':'Statutory independent-testing mandate unsupported; no favorable threshold or assurance opinion, even with independence booleans.',
 'T2-unknown-authority':'Unknown authority review withholds dependent favorable threshold.',
 'T2-context-change':'Changed legal-entity context rejected at intake.',
 'T2-access-denied':'Source audience mismatch rejected at intake.'}
save('before-run-expectations.json',expectations)
print('Saved 21 independently authored raw intakes and before-run expectations')
