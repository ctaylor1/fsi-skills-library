"""Bounded supplied-input review. No source authentication or business action."""
from decimal import Decimal
from foundation_contract import (D,ratio,date_value,exact,validate_common,validate_actual_date,validate_referenced_sources,require_sources,finish,cli_compute)
from native_integrity import canonical_hash

@exact
def analyze(d):
    require_sources(d,[x.get('source_ref') for x in d['intentions']])
    issues=[];rows=[];total=Decimal(0);ids=set();participation=D(d['maximum_adv_fraction'])
    if not 0<participation<=1:raise ValueError('participation fraction outside(0,1]')
    for r in d['intentions']:
        if r['intent_id'] in ids:raise ValueError('duplicate intent')
        ids.add(r['intent_id']);q=D(r['quantity']);px=D(r['price']);adv=D(r['adv']);bps=D(r['quoted_cost_bps'])
        if q<=0 or px<=0 or adv<=0 or bps<0 or r['side'] not in {'buy','sell'}:raise ValueError('unsupported trade/market domain')
        if r['currency']!=d['currency']:raise ValueError('cross-currency needs explicit FX/settlement adapter')
        validate_actual_date(d,r['market_as_of'],r['source_ref'])
        if date_value(r['market_as_of'])!=date_value(d['as_of']):raise ValueError('market snapshot stale for supplied trading date')
        if date_value(r['settlement_date'])<date_value(d['as_of']):raise ValueError('settlement date before trading review')
        fraction=ratio(q,adv);notional=q*px;cost=notional*bps/10000;total+=cost;findings=[]
        if q>adv*participation:findings.append('participation limit exceeded; scheduling requires desk review')
        if r.get('broker_approval_status')!='approved' or not r.get('broker_approval_ref'):findings.append('broker approval evidence missing')
        if r.get('mandate_review_status')!='reviewed' or not r.get('mandate_review_ref'):findings.append('mandate review evidence missing')
        for field in ('broker_approval_ref','mandate_review_ref'):
            if r.get(field):require_sources(d,[r[field]],require_approved=True)
        issues.extend(r['intent_id']+': '+x for x in findings)
        rows.append({'intent_id':r['intent_id'],'notional':str(notional),'adv_fraction':fraction,'estimated_quoted_cost':str(cost),'findings':findings,'execution_authority':False})
    if not rows:raise ValueError('trade intentions required')
    return {'intent_review':rows,'estimated_total_cost':str(total),'routing_performed':False,'funding_review_required':True},issues

SKILL='buy-side-trading-planner'
METHOD='supplied-trade-intent-feasibility'
LIMITS=['Quoted cost is an estimate, not a market impact model or execution guarantee.', 'No broker selection, schedule optimizer, calendar service, funding reservation or OMS connectivity.']
HANDOFFS=['transaction-cost-estimator', 'best-execution-reviewer', 'investment-mandate-reviewer']

def validate(doc):
    errors=validate_common(doc)
    if errors:return errors
    errors+=validate_referenced_sources(doc)
    if doc.get('requested_action','review') not in ('review','draft'):errors.append('business execution unsupported')
    if errors:return errors
    try:analyze(doc)
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError) as exc:errors.append(str(exc))
    return errors

def compute(doc):
    errors=validate(doc)
    if errors:raise ValueError('; '.join(errors))
    results,issues=analyze(doc)
    return finish(doc,SKILL,METHOD,results,issues=issues,limitations=LIMITS,handoffs=HANDOFFS)

if __name__=='__main__':cli_compute(compute)
