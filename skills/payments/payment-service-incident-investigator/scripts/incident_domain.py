"""Service incident evidence: attempts, customer outcomes and money stay distinct."""
from collections import Counter, defaultdict
from decimal import Decimal
import re
from payment_contract import money, stable_hash, timestamp
from payment_foundation import finding

SKILL = 'payment-service-incident-investigator'
OUTCOMES = {'succeeded', 'failed', 'unknown'}


def validate(data):
    errors=[]
    for key in ('window','coverage','containment','recovery'):
        if key in data and not isinstance(data[key],dict): errors.append(key+' must be an object')
    for key in ('payments','attempts','timeline','hypotheses'):
        if not isinstance(data.get(key,[]),list) or any(not isinstance(r,dict) for r in data.get(key,[])): errors.append(key+' must be a list of objects')
    for row in data.get('payments',[]):
        if 'currency' in row and not re.fullmatch(r'[A-Z]{3}',str(row['currency'])): errors.append('currency must be three uppercase letters')
        if 'amount' in row and money(row['amount'])<0: errors.append('payment amount must be nonnegative')
    for row in data.get('attempts',[])+data.get('timeline',[]):
        if row.get('at'): timestamp(row['at'])
    coverage=data.get('coverage',{})
    if 'expected_unique_payments' in coverage and (type(coverage['expected_unique_payments']) is not int or coverage['expected_unique_payments']<0): errors.append('expected_unique_payments must be a nonnegative integer')
    for key in ('matched_payment_ids','unresolved_payment_ids'):
        ids=data.get('recovery',{}).get(key,[])
        if not isinstance(ids,list) or any(not isinstance(i,str) for i in ids): errors.append(key+' must be a list of strings')
    return errors


def analyze(request):
    d=request['data']; findings=[]
    def gap(code,msg,row=None): findings.append(finding(code,msg,(row or {}).get('source_ids',[])))
    window=d.get('window',{})
    try:
        start,end=timestamp(window['start']),timestamp(window['end'])
        if start>=end or end.date().isoformat()>request['as_of']: raise ValueError('invalid window')
    except (KeyError,ValueError,TypeError):
        return {'result':{'impact':None},'findings':[finding('window-unresolved','A bounded incident observation window is required.')],'handoffs':[]}
    def unique(rows,key):
        groups=defaultdict(list)
        for row in rows: groups[row.get(key)].append(row)
        accepted=[]; excluded=[]; duplicates=0
        for identity, group in groups.items():
            if not identity or len({stable_hash(r) for r in group})>1:
                excluded.append(identity); gap('identity-conflict','Quarantine conflicting '+key+': '+str(identity)); continue
            duplicates+=len(group)-1; accepted.append(group[0])
        return accepted,excluded,duplicates
    payments,excluded,pdupes=unique(d.get('payments',[]),'payment_id')
    usable=[]
    for row in payments:
        required=('legal_entity_id','currency','amount','outcome','source_ids','outcome_authority','lifecycle_state')
        if any(k not in row or row[k] in (None,'',[]) for k in required) or row.get('outcome') not in OUTCOMES:
            excluded.append(row['payment_id']); gap('payment-evidence-gap','Payment outcome/monetary basis incomplete: '+row['payment_id'],row); continue
        if row['outcome']=='succeeded' and row.get('lifecycle_state') not in {'settled','funded','posted'}:
            row={**row,'outcome':'unknown'}; gap('authorization-not-outcome','Authorization/intake does not establish completed customer payment outcome.',row)
        usable.append(row)
    pindex={r['payment_id']:r for r in usable}
    attempts,aexcluded,adupes=unique(d.get('attempts',[]),'attempt_id'); accepted_attempts=[]
    for row in attempts:
        if row.get('payment_id') not in pindex or not row.get('at') or not row.get('source_ids') or row.get('status') not in OUTCOMES:
            aexcluded.append(row['attempt_id']); gap('attempt-evidence-gap','Attempt has unresolved payment linkage, time, status or evidence: '+row['attempt_id'],row); continue
        if not start <= timestamp(row['at']) < end:
            aexcluded.append(row['attempt_id']); gap('attempt-outside-window','Attempt excluded from incident denominator: '+row['attempt_id'],row); continue
        accepted_attempts.append(row)
    coverage=d.get('coverage',{})
    complete=coverage.get('complete') is True and coverage.get('expected_unique_payments')==len(usable) and bool(coverage.get('source_ids')) and not excluded
    if not complete: gap('population-incomplete','A complete source-bound eligible unique-payment inventory is needed for population impact rates.',coverage)
    if not usable: gap('payments-missing','Provide payment outcome inventory separately from retry/API logs.')
    counts=Counter(r['outcome'] for r in usable); amounts=defaultdict(lambda:defaultdict(Decimal))
    for row in usable: amounts[(row['legal_entity_id'],row['currency'])][row['outcome']]+=money(row['amount'])
    impact={'unique_payments':len(usable),'attempts':len(accepted_attempts),'retry_attempts':len(accepted_attempts)-len({r['payment_id'] for r in accepted_attempts}),'payment_outcomes':{s:counts[s] for s in sorted(OUTCOMES)},'attempt_outcomes':dict(Counter(r['status'] for r in accepted_attempts)),'population_coverage_verified_from_supplied_record':complete,'confirmed_success_rate':str(Decimal(counts['succeeded'])/len(usable)) if complete and usable else None,'eventual_success_rate':None if counts['unknown'] or not complete else str(Decimal(counts['succeeded'])/len(usable)) if usable else None,'payment_rows_deduplicated':pdupes,'attempt_rows_deduplicated':adupes,'quarantined_payment_ids':excluded,'quarantined_attempt_ids':aexcluded,'monetary_partitions':[{'legal_entity_id':k[0],'currency':k[1],'confirmed_success_amount':str(v['succeeded']),'failed_payment_amount':str(v['failed']),'unknown_outcome_amount':str(v['unknown']),'actual_loss':None} for k,v in sorted(amounts.items())]}
    timeline=[]; tids=Counter(r.get('event_id') for r in d.get('timeline',[]))
    timeline_rows=d.get('timeline',[])
    for row in sorted(timeline_rows,key=lambda r:timestamp(r['at']).timestamp() if r.get('at') else float('-inf')):
        if not row.get('event_id') or tids[row.get('event_id')]>1 or not row.get('at') or not row.get('source_ids') or row.get('kind') not in {'release','provider-status','trace','recovery','reconciliation'}:
            gap('timeline-evidence-gap','Timeline event identity/type/time/evidence unresolved.',row); continue
        if timestamp(row['at']).date().isoformat()>request['as_of']:
            gap('future-timeline-event','Future event cannot explain an observed incident.',row); continue
        timeline.append({**row,'causal_status':'observation only'})
    if not timeline: gap('timeline-missing','Supply release, trace and provider-status observations with UTC timestamps and version references.')
    hypotheses=[]
    for row in d.get('hypotheses',[]):
        if not row.get('supporting_event_ids') or not set(row.get('supporting_event_ids',[])).issubset({r['event_id'] for r in timeline}) or not row.get('discriminating_test'):
            gap('hypothesis-unsubstantiated','Hypothesis needs known observations and a discriminating next test.',row)
        hypotheses.append({**row,'causality':'unproven hypothesis','causal_conclusion':False})
    containment=d.get('containment',{}); replay=containment.get('replay',{})
    if containment.get('strategy') not in {'pause-new-intake','status-and-reconcile','observe-only'} or not containment.get('owner') or not containment.get('source_ids'):
        gap('containment-unresolved','Containment must identify owner and bounded strategy; no blind resend.',containment)
    replay_assessment='not proposed'
    if replay:
        replay_assessment='blocked pending original outcome and exact request evidence'
        pid=replay.get('payment_id'); payment=pindex.get(pid,{})
        safe=(payment.get('outcome')=='failed' and replay.get('authoritative_no_effect') is True and replay.get('same_idempotency_key') is True and replay.get('same_payload_hash') is True and replay.get('source_ids'))
        if safe: replay_assessment='candidate for separately authorized review; no execution'
        else: gap('unsafe-replay','Unknown outcomes, new keys, changed payloads or missing no-effect evidence prohibit a resend proposal.',replay)
    recovery=d.get('recovery',{})
    for field in ('owner','support_handoff','financial_reconciliation_ref','matched_payment_ids','unresolved_payment_ids','source_ids'):
        if field not in recovery or recovery[field] in (None,''): gap('recovery-evidence-gap','Recovery '+field+' is unresolved.',recovery)
    matched=recovery.get('matched_payment_ids',[]); unresolved=recovery.get('unresolved_payment_ids',[])
    if len(set(matched))!=len(matched) or len(set(unresolved))!=len(unresolved) or set(matched)&set(unresolved) or set(matched)|set(unresolved)!=set(pindex): gap('recovery-coverage-gap','Recovery partition must cover each unique payment exactly once.',recovery)
    if any(r['outcome']=='unknown' and r['payment_id'] not in unresolved for r in usable): gap('unknown-outcome-open','Unknown outcomes must remain in the unresolved recovery queue.',recovery)
    chains=[{'payment_id':pid,'outcome':pindex[pid]['outcome'],'attempts':sorted([r for r in accepted_attempts if r['payment_id']==pid],key=lambda r:timestamp(r['at']))} for pid in sorted(pindex)]
    return {'result':{'incident_id':request['request_id'],'window':window,'impact':impact,'retry_chains':chains,'timeline':timeline,'hypotheses':hypotheses,'containment_plan':containment,'replay_assessment':replay_assessment,'recovery_plan':recovery,'incident_closed':False,'root_cause_confirmed':False},'findings':findings,'handoffs':[{'target_skill':'payment-integration-readiness-reviewer','reason':'Review recovery and regression evidence before a release decision.','required_inputs':['incident timeline and affected versions','negative-path test artifacts','reconciliation and unresolved payment inventory']},{'target_skill':'payment-repair-planner','reason':'Assess individual unresolved money outcomes under the separate repair gate.','required_inputs':['original payment identities','authoritative outcome evidence','exact proposed repair and authority']}], 'limitations':['Inline source records are inspected as supplied, not authenticated. Failed/unknown payment amounts are exposure categories, not realized losses. Frequency and release coincidence do not establish cause.']}
