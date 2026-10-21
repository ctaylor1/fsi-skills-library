"""RFP ownership, eligibility, commercial and approval preparation; no submission."""
from foundation_contract import D,date_value,exact
from business_evidence import start,bound,items,num,text,flag,values,current,support,F,complete,guard,statement,compare, observed
SKILL='institutional-proposal-responder'

@exact
def compute(doc):
    start(doc,{'engagement','policy','questions','answers','data_points','eligibility','commercial','approvals'})
    if doc.get('mode')!='rfp':raise ValueError('new proposal mode must be rfp')
    issues=[];eng=bound(doc,doc.get('engagement'),issues,'engagement');policy=bound(doc,doc.get('policy'),issues,'RFP policy',True)
    questions=items(doc,'questions',issues);answers=items(doc,'answers',issues,True);data=items(doc,'data_points',issues)
    eligibility=items(doc,'eligibility',issues);commercial=bound(doc,doc.get('commercial'),issues,'commercial');approvals=items(doc,'approvals',issues,True)
    responses=[];appendix={};eligibility_rows=[];approval_rows=[];economics=None
    current_answers={a['id']:a for a in answers if current(a,doc,issues,'approved answer')};data_idx={d['id']:d for d in data}
    for q in questions:
        owner=text(q,'owner');due=date_value(q.get('due_at'));text(q,'text')
        answer=current_answers.get(q.get('answer_id'));response=None;state='owner-action-required';evidence=[]
        if answer:
            required=values(answer,'data_ids')
            supported=all(k in data_idx and data_idx[k].get('reconciled') is True for k in required)
            if answer.get('kind')=='performance' and not required:supported=False
            if supported:
                response=statement(answer,issues,'RFP answer')
                if response is not None:
                    state='drafted';evidence=[support(answer)]+[support(data_idx[k]) for k in required]
                    for key in required:appendix[key]={'id':key,'value':data_idx[key].get('value'),'evidence':support(data_idx[key])}
            else:issues.append('RFP answer requires reconciled supporting figures')
        if state!='drafted':issues.append('RFP question needs owner-supplied approved answer')
        if due<date_value(doc['as_of']):issues.append('RFP question deadline passed')
        responses.append({'id':q['id'],'owner':owner,'due_at':q['due_at'],'status':state,'text':response,'supporting_evidence':evidence,'question_evidence':support(q)})
    if not questions:issues.append('RFP question inventory unavailable')
    if policy and current(policy,doc,issues,'RFP policy'):
        criteria=policy.get('eligibility_criteria')
        if not isinstance(criteria,list) or not criteria:raise ValueError('RFP eligibility criteria required')
        for criterion in criteria:
            cid=text(criterion,'id');matches=[e for e in eligibility if e.get('criterion_id')==cid]
            status=compare(matches[0].get('value'),text(criterion,'operator'),criterion.get('threshold')) if len(matches)==1 else 'unknown'
            if status!='met':issues.append('RFP eligibility criterion unresolved')
            eligibility_rows.append({'id':cid,'status':status,'owner':text(criterion,'owner'),'evidence':support(matches[0]) if len(matches)==1 else None})
        author=text(eng,'author') if eng else None
        roles=values(policy,'approval_roles')
        if not roles:issues.append('RFP approval policy must identify required roles')
        for role in roles:
            matching=[a for a in approvals if a.get('role')==role and a.get('status')=='recorded' and isinstance(a.get('actor'),str) and bool(a['actor'].strip()) and a.get('actor')!=author and observed(doc,a,'recorded_at')]
            status='recorded-supplied' if len(matching)==1 else 'outstanding'
            if status=='outstanding':issues.append('RFP approval or separation of duties unresolved')
            approval_rows.append({'role':role,'status':status,'evidence':support(matching[0]) if len(matching)==1 else None})
        if commercial:
            capital=num(commercial,'mandate_size',0);fee=num(commercial,'fee_bps',0,10000);revenue=capital*fee/D(10000)
            margin=revenue-num(commercial,'annual_service_cost',0)
            okay=fee>=num(policy,'minimum_fee_bps',0,10000) and margin>=num(policy,'minimum_annual_contribution')
            if not okay:issues.append('commercial proposal outside supplied policy')
            economics={'annual_revenue':F(revenue),'annual_contribution':F(margin),'meets_policy':okay,'evidence':support(commercial),'policy_evidence':support(policy)}
    else:issues.append('current eligibility/commercial/approval policy unavailable')
    if eng and date_value(eng.get('submission_due'))<date_value(doc['as_of']):issues.append('RFP submission deadline passed')
    return complete(doc,SKILL,'rfp-owner-eligibility-commercial-workflow',{'responses':responses,'data_appendix':list(appendix.values()),'eligibility':eligibility_rows,'commercial_review':economics,'approval_queue':approval_rows,'review_readiness':'blocked' if issues else 'ready-for-human-review','submission':'not-performed'},issues,
                    ['Source-linked owner workflow; no bid decision, negotiation, signature, attestation or submission.','Approvals are supplied records, not authenticated authority. Unknown eligibility never becomes eligible.'])

def validate(doc):return guard(compute,doc)
