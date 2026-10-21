#!/usr/bin/env python3
"""Supplied private-credit scenarios, definition-scoped covenants and maturity evidence."""
from foundation_contract import D, date_value, ratio, exact, finish, source_issues, validate_common, cli_compute, validate_referenced_sources

@exact
def compute(doc):
    errors=validate_common(doc)
    if not errors:
        referenced_issues=validate_referenced_sources(doc)
        if 'source withheld for audience restriction' in referenced_issues:
            raise ValueError('request withheld for audience restriction')
        errors.extend(x for x in referenced_issues if "observation source as-of exceeds review date" in x)
    if errors:raise ValueError('; '.join(errors))
    facility=doc['facility'];issues=[];fg=source_issues(doc,facility.get('source_ref'));horizon=doc['maturity_watch_days']
    if isinstance(horizon,bool) or not isinstance(horizon,int) or horizon<0:raise ValueError('maturity watch days must be nonnegative integer')
    maturity_days=(date_value(facility['maturity_date'])-date_value(doc['as_of'])).days
    if maturity_days<=horizon:issues.append('facility maturity within watch horizon or past due; review refinancing evidence')
    if facility.get('balloon_amount') is None:fg.append('balloon amount unknown')
    elif D(facility['balloon_amount'])<0:raise ValueError('balloon cannot be negative')
    covenants=doc['covenants'];ids=set()
    for c in covenants:
        if c['covenant_id'] in ids:raise ValueError('duplicate covenant_id')
        ids.add(c['covenant_id'])
        if c['metric'] not in {'net_leverage','interest_coverage','dscr'} or c['direction'] not in {'maximum','minimum'}:raise ValueError('unsupported metric or direction')
    results=[];seen=set()
    for s in doc['scenarios']:
        if s['scenario_id'] in seen:raise ValueError('duplicate scenario_id')
        seen.add(s['scenario_id']);g=fg+source_issues(doc,s.get('source_ref'));values=None;pairs={}
        fields=('debt','cash','ebitda','cash_interest','scheduled_principal','cash_available_for_debt_service')
        if any(s.get(k) is None for k in fields):g.append('scenario debt-service observation unknown')
        if not s.get('definition_id'):g.append('reviewed financial definition id required')
        if not g:
            a={k:D(s[k]) for k in fields}
            if any(a[k]<0 for k in ('debt','cash','cash_interest','scheduled_principal')):raise ValueError('debt/cash/service amounts must be nonnegative')
            pairs={'net_leverage':(a['debt']-a['cash'],a['ebitda']),'interest_coverage':(a['ebitda'],a['cash_interest']),'dscr':(a['cash_available_for_debt_service'],a['cash_interest']+a['scheduled_principal'])}
            values={metric:ratio(n,d) if d>0 else None for metric,(n,d) in pairs.items()}
        checks=[]
        for c in covenants:
            cg=source_issues(doc,c.get('source_ref'))
            if c.get('definition_id')!=s.get('definition_id') or not c.get('definition_id'):cg.append('covenant and scenario definitions do not match')
            if c.get('status')!='active':cg.append('covenant applicability is not active; obtain reviewed terms')
            value=None if values is None else values[c['metric']]
            if value is None or c.get('threshold') is None:cg.append('ratio or threshold not evaluable')
            headroom=None;exact_margin=None
            if not cg:
                threshold=D(c['threshold']);numerator,denominator=pairs[c['metric']]
                exact_margin=threshold*denominator-numerator if c['direction']=='maximum' else numerator-threshold*denominator
                headroom=ratio(exact_margin,denominator)
            state='not_evaluable' if exact_margin is None else 'potential_exception' if exact_margin<0 else 'within_supplied_threshold'
            if state=='potential_exception':issues.append(s['scenario_id']+'/'+c['covenant_id']+': potential covenant exception; no default determination')
            issues.extend(s['scenario_id']+'/'+c['covenant_id']+': '+x for x in cg)
            checks.append({'covenant_id':c['covenant_id'],'metric':c['metric'],'value':value,'headroom':headroom,'exact_cross_product_margin':None if exact_margin is None else str(exact_margin),'state':state,'legal_default':None})
        issues.extend(s['scenario_id']+': '+x for x in g);results.append({'scenario_id':s['scenario_id'],'ratios':values,'covenant_checks':checks,'source_ref':s.get('source_ref') if values else None})
    if not seen:raise ValueError('scenarios required')
    issues.extend(fg)
    return finish(doc,'private-credit-investment-reviewer','supplied-credit-scenarios-covenant-basis/1',{'facility_id':facility['facility_id'],'days_to_maturity':None if fg else maturity_days,'balloon_amount':None if fg else facility.get('balloon_amount'),'scenarios':results,'ratio_rounding_places':12},issues,limitations=['Supplied comparable financial definitions only; no issuer research extraction, cashflow forecast, valuation, recovery model, commitment, legal default or waiver decision.','Displayed ratios/headroom round to12 places; threshold flags use exact cross-products with positive denominators, so display rounding does not determine the flag.'])

if __name__=='__main__':cli_compute(compute)
