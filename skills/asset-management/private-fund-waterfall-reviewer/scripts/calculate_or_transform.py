#!/usr/bin/env python3
"""Contract-supplied whole-fund no-catchup analytical distribution tiers."""
from foundation_contract import D, exact, finish, source_issues, validate_common, cli_compute, validate_referenced_sources

@exact
def compute(doc):
    errors=validate_common(doc)
    if not errors:
        referenced_issues=validate_referenced_sources(doc)
        if 'source withheld for audience restriction' in referenced_issues:
            raise ValueError('request withheld for audience restriction')
        errors.extend(x for x in referenced_issues if "observation source as-of exceeds review date" in x)
    if errors:raise ValueError('; '.join(errors))
    terms=doc['terms'];state=doc['distribution_state'];issues=source_issues(doc,terms.get('source_ref'))+source_issues(doc,state.get('source_ref'))
    unsupported=[]
    required={'waterfall_style':'european_whole_fund','catch_up':False,'preferred_method':'supplied_accrued_entitlement','gp_capital_participation':False,'interim_clawback':False,'terms_reviewed':True}
    for key,expected in required.items():
        if terms.get(key)!=expected or (isinstance(expected,bool) and not isinstance(terms.get(key),bool)):unsupported.append(key)
    if not terms.get('contract_id'):issues.append('contract identity unknown')
    for key in ('distributable_cash','unreturned_lp_capital','accrued_preferred_return'):
        if state.get(key) is None:issues.append(key+' unknown')
    if terms.get('carry_fraction') is None:issues.append('carry fraction unknown')
    if unsupported:issues.append('unsupported_engine_features: '+', '.join(unsupported))
    result={'method_supported':not unsupported,'contract_id':terms.get('contract_id'),'tiers':None,'lp_total':None,'gp_total':None,'residual':None,'certifies_contract_compliance':False}
    if not issues:
        cash=D(state['distributable_cash']);capital=D(state['unreturned_lp_capital']);pref=D(state['accrued_preferred_return']);carry=D(terms['carry_fraction'])
        if min(cash,capital,pref)<0 or not 0<=carry<=1:raise ValueError('nonnegative balances and carry in [0,1] required')
        roc=min(cash,capital);remaining=cash-roc;paid_pref=min(remaining,pref);remaining-=paid_pref;gp=remaining*carry;lp_residual=remaining-gp;lp=roc+paid_pref+lp_residual
        result.update(tiers=[{'tier':'return_unreturned_lp_capital','lp':str(roc),'gp':'0'},{'tier':'pay_supplied_preferred_entitlement','lp':str(paid_pref),'gp':'0'},{'tier':'split_residual','lp':str(lp_residual),'gp':str(gp)}],lp_total=str(lp),gp_total=str(gp),residual=str(cash-lp-gp),unreturned_capital_after=str(capital-roc),unpaid_preferred_after=str(pref-paid_pref),source_refs=[terms['source_ref'],state['source_ref']])
    return finish(doc,'private-fund-waterfall-reviewer','european-no-catchup-supplied-preferred/1',result,issues,limitations=['Explicit contract-specific subset: aggregate LP pool; no American/deal-by-deal waterfall, catch-up, GP invested capital, interim clawback, recycling, tax allocation or preferred-return accrual/IRR calculation.','Amounts are unrounded analytical entitlements; legal interpretation, independent benchmark and settlement rounding require professional review. No payment instruction is produced.'])

if __name__=='__main__':cli_compute(compute)
