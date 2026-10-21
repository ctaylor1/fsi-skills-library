"""Supplied-factor liability PV, finite-difference sensitivity and real-asset cash coverage."""
from datetime import timedelta
from foundation_contract import D, exact, ratio, finish, text, date_value, require_sources, validate_common, validate_actual_date
from specialist_contract import validate_specialist_common as validate_common

def rows(doc,key):
    values=doc.get(key)
    if not isinstance(values,list) or not values or len(values)>10000: raise ValueError(key+' requires1..10000 rows')
    seen=set()
    for row in values:
        fields(doc,row,'id','currency')
        if row['id'] in seen or row['currency']!=doc['currency']: raise ValueError('duplicate identity or mixed currency in '+key)
        seen.add(row['id'])
    return values

def fields(doc,row,*keys):
    if not isinstance(row,dict) or any(not text(row.get(k)) for k in keys): raise ValueError('missing '+', '.join(keys))
    require_sources(doc,[row.get('source_ref')])

def n(row,key,low=0,high=None):
    value=D(row.get(key))
    if value<D(low) or high is not None and value>D(high): raise ValueError(key+' outside supported range')
    return value

@exact
def compute(doc):
    errors=validate_common(doc)
    if errors: raise ValueError('; '.join(errors))
    if doc.get('extension')!='liability-real-assets': raise ValueError('unsupported extension')
    if 'institutional_constraints' in doc or 'candidates' in doc: raise ValueError('legacy candidate fields cannot be mixed with the extension')
    policy=doc.get('policy');fields(doc,policy,'version','reviewed_by','objective','currency','discount_basis','effective_from','expires')
    if policy['currency']!=doc['currency'] or not date_value(policy['effective_from'])<=date_value(doc['as_of'])<=date_value(policy['expires']): raise ValueError('policy currency or effective period mismatch')
    if policy['discount_basis']!='supplied-factors-by-dated-liability': raise ValueError('local subset requires explicit discount factors; curve/actuarial/ALM engines remain external')
    limit=n(policy,'maximum_illiquid_fraction',0,1);max_age=n(policy,'maximum_valuation_age_days');shock=n(policy,'parallel_shift_bps',0,10000)
    if max_age!=max_age.to_integral_value() or shock<=0: raise ValueError('integer valuation age and positive parallel shock required')
    liabilities=rows(doc,'liability_cashflows');assets=rows(doc,'assets');factors=rows(doc,'discount_factors');scenarios=rows(doc,'scenarios')
    cashflows=doc.get('asset_cashflows')
    if not isinstance(cashflows,list) or len(cashflows)>10000: raise ValueError('explicit bounded asset cashflow list required')
    require_sources(doc,[doc.get('inventory_source_ref')]);issues=[]
    if doc.get('inventory_complete') is not True: issues.append('asset/liability cashflow completeness is unestablished')
    by_liability={r['id']:r for r in liabilities};by_asset={r['id']:r for r in assets};pv={key:D(0) for key in ('base','down','up')};seen=set()
    for row in liabilities:
        fields(doc,row,'due_date','liability_basis')
        if date_value(row['due_date'])<date_value(doc['as_of']): raise ValueError('past-due liability requires separate reconciliation')
        n(row,'amount')
    for row in factors:
        fields(doc,row,'liability_id','due_date','policy_version')
        lid=row['liability_id']
        if lid not in by_liability or lid in seen or row['due_date']!=by_liability[lid]['due_date'] or row['policy_version']!=policy['version']: raise ValueError('discount factor liability/date/version mapping mismatch')
        seen.add(lid)
        for key in pv:
            factor=n(row,key+'_factor',0,10)
            if factor<=0: raise ValueError('discount factors must be positive')
            pv[key]+=n(by_liability[lid],'amount')*factor
        if not n(row,'down_factor')>=n(row,'base_factor')>=n(row,'up_factor'): raise ValueError('positive liabilities require ordered parallel-rate-shift discount factors')
    if seen!=set(by_liability): raise ValueError('every liability requires exactly one dated factor triplet')
    stale=set()
    for row in assets:
        fields(doc,row,'asset_class','earliest_liquidation_date','valuation_date','valuation_basis')
        if type(row.get('illiquid')) is not bool or type(row.get('real_asset')) is not bool: raise ValueError('illiquid/real_asset flags must be booleans')
        if row['real_asset'] and row['asset_class'] not in {'real-estate','infrastructure','natural-resources'}: raise ValueError('unsupported real-asset class')
        valued=validate_actual_date(doc,row['valuation_date'],row['source_ref']);date_value(row['earliest_liquidation_date'])
        n(row,'market_value');n(row,'liquidation_fraction',0,1)
        if (date_value(doc['as_of'])-valued).days>max_age: stale.add(row['id']);issues.append('asset valuation exceeds supplied age limit: '+row['id'])
    flow_ids=set();principal={aid:D(0) for aid in by_asset}
    for row in cashflows:
        fields(doc,row,'id','asset_id','date','kind','currency')
        if row['id'] in flow_ids or row['asset_id'] not in by_asset or row['currency']!=doc['currency']: raise ValueError('asset flow identity/currency mismatch')
        flow_ids.add(row['id']);when=date_value(row['date']);amount=n(row,'amount')
        if when<date_value(doc['as_of']): raise ValueError('historical asset cashflow cannot be available again')
        if row['kind']=='principal':
            asset=by_asset[row['asset_id']]
            if when<date_value(asset['earliest_liquidation_date']): raise ValueError('principal cashflow predates supplied liquidity date')
            principal[row['asset_id']]+=amount
        elif row['kind']!='distribution': raise ValueError('asset cashflows must distinguish principal from distributions')
    for aid,amount in principal.items():
        if amount>n(by_asset[aid],'market_value')*n(by_asset[aid],'liquidation_fraction'): raise ValueError('cumulative principal cashflow exceeds supplied liquidatable asset value')
    opening=n(doc,'opening_cash');shift=shock/D(10000);duration=ratio(pv['down']-pv['up'],D(2)*pv['base']*shift);convexity=ratio(pv['down']+pv['up']-D(2)*pv['base'],pv['base']*shift*shift)
    if pv['base']==0: issues.append('zero liability PV makes duration, convexity and funding ratio undefined')
    scenario_results=[]
    for scenario in scenarios:
        fields(doc,scenario,'policy_version','discount_case')
        if scenario['policy_version']!=policy['version'] or scenario['discount_case'] not in pv: raise ValueError('scenario policy or discount case mismatch')
        multiplier=n(scenario,'liability_multiplier',0,10);shocks=scenario.get('asset_shocks')
        if not isinstance(shocks,list) or len(shocks)!=len(assets): raise ValueError('scenario must cover every asset exactly once')
        mapped={};asset_value=opening;illiquid=D(0);projected=[];gaps=[]
        for row in shocks:
            fields(doc,row,'asset_id')
            aid=row['asset_id']
            if aid not in by_asset or aid in mapped: raise ValueError('unknown or duplicate scenario asset')
            price=n(row,'price_return',-1,10);cash=n(row,'cashflow_multiplier',0,10);delay=n(row,'delay_days',0,36500)
            if delay!=delay.to_integral_value(): raise ValueError('delay_days must be integer')
            mapped[aid]=(price,cash,int(delay));value=n(by_asset[aid],'market_value')*(D(1)+price);asset_value+=value
            if by_asset[aid]['illiquid']: illiquid+=value
            if principal[aid]*cash>value*n(by_asset[aid],'liquidation_fraction'): gaps.append('stressed principal cashflow exceeds stressed liquidatable value: '+aid)
        for flow in cashflows:
            price,cash,delay=mapped[flow['asset_id']];projected.append((date_value(flow['date'])+timedelta(days=delay),n(flow,'amount')*cash))
        coverage=[]
        for day in sorted({r['due_date'] for r in liabilities}):
            due=date_value(day);available=opening+sum((amount for date,amount in projected if date<=due),D(0));need=sum((n(r,'amount')*multiplier for r in liabilities if date_value(r['due_date'])<=due),D(0));gap=available-need
            coverage.append({'due_date':day,'available_cash':str(available),'liability_cash':str(need),'headroom':str(gap)})
            if gap<0: gaps.append('dated liability cash shortfall: '+day)
        if illiquid>asset_value*limit: gaps.append('stressed illiquid assets exceed supplied institutional limit')
        selected_pv=pv[scenario['discount_case']]*multiplier
        issues.extend(scenario['id']+': '+g for g in gaps)
        qualified=doc.get('inventory_complete') is True and not stale and not any('principal cashflow exceeds' in g for g in gaps)
        scenario_results.append({'id':scenario['id'],'asset_value':str(asset_value) if qualified else None,'liability_pv':str(selected_pv) if doc.get('inventory_complete') is True else None,
                                 'funding_gap':str(asset_value-selected_pv) if qualified else None,'funded_ratio':ratio(asset_value,selected_pv) if qualified else None,
                                 'illiquid_fraction':ratio(illiquid,asset_value) if qualified else None,'cash_coverage':coverage if qualified else [],'issues':gaps,'selected':False})
    return finish(doc,'institutional-investment-solutions-planner','dated-liability-real-asset-scenarios-v1',{'extension':'liability-real-assets','liability_present_values':{k:str(v) if doc.get('inventory_complete') is True else None for k,v in pv.items()},'parallel_shift_bps':str(shock),'effective_duration':duration if doc.get('inventory_complete') is True else None,'effective_convexity':convexity if doc.get('inventory_complete') is True else None,'scenarios':scenario_results,'portfolio_optimized':False,'actuarial_valuation':False,'delegated_authority_granted':False},issues,
                  ['PV is the sum of supplied dated amounts times supplied factor triplets; no curve interpolation, liability projection, mortality, inflation calibration or accounting liability certification.',
                   'Central finite differences use the same supplied parallel shock on either side; factors and asset scenarios are independently reviewed inputs, not market forecasts.',
                   'Real-asset values and cashflows are supplied; no appraisal, look-through leverage, ALM optimization, nonlinear option valuation or execution.'])
