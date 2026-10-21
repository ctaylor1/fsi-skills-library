#!/usr/bin/env python3
"""Compare dated private-asset metrics with supplied watch thresholds and cash runway."""
from foundation_contract import D, date_value, ratio, exact, finish, source_issues, validate_common, cli_compute, validate_referenced_sources, validate_actual_date

@exact
def compute(doc):
    errors=validate_common(doc)
    if not errors:
        referenced_issues=validate_referenced_sources(doc)
        if 'source withheld for audience restriction' in referenced_issues:
            raise ValueError('request withheld for audience restriction')
        errors.extend(x for x in referenced_issues if "observation source as-of exceeds review date" in x)
    if errors:raise ValueError('; '.join(errors))
    issues=[];findings=[];seen=set();cutoff=date_value(doc['as_of']);maxage=doc['maximum_observation_age_days']
    if isinstance(maxage,bool) or not isinstance(maxage,int) or maxage<0:raise ValueError('nonnegative integer maximum observation age required')
    for m in doc['metrics']:
        if m['metric_id'] in seen:raise ValueError('duplicate metric_id')
        seen.add(m['metric_id']);g=source_issues(doc,m.get('source_ref'))+source_issues(doc,m.get('threshold_source_ref'))
        when=date_value(m['observed_at'])
        if when>cutoff or (cutoff-when).days>maxage:g.append('observation outside allowed date window')
        if not m.get('unit') or m.get('unit')!=m.get('threshold_unit'):g.append('metric and threshold units differ or unknown')
        if m.get('direction') not in {'minimum','maximum'}:raise ValueError('threshold direction required')
        if m.get('value') is None or m.get('threshold') is None:g.append('metric or threshold unknown')
        headroom=delta=None;state='not_evaluable'
        if not g:
            validate_actual_date(doc,m['observed_at'],m['source_ref'])
            value=D(m['value']);threshold=D(m['threshold']);headroom=value-threshold if m['direction']=='minimum' else threshold-value;state='watch_exception' if headroom<0 else 'within_supplied_threshold'
            if m.get('prior_value') is not None:
                prior=date_value(m['prior_observed_at']);pg=source_issues(doc,m.get('prior_source_ref'))
                if prior>=when or m.get('prior_unit')!=m['unit']:pg.append('prior observation is not comparable')
                if pg:issues.extend(m['metric_id']+': '+x for x in pg)
                else:
                    validate_actual_date(doc,m['prior_observed_at'],m['prior_source_ref'])
                    delta=value-D(m['prior_value'])
            if headroom<0:issues.append(m['metric_id']+': supplied watch threshold crossed; investigate')
        issues.extend(m['metric_id']+': '+x for x in g);findings.append({'metric_id':m['metric_id'],'state':state,'headroom':None if headroom is None else str(headroom),'change_from_prior':None if delta is None else str(delta),'unit':m.get('unit'),'source_ref':m.get('source_ref') if not g else None,'legal_breach_determined':False})
    if not seen:raise ValueError('metrics must be nonempty')
    liquidity=doc['liquidity'];lg=source_issues(doc,liquidity.get('source_ref'));runway=None
    if any(liquidity.get(k) is None for k in ('cash_available','monthly_net_cash_burn')):lg.append('liquidity observations unknown')
    observed=date_value(liquidity['observed_at'])
    if observed>cutoff or (cutoff-observed).days>maxage:lg.append('liquidity observation stale or future')
    if not lg:
        validate_actual_date(doc,liquidity['observed_at'],liquidity['source_ref'])
        cash=D(liquidity['cash_available']);burn=D(liquidity['monthly_net_cash_burn'])
        if cash<0:raise ValueError('cash available must be nonnegative')
        if burn>0:runway=ratio(cash,burn)
        else:lg.append('positive burn not supplied; finite runoff estimate not applicable')
    events=[];eventids=set()
    for e in doc.get('events',[]):
        if e['event_id'] in eventids:raise ValueError('duplicate event_id')
        eventids.add(e['event_id']);eg=source_issues(doc,e.get('source_ref'))
        if date_value(e['event_date'])>cutoff:eg.append('future event excluded from observed chronology')
        if eg:issues.extend(e['event_id']+': '+x for x in eg)
        else:
            validate_actual_date(doc,e['event_date'],e['source_ref'])
            events.append({'event_id':e['event_id'],'event_date':e['event_date'],'event_type':e['event_type'],'source_ref':e['source_ref']})
    issues.extend(lg)
    return finish(doc,'private-investment-monitor','dated-private-asset-watch-review/1',{'metric_findings':findings,'constant_burn_runway_months':runway,'events':sorted(events,key=lambda e:(e['event_date'],e['event_id']))},issues,limitations=['Threshold flags are monitoring signals; covenant default, valuation change and remedial action remain separate professional determinations.','Runway assumes the supplied monthly burn remains constant and excludes future financing; it is not a liquidity forecast.'])

if __name__=='__main__':cli_compute(compute)
