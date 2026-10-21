"""Independent fresh-platform exercise. Expectations are hand-derived, not package goldens."""
import copy
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[4]
PACKAGE=ROOT/'skills/asset-management/investment-platform-modernization-planner'
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(PACKAGE/'scripts'))
import shared_architecture
from workflow_foundation import run

REF={'source_ref':'migration-evidence'}
SREF={'source_refs':['migration-evidence']}
source={'source_ref':'migration-evidence','version':'r2','as_of':'2026-10-04','known_at':'2026-10-04','locator':'SYNTHETIC ABOR migration rehearsal; independent reviewer-created evidence'}
profile={'profile_id':'institution-architecture-review','version':'2','reviewed_by':'test-data-owner','jurisdictions':['TEST'],'lines_of_business':['asset-management'],'effective_from':'2026-01-01','effective_to':'2027-01-01','method':'component-interface-requirements-v1',**SREF}
architecture={'case_id':'independent-fund-migration','as_of':'2026-10-04','context':{'capacity':'design-review','represented_party':'SYNTHETIC ASSET MANAGER','object_id':'FUND-ALPHA-ABOR','jurisdiction':'TEST','line_of_business':'asset-management'},'sources':[{'source_ref':source['source_ref'],'version':source['version'],'as_of':source['as_of'],'locator':source['locator']}],'unresolved_issues':[],'data':{'profile':profile,'business_outcome':'Migrate one fund accounting book while preserving exact lot balances','owner':'migration-owner','currency':'USD','cost_period':'month','scope':'FUND-ALPHA ABOR two-lot trial balance','inventory_complete':True}}
a=architecture['data']
a['components']=[{'component_id':id,'responsibility':role,'owner':'accounting-platform-owner','technology_choice':tech,'alternative':'retain current ledger','tradeoff':'review operational evidence','failure_domain':id,'data_classification':'confidential','retention_rule':'supplied record-retention schedule','recovery_runbook':'restore and reconcile identified snapshot','currency':'USD','cost_period':'month','cost':cost,**SREF} for id,role,tech,cost in [('old','current ABOR','legacy ledger',400),('new','proposed ABOR','candidate ledger',650)]]
a['interfaces']=[{'interface_id':'extract','from_component':'old','to_component':'new','contract_version':'positions-v3','payload_schema':'fund/book/account/instrument/lot/date/value/currency','purpose':'parallel accounting record comparison','authentication':'institution workload identity','authorization_scope':'fund-alpha.read','encryption':'approved TLS','timeout':'10 seconds','failure_route':'halt rehearsal and notify controller','trace_id':'migration run ID','delivery':'at-most-once','operation':'read','purpose_reviewed':True,'max_attempts':1,**SREF}]
a['requirements']=[{'requirement_id':'CAPACITY','component_id':'new','metric':'throughput','unit':'records/hour','owner':'platform-owner','workload_profile':'two-lot-rehearsal-v1','operator':'>=','threshold':'100',**SREF}]
a['measurements']=[{'requirement_id':'CAPACITY','component_id':'new','metric':'throughput','unit':'records/hour','workload_profile':'two-lot-rehearsal-v1','observed_on':'2026-10-03','value':'125',**SREF}]
doc={'request_id':'INDEPENDENT-PLATFORM-01','object_id':'FUND-ALPHA-ABOR','as_of':'2026-10-04','knowledge_cutoff':'2026-10-04','currency':'USD','audience':'internal-review','sources':[source],'unresolved_issues':[],'shared_reviews':{'architecture':{'input':architecture,'output':run(architecture,'solution-architecture-planner',shared_architecture.evaluate,shared_architecture.validate),**REF}}}
doc['platforms']=[{'id':id,'component_id':component,'role':'ABOR','owner':'fund-controller','provider':'synthetic ledger provider','provider_contract_version':'c3','provider_contract_source_ref':'migration-evidence','licensed_purpose':'FUND-ALPHA accounting rehearsal','record_identity':'fund/book/account/security/lot/date','history_retention':'retain all supplied close revisions','failure_owner':'accounting-platform-owner',**REF} for id,component in [('old-book','old'),('new-book','new')]]
doc['excluded_roles']=[{'id':'excluded-'+role,'role':role,'rationale':'Unchanged system; no migration in this bounded ABOR rehearsal','reviewed_by':'migration-owner',**REF} for role in ['PMS','OMS','EMS','IBOR','custodian','market-data']]
doc['responsibilities']=[{'id':'authority-'+state,'platform_id':platform,'domain':'general-ledger','book_scope':'FUND-ALPHA-ABOR','authoritative_state':state,'version':'1','reconciliation_owner':'fund-controller',**REF} for state,platform in [('current','old-book'),('proposed','new-book')]]
doc['requirements']=[{'id':'accounting-batch-throughput','architecture_requirement_id':'CAPACITY','description':'Process bounded rehearsal inventory within operator window','owner':'fund-controller','mandatory':True,'disposition':'met',**REF}]
doc['snapshots']=[{'id':id,'platform_id':platform,'version':'close-v1','sha256':digest*64,'observed_on':'2026-10-02',**REF} for id,platform,digest in [('snapshot-old','old-book','a'),('snapshot-new','new-book','b')]]
grains=[{'fund_id':'FUND-ALPHA','book_id':'ABOR','account_id':'ACCOUNT-USD','instrument_id':'SEC-'+str(n),'lot_id':'LOT-'+str(n),'valuation_date':'2026-10-01','measure':'market-value','unit':'currency','currency':'USD'} for n in (1,2)]
doc['batches']=[{'id':'WAVE-ONE','owner':'migration-owner','wave':1,'depends_on':[],'mapping_version':'map-v3','source_snapshot':'snapshot-old','target_snapshot':'snapshot-new','rollback_owner':'fund-controller','rollback_trigger':'any unreconciled lot or failed recovery objective','rollback_runbook':'retain old authority; restore and reconcile target snapshot','expected_grains':grains,'grain_inventory_reviewed':True,'new_writes_after_cutover':False,**REF}]
doc['reconciliations']=[{'id':'recon-'+str(i),'batch_id':'WAVE-ONE','mapping_version':'map-v3','tolerance':'0.00000001','tolerance_reviewed_by':'fund-controller','tolerance_source_ref':'migration-evidence','source':{**grain,'snapshot_id':'snapshot-old','value':value,**REF},'target':{**grain,'snapshot_id':'snapshot-new','value':value,**REF},**REF} for i,(grain,value) in enumerate(zip(grains,['800.125','320.875']),1)]
doc['exceptions']=[]
doc['parallel_runs']=[{'id':'rehearsal-02','batch_id':'WAVE-ONE','mapping_version':'map-v3','source_snapshot':'snapshot-old','target_snapshot':'snapshot-new','window_start':'2026-10-01','window_end':'2026-10-02','owner':'fund-controller','exception_ids':[],**REF}]
doc['recoveries']=[{'id':'recovery-02','run_id':'rehearsal-02','owner':'recovery-owner','observed_on':'2026-10-03','threshold_reviewed_by':'fund-controller','threshold_source_ref':'migration-evidence','rollback_status':'passed','observed_rto_seconds':'30','rto_limit_seconds':'60','observed_rpo_seconds':'0','rpo_limit_seconds':'0',**REF}]
doc['gates']=[{'id':'gate-'+kind,'batch_id':'WAVE-ONE','kind':kind,'owner':'migration-owner','status':'passed','reviewed_by':'fund-controller','observed_on':'2026-10-03','evidence_ids':evidence,**REF} for kind,evidence in [('reconciliation',['recon-1','recon-2']),('parallel-run',['rehearsal-02']),('rollback',['recovery-02']),('security',['external-security-review-v3']),('business-acceptance',['controller-review-v2'])]]

def save(name,value):
    (OUT/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')

def calculate(name,request):
    save(name+'-request',request)
    completed=subprocess.run([sys.executable,'-B',str(PACKAGE/'scripts/calculate_or_transform.py'),str(OUT/(name+'-request.json'))],capture_output=True,text=True)
    if completed.returncode:
        return {'exit':completed.returncode,'stderr':completed.stderr.strip()}
    output=json.loads(completed.stdout);save(name+'-output',output)
    check=subprocess.run([sys.executable,'-B',str(PACKAGE/'scripts/validate_output.py'),str(OUT/(name+'-output.json')),'--input',str(OUT/(name+'-request.json'))],capture_output=True,text=True)
    return {'exit':0,'output':output,'output_validation_exit':check.returncode}

results=[]
def exercise(name,request,expectation,check):
    actual=calculate(name,request)
    result={'case':name,'expectation':expectation,'passed':bool(check(actual)),'exit':actual['exit']}
    if actual['exit']==0:
        result.update(readiness=actual['output']['results']['readiness'],issues=actual['output']['unresolved_issues'],output_validation_exit=actual['output_validation_exit'])
    else:result['stderr']=actual['stderr']
    results.append(result)

exercise('balanced',doc,'Two exact lot comparisons, shared cost1050, observed capacity met, human-review only.',lambda r:r['exit']==0 and r['output_validation_exit']==0 and r['output']['results']['readiness']=='evidence-ready-for-human-review' and [x['difference'] for x in r['output']['results']['reconciliation']]==['0.000','0.000'] and r['output']['results']['shared_architecture']['supplied_period_cost']=='1050' and r['output']['results']['cutover_authorized'] is False)
v=copy.deepcopy(doc);v['reconciliations'][0]['target']['value']='800.12500002';v['reconciliations'][1]['target']['value']='320.87499998'
exercise('offsetting-breaks',v,'Opposite 2e-8 breaks each exceed 1e-8 tolerance even though net is zero.',lambda r:r['exit']==0 and r['output']['results']['readiness']=='blocked' and all(not x['within_tolerance'] for x in r['output']['results']['reconciliation']))
v=copy.deepcopy(doc);v['reconciliations'][0]['target']['value']='800.12500001'
exercise('exact-tolerance',v,'Difference exactly1e-8 meets inclusive1e-8 policy.',lambda r:r['exit']==0 and r['output']['results']['reconciliation'][0]['within_tolerance'])
v=copy.deepcopy(doc);v['reconciliations'].pop();v['gates'][0]['evidence_ids']=['recon-1']
exercise('missing-lot',v,'Deleting one expected comparison must block despite supplied passed gates.',lambda r:r['exit']==0 and r['output']['results']['readiness']=='blocked')
v=copy.deepcopy(doc);v['reconciliations'][0]['target']['lot_id']='DIFFERENT-LOT'
exercise('wrong-lot',v,'Different target lot cannot match by security/account only.',lambda r:r['exit']!=0)
v=copy.deepcopy(doc);v['recoveries'][0]['observed_rto_seconds']='60.000000001'
exercise('recovery-breach',v,'Observed RTO above60 blocks without rounding down.',lambda r:r['exit']==0 and r['output']['results']['readiness']=='blocked')
v=copy.deepcopy(doc);v['recoveries'][0]['observed_on']='2026-09-30'
exercise('early-recovery',v,'Recovery before rehearsal completion cannot prove this rehearsal recovery.',lambda r:r['exit']!=0)
v=copy.deepcopy(doc);v['gates'][2]['observed_on']='2026-10-02'
exercise('early-native-gate',v,'Rollback signoff before its recovery observation must fail.',lambda r:r['exit']!=0)
v=copy.deepcopy(doc);v['exceptions']=[{'id':'exception-1','batch_id':'WAVE-ONE','owner':'controller','description':'accepted small unresolved value break','status':'accepted',**REF}];v['parallel_runs'][0]['exception_ids']=['exception-1']
exercise('accepted-exception',v,'Accepted exception remains blocked; acceptance is not resolution.',lambda r:r['exit']==0 and r['output']['results']['readiness']=='blocked')
v=copy.deepcopy(doc);v['batches'][0]['depends_on']=['WAVE-ONE']
exercise('cyclic-wave',v,'Self-dependency must fail rather than choosing an order.',lambda r:r['exit']!=0)
v=copy.deepcopy(doc);v['sources'][0]['known_at']='2026-10-05'
exercise('future-source',v,'Source known beyond cutoff cannot enter rehearsal evidence.',lambda r:r['exit']!=0)
v=copy.deepcopy(doc);v['shared_reviews']['architecture']['output']['results']['supplied_period_cost']='1'
exercise('shared-cost-tamper',v,'Fabricated generic architecture result fails detached reconstruction.',lambda r:r['exit']!=0)
v=copy.deepcopy(doc);v['batches'][0].update(new_writes_after_cutover=True,delta_replay_evidence='current-run-delta-replay',delta_replay_source_ref='migration-evidence',delta_replay_status='passed',delta_replay_observed_on='2026-09-01')
exercise('delta-before-rehearsal',v,'A delta replay before the entire Oct rehearsal cannot establish rollback coverage for its new writes; block or reject.',lambda r:r['exit']!=0 or r['output']['results']['readiness']=='blocked')
v=copy.deepcopy(doc);v['exceptions']=[{'id':'exception-1','batch_id':'WAVE-ONE','owner':'controller','description':'post-run issue resolved after signoff','status':'closed','resolution':'fixed mapping and rechecked','resolution_source_ref':'migration-evidence','resolved_on':'2026-10-04',**REF}];v['parallel_runs'][0]['exception_ids']=['exception-1']
exercise('closure-after-gates',v,'Signoffs on Oct3 cannot include closure first observed Oct4; block or require fresh evidence review.',lambda r:r['exit']!=0 or r['output']['results']['readiness']=='blocked')
report={'reviewer':'independent AM data adapter agent','source':'Fresh synthetic two-lot ABOR migration; no package goldens used as expected results.','checks':len(results),'passed':sum(r['passed'] for r in results),'results':results,'limitations':'Offline supplied-evidence methods only; no production access, real source truth, professional acceptance or model behavior test.'}
save('report',report)
print(json.dumps(report,indent=2))

raise SystemExit(any(not result["passed"] for result in results))
