"""Reviewed subscription/NAV facility arithmetic, not a lender borrowing certificate."""
from foundation_contract import D, exact, ratio, finish, text, date_value, require_sources, validate_common
from specialist_contract import validate_specialist_common as validate_common

SKILL='private-fund-financing-reviewer'

def fields(doc,row,*names):
    if not isinstance(row,dict) or any(not text(row.get(k)) for k in names): raise ValueError('required fields: '+', '.join(names))
    require_sources(doc,[row.get('source_ref')])

def number(row,key,low=0,high=None):
    n=D(row.get(key))
    if n<D(low) or high is not None and n>D(high): raise ValueError(key+' outside supported range')
    return n

@exact
def compute(doc):
    errors=validate_common(doc)
    if errors: raise ValueError('; '.join(errors))
    mode=doc.get('mode')
    if mode not in {'subscription','nav'}: raise ValueError('mode must be subscription or nav; hybrid facilities require an approved engine')
    agreement=doc.get('agreement'); fields(doc,agreement,'version','reviewed_by','effective_from','expires','concentration_method','currency','proceeds_assumption')
    if agreement['currency']!=doc['currency']: raise ValueError('agreement currency differs from request')
    if not date_value(agreement['effective_from'])<=date_value(doc['as_of'])<=date_value(agreement['expires']): raise ValueError('reviewed agreement is not effective at review date')
    if agreement['concentration_method']!='fixed-pre-cap-credit-base': raise ValueError('unsupported agreement concentration method')
    if agreement.get('facility_type')!=mode: raise ValueError('agreement facility type differs from mode')
    allowed=agreement.get('permitted_proceeds')
    if not isinstance(allowed,list) or not allowed or any(not text(x) for x in allowed): raise ValueError('explicit permitted_proceeds list required')
    terms=doc.get('facility'); fields(doc,terms,'id','agreement_version','maturity_date','proposed_draw_date','proceeds_use','cost_assumption')
    if terms['agreement_version']!=agreement['version']: raise ValueError('facility agreement version mismatch')
    issues=[]
    if terms['proceeds_use'] not in allowed: issues.append('proposed proceeds use is outside supplied reviewed agreement')
    if date_value(terms['proposed_draw_date'])<date_value(doc['as_of']) or date_value(terms['proposed_draw_date'])>date_value(terms['maturity_date']): issues.append('proposed draw date is historical or after facility maturity')
    if not date_value(agreement['effective_from'])<=date_value(terms['proposed_draw_date'])<=date_value(agreement['expires']):
        issues.append('proposed draw date is outside supplied reviewed agreement effective period')
    assets=doc.get('collateral');limits=doc.get('concentration_limits')
    if not isinstance(assets,list) or not assets or len(assets)>10000 or not isinstance(limits,list) or not limits: raise ValueError('bounded collateral and concentration inventories required')
    if doc.get('inventory_complete') is not True: issues.append('collateral inventory completeness is unestablished')
    require_sources(doc,[doc.get('inventory_source_ref')])
    base_field='uncalled_commitment' if mode=='subscription' else 'nav'
    forbidden='nav' if mode=='subscription' else 'uncalled_commitment'
    identities=set();credits={};raw=D(0);details=[]
    for row in assets:
        fields(doc,row,'id','agreement_version','concentration_group','eligibility_reason','currency')
        if row['id'] in identities: raise ValueError('duplicate collateral identity')
        identities.add(row['id'])
        if row['agreement_version']!=agreement['version'] or row['currency']!=doc['currency']: raise ValueError('collateral agreement version or currency mismatch')
        if forbidden in row: raise ValueError('subscription commitments and NAV collateral cannot be mixed')
        if type(row.get('eligible')) is not bool: raise ValueError('collateral eligibility must be an explicit boolean')
        amount=number(row,base_field);haircut=number(row,'haircut',0,1);advance=number(row,'advance_rate',0,1);raw+=amount
        credit=amount*(D(1)-haircut)*advance if row['eligible'] else D(0)
        credits[row['concentration_group']]=credits.get(row['concentration_group'],D(0))+credit
        details.append({'id':row['id'],'eligible':row['eligible'],'gross_collateral':str(amount),'pre_cap_credit':str(credit),'concentration_group':row['concentration_group']})
    expected_total=number(terms,'total_uncalled_commitments' if mode=='subscription' else 'fund_nav')
    if raw!=expected_total: issues.append('collateral values do not reconcile to supplied complete collateral total')
    total_credit=sum(credits.values(),D(0));caps={};group_results=[]
    for limit in limits:
        fields(doc,limit,'group','agreement_version')
        if limit['group'] in caps or limit['agreement_version']!=agreement['version']: raise ValueError('duplicate group or concentration agreement mismatch')
        caps[limit['group']]=number(limit,'maximum_fraction',0,1)
    if set(caps)!=set(credits): raise ValueError('every collateral group requires exactly one supplied concentration limit')
    borrowing_base=D(0)
    for group,credit in credits.items():
        cap=total_credit*caps[group];included=min(credit,cap);borrowing_base+=included
        group_results.append({'group':group,'pre_cap_credit':str(credit),'cap_amount':str(cap),'included_credit':str(included),'concentration_deduction':str(credit-included)})
    limit=number(terms,'commitment_limit');outstanding=number(terms,'outstanding');draw=number(terms,'proposed_draw');lc=number(terms,'letters_of_credit');reserve=number(terms,'reserves')
    proforma=outstanding+draw;used=proforma+lc+reserve;availability=min(limit,borrowing_base)-used
    nav=number(terms,'fund_nav');other=number(terms,'other_fund_debt');max_lev=number(agreement,'maximum_fund_debt_to_nav',0,10)
    if nav<=0: raise ValueError('positive independently supplied fund NAV required for leverage review')
    total_debt=proforma+other;leverage_headroom=nav*max_lev-total_debt
    covenant_limit=number(agreement,'maximum_facility_debt');covenant_headroom=covenant_limit-proforma
    if availability<0: issues.append('pro forma usage exceeds borrowing base or commitment')
    if leverage_headroom<0: issues.append('pro forma fund debt exceeds supplied leverage covenant')
    if covenant_headroom<0: issues.append('pro forma facility debt exceeds supplied covenant')
    days=number(terms,'accrual_days',0,3660);basis=number(terms,'day_basis')
    if days!=days.to_integral_value() or basis not in {D(360),D(365)}: raise ValueError('integer accrual_days and 360/365 day_basis required')
    interest=number(terms,'interest_rate',0,1);undrawn_rate=number(terms,'undrawn_fee_rate',0,1);upfront=number(terms,'upfront_fee')
    undrawn=max(D(0),limit-proforma-lc)
    interest_cost=ratio(proforma*interest*days,basis);undrawn_cost=ratio(undrawn*undrawn_rate*days,basis)
    result={'mode':mode,'collateral':details,'concentration':group_results,'pre_cap_credit':str(total_credit),'borrowing_base':str(borrowing_base),
            'pro_forma_drawn':str(proforma),'pro_forma_usage_including_lc_reserves':str(used),'draw_headroom':str(availability),
            'commitment_headroom':str(limit-used),'borrowing_base_headroom':str(borrowing_base-used),'fund_debt':str(total_debt),
            'fund_debt_to_nav':ratio(total_debt,nav),'leverage_headroom':str(leverage_headroom),'facility_covenant_headroom':str(covenant_headroom),
            'interest_cost':interest_cost,'undrawn_fee_cost':undrawn_cost,'upfront_fee':str(upfront),'total_period_cost':str(D(interest_cost)+D(undrawn_cost)+upfront),
            'agreement_version':agreement['version'],'proceeds_use':terms['proceeds_use'],'borrowing_authorized':False,'lender_certificate':False}
    if doc.get('inventory_complete') is not True or raw!=expected_total:
        for key in ('borrowing_base','draw_headroom','borrowing_base_headroom'): result[key]=None
    return finish(doc,SKILL,'reviewed-facility-credit-base-v1',result,issues,
                  ['Concentration caps use the fixed total eligible haircut-and-advance credit before caps; no circular borrowing-base or hybrid facility method.',
                   'Simple constant-balance period interest and undrawn fees, rounded independently to12 decimals; no compounding, PIK, FX, waterfall or covenant legal interpretation.',
                   'Terms, collateral eligibility, NAV, completeness and review identity are supplied evidence, not authenticated approvals.'],
                  ['private-capital-commitment-planner','private-fund-performance-analyzer'])

def validate(doc):
    try: compute(doc); return []
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError,AttributeError) as exc: return [str(exc)]
