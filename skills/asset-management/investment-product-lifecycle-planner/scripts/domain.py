"""Launch, merge and close gates with transparent product unit economics."""
from foundation_contract import D, exact, ratio
from business_evidence import start,bound,items,num,text,values,flag,support,F,complete,guard,current
SKILL='investment-product-lifecycle-planner'

@exact
def compute(doc):
    if isinstance(doc, dict) and 'mode' in doc: raise ValueError('this calculator has no selectable mode')
    start(doc,{'action','product','policy','gates'})
    if doc.get('action') not in {'launch','merge','close'}: raise ValueError('action must be launch, merge or close')
    issues=[];product=bound(doc,doc.get('product'),issues,'product');policy=bound(doc,doc.get('policy'),issues,'policy',True);gates=items(doc,'gates',issues,True)
    decision=[];economics=None;action=doc['action']
    if policy and current(policy,doc,issues,'policy'):
        required=values(policy,action+'_required_gates');index={g['id']:g for g in gates}
        if not required: issues.append('lifecycle policy requires explicit decision gates')
        for key in required:
            g=index.get(key);state='unknown' if g is None else g.get('status')
            if state not in {'passed','failed','unknown'}: raise ValueError('unsupported gate status')
            row={'gate':key,'status':state,'owner':text(g,'owner') if g else None}
            if g:row['evidence']=support(g)
            decision.append(row)
            if state!='passed':issues.append('required lifecycle gate is not passed')
    else:issues.append('current lifecycle decision policy unavailable')
    if product:
        aum=num(product,'forecast_aum',0);net_bps=num(product,'fee_bps',0,10000)-num(product,'variable_cost_bps',0,10000)
        fixed=num(product,'annual_fixed_cost',0);oneoff=num(product,'one_off_cost',0)
        annual=aum*net_bps/D(10000)-fixed
        economics={'annual_contribution':F(annual),'first_year_contribution':F(annual-oneoff),'break_even_aum':ratio(fixed*D(10000),net_bps) if net_bps>0 else None,'evidence':support(product)}
        if net_bps<=0:issues.append('fee margin cannot cover fixed costs')
        if action=='merge':
            savings=num(product,'annual_synergy_savings',0);retention=num(product,'retention_fraction',0,1)
            economics.update(retained_aum=F(aum*retention),payback_years=ratio(oneoff,savings) if savings>0 else None)
            if savings<=0:issues.append('merger payback unavailable without positive supplied savings')
        if action=='close':
            proceeds=num(product,'liquidation_proceeds',0);liabilities=num(product,'liabilities',0);reserve=num(product,'closure_reserve',0)
            economics['modeled_residual']=F(proceeds-liabilities-reserve-oneoff)
            if proceeds<liabilities+reserve+oneoff:issues.append('modeled closure resources insufficient')
    return complete(doc,SKILL,'lifecycle-gates-unit-economics',{'action':action,'gates':decision,'economics':economics,'review_readiness':'blocked' if issues else 'eligible-for-human-review','decision':'not-made'},issues,
                    ['Policy gates are supplied firm decisions, not a legal authorization or complete jurisdictional checklist.','AUM, retention and savings are scenarios; no launch, merger, closure or investor notice occurs.'])

def validate(doc):return guard(compute,doc)
