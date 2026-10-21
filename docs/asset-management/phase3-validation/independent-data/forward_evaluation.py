from pathlib import Path
import copy,json,subprocess,sys
root=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
p=root/'skills/asset-management/investment-data-architecture-planner';dest=root/'docs/asset-management/phase3-validation/independent-data'
sys.path.insert(0,str(p/'scripts'))
import shared_architecture
from workflow_foundation import run
refs=['architecture-evidence','architecture-artifact','dictionary','rights','entitlement-observation','research-history','queries','telemetry']
common={'source_refs':['architecture-evidence']}
components=[]
for key,cost,responsibility in [('history-store','1000','Retain licensed research history and prior assertions'),('research-reader','250','Serve exact point-in-time read requests')]:
 components.append({'component_id':key,'responsibility':responsibility,'owner':'Research Data Engineering','technology_choice':'Institution-managed bounded relational service','alternative':'Versioned object exports','tradeoff':'Indexed retrieval versus simpler archived exports','failure_domain':key,'data_classification':'Licensed research','retention_rule':'Agreement-specific retention schedule','recovery_runbook':'Restore immutable snapshot then replay observed corrections','currency':'USD','cost_period':'annual-test','cost':cost,**common})
shared={'case_id':'FORWARD-DATA-20261004','as_of':'2026-10-04','context':{'capacity':'investment-data-design-review','represented_party':'EXAMPLE-AM','object_id':'RESEARCH-HISTORY-DESIGN','jurisdiction':'TEST-INSTITUTION','line_of_business':'asset-management'},'sources':[{'source_ref':'architecture-evidence','version':'17','as_of':'2026-10-04','locator':'Synthetic independent component measurements'}],'unresolved_issues':[],'data':{'profile':{'profile_id':'ARCH-DESIGN','version':'4','reviewed_by':'Synthetic institution architect','jurisdictions':['TEST-INSTITUTION'],'lines_of_business':['asset-management'],'effective_from':'2026-01-01','effective_to':'2026-12-31','method':'component-interface-requirements-v1',**common},'business_outcome':'Replay what licensed analyst data was known before and after a correction','owner':'Research data owner','currency':'USD','cost_period':'annual-test','scope':'One licensed field on exact namespaced security identifiers','inventory_complete':True,'components':components,'interfaces':[{'interface_id':'history-read','from_component':'research-reader','to_component':'history-store','contract_version':'read-contract-2','payload_schema':'Exact field and namespaced security with valid/known days','purpose':'historical-research','authentication':'Institution workload identity','authorization_scope':'Named analyst research principal and licensed dataset','encryption':'Institution-approved TLS','timeout':'2 seconds','failure_route':'Return unavailable; alert research-data owner','trace_id':'request-id','delivery':'synchronous','operation':'read','purpose_reviewed':True,'max_attempts':1,**common}],'requirements':[{'requirement_id':'read-latency','component_id':'research-reader','metric':'mean_read_latency','unit':'milliseconds','owner':'Research data owner','workload_profile':'100 synthetic point-in-time lookup requests','operator':'<=','threshold':'600',**common}],'measurements':[{'requirement_id':'read-latency','component_id':'research-reader','metric':'mean_read_latency','unit':'milliseconds','workload_profile':'100 synthetic point-in-time lookup requests','observed_on':'2026-10-03','value':'550',**common}]}}
doc={'request_id':'FORWARD-DATA-20261004','object_id':'RESEARCH-HISTORY-DESIGN','as_of':'2026-10-04','knowledge_cutoff':'2026-10-04','currency':'USD','audience':'internal-review','sources':[{'source_ref':k,'version':'17' if k=='architecture-evidence' else '1','as_of':'2026-10-04','known_at':'2026-10-04','locator':'Independent synthetic '+k} for k in refs],'unresolved_issues':[],'purpose':'historical-research','principal':'analyst-research-reader','snapshot_id':'history-export-20261004','owner':'Research data owner','shared_reviews':{'architecture':{'input':shared,'output':run(shared,'solution-architecture-planner',shared_architecture.evaluate,shared_architecture.validate),'source_ref':'architecture-artifact'}},'datasets':[{'dataset_id':'research-targets','owner':'Research data owner','classification':'Licensed research','retention_rule':'Preserve revisions for agreement-authorized replay','component_id':'history-store','license_id':'research-license','grain_dimensions':['security'],'source_ref':'dictionary'}],'fields':[{'field_id':'target-price','dataset_id':'research-targets','definition':'Supplied synthetic analyst target price; no market value calculation','unit':'USD-per-share','currency':'USD','source_system':'Synthetic Research Provider A','source_field':'TARGET_PRICE','transformation':'identity','transformation_version':'1','owner':'Research data owner','value_type':'decimal','nullable':False,'source_ref':'dictionary'}],'identities':[{'identity_id':'SEC-A','dimension':'security','namespace':'provider-A/security','native_key':'ABC','source_ref':'dictionary'},{'identity_id':'SEC-B','dimension':'security','namespace':'provider-B/security','native_key':'ABC','source_ref':'dictionary'}],'licenses':[{'license_id':'research-license','dataset_id':'research-targets','principal':'analyst-research-reader','license_version':'7','contract_locator':'Synthetic agreement section 4','purposes':['historical-research'],'audiences':['internal-review'],'effective_from':'2026-01-01','effective_to':'2026-12-31','source_ref':'rights'}],'permission_observations':[{'observation_id':'permission-20261004','dataset_id':'research-targets','principal':'analyst-research-reader','purpose':'historical-research','audience':'internal-review','operation':'read','decision':'allowed','observed_on':'2026-10-04','source_ref':'entitlement-observation'}],'history':[],'queries':[],'monitors':[{'monitor_id':'history-freshness','dataset_id':'research-targets','snapshot_id':'history-export-20261004','owner':'Research data owner','metric':'snapshot_age','unit':'hours','operator':'<=','threshold':'24','value':'4','basis':'observed','observed_on':'2026-10-04','incident_route':'Research data incident queue','runbook':'Hold dependent replay and inspect provider delivery','source_ref':'telemetry'}]}
for rid,value,valid_from,valid_to,known_from,known_to in [('SEP-INITIAL','75.10','2026-09-01','2026-10-01','2026-09-03','2026-09-22'),('SEP-CORRECTED','76.90','2026-09-01','2026-10-01','2026-09-22',None),('OCT-INITIAL','80.25','2026-10-01',None,'2026-10-01',None)]:
 doc['history'].append({'record_id':rid,'field_id':'target-price','dimensions':{'security':'SEC-A'},'unit':'USD-per-share','currency':'USD','value':value,'valid_from':valid_from,'valid_to':valid_to,'known_from':known_from,'known_to':known_to,'source_ref':'research-history'})
for qid,valid,known,security in [('pre-correction','2026-09-15','2026-09-20','SEC-A'),('post-correction','2026-09-15','2026-09-25','SEC-A'),('valid-boundary','2026-10-01','2026-10-02','SEC-A'),('different-namespace','2026-09-15','2026-09-25','SEC-B')]:doc['queries'].append({'query_id':qid,'field_id':'target-price','dimensions':{'security':security},'valid_on':valid,'known_on':known,'source_ref':'queries'})
expected={'purpose':'Independent source-complete review of corrected analyst target history with exact identifier namespaces. No live integration or production acceptance.','baseline_values':{'pre-correction':'75.10','post-correction':'76.90','valid-boundary':'80.25','different-namespace':None},'baseline_records':{'pre-correction':['SEP-INITIAL'],'post-correction':['SEP-CORRECTED'],'valid-boundary':['OCT-INITIAL'],'different-namespace':[]},'baseline_shared_cost':'1250','baseline_monitor_meets':True,'baseline_permission_verified':False,'checks':[]}

def execute(name,request):
 path=dest/(name+'-input.json');path.write_text(json.dumps(request,indent=2)+'\n')
 result=subprocess.run([sys.executable,str(p/'scripts/calculate_or_transform.py'),str(path)],text=True,capture_output=True)
 if result.returncode:
  (dest/(name+'-error.txt')).write_text(result.stderr);return None,result.returncode
 (dest/(name+'-output.json')).write_text(result.stdout)
 out=json.loads(result.stdout)
 verified=subprocess.run([sys.executable,str(p/'scripts/validate_output.py'),str(dest/(name+'-output.json')),'--input',str(path)],capture_output=True,text=True)
 if verified.returncode:raise RuntimeError(verified.stdout+verified.stderr)
 return out,0

def check(name,condition,detail):
 expected['checks'].append({'id':name,'passed':bool(condition),'detail':detail})

out,code=execute('fresh-research-history',doc)
check('baseline-evaluates',code==0,'Actual compute and detached output validation')
if out:
 by={r['query_id']:r for r in out['results']['resolved_sample']}
 for qid,value in expected['baseline_values'].items():
  check('value-'+qid,by[qid]['value']==value,{'expected':value,'actual':by[qid]['value']})
  check('record-'+qid,by[qid]['record_ids']==expected['baseline_records'][qid],{'expected':expected['baseline_records'][qid],'actual':by[qid]['record_ids']})
 check('shared-cost',out['results']['shared_reviews'][0]['results']['supplied_period_cost']=='1250','1000 plus 250 supplied same-period cost')
 check('monitor-observed',out['results']['observability'][0]['meets'] is True,'4 hours <= 24 hours')
 check('permission-unverified',out['results']['permission_verified'] is False,'Declared permission remains unauthenticated')

x=copy.deepcopy(doc);conflict=copy.deepcopy(x['history'][1]);conflict['record_id']='SEP-SECOND-ASSERTION';x['history'].append(conflict)
out,code=execute('overlapping-same-value',x)
by={r['query_id']:r for r in out['results']['resolved_sample']}
check('same-valued-conflict-withheld',by['post-correction']['value'] is None and len(by['post-correction']['record_ids'])==2,'Equal values do not remove two active assertions')

x=copy.deepcopy(doc);x['permission_observations'][0]['decision']='denied'
out,code=execute('denied-permission',x)
check('denied-values-withheld',all(r['value'] is None for r in out['results']['resolved_sample']),'No local sample value exposed when supplied permission denied')

x=copy.deepcopy(doc);x['monitors'][0]['basis']='projected'
out,code=execute('projected-observability',x)
check('projected-is-not-measured',out['results']['observability'][0]['meets'] is None and out['status']=='needs-review','Projected control target is not observed evidence')

x=copy.deepcopy(doc);x['history'][1]['known_from']='2026-10-05'
out,code=execute('future-correction',x)
check('future-correction-rejected',code!=0,'Actual known event cannot postdate source/review cutoff')

x=copy.deepcopy(doc);x['shared_reviews']['architecture']['input']['data']['requirements'][0]['threshold']='500';x['shared_reviews']['architecture']['output']=run(x['shared_reviews']['architecture']['input'],'solution-architecture-planner',shared_architecture.evaluate,shared_architecture.validate)
out,code=execute('shared-measured-breach',x)
check('shared-breach-withholds-samples',all(r['value'] is None for r in out['results']['resolved_sample']),'Native architecture measured breach remains open and blocks dependent values')

(dest/'expectations-and-results.json').write_text(json.dumps(expected,indent=2)+'\n')
print(json.dumps({'checks':len(expected['checks']),'failed':[x for x in expected['checks'] if not x['passed']]},indent=2))
