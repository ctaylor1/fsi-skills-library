#!/usr/bin/env python3
"""Roll forward caller-supplied LP cash and unfunded scenarios without forecasting."""
from foundation_contract import D, date_value, exact, finish, source_issues, validate_common, cli_compute, validate_referenced_sources

@exact
def compute(doc):
    errors=validate_common(doc)
    if not errors:
        referenced_issues=validate_referenced_sources(doc)
        if 'source withheld for audience restriction' in referenced_issues:
            raise ValueError('request withheld for audience restriction')
        errors.extend(x for x in referenced_issues if "observation source as-of exceeds review date" in x)
    if errors: raise ValueError('; '.join(errors))
    issues=[];results=[];seen=set();opening=doc['opening_balances'];basegaps=source_issues(doc,opening.get('source_ref'))
    if any(opening.get(k) is None for k in ('cash','unfunded','liquidity_floor')):basegaps.append('opening balances or liquidity floor unknown')
    for scenario in doc['scenarios']:
        sid=scenario['scenario_id']
        if sid in seen:raise ValueError('duplicate scenario_id')
        seen.add(sid);gaps=basegaps+source_issues(doc,scenario.get('source_ref'));periods=[];last=date_value(doc['as_of']);cash=uf=floor=None
        if not gaps:
            cash=D(opening['cash']);uf=D(opening['unfunded']);floor=D(opening['liquidity_floor'])
            if uf<0 or floor<0:raise ValueError('opening unfunded/floor must be nonnegative')
        if not scenario['periods']:gaps.append('scenario has no periods')
        for p in scenario['periods']:
            end=date_value(p['period_end'])
            if end<=last:raise ValueError('scenario periods must increase strictly after as_of')
            last=end;pg=source_issues(doc,p.get('source_ref'))
            fields=('new_commitments','calls','distributions','recallable_reinstatement','other_cash_flow')
            if any(p.get(k) is None for k in fields):pg.append('scenario cashflow assumption unknown')
            if pg:gaps.extend(p['period_end']+': '+x for x in pg);cash=uf=None
            if cash is None:
                periods.append({'period_end':p['period_end'],'closing_cash':None,'closing_unfunded':None,'liquidity_headroom':None,'status':'not_evaluable'});continue
            a={k:D(p[k]) for k in fields}
            if any(a[k]<0 for k in fields if k!='other_cash_flow'):raise ValueError('calls/distributions/commitments/reinstatements must be nonnegative')
            if a['recallable_reinstatement']>a['distributions']:raise ValueError('reinstatement exceeds distribution')
            cash+=a['distributions']+a['other_cash_flow']-a['calls'];uf+=a['new_commitments']+a['recallable_reinstatement']-a['calls'];headroom=cash-floor
            flags=[]
            if headroom<0:flags.append('liquidity_floor_shortfall')
            if uf<0:flags.append('calls_exceed_available_commitment')
            issues.extend(sid+'/'+p['period_end']+': '+f for f in flags)
            periods.append({'period_end':p['period_end'],'source_ref':p['source_ref'],'closing_cash':str(cash),'closing_unfunded':str(uf),'liquidity_headroom':str(headroom),'flags':flags,'status':'scenario_arithmetic'})
        issues.extend(sid+': '+g for g in gaps);results.append({'scenario_id':sid,'periods':periods,'forecast':False,'commitment_authorized':False})
    if not seen:raise ValueError('nonempty scenarios required')
    return finish(doc,'private-capital-commitment-planner','supplied-scenario-cash-unfunded-pacing/1',{'scenarios':results},issues,limitations=['Calls consume unfunded commitment in this bounded model; outside-commitment fees and financing require separate explicit modeling.','Scenario schedules are assumptions, not estimated call/distribution forecasts. New commitments have no immediate cash effect unless a call is separately scheduled.'])

if __name__=='__main__': cli_compute(compute)
