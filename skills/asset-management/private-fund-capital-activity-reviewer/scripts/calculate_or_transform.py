#!/usr/bin/env python3
"""Reconcile explicit LP unfunded effects and cash direction from supplied notices."""
from foundation_contract import D, date_value, exact, finish, source_issues, validate_common, cli_compute, validate_referenced_sources, validate_actual_date

@exact
def compute(doc):
    errors=validate_common(doc)
    if not errors:
        referenced_issues=validate_referenced_sources(doc)
        if 'source withheld for audience restriction' in referenced_issues:
            raise ValueError('request withheld for audience restriction')
        errors.extend(x for x in referenced_issues if "observation source as-of exceeds review date" in x)
    if errors: raise ValueError('; '.join(errors))
    issues=[]; ledgers=[]; ids=set(); lps=doc['lp_balances'];events=doc['events']
    if not lps or not isinstance(events,list): raise ValueError('LP balances and events list required')
    if len({x['lp_id'] for x in lps})!=len(lps): raise ValueError('duplicate LP identity')
    lpids={x['lp_id'] for x in lps}
    for e in events:
        if e['event_id'] in ids or e['lp_id'] not in lpids: raise ValueError('duplicate event or unmapped LP')
        ids.add(e['event_id'])
    for lp in lps:
        lid=lp['lp_id'];gaps=source_issues(doc,lp.get('source_ref'));contributions=D('0');distributions=D('0');change=D('0');detail=[]
        if lp.get('opening_unfunded') is None: gaps.append('opening unfunded unknown')
        for e in [x for x in events if x['lp_id']==lid]:
            eg=source_issues(doc,e.get('source_ref'))
            if date_value(e['event_date'])>date_value(doc['as_of']): eg.append('future event is not booked activity')
            if e.get('currency')!=doc['currency']: eg.append('currency mismatch; no FX supplied')
            if e['type'] not in {'call','distribution','commitment_change'}: raise ValueError('unsupported capital event type')
            if e.get('unfunded_effect') not in {'increase','decrease','none'}: eg.append('explicit unfunded effect required')
            if e.get('amount') is None or e.get('unfunded_amount') is None: eg.append('cash or unfunded amount unknown')
            if e['type']=='distribution' and not isinstance(e.get('recallable'),bool): eg.append('recallable classification unknown')
            if eg: gaps.extend(e['event_id']+': '+g for g in eg);continue
            validate_actual_date(doc,e['event_date'],e['source_ref'])
            amount=D(e['amount']);impact=D(e['unfunded_amount'])
            if amount<0 or impact<0: raise ValueError('capital amounts must be nonnegative')
            if e['type']=='commitment_change' and amount!=impact: raise ValueError('noncash commitment change amount must equal its explicit unfunded impact')
            if e['type'] in {'call','distribution'} and impact>amount: raise ValueError('unfunded amount exceeds cash amount')
            if e['unfunded_effect']=='none' and impact!=0: raise ValueError('none effect requires zero unfunded amount')
            if e['type']=='call' and e['unfunded_effect']=='increase': raise ValueError('call cannot increase unfunded in this method')
            if e['type']=='distribution' and (e['unfunded_effect']=='decrease' or (e['recallable'] and (e['unfunded_effect']!='increase' or impact==0)) or (not e['recallable'] and impact!=0)): raise ValueError('recallable distribution and reinstatement inconsistent')
            signed=impact if e['unfunded_effect']=='increase' else -impact if e['unfunded_effect']=='decrease' else D('0')
            change+=signed
            if e['type']=='call':contributions+=amount
            if e['type']=='distribution':distributions+=amount
            detail.append({'event_id':e['event_id'],'source_ref':e['source_ref'],'unfunded_change':str(signed),'cash_to_lp':str(amount if e['type']=='distribution' else -amount if e['type']=='call' else D('0'))})
        closing=None if gaps else D(lp['opening_unfunded'])+change
        residual=None if closing is None or lp.get('reported_closing_unfunded') is None else D(lp['reported_closing_unfunded'])-closing
        if closing is not None and closing<0:gaps.append('negative unfunded balance requires investigation')
        if lp.get('reported_closing_unfunded') is None:gaps.append('reported closing unfunded unavailable')
        if residual is not None and residual!=0:gaps.append('reported closing unfunded differs from rollforward')
        issues.extend(lid+': '+g for g in gaps)
        ledgers.append({'lp_id':lid,'events_reviewed':detail,'known_calls':str(contributions),'known_distributions':str(distributions),'known_net_cash_to_lp':str(distributions-contributions),'calculated_closing_unfunded':None if closing is None else str(closing),'reported_minus_calculated':None if residual is None else str(residual),'complete':not gaps})
    return finish(doc,'private-fund-capital-activity-reviewer','explicit-lp-unfunded-rollforward/1',{'lp_rollforwards':ledgers},issues,limitations=['Single currency, supplied notices only; no payment, accounting posting, NAV, IRR or legal recallability determination.','Known cash subtotals are partial whenever a source/event is excluded; no missing amount is zero-filled.'])

if __name__=='__main__': cli_compute(compute)
