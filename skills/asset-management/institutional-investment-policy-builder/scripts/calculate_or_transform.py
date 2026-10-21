"""Bounded supplied-input review. No source authentication or business action."""
from decimal import Decimal
from foundation_contract import (D,ratio,date_value,exact,validate_common,validate_referenced_sources,require_sources,finish,cli_compute)
from native_integrity import canonical_hash

@exact
def analyze(d):
    require_sources(d,[d['objectives'].get('source_ref'),d.get('benchmark',{}).get('source_ref')]+[x.get('source_ref') for x in d['constraints']['dated_outflows']])
    issues=[];objectives=d['objectives'];constraints=d['constraints'];governance=d['governance']
    if d['institution_type'] not in {'pension','endowment','foundation','sovereign','insurer','corporate','ocio'}:raise ValueError('supported institutional type required; households use wealth planning')
    required=['return_objective','risk_tolerance','horizon_years','tax_status','legal_constraints','spending_policy']
    for key in required:
        if objectives.get(key) in (None,'',[]):issues.append('objective missing: '+key)
    if objectives.get('horizon_years') is not None and D(objectives['horizon_years'])<=0:raise ValueError('positive horizon required')
    ranges=constraints['allocation_ranges'];seen=set();minimum=maximum=Decimal(0)
    for row in ranges:
        if row['asset_class'] in seen:raise ValueError('duplicate allocation class')
        seen.add(row['asset_class']);lo=D(row['minimum']);hi=D(row['maximum'])
        if not 0<=lo<=hi<=1:raise ValueError('allocation ranges require0<=min<=max<=1')
        minimum+=lo;maximum+=hi
    if not ranges or minimum>1 or maximum<1:issues.append('allocation ranges cannot fund a100-percent portfolio')
    liquidity=D(constraints['liquidity_reserve']);liabilities=sum((D(r['amount']) for r in constraints['dated_outflows']),Decimal(0))
    if liquidity<0 or any(D(r['amount'])<0 for r in constraints['dated_outflows']):raise ValueError('nonnegative reserve and dated outflows required')
    for r in constraints['dated_outflows']:
        if date_value(r['date'])<date_value(d['as_of']):raise ValueError('policy forward outflow is before review date')
    if liquidity<liabilities:issues.append('stated reserve is below supplied dated outflows; liquidity review required')
    for role in ['investment_owner','risk_owner','review_owner','approval_owner']:
        if not governance.get(role):issues.append('governance owner missing: '+role)
    if not d.get('benchmark',{}).get('version'):issues.append('versioned benchmark missing')
    sections={'institution_type':d['institution_type'],'objectives':objectives,'constraints':constraints,'governance':governance,'benchmark':d.get('benchmark')}
    return {'policy_sections':sections,'range_minimum_sum':str(minimum),'range_maximum_sum':str(maximum),'dated_outflows':str(liabilities),'reserve_gap':str(liquidity-liabilities),'approval_state':'not-approved'},issues

SKILL='institutional-investment-policy-builder'
METHOD='institutional-policy-consistency'
LIMITS=['No optimization, suitability determination or policy adoption.', 'Liquidity outflows are supplied; uncertain liabilities require separate modeling.']
HANDOFFS=['asset-allocation-planner', 'investment-mandate-reviewer']

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
