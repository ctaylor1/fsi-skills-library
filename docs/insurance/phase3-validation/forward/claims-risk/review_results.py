import hashlib,json,sys
from decimal import Decimal
from pathlib import Path
ROOT=Path('/tmp/insurance-p3-forward-claims-risk')
phase=sys.argv[1] if len(sys.argv)>1 else 'original'
mapped=sys.argv[2] if len(sys.argv)>2 else 'mapped-original'
freeze=json.loads((ROOT/'freeze-manifest.json').read_text())
records=[]
run_label='frozen-evidence'
def equivalent(a,b):
    if a is None or b is None or isinstance(a,(bool,list,dict)) or isinstance(b,(bool,list,dict)): return a==b
    try: return Decimal(str(a))==Decimal(str(b))
    except Exception: return a==b
def check(name,actual,expected): records.append(dict(case=key,run=run_label,check=name,actual=actual,expected=expected,passed=equivalent(actual,expected)))
for f in freeze['files']:
    key='frozen-evidence'; check(f['path']+' unchanged',hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest(),f['sha256'])
for c in freeze['cases']:
    key=c['key']; folder=ROOT/c['skill']/key
    run_label=mapped if c['skill']=='insurance-orsa-packager' else (phase if (folder/phase).exists() else 'original')
    run=folder/run_label
    d=json.loads((run/'output.json').read_text()); r=d.get('results',{}); e=json.loads((folder/'expected.json').read_text())
    logs=json.loads((run/'command-log.json').read_text())
    if key=='recovery-boolean-money':
        check('input rejects boolean money',logs[0]['exit_code']!=0,True); check('calculation rejects boolean money',logs[1]['exit_code']!=0,True); continue
    check('all native commands pass',[x['exit_code'] for x in logs],[0,0,0])
    source_name='mapped-input.json' if c['skill']=='insurance-orsa-packager' else 'input.json'
    check('retained source exact',d['source_document'],json.loads((folder/source_name).read_text()))
    for field,val in [('action_taken',False),('human_review_required',True),('approval','not_requested'),('execution','not_performed')]:check('authority '+field,d.get(field),val)
    for field,val in [('approval','not_requested'),('execution','not_performed'),('evidence_assurance','supplied_not_authenticated')]:check('artifact '+field,d['artifact'].get(field),val)
    status=e.get('status')
    allowed={'needs-review-or-needs-data':['needs-review','needs-data'],'not-applicable-or-needs-data':['not-applicable','needs-data'],'needs-data-or-needs-review':['needs-data','needs-review']}.get(status,[status])
    if key=='recovery-net-exceeds-interest': allowed=['needs-review','needs-data']
    check('review state',d['status'] in allowed,True)
    codes=[f['code'] for f in d['findings']]
    if key=='recovery-multi-interest':
        check('pro rata allocations',[x['net_collection_share'] for x in r['allocation_schedule']],['8100','900','900','450'])
        check('collection net values',[x['net_amount'] for x in r['collections']],['5000','4000','1350'])
        check('source date deltas',[x['days_to_supplied_limitation'] for x in r['rights_register']],[17,-3])
        check('limitation review surfaced','limitation-review' in codes,True);check('late task surfaced','task-after-limitation' in codes,True)
    elif key.startswith('recovery-'):
        check('allocation withheld',r['allocation_schedule'],None)
        if key=='recovery-unknown-cost':check('unknown cost retained',r['collections'][0]['cost_amount'],None);check('unknown net retained',r['collections'][0]['net_amount'],None)
    elif key=='benefit-daily-cap-waiting':
        check('waiting-day boundary',r['eligibility_start'],e['first_potential_benefit_day'])
        for p in r['period_reviews']:
            exp=e['periods'][p['period_id']]
            for native,want in [('calendar_days_after_waiting','eligible_days'),('gross_scenario','gross'),('offsets','offset'),('net_before_remaining_cap','net')]:check(p['period_id']+' '+native,p[native],exp[want])
        check('uncapped sum',r['total_net_scenario'],6000);check('remaining balance cap',r['capped_scenario'],5500)
    elif key=='benefit-conflicting-medical-evidence':
        check('conflicting assessment',r['period_reviews'][0]['criteria'][0]['evidence_state'],'conflicting');check('contrary observation preserved',r['period_reviews'][0]['criteria'][0]['observation_ids'],['AUGC-M','CONTRARY'])
        check('conflicting period gross withheld',r['period_reviews'][0]['gross_scenario'],None);check('conflicting aggregate withheld',r['capped_scenario'],None)
    elif key=='benefit-unsupported-monthly-method':
        check('unsupported waiting-day calculation withheld',r['eligibility_start'],None)
        for p in r['period_reviews']:
            for f in ['calendar_days_after_waiting','gross_scenario','net_before_remaining_cap']:check('unsupported '+p['period_id']+' '+f,p[f],None)
        check('unsupported aggregate withheld',r['capped_scenario'],None)
    elif key=='benefit-unknown-offset-inventory':
        for p in r['period_reviews']:
            check(p['period_id']+' unknown offset stays unknown',p['offsets'],None);check(p['period_id']+' net withheld',p['net_before_remaining_cap'],None)
        check('unknown offset aggregate withheld',r['capped_scenario'],None)
    elif key.startswith('dispute-'):
        check('chronology order',[x['event_id'] for x in r['chronology']],['E1','E2'])
        check('contrary evidence retained',[x['evidence_id'] for x in r['reason_evidence_matrix'][0]['contrary']],['V2'])
        for f in ['merits_determined','submitted','carrier_response_drafted']:check(f,r[f],False)
        if key=='dispute-unanswered-reason-elapsed-date':check('unaddressed reason surfaced','unaddressed-reason' in codes,True);check('elapsed date surfaced','past-supplied-deadline' in codes,True)
        if key=='dispute-carrier-capacity':check('capacity boundary surfaced','claimant-capacity' in codes,True)
    elif key.startswith('siu-'):
        check('no fraud verdict',r['fraud_verdict'],'not-determined');check('no claim decision',r['claim_decision'],'not-performed');check('no referral',r['referral_submitted'],False);check('no authentication',r['evidence_authentication'],'not-performed')
        if key=='siu-innocent-alternative-custody':check('UTC chain holder',r['custody_register'][0]['current_holder'],'Synthetic SIU analyst');check('alternative task ready',r['task_plan'][0]['draft_state'],'review-ready')
        if key=='siu-simultaneous-custody-no-alternative':check('ambiguous holder withheld',r['custody_register'][0]['current_holder'],None);check('custody gap','custody-break' in codes,True);check('alternative gap','alternative-test' in codes,True)
        if key=='siu-unsupported-covert-method':check('unsupported task withheld',r['task_plan'][0]['draft_state'],'needs-data');check('authority gap','task-authority' in codes,True)
    elif key.startswith('exposure-'):
        check('no loss estimate',r['loss_estimate'],None);check('peril slices not additive',r['peril_slices_additive'],False)
        if key=='exposure-duplicate-policy-location':check('duplicate totals withheld',r['tiv_by_currency'],None)
        else:
            for cur,val in e['tiv_by_currency'].items():check(cur+' TIV',r['tiv_by_currency'][cur],val)
            check('physical L1 grouping',next(x['tiv'] for x in r['location_tiv'] if x['location_id']=='L1'),2000000)
            check('USD wind overlap',next(x['tiv'] for x in r['peril_tiv'] if x['currency']=='USD' and x['peril']=='wind'),2000000)
            if key=='exposure-quality-gap-keeps-known-tiv':check('quality findings retained',len(r['quality_register'][0]['issues']),2)
    elif key=='cat-joint-weighted-occurrences':
        check('aggregate AAL',r['aggregate_aal'],1025000);check('mean annual max occurrence',r['mean_annual_max_occurrence_loss'],650000)
        for a in r['annual_states']:
            check(a['year_id']+' aggregate',a['aggregate_loss'],e['annual_states'][a['year_id']]['aggregate']);check(a['year_id']+' occurrence',a['occurrence_loss'],e['annual_states'][a['year_id']]['occurrence'])
        for q in r['exceedance_probabilities']:
            exp=e['exceedance']['t'+q['threshold']]
            check(q['threshold']+' AEP',q['aggregate_exceedance_probability'],exp['AEP']);check(q['threshold']+' OEP',q['occurrence_exceedance_probability'],exp['OEP'])
    elif key.startswith('cat-'):
        check('AAL',r['aggregate_aal'],1090000 if key=='cat-event-rate-above-one' else None);check('unsupported curves withheld',r['exceedance_probabilities'],None);check('unavailable max occurrence withheld',r['mean_annual_max_occurrence_loss'],None)
    elif key.startswith('orsa-'):
        check('no ORSA approval',r['orsa_approved'],False);check('no external submission',r['external_submission_authorized'],False)
        if key=='orsa-negative-stress-surpluses':
            for i,z in enumerate(r['scenario_reconciliations']):
                check(str(i)+' capital',z['capital']['calculated_surplus'],e['capital_surpluses'][i]);check(str(i)+' liquidity',z['liquidity']['calculated_surplus'],e['liquidity_surpluses'][i]);check(str(i)+' capital difference',z['capital']['difference'],0);check(str(i)+' liquidity difference',z['liquidity']['difference'],0)
            check('two shortfalls surfaced',codes.count('scenario-shortfall'),2)
        elif key=='orsa-missing-liquidity-open-board-mismatch':
            check('missing liquidity not fabricated',r['scenario_reconciliations'][1]['liquidity'],None);check('reported break preserved',r['scenario_reconciliations'][2]['capital']['difference'],-1000000);check('open governance preserved','governance-open' in codes,True)
        else:check('baseline cannot cover material risks',r['uncovered_material_risks'],['R-CAT','R-LIQ'])
report=dict(native_phase=phase,orsa_mapping_phase=mapped,checks=len(records),passed=sum(x['passed'] for x in records),failed=sum(not x['passed'] for x in records),cases=len(freeze['cases']),failures=[x for x in records if not x['passed']],results=records)
(ROOT/(phase+'-practitioner-checks.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
