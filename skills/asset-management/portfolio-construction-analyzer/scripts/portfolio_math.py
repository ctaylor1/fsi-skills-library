"""Bounded long-only supplied candidate analytics, v1.0 (MIT). No optimizer."""
from decimal import Context,Decimal,localcontext
from foundation_contract import D,ratio

def validate_model(assets,covariance):
    if not isinstance(assets,list) or not assets or len(assets)>100:raise ValueError('1..100 assets required')
    ids=[a['id'] for a in assets]
    if any(not isinstance(k,str) or not k for k in ids) or len(set(ids))!=len(ids):raise ValueError('unique asset ids required')
    for a in assets:
        D(a['expected_return'])
        if D(a['liquidity_days'])<0:raise ValueError('nonnegative liquidity days required')
        if not isinstance(a['group'],str) or not a['group']:raise ValueError('asset group required')
    n=len(assets)
    if not isinstance(covariance,list) or len(covariance)!=n or any(not isinstance(row,list) or len(row)!=n for row in covariance):raise ValueError('covariance dimensions mismatch')
    matrix=[[D(x) for x in row] for row in covariance]
    if any(matrix[i][j]!=matrix[j][i] for i in range(n) for j in range(n)):raise ValueError('covariance must be symmetric')
    # LDL PSD check uses explicitly bounded high precision, not rounded portfolio dollars.
    with localcontext(Context(prec=100)):
        work=[row[:] for row in matrix];tolerance=Decimal('1e-30')
        for k in range(n):
            pivot=work[k][k]
            if pivot < -tolerance:raise ValueError('covariance is not positive semidefinite')
            if abs(pivot)<=tolerance:
                if any(abs(work[i][k])>tolerance for i in range(k+1,n)):raise ValueError('covariance is not positive semidefinite')
                continue
            for i in range(k+1,n):
                for j in range(k+1,n):work[i][j]-=work[i][k]*work[k][j]/pivot
    return matrix

def evaluate(assets,covariance,weights):
    matrix=validate_model(assets,covariance)
    if not isinstance(weights,dict) or set(weights)!={a['id'] for a in assets}:raise ValueError('weights must exactly cover asset universe')
    w=[D(weights[a['id']]) for a in assets]
    if any(x<0 or x>1 for x in w) or sum(w)!=1:raise ValueError('long-only fractional weights must sum exactly to1')
    expected=sum((v*D(a['expected_return']) for v,a in zip(w,assets)),Decimal(0))
    variance=sum((w[i]*w[j]*matrix[i][j] for i in range(len(w)) for j in range(len(w))),Decimal(0))
    if variance<0:raise ValueError('negative portfolio variance')
    with localcontext(Context(prec=100)):vol=format(variance.sqrt().quantize(Decimal('1e-12')),'f')
    groups={group:str(sum((v for v,a in zip(w,assets) if a['group']==group),Decimal(0))) for group in sorted({a['group'] for a in assets})}
    return {'expected_return':str(expected),'variance':str(variance),'annualized_volatility':vol,'group_weights':groups}

from foundation_contract import exact
from native_integrity import canonical_hash

@exact
def review_candidates(d):
    issues=[];rows=[];assets=d['assets'];constraints=d['constraints'];seen=set()
    for candidate in d['candidates']:
        if candidate['id'] in seen:raise ValueError('duplicate candidate id')
        seen.add(candidate['id']);analysis=evaluate(assets,d['covariance'],candidate['weights']);findings=[]
        for group,bounds in constraints.get('group_ranges',{}).items():
            lo=D(bounds['min']);hi=D(bounds['max']);weight=D(analysis['group_weights'].get(group,'0'))
            if not 0<=lo<=hi<=1:raise ValueError('invalid group bounds')
            if not lo<=weight<=hi:findings.append('group range: '+group)
        maximum=D(constraints.get('max_position','1'))
        if not 0<maximum<=1:raise ValueError('max_position outside(0,1]')
        for key,w in candidate['weights'].items():
            if D(w)>maximum:findings.append('position limit: '+key)
        if 'minimum_expected_return' in constraints and D(analysis['expected_return'])<D(constraints['minimum_expected_return']):findings.append('expected return below supplied objective')
        if 'maximum_volatility' in constraints:
            maximum_volatility=D(constraints['maximum_volatility'])
            if maximum_volatility<0:raise ValueError('maximum_volatility must be nonnegative')
            if Decimal(analysis['variance'])>maximum_volatility*maximum_volatility:findings.append('volatility exceeds supplied limit')
        horizon=D(constraints.get('liquidity_horizon_days','7'));limit=D(constraints.get('max_illiquid_weight','1'))
        if horizon<0 or not 0<=limit<=1:raise ValueError('invalid liquidity constraints')
        illiquid=sum((D(candidate['weights'][a['id']]) for a in assets if D(a['liquidity_days'])>horizon),Decimal(0))
        if illiquid>limit:findings.append('illiquid allocation limit')
        scenarios=[]
        for scenario in d.get('scenarios',[]):
            if set(scenario['asset_returns'])!={a['id'] for a in assets}:raise ValueError('scenario must cover exact asset universe')
            shock=sum((D(candidate['weights'][a['id']])*D(scenario['asset_returns'][a['id']]) for a in assets),Decimal(0))
            scenarios.append({'id':scenario['id'],'portfolio_return':str(shock)})
        rows.append({'id':candidate['id'],**analysis,'illiquid_weight':str(illiquid),'constraint_findings':findings,'scenarios':scenarios,'feasible_under_supplied_constraints':not findings})
        issues.extend(candidate['id']+': '+x for x in findings)
    if not rows:raise ValueError('candidate portfolios required')
    engine_state='not-requested'
    if d.get('optimization_requested'):
        engine=d.get('engine_result')
        expected=canonical_hash({k:d[k] for k in ['assets','covariance','constraints']})
        if not engine:engine_state='unavailable';issues.append('optimization requires separately approved engine; local review does not optimize')
        else:
            for key in ['engine_id','engine_version','method_id','method_version','acceptance_ref']:
                if not isinstance(engine.get(key),str) or not engine[key]:raise ValueError('engine metadata missing: '+key)
            if engine.get('input_hash')!=expected:raise ValueError('engine result does not bind current model inputs')
            if engine.get('candidate_id') not in seen:raise ValueError('engine candidate absent from independently checked alternatives')
            engine_state='supplied-result-feasibility-checked';issues.append('engine approval and optimality remain supplied assertions requiring independent institutional acceptance')
    return {'candidates':rows,'selection':None,'engine_state':engine_state,'covariance_convention':'annualized return fractions squared; supplied order matches assets'},issues
