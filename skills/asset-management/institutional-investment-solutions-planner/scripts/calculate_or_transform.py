#!/usr/bin/env python3
"""Compare supplied institutional candidate constraints and liability cash coverage."""
from foundation_contract import D, date_value, ratio, exact, finish, source_issues, validate_common, cli_compute, validate_referenced_sources

@exact
def compute(doc):
    if isinstance(doc,dict) and 'extension' in doc:
        if doc['extension']!='liability-real-assets': raise ValueError('unsupported institutional solutions extension')
        from liability_real_assets import compute as extension_compute
        return extension_compute(doc)
    errors=validate_common(doc)
    if not errors:
        referenced_issues=validate_referenced_sources(doc)
        if 'source withheld for audience restriction' in referenced_issues:
            raise ValueError('request withheld for audience restriction')
        errors.extend(x for x in referenced_issues if "observation source as-of exceeds review date" in x)
    if errors:raise ValueError('; '.join(errors))
    mandate=doc['institutional_constraints'];issues=[];mg=source_issues(doc,mandate.get('source_ref'));results=[];seen=set();liabilities=doc['liabilities']
    if not mandate.get('objective') or not mandate.get('governance_owner'):mg.append('institutional objective or governance owner missing')
    if mandate.get('maximum_illiquid_fraction') is None:mg.append('illiquidity limit unknown')
    if not isinstance(mandate.get('permitted_delegated_actions'),list):raise ValueError('explicit delegated-action list required')
    liability_ids=set()
    for l in liabilities:
        if l['liability_id'] in liability_ids:raise ValueError('duplicate liability_id')
        liability_ids.add(l['liability_id']);mg.extend(source_issues(doc,l.get('source_ref')))
        if l.get('amount') is None:mg.append('liability amount unknown')
        elif D(l['amount'])<0:raise ValueError('liability amounts must be nonnegative')
        if date_value(l['due_date'])<date_value(doc['as_of']):mg.append('past-due liability requires separate reconciliation')
    if not liabilities:mg.append('liability schedule missing; liquidity fit not established')
    for candidate in doc['candidates']:
        cid=candidate['candidate_id']
        if cid in seen:raise ValueError('duplicate candidate_id')
        seen.add(cid);g=mg+source_issues(doc,candidate.get('source_ref'));coverage=[];illiquid=None;flags=[]
        if any(candidate.get(k) is None for k in ('total_assets','illiquid_assets')):g.append('candidate asset coverage unknown')
        if not isinstance(candidate.get('delegated_actions'),list):raise ValueError('candidate delegated actions must be a list')
        unpermitted=sorted(set(candidate['delegated_actions'])-set(mandate['permitted_delegated_actions']))
        if unpermitted:flags.append('candidate delegation exceeds supplied institutional authority')
        dates=set()
        for flow in candidate['liquidity_availability']:
            g.extend(source_issues(doc,flow.get('source_ref')))
            if flow['available_date'] in dates:raise ValueError('consolidate availability at each date before review')
            dates.add(flow['available_date']);date_value(flow['available_date'])
            if flow.get('amount') is None:g.append('liquidity availability unknown')
            elif D(flow['amount'])<0:raise ValueError('available cash must be nonnegative')
        if not g:
            assets=D(candidate['total_assets']);ill=D(candidate['illiquid_assets']);limit=D(mandate['maximum_illiquid_fraction'])
            if assets<=0 or not 0<=ill<=assets or not 0<=limit<=1:raise ValueError('invalid asset/illiquidity constraint')
            illiquid=ratio(ill,assets)
            if ill>assets*limit:flags.append('illiquid assets exceed supplied limit')
            if sum((D(f['amount']) for f in candidate['liquidity_availability']),D('0'))>assets:g.append('cash availability exceeds candidate assets; financing not supported')
            else:
                for due in sorted({l['due_date'] for l in liabilities}):
                    available=sum((D(f['amount']) for f in candidate['liquidity_availability'] if f['available_date']<=due),D('0'));needed=sum((D(l['amount']) for l in liabilities if l['due_date']<=due),D('0'));headroom=available-needed
                    coverage.append({'due_date':due,'cumulative_cash_available':str(available),'cumulative_liabilities':str(needed),'headroom':str(headroom)})
                    if headroom<0:flags.append('liability cash shortfall at '+due)
        issues.extend(cid+': '+x for x in g+flags);results.append({'candidate_id':cid,'illiquid_fraction':illiquid,'liability_coverage':coverage,'fit_gaps':g+flags,'unpermitted_delegated_actions':unpermitted,'selected':False})
    if not seen:raise ValueError('candidate alternatives required')
    return finish(doc,'institutional-investment-solutions-planner','institutional-constraint-candidate-fit/1',{'candidates':results,'ranking':None,'delegated_authority_granted':False},issues,limitations=['Supplied alternatives and constraints only; no optimized allocation, manager selection, liability valuation, guaranteed return, fiduciary opinion or mandate delegation.','Liquidity availability amounts are incremental scenario assumptions; double-counted assets, financing, collateral and uncertainty require separate institutional review.'])

if __name__=='__main__':cli_compute(compute)
