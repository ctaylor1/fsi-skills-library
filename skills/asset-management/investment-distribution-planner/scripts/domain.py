"""Literal distribution-policy matching with fee, eligibility and conflict gates."""
from foundation_contract import D,exact
from business_evidence import start,items,num,text,flag,current,support,F,complete,guard
SKILL='investment-distribution-planner'

@exact
def compute(doc):
    if isinstance(doc, dict) and 'mode' in doc: raise ValueError('this calculator has no selectable mode')
    start(doc,{'opportunities','policies'})
    issues=[];opportunities=items(doc,'opportunities',issues);policies=items(doc,'policies',issues,True);rows=[]
    policies=[p for p in policies if current(p,doc,issues,'distribution policy')]
    for o in opportunities:
        keys=('jurisdiction','channel','investor_type','product_type')
        for key in keys:text(o,key)
        matches=[p for p in policies if all(p.get(k)==o[k] for k in keys)]
        row={'id':o['id'],'eligibility':'unknown','controls':[],'evidence':support(o)}
        if len(matches)!=1:issues.append('no unique current distribution policy');rows.append(row);continue
        p=matches[0];checks={}
        checks['policy_allows']=flag(p,'allowed')
        checks['minimum_subscription']=num(o,'subscription',0)>=num(p,'minimum_subscription',0)
        checks['investor_evidence']=flag(o,'eligibility_confirmed')
        checks['fee_cap']=num(o,'fee_bps',0,10000)<=num(p,'maximum_fee_bps',0,10000)
        checks['rebate_cap']=num(o,'rebate_bps',0,10000)<=num(p,'maximum_rebate_bps',0,10000)
        checks['net_fee_nonnegative']=num(o,'fee_bps')>=num(o,'rebate_bps')
        checks['conflict_disclosure']=not flag(o,'has_conflict') or flag(o,'conflict_disclosed')
        checks['agreement']=flag(o,'distribution_agreement_current')
        row.update(eligibility='meets-supplied-policy' if all(checks.values()) else 'blocked',controls=checks,
                   annual_net_fee=F(num(o,'subscription')*(num(o,'fee_bps')-num(o,'rebate_bps'))/D(10000)),policy_id=p['id'],policy_evidence=support(p))
        if not all(checks.values()):issues.append('distribution opportunity has unresolved eligibility, commercial or conflict gate')
        rows.append(row)
    if not rows:issues.append('no assessable distribution opportunities')
    return complete(doc,SKILL,'distribution-scope-commercial-gates',{'opportunities':rows,'outreach_authorized':False},issues,
                    ['Jurisdiction/channel/investor/product matching is exact; no cross-border legal eligibility is inferred.','Policy and investor confirmations are supplied assertions requiring human verification; no prospect contact or offer occurs.'])

def validate(doc):return guard(compute,doc)
