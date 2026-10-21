#!/usr/bin/env python3
"""Principal transaction sources/uses, simple primary ownership and scenario evidence."""
from foundation_contract import D, ratio, exact, finish, source_issues, validate_common, cli_compute, validate_referenced_sources

@exact
def compute(doc):
    errors=validate_common(doc)
    if not errors:
        referenced_issues=validate_referenced_sources(doc)
        if 'source withheld for audience restriction' in referenced_issues:
            raise ValueError('request withheld for audience restriction')
        errors.extend(x for x in referenced_issues if "observation source as-of exceeds review date" in x)
    if errors:raise ValueError('; '.join(errors))
    issues=[];tx=doc['transaction'];tg=source_issues(doc,tx.get('source_ref'));totals={};ids=set();trace=[]
    for side in ('funding_sources','uses'):
        amount=D('0');gaps=[]
        if not tx[side]:gaps.append(side+' not supplied')
        for row in tx[side]:
            if row['line_id'] in ids:raise ValueError('duplicate sources/uses line_id')
            ids.add(row['line_id']);rg=source_issues(doc,row.get('source_ref'))
            if row.get('currency')!=doc['currency']:rg.append('currency mismatch')
            if row.get('amount') is None:rg.append('amount unknown')
            if rg:gaps.extend(row['line_id']+': '+g for g in rg);continue
            n=D(row['amount'])
            if n<0:raise ValueError('sources/uses amounts must be nonnegative')
            amount+=n;trace.append({'line_id':row['line_id'],'side':side,'amount':str(n),'source_ref':row['source_ref']})
        issues.extend(gaps);totals[side]=None if gaps or tg else amount
    residual=None if any(v is None for v in totals.values()) else totals['funding_sources']-totals['uses']
    if residual is not None and residual!=0:issues.append('transaction sources and uses do not balance')
    ownership=None;ownership_note='simple new-money common-equity model only'
    if tx.get('security_type')!='common_equity' or tx.get('secondary_purchase') is not False:issues.append('ownership engine gap: only primary common-equity issuance supported')
    elif not tg and all(tx.get(k) is not None for k in ('pre_money_equity_value','new_primary_equity','investor_primary_amount')):
        pre=D(tx['pre_money_equity_value']);new=D(tx['new_primary_equity']);investor=D(tx['investor_primary_amount'])
        if pre<0 or new<0 or investor<0 or investor>new:raise ValueError('invalid primary equity capitalization')
        ownership=ratio(investor,pre+new)
        if ownership is None:issues.append('post-money equity value is zero; ownership unknown')
    else:issues.append('capitalization fields or source unknown')
    required=set(doc['required_diligence_topics']);covered=set();coverage=[]
    if not required:raise ValueError('explicit required diligence topics required')
    for item in doc['diligence_evidence']:
        g=source_issues(doc,item.get('source_ref'))
        if item.get('status') not in {'supported','open','contradicted'}:raise ValueError('unsupported diligence evidence status')
        if not g and item['status']=='supported':covered.add(item['topic'])
        else:issues.extend(g or ['diligence '+item['topic']+': '+item['status']])
        coverage.append({'topic':item['topic'],'supplied_status':item['status'],'eligible':not g,'source_ref':item.get('source_ref') if not g else None})
    issues.extend('diligence evidence gap: '+x for x in sorted(required-covered))
    scenarios=[];seen=set()
    for s in doc['scenarios']:
        if s['scenario_id'] in seen:raise ValueError('duplicate scenario_id')
        seen.add(s['scenario_id']);g=source_issues(doc,s.get('source_ref'));metrics=None
        fields=('debt','cash','ebitda','cash_interest')
        if any(s.get(k) is None for k in fields):g.append('scenario financial assumption unknown')
        if not g:
            a={k:D(s[k]) for k in fields}
            if min(a['debt'],a['cash'],a['cash_interest'])<0:raise ValueError('debt, cash and interest must be nonnegative')
            metrics={'net_debt':str(a['debt']-a['cash']),'net_debt_to_ebitda':ratio(a['debt']-a['cash'],a['ebitda']) if a['ebitda']>0 else None,'ebitda_to_cash_interest':ratio(a['ebitda'],a['cash_interest']) if a['cash_interest']>0 else None,'ratio_rounding_places':12}
            if a['ebitda']<=0 or a['cash_interest']<=0:g.append('nonpositive denominator prevents at least one ratio')
        issues.extend(s['scenario_id']+': '+x for x in g);scenarios.append({'scenario_id':s['scenario_id'],'metrics':metrics,'source_ref':s.get('source_ref') if metrics else None,'assumption_not_forecast':True})
    issues.extend(tg)
    return finish(doc,'private-investment-due-diligence-reviewer','principal-transaction-evidence-review/1',{'sources_uses':{'totals':{k:None if v is None else str(v) for k,v in totals.items()},'funding_minus_uses':None if residual is None else str(residual),'eligible_lines':trace},'primary_post_money_ownership_fraction':ownership,'ownership_scope':ownership_note,'diligence_coverage':coverage,'scenarios':scenarios},issues,limitations=['No legal, tax, quality-of-earnings, valuation or investment approval opinion. Supplied diligence statuses are declarations requiring specialist review.','Ownership excludes preferences, options, convertibles and secondary transfers. Ratios are rounded to12 decimal places and use supplied scenario definitions.'])

if __name__=='__main__':cli_compute(compute)
