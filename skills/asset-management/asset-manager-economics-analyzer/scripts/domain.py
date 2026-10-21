"""AUM rollforward, fee economics and capacity scenarios on supplied product books."""
from foundation_contract import D, exact, ratio, date_value
from business_evidence import start, items, num, text, support, F, complete, guard, observed
SKILL='asset-manager-economics-analyzer'

@exact
def compute(doc):
    if isinstance(doc, dict) and 'mode' in doc: raise ValueError('this calculator has no selectable mode')
    start(doc, {'products','scenarios'})
    issues=[]; products=items(doc,'products',issues); scenarios=items(doc,'scenarios',issues)
    if not products: issues.append('product economics evidence unavailable')
    results=[]; total_aum=D(0); total_revenue=D(0); total_profit=D(0)
    by_id={}
    for p in products:
        if date_value(p.get('period_start'))>date_value(p.get('period_end')) or not observed(doc,p,'period_end'): raise ValueError('product AUM period invalid')
        opening=num(p,'opening_aum',0); subs=num(p,'subscriptions',0); reds=num(p,'redemptions',0)
        close=num(p,'closing_aum',0); average=num(p,'average_fee_aum',0)
        expected=opening+subs-reds+num(p,'performance_change')+num(p,'fx_change')+num(p,'other_change')
        difference=close-expected; tolerance=num(p,'tolerance',0)
        revenue=average*num(p,'fee_bps',0,10000)/D(10000)+num(p,'other_revenue',0)
        costs=average*num(p,'variable_cost_bps',0,10000)/D(10000)+num(p,'fixed_cost',0)+num(p,'allocated_overhead',0)
        capacity=num(p,'capacity_aum',0); profit=revenue-costs
        row={'id':text(p,'id'),'aum_reconciled':abs(difference)<=tolerance,'expected_closing_aum':F(expected),'aum_difference':F(difference),
             'net_flows':F(subs-reds),'annualized_fee_revenue':F(revenue),'annualized_costs':F(costs),'annualized_profit':F(profit),
             'profit_margin':ratio(profit,revenue),'capacity_headroom':F(capacity-close),'evidence':support(p)}
        if abs(difference)>tolerance: issues.append('AUM rollforward does not reconcile for supplied product')
        if close>capacity: issues.append('supplied capacity exceeded')
        by_id[p['id']]=(p,row);results.append(row);total_aum+=close;total_revenue+=revenue;total_profit+=profit
    all_visible=len(products)==len(doc['products']) and all(r['aum_reconciled'] for r in results)
    for row in results:
        p=by_id[row['id']][0]
        row['aum_mix']=ratio(num(p,'closing_aum'),total_aum) if all_visible else None
        row['revenue_mix']=ratio(num(p,'average_fee_aum')*num(p,'fee_bps')/D(10000)+num(p,'other_revenue'),total_revenue) if all_visible else None
    stress=[]
    for s in scenarios:
        target=by_id.get(text(s,'product_id'))
        if not target: issues.append('scenario product evidence unavailable');continue
        p,base=target
        if not base['aum_reconciled']: issues.append('scenario omitted because opening product book is unreconciled');continue
        redemption=num(s,'redemption_fraction',0,1);market=num(s,'market_return',-1)
        aum=num(p,'closing_aum')*(D(1)-redemption)*(D(1)+market)+num(s,'new_sales',0)
        fee=max(D(0),num(p,'fee_bps')+num(s,'fee_change_bps'))
        rev=aum*fee/D(10000)+num(p,'other_revenue');cost=aum*num(p,'variable_cost_bps')/D(10000)+num(p,'fixed_cost')+num(p,'allocated_overhead')+num(s,'incremental_cost',0)
        stress.append({'id':s['id'],'product_id':s['product_id'],'scenario_aum':F(aum),'annualized_revenue':F(rev),'annualized_profit':F(rev-cost),'capacity_headroom':F(num(p,'capacity_aum')-aum),'evidence':support(s)})
    totals={'closing_aum':F(total_aum),'annualized_revenue':F(total_revenue),'annualized_profit':F(total_profit)} if all_visible and products else None
    return complete(doc,SKILL,'aum-flow-fx-fee-bridge',{'products':results,'totals':totals,'scenarios':stress},issues,
                    ['Amounts share the stated currency and units; fees use supplied average billable AUM, not closing AUM.','Scenario ordering: redemptions, market return, then new sales. No forecast or valuation of the management company.'])

def validate(doc): return guard(compute,doc)
