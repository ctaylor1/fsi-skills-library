"""Payment queue economics with explicit cohorts and non-additive opportunities."""
from collections import Counter, defaultdict
from decimal import Decimal
import re
from payment_contract import money, stable_hash, timestamp
from payment_foundation import finding

SKILL = 'payment-operations-improvement-analyzer'


def validate(data):
    errors = []
    for key in ('window', 'staffing'):
        if key in data and not isinstance(data[key], dict): errors.append(key + ' must be an object')
    for key in ('cases', 'opportunities'):
        if not isinstance(data.get(key, []), list) or any(not isinstance(r, dict) for r in data.get(key, [])): errors.append(key + ' must be a list of objects')
    for row in data.get('cases', []):
        if 'currency' in row and not re.fullmatch(r'[A-Z]{3}', str(row['currency'])): errors.append('currency must be three uppercase letters')
        for k in ('handling_minutes', 'rework_minutes'):
            if k in row and (money(row[k]) < 0): errors.append(k + ' must be nonnegative')
        for k in ('created_at', 'completed_at'):
            if row.get(k): timestamp(row[k])
        for k in ('automated', 'stp_eligible'):
            if k in row and type(row[k]) is not bool: errors.append(k + ' must be boolean')
    for row in data.get('opportunities', []):
        if 'uses_ai' in row and type(row['uses_ai']) is not bool: errors.append('uses_ai must be boolean')
        if 'ai_controls' in row and not isinstance(row['ai_controls'], dict): errors.append('ai_controls must be an object')
        if 'case_ids' in row and (not isinstance(row['case_ids'], list) or any(not isinstance(c, str) for c in row['case_ids'])): errors.append('case_ids must be a list of strings')
        for k in ('automation_fraction', 'realization_fraction', 'error_rate'):
            if k in row and not 0 <= money(row[k]) <= 1: errors.append(k + ' must be between zero and one')
        for k in ('review_minutes_per_case', 'error_minutes_per_case', 'error_cost_per_case', 'technology_cost', 'implementation_cost', 'cash_reduction_cap'):
            if k in row and money(row[k]) < 0: errors.append(k + ' must be nonnegative')
    if 'population_complete' in data.get('window', {}) and type(data['window']['population_complete']) is not bool: errors.append('population_complete must be boolean')
    for k in ('cost_per_hour', 'available_hours'):
        if k in data.get('staffing', {}) and money(data['staffing'][k]) < 0: errors.append('staffing '+k+' must be nonnegative')
    return errors


def analyze(request):
    data = request['data']; findings = []
    def gap(code, message, row=None): findings.append(finding(code, message, (row or {}).get('source_ids', [])))
    window = data.get('window', {})
    try:
        start, end = timestamp(window['start']), timestamp(window['end'])
        if start >= end or end.date().isoformat() > request['as_of']: raise ValueError('invalid period')
    except (ValueError, TypeError, KeyError):
        gap('window-unresolved', 'Supply a closed observation window, start inclusive and end exclusive, no later than as_of.')
        return {'result': {'metrics': None, 'opportunity_models': []}, 'findings': findings, 'handoffs': []}
    if window.get('population_complete') is not True or not window.get('source_ids'):
        gap('population-unverified', 'Queue inventory completeness and its source must be supplied; missing cases are not zero.')
    groups = defaultdict(list)
    for row in data.get('cases', []): groups[row.get('case_id')].append(row)
    cases = []; excluded = []; duplicate_count = 0
    for cid, rows in groups.items():
        if not cid or len({stable_hash(r) for r in rows}) != 1:
            excluded.append(cid); gap('case-identity-conflict', 'Conflicting or missing case identity is quarantined: ' + str(cid)); continue
        row = rows[0]; duplicate_count += len(rows)-1
        required = ('task', 'legal_entity_id', 'team', 'currency', 'created_at', 'status', 'source_ids')
        if any(not row.get(k) for k in required) or row.get('status') not in {'open', 'completed', 'unknown'}:
            excluded.append(cid); gap('case-incomplete', 'Case cannot enter a denominator without identity, task, status and evidence: '+cid, row); continue
        created = timestamp(row['created_at'])
        completed = timestamp(row['completed_at']) if row.get('completed_at') else None
        if created >= end or (completed and (completed < created or completed >= end)) or (row['status'] == 'completed') != bool(completed):
            excluded.append(cid); gap('case-time-conflict', 'Case snapshot must be consistent at the window end: '+cid, row); continue
        cases.append(row)
    if excluded: gap('denominator-incomplete', 'Reported metrics cover only unambiguous supplied cases; excluded cases prevent a complete population claim.')
    if not cases: gap('cases-missing', 'Supply payment work-item records; aggregate claimed savings alone cannot establish a baseline.')
    completed = [r for r in cases if r['status']=='completed' and start <= timestamp(r['completed_at']) < end]
    eligible = [r for r in completed if r.get('stp_eligible') is True]
    open_cases = [r for r in cases if r['status']=='open']
    missing_effort = [r for r in completed if any(k not in r for k in ('handling_minutes','rework_minutes','automated','stp_eligible'))]
    if missing_effort: gap('effort-incomplete', 'Completed cohort has unknown handling/rework/STP fields; associated totals and rates remain null.')
    partitions = defaultdict(list)
    for row in cases: partitions[(row['legal_entity_id'],row['team'],row['currency'])].append(row)
    workload = []
    for key, rows in sorted(partitions.items()):
        done = [r for r in completed if r in rows]; opened = [r for r in open_cases if r in rows]
        effort_known = all('handling_minutes' in r and 'rework_minutes' in r for r in done)
        ages = [(end-timestamp(r['created_at'])).total_seconds()/86400 for r in opened]
        workload.append({'legal_entity_id':key[0], 'team':key[1], 'currency':key[2], 'completed_cases':len(done), 'open_cases':len(opened), 'oldest_open_age_days':round(max(ages),4) if ages else None, 'handling_minutes':str(sum((money(r['handling_minutes']) for r in done),Decimal(0))) if effort_known else None, 'rework_minutes':str(sum((money(r['rework_minutes']) for r in done),Decimal(0))) if effort_known else None})
    metrics = {'window':window, 'cohort_basis':'completed_at within [start,end); backlog at end; deduplicated case identities', 'unique_cases_supplied':len(cases), 'exact_duplicate_rows_removed':duplicate_count, 'quarantined_case_ids':excluded, 'arrivals':sum(start <= timestamp(r['created_at']) < end for r in cases), 'completed_cases':len(completed), 'open_cases':len(open_cases), 'unknown_status_cases':sum(r['status']=='unknown' for r in cases), 'stp_eligible_completed':len(eligible), 'stp_completed':sum(r.get('automated') is True for r in eligible), 'stp_rate':str(Decimal(sum(r.get('automated') is True for r in eligible))/len(eligible)) if eligible and not missing_effort else None, 'rework_case_rate':str(Decimal(sum(money(r.get('rework_minutes',0))>0 for r in completed))/len(completed)) if completed and not missing_effort else None, 'workload_partitions':workload}
    staffing = data.get('staffing', {})
    models=[]; reserved=Counter(); ids=Counter(r.get('opportunity_id') for r in data.get('opportunities', []))
    index={r['case_id']:r for r in completed}
    for opp in data.get('opportunities', []):
        reasons=[]; oid=opp.get('opportunity_id'); selected=opp.get('case_ids', [])
        if not oid or ids[oid]>1: reasons.append('opportunity identity missing or repeated')
        required=('task','owner','automation_fraction','realization_fraction','error_rate','review_minutes_per_case','error_minutes_per_case','error_cost_per_case','technology_cost','implementation_cost','cash_reduction_cap','source_ids')
        for field in required:
            if field not in opp or opp[field] in (None,'',[]): reasons.append(field+' missing')
        if not selected or len(set(selected))!=len(selected) or any(c not in index for c in selected): reasons.append('explicit unique eligible completed case set required')
        rows=[index[c] for c in selected if c in index]
        if any(r['task'] != opp.get('task') for r in rows): reasons.append('task does not match selected cases')
        partitions_used={(r['legal_entity_id'],r['team'],r['currency']) for r in rows}
        if len(partitions_used)!=1: reasons.append('opportunity cannot mix entity, team or currency')
        if any('handling_minutes' not in r or 'rework_minutes' not in r for r in rows): reasons.append('baseline effort unknown')
        if any(reserved[c] for c in selected): reasons.append('overlaps another opportunity; models are alternatives and cannot be added')
        for c in selected: reserved[c]+=1
        if staffing.get('window')!={'start':window['start'],'end':window['end']} or staffing.get('currency') != (rows[0]['currency'] if rows else None): reasons.append('staffing cost period/currency must match observed cohort')
        for field in ('cost_per_hour','available_hours','source_ids'):
            if field not in staffing: reasons.append('staffing '+field+' missing')
        if rows and (staffing.get('legal_entity_id'),staffing.get('team'))!=(rows[0]['legal_entity_id'],rows[0]['team']): reasons.append('staffing scope differs from cases')
        controls=opp.get('ai_controls', {})
        if opp.get('uses_ai') is True:
            for field in ('task_definition','evaluation_dataset_ref','label_maturity','false_positive_cost','false_negative_cost','quality_threshold','human_review_scope','escalation_owner','pilot_scope','stop_conditions','model_version','source_ids'):
                if not controls.get(field): reasons.append('AI '+field+' unresolved')
        model={'opportunity_id':oid,'task':opp.get('task'),'case_ids':selected,'period':window,'ai_controls':controls,'cash_savings':None,'capacity_hours':None,'net_economic_value':None,'aggregation':'standalone scenario; never sum overlapping opportunities','issues':reasons}
        if not reasons:
            baseline=sum((money(r['handling_minutes'])+money(r['rework_minutes']) for r in rows),Decimal(0))
            n=Decimal(len(rows)); gross=baseline*money(opp['automation_fraction'])
            overhead=n*(money(opp['review_minutes_per_case'])+money(opp['error_rate'])*money(opp['error_minutes_per_case']))
            net=max(Decimal(0),gross-overhead); available=money(staffing['available_hours']); rate=money(staffing['cost_per_hour'])
            if available<0 or rate<0: reasons.append('staffing values must be nonnegative')
            else:
                hours=min(net/60,available); capacity_value=hours*rate
                cash=min(capacity_value*money(opp['realization_fraction']),money(opp['cash_reduction_cap']))
                error_cost=n*money(opp['error_rate'])*money(opp['error_cost_per_case'])
                cost=money(opp['technology_cost'])+money(opp['implementation_cost'])+error_cost
                model.update({'baseline_effort_minutes':str(baseline),'gross_minutes_avoided':str(gross),'oversight_and_error_minutes':str(overhead),'capacity_hours':str(hours),'capacity_value':str(capacity_value),'cash_savings':str(cash),'expected_error_cost':str(error_cost),'period_cost':str(cost),'net_economic_value':str(cash-cost),'cash_realization_is_supplied_assumption':True})
        for reason in reasons: gap('opportunity-evidence-gap',str(oid)+': '+reason,opp)
        models.append(model)
    if not models: gap('opportunities-missing','No task-specific improvement scenario supplied.')
    return {'result':{'metrics':metrics,'opportunity_models':models,'combined_savings':None,'production_automation_approved':False},'findings':findings,'handoffs':[{'target_skill':'ai-evaluation-benchmark-builder','reason':'Design task-specific evaluation for proposed payment automation.','required_inputs':['task cohort and label maturity','error/friction costs','pilot and stop gates']},{'target_skill':'model-risk-documenter','reason':'Review human oversight and model governance for the proposed operation.','required_inputs':['model version and task scope','evaluation evidence','accountable control owners']}], 'limitations':['Queue records and cost assumptions are supplied evidence. Capacity value is not cash savings; no annualization or combined benefit is inferred.']}
