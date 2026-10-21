"""Public-security, manager and allocation committee review methods; no decision."""
from foundation_contract import D,exact,ratio,date_value
from business_evidence import start,bound,items,num,text,flag,values,current,support,F,complete,guard,statement
SKILL='investment-committee-memo-builder'

@exact
def compute(doc):
    mode=doc.get('mode')
    fields={'public-security':{'proposal','scenarios'},'manager':{'proposal','manager_evidence'},'allocation':{'allocations'}}
    start(doc,{'policy','thesis'}|fields.get(mode,set()))
    if mode not in {'public-security','manager','allocation'}:raise ValueError('unsupported new IC mode')
    issues=[];proposal=bound(doc,doc.get('proposal'),issues,'proposal') if mode!='allocation' else None;policy=bound(doc,doc.get('policy'),issues,'mandate policy',True)
    thesis=items(doc,'thesis',issues,True);notes=[];analysis={};policy_ok=bool(policy and current(policy,doc,issues,'mandate policy'))
    if not policy_ok:issues.append('current mandate policy unavailable')
    for point in thesis:
        if not current(point,doc,issues,'thesis content'):continue
        claim=statement(point,issues,'thesis content')
        if claim is not None:notes.append({'id':point['id'],'text':claim,'evidence':support(point)})
    if not notes:issues.append('approved thesis evidence unavailable')
    if mode=='public-security' and proposal:
        price=num(proposal,'current_price',0)
        if price==0:raise ValueError('current security price must be positive')
        scenarios=items(doc,'scenarios',issues);names={s.get('case') for s in scenarios}
        if names!={'base','downside','upside'} or len(scenarios)!=3:issues.append('three unique downside/base/upside scenarios required')
        rows=[];weighted_price=D(0);weighted_income=D(0);probability=D(0)
        for s in scenarios:
            prob=num(s,'probability',0,1);target=num(s,'target_price',0);income=num(s,'income',0)
            rows.append({'case':text(s,'case'),'total_return':ratio(target+income-price,price),'probability':F(prob),'evidence':support(s)})
            weighted_price+=target*prob;weighted_income+=income*prob;probability+=prob
        if probability!=1:issues.append('scenario probabilities must sum to one')
        returns={s.get('case'):num(s,'target_price')+num(s,'income') for s in scenarios}
        if names=={'base','downside','upside'} and not returns['downside']<=returns['base']<=returns['upside']:issues.append('scenario downside/base/upside ordering inconsistent')
        proposed=num(proposal,'proposed_weight',0,1);existing=num(proposal,'current_weight',0,1)
        analysis={'security_id':text(proposal,'security_id'),'scenarios':rows,'expected_total_return':ratio(weighted_price+weighted_income-price,price) if probability==1 and len(rows)==3 and names=={'base','downside','upside'} and returns['downside']<=returns['base']<=returns['upside'] else None,'proposed_weight':F(proposed),'evidence':support(proposal)}
        if policy_ok:
            sector_after=num(proposal,'current_sector_weight',0,1)-existing+proposed
            if proposed>num(policy,'single_name_limit',0,1) or sector_after>num(policy,'sector_limit',0,1):issues.append('proposed security allocation breaches hard mandate limit')
            if text(proposal,'security_type') not in values(policy,'allowed_security_types'):issues.append('security type outside mandate')
            analysis['sector_weight_after']=F(sector_after);analysis['policy_evidence']=support(policy)
    elif mode=='manager' and proposal:
        evidence=bound(doc,doc.get('manager_evidence'),issues,'manager diligence')
        capital=num(proposal,'proposed_commitment',0);nav=num(proposal,'portfolio_nav',0)
        if nav==0:raise ValueError('portfolio_nav must be positive')
        analysis={'manager_id':text(proposal,'manager_id'),'proposed_commitment':F(capital),'allocation_fraction':ratio(capital,nav),'evidence':support(proposal)}
        if not evidence or evidence.get('manager_id')!=proposal['manager_id'] or evidence.get('status')!='meets-supplied-review-policy' or num(evidence,'material_issues',0)!=0 or date_value(evidence.get('review_by'))<date_value(doc['as_of']):
            issues.append('manager diligence missing, unresolved, stale or wrong manager')
        else:analysis['diligence_evidence']=support(evidence)
        if policy_ok:
            if capital>nav*num(policy,'manager_limit',0,1):issues.append('proposed manager commitment breaches mandate limit')
            analysis['policy_evidence']=support(policy)
    elif mode=='allocation':
        allocations=items(doc,'allocations',issues);proposed_total=D(0);current_total=D(0);expected=D(0);turnover=D(0);liquid=D(0);rows=[]
        for a in allocations:
            weight=num(a,'proposed_weight',0,1);old=num(a,'current_weight',0,1);lower=num(a,'minimum_weight',0,1);upper=num(a,'maximum_weight',0,1)
            if lower>upper or not lower<=weight<=upper:issues.append('allocation violates supplied hard asset-class bounds')
            contribution=weight*num(a,'expected_return',-1);expected+=contribution;turnover+=abs(weight-old);proposed_total+=weight;current_total+=old
            if flag(a,'liquid'):liquid+=weight
            rows.append({'id':a['id'],'proposed_weight':F(weight),'active_change':F(weight-old),'expected_return_contribution':F(contribution),'evidence':support(a)})
        reconciled=proposed_total==1 and current_total==1 and len(allocations)==len(doc['allocations'])
        if not reconciled:issues.append('current and proposed allocation weights must each reconcile to one')
        if policy_ok and liquid<num(policy,'minimum_liquid_weight',0,1):issues.append('proposed allocation breaches liquid-weight minimum')
        analysis={'allocations':rows,'expected_return':F(expected) if reconciled else None,'one_way_turnover':F(turnover/D(2)) if reconciled else None,'liquid_weight':F(liquid) if reconciled else None,'policy_evidence':support(policy) if policy_ok else None}
    return complete(doc,SKILL,'ic-'+mode+'-review',{'mode':mode,'thesis':notes,'analysis':analysis,'committee_decision':'pending','review_readiness':'blocked' if issues else 'ready-for-human-adjudication'},issues,
                    ['Scenario expected returns are supplied assumptions, not forecasts or recommendations.','No order, funding, manager appointment, asset-allocation optimization or committee approval occurs.','Allocation mode evaluates supplied weights and first-moment returns; it does not estimate covariance, tax or execution costs.'])

def validate(doc):return guard(compute,doc)
