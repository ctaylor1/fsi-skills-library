from pathlib import Path
import copy, json, hashlib, subprocess, sys
ROOT=Path('/tmp/insurance-cat-data-forward-20260918')
PYTHON='/tmp/fsi-p0-venv/bin/python'
def save(p, v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2)+'\n')
def fixture(name, package, request, data):
    folder=ROOT/'runs'/name
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'raw-request.txt').write_text(request+'\n')
    save(folder/'input.json',data)
    scripts=ROOT/'packages'/package/'scripts'
    steps=[]
    for script, file in [('validate_input.py','input.json'),('calculate_or_transform.py','input.json'),('validate_output.py','output.json')]:
        argv=[PYTHON,str(scripts/script),str(folder/file)]
        p=subprocess.run(argv,text=True,capture_output=True)
        log={'argv':argv,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
        save(folder/(script+'.result.json'),log)
        steps.append(log)
        if script=='calculate_or_transform.py' and p.returncode==0:
            (folder/'output.json').write_text(p.stdout)
    argv=[PYTHON,'-c','import json,sys; from validate_output import validate; p=json.load(open(sys.argv[1])); d=json.load(open(sys.argv[2])); errors=validate(p,d); print(json.dumps({"errors":errors})); raise SystemExit(bool(errors))',str(folder/'output.json'),str(folder/'input.json')]
    p=subprocess.run(argv,cwd=scripts,text=True,capture_output=True)
    save(folder/'validate_with_original_input.result.json',{'argv':argv,'cwd':str(scripts),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    output=json.loads((folder/'output.json').read_text())
    return {'name':name,'completeness':output['completeness'],'evaluability':output['evaluability'],'validation_exit_codes':[r['exit_code'] for r in steps]+[p.returncode], 'dedup':output.get('dedup'),'overall_severity':output.get('overall_severity'),'break_counts':output.get('break_counts'),'checks':output.get('checks'),'unresolved_issues':output['unresolved_issues'],'comparisons':output.get('comparisons')}

base={'as_of':'2026-09-18T12:00:00-04:00','config_version':'synthetic-cat-policy-1.0','exposure_snapshot_id':'portfolio-20260918-v1','context':{'capacity':'catastrophe risk analyst','represented_party':'Synthetic Carrier A','object_id':'synthetic-coastal-property-portfolio','jurisdiction':'US-FL','line_of_business':'commercial property'},'financial_context':{'currency':'USD','unit':'currency','financial_basis':'gross','limit_grain':'location'},'data_coverage':{'events':'complete','exposures':'complete','models':'complete'},'events':[{'event_id':'HUR-SYN-01','name':'Synthetic Hurricane Rowan','peril':'hurricane','footprint_zones':['coast-A'],'footprint_version':'rowan-footprint-v3','footprint_as_of':'2026-09-18T11:00:00-04:00','source_ref':'synthetic-event-feed-rowan'}],'locations':[],'prior_alerts':[],'sources':[{'source':'policy_admin','source_ref':'synthetic-exposure-feed','version':'portfolio-20260918-v1','as_of':'2026-09-18T11:30:00-04:00'},{'source':'event_feed','source_ref':'synthetic-event-feed-rowan','version':'rowan-footprint-v3','as_of':'2026-09-18T11:00:00-04:00'},{'source':'cat_model','source_ref':'synthetic-model-run-42','version':'synthetic-model-v5','as_of':'2026-09-18T11:45:00-04:00'},{'source':'risk_policy','source_ref':'synthetic-cat-risk-owner-threshold-policy','version':'synthetic-cat-policy-1.0','as_of':'2026-09-01T09:00:00-04:00'}],'config':{'zone_accum_limit':{'default':20000000},'single_location_max':15000000,'modeled_loss_appetite':30000000,'approaching_ratio':0.9,'stale_valuation_years':3,'max_source_staleness_hours':{'default':24}}}
for i in (1,2):
    base['locations'].append({'location_id':f'LOC-{i}','limit_id':f'allocated-limit-{i}','zone':'coast-A','peril_exposed':['hurricane'],'limit':12000000,'tiv':16000000,'geocoded':True,'valuation_date':'2026-06-30','source_ref':f'synthetic-exposure-feed/row/{i}','modeled_losses':[{'event_id':'HUR-SYN-01','peril':'hurricane','footprint_version':'rowan-footprint-v3','exposure_snapshot_id':'portfolio-20260918-v1','model_version':'synthetic-model-v5','model_run_id':'synthetic-model-run-42','currency':'USD','unit':'currency','financial_basis':'gross','statistic':'scenario_range','scenario_set_id':'rowan-aligned-scenarios-v1','scenario_ids':{'low':'track-west','mid':'track-center','high':'track-east'},'low':3000000*i,'mid':7000000*i,'high':12000000*i}]})
results=[]
results.append(fixture('cat_complete_exposed','catastrophe-exposure-monitor','Prepare a monitor result for the supplied synthetic hurricane and complete two-location USD gross portfolio. This controlled baseline establishes the active zone and event-model alert keys for the feed-loss scenarios.',base))
prior=json.loads((ROOT/'runs/cat_complete_exposed/output.json').read_text())
prior_keys=[a['alert_key'] for a in prior['alerts']]
for name,missing in [('cat_event_feed_unavailable','event_feed'),('cat_exposure_feed_unavailable','policy_admin')]:
    d=copy.deepcopy(base);d['prior_alerts']=prior_keys;d['sources']=[s for s in d['sources'] if s['source']!=missing]
    if missing=='event_feed':d['events']=[];d['data_coverage']['events']='unavailable'
    else:d['locations']=[];d['data_coverage']['exposures']='unavailable'
    results.append(fixture(name,'catastrophe-exposure-monitor',f'Today the {missing} snapshot is unavailable. The prior complete monitor had active hurricane zone accumulation and event modeled-loss alerts. Prepare today\'s monitor result and explain what can be concluded about those alerts.',d))
d=copy.deepcopy(base);d['prior_alerts']=prior_keys;d['locations'][1]['modeled_losses']=[];d['data_coverage']['models']='partial'
results.append(fixture('cat_one_exposed_location_unmodeled','catastrophe-exposure-monitor','The same hurricane affects both portfolio locations. Exposure records are complete, but LOC-2 has no event-model result. Prepare the monitor result, including whether an event modeled-loss total can be reported.',d))
d=copy.deepcopy(base);d['prior_alerts']=prior_keys
for loc in d['locations']:loc['zone']='inland-B';loc['modeled_losses']=[]
results.append(fixture('cat_complete_no_exposed_locations','catastrophe-exposure-monitor','The complete current portfolio contains two insured locations outside the hurricane footprint. The complete current event feed and sources are available, and no location has event exposure; no location model is applicable. Prepare today\'s monitor result and distinguish measured zero exposure from feed absence.',d))

basis={'key':'coastal-property','metric':'losses','period':'2026-Q2','unit':'currency','date_basis':'accident_quarter','valuation_date':'2026-06-30'}
priorrow={**basis,'value':2000000,'currency':'EUR','financial_basis':'gross','definition_version':'gross-incurred-loss-v2','source_ref':'synthetic-prior-loss-export/row/1'}
currentrow={**basis,'value':1100000,'currency':'USD','financial_basis':'net','definition_version':'net-paid-loss-v3','source_ref':'synthetic-current-loss-export/row/1'}
recon={'as_of':'2026-09-18','config_version':'synthetic-reconciliation-policy-1.0','context':{'capacity':'actuarial data steward','represented_party':'Synthetic Carrier A','object_id':'synthetic-loss-comparison-2026-Q2','jurisdiction':'US','line_of_business':'commercial property'},'sources':[{'source_ref':'synthetic-prior-loss-export','version':'prior-export-v1','as_of':'2026-09-17'},{'source_ref':'synthetic-current-loss-export','version':'current-export-v1','as_of':'2026-09-18'},{'source_ref':'synthetic-metric-definitions','version':'definition-registry-v3','as_of':'2026-09-18'},{'source_ref':'synthetic-reconciliation-policy','version':'synthetic-reconciliation-policy-1.0','as_of':'2026-09-18'}],'current':[currentrow,{**currentrow,'value':1350000,'source_ref':'synthetic-current-loss-export/row/2'}],'prior':[priorrow],'expected_periods':['2026-Q2'],'expected_series':[{'key':'coastal-property','metric':'losses'}],'config':{'movement_pct':20,'definition_baseline_version':'net-paid-loss-v3'}}
results.append(fixture('reconciliation_conflicting_duplicates_and_basis','actuarial-data-lineage-checker','Review current USD net paid losses against prior EUR gross incurred losses for coastal-property, metric losses, period 2026-Q2. The current export contains conflicting duplicates of 1,100,000 and 1,350,000; prior is 2,000,000. Explain whether movement is meaningful and prepare source-linked reconciliation review findings. Do not pick a duplicate, convert currency, or treat paid and incurred as the same metric.',recon))
d=copy.deepcopy(recon);d['current']=d['current'][:1]
results.append(fixture('reconciliation_incompatible_basis_isolated','actuarial-data-lineage-checker','As a controlled isolate, use the first current observation only to examine comparability of USD net paid losses with EUR gross incurred losses for the same named metric and period. This is not a source-correction decision.',d))
d=copy.deepcopy(recon);d['prior']=[{**d['current'][0],'value':1000000,'source_ref':'synthetic-prior-loss-export/row/1'}]
results.append(fixture('reconciliation_conflicting_duplicates_isolated','actuarial-data-lineage-checker','As a controlled isolate, both periods now use USD net paid loss with matching definition/date bases, but two conflicting current rows remain. Prepare a reconciliation review without choosing one.',d))
save(ROOT/'summary.json',results)
hashes={}
for p in (ROOT/'packages').rglob('*'):
    if p.is_file() and p.suffix in {'.py','.md'} and 'test_' not in p.name:
        hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
save(ROOT/'snapshot-hashes.json',hashes)
print(json.dumps(results,indent=2))
