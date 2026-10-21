"""Institutional manager evidence matrix, fee/capacity review and policy-gated scoring."""
from foundation_contract import D,exact,ratio,date_value
from business_evidence import start,bound,items,num,text,flag,values,current,support,F,complete,guard,compare, observed
SKILL='investment-manager-due-diligence-reviewer'
DIMENSIONS={'investment','operations','team','capacity','fees','performance'}

@exact
def compute(doc):
    start(doc,{'manager','policy','evidence','fee_terms','performance'})
    if doc.get('mode')!='institutional':raise ValueError('new manager review mode must be institutional')
    issues=[];manager=bound(doc,doc.get('manager'),issues,'manager');policy=bound(doc,doc.get('policy'),issues,'institutional policy',True)
    evidence=items(doc,'evidence',issues);fees=bound(doc,doc.get('fee_terms'),issues,'fee terms');performance=bound(doc,doc.get('performance'),issues,'performance')
    matrix=[];fee_result=None;perf_result=None;score=None;capacity=None
    if manager:
        current_aum=num(manager,'strategy_aum',0);capacity_aum=num(manager,'capacity_aum',0);proposed=num(manager,'proposed_commitment',0)
        capacity={'available_capacity':F(capacity_aum-current_aum),'post_commitment_headroom':F(capacity_aum-current_aum-proposed),'evidence':support(manager)}
        if current_aum+proposed>capacity_aum:issues.append('proposed commitment exceeds supplied strategy capacity')
    if policy and current(policy,doc,issues,'institutional policy'):
        criteria=policy.get('criteria')
        if not isinstance(criteria,list) or not criteria:raise ValueError('institutional criteria required')
        seen=set();dims=set();weighted=D(0);weights=D(0);scoreable=True
        for criterion in criteria:
            cid=text(criterion,'id');dim=text(criterion,'dimension')
            if cid in seen or dim not in DIMENSIONS:raise ValueError('duplicate criterion or unsupported diligence dimension')
            seen.add(cid);dims.add(dim)
            matches=[e for e in evidence if e.get('criterion_id')==cid]
            status='unknown';source=None
            if len(matches)==1:
                e=matches[0];source=support(e)
                if not flag(criterion,'independent_required') or e.get('origin')=='independent':
                    status=compare(e.get('value'),text(criterion,'operator'),criterion.get('threshold'))
            required=flag(criterion,'required')
            if status=='unknown':scoreable=False
            if required and status!='met':issues.append('institutional manager required criterion unresolved');scoreable=False
            weight=num(criterion,'weight',0);weights+=weight
            if status=='met':weighted+=weight
            matrix.append({'criterion_id':cid,'dimension':dim,'status':status,'required':required,'evidence':source})
        if dims!=DIMENSIONS:issues.append('institutional policy does not cover all six diligence dimensions');scoreable=False
        if policy.get('scoring_method')=='weighted-met-fraction' and scoreable and weights>0:score=ratio(weighted,weights)
        elif policy.get('scoring_method') not in {None,'none','weighted-met-fraction'}:raise ValueError('unsupported manager scoring method')
    else:issues.append('current institutional diligence policy unavailable; no score or eligibility conclusion')
    if fees:
        capital=num(fees,'capital',0);base=capital*(num(fees,'management_bps',0,10000)+num(fees,'other_bps',0,10000))/D(10000)
        if fees.get('method')!='flat-management-and-expense-only':issues.append('complex incentive, tier or waterfall fee terms require separate model')
        else:fee_result={'annual_flat_fee':F(base),'capital':F(capital),'fee_bps':F(num(fees,'management_bps')+num(fees,'other_bps')),'evidence':support(fees)}
    if performance:
        if performance.get('basis')=='net' and performance.get('reconciled') is True and observed(doc,performance,'period_end'):
            manager_return=num(performance,'manager_return',-1);benchmark=num(performance,'benchmark_return',-1)
            perf_result={'manager_return':F(manager_return),'benchmark_return':F(benchmark),'arithmetic_excess':F(manager_return-benchmark),'benchmark_id':text(performance,'benchmark_id'),'period_end':performance['period_end'],'evidence':support(performance)}
        else:issues.append('manager performance basis or reconciliation unresolved')
    return complete(doc,SKILL,'institutional-manager-policy-evidence',{'criteria':matrix,'capacity':capacity,'fees':fee_result,'performance':perf_result,'policy_score':score,'eligibility':'unresolved' if issues else 'meets-supplied-review-policy','manager_appointment':'not-made'},issues,
                    ['Institutional mode is distinct from legacy US/USD household analysis.','Independent evidence labels and manager assertions are supplied, not authenticated; no manager ranking without explicit policy.','No background checks, custody verification, GIPS certification, incentive waterfall modeling or manager appointment.'])

def validate(doc):return guard(compute,doc)
