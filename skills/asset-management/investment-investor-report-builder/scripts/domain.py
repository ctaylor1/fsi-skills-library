"""Investor-report preparation: capital bridge, comparable performance and approved content."""
from foundation_contract import D,date_value,exact,ratio
from business_evidence import start,bound,items,num,text,flag,values,current,support,F,complete,guard,statement, observed
SKILL='investment-investor-report-builder'

@exact
def compute(doc):
    if isinstance(doc, dict) and 'mode' in doc: raise ValueError('this calculator has no selectable mode')
    start(doc,{'share_class','period_start','period_end','capital','performance','report_policy','disclosures','commentary'})
    if date_value(doc['period_start'])>date_value(doc['period_end']) or date_value(doc['period_end'])>date_value(doc['as_of']):raise ValueError('report period must end by as_of')
    if not isinstance(doc.get('share_class'),str) or not doc['share_class']:raise ValueError('share_class required')
    issues=[];capital=bound(doc,doc.get('capital'),issues,'capital');performance=bound(doc,doc.get('performance'),issues,'performance')
    policy=bound(doc,doc.get('report_policy'),issues,'report policy',True);disclosures=items(doc,'disclosures',issues,True);commentary=items(doc,'commentary',issues,True)
    cap=None;perf=None;content=[]
    def scope(row):
        return all(row.get(k)==doc[k] for k in ('share_class','period_start','period_end')) and observed(doc,row,'period_end')
    if capital:
        if not scope(capital):issues.append('capital scope mismatch')
        else:
            expected=num(capital,'opening',0)+num(capital,'contributions',0)-num(capital,'distributions',0)+num(capital,'income')-num(capital,'expenses',0)+num(capital,'realized_gain')+num(capital,'unrealized_gain')+num(capital,'fx_change')
            diff=num(capital,'closing',0)-expected;okay=abs(diff)<=num(capital,'tolerance',0)
            if okay:cap={'opening':F(num(capital,'opening')),'closing':F(num(capital,'closing')),'net_contributions':F(num(capital,'contributions')-num(capital,'distributions')),'expected_closing':F(expected),'difference':F(diff),'reconciled':True,'evidence':support(capital)}
            else:issues.append('capital bridge failed; investor figures withheld')
    if performance:
        if not scope(performance) or performance.get('method')!='time-weighted' or performance.get('reconciled') is not True:
            issues.append('performance scope, method or reconciliation unresolved')
        else:
            net=num(performance,'fund_net_return',-1);benchmark=num(performance,'benchmark_return',-1);basis=text(performance,'benchmark_basis')
            if basis not in {'total-return','net-total-return'}:issues.append('benchmark basis not comparable')
            else:
                perf={'fund_net_return':F(net),'benchmark_return':F(benchmark),'arithmetic_excess':F(net-benchmark),'relative_return':ratio(D(1)+net,D(1)+benchmark),'benchmark_id':text(performance,'benchmark_id'),'benchmark_basis':basis,'method':'supplied-time-weighted-return','evidence':support(performance)}
                if perf['relative_return'] is not None:perf['relative_return']=F(D(perf['relative_return'])-D(1))
                else:issues.append('relative return undefined for a total-loss benchmark')
                if 'fund_gross_return' in performance:perf['fund_gross_return']=F(num(performance,'fund_gross_return',-1))
    supplied_disclosures={}
    for row in disclosures+commentary:
        if not current(row,doc,issues,'report content'):continue
        content_text=statement(row,issues,'report content')
        if content_text is None:continue
        entry={'id':row['id'],'text':content_text,'evidence':support(row)}
        content.append(entry)
        if row in disclosures:supplied_disclosures[row['id']]=entry
    if policy and current(policy,doc,issues,'report policy'):
        required=values(policy,'required_disclosures')
        if not required:issues.append('report disclosure policy is empty')
        for key in required:
            if key not in supplied_disclosures:issues.append('required report disclosure missing or unavailable')
    else:issues.append('current report publication policy unavailable')
    return complete(doc,SKILL,'investor-capital-performance-review',{'share_class':doc['share_class'],'period_start':doc['period_start'],'period_end':doc['period_end'],'capital_bridge':cap,'performance':perf,'content':content,'publication_status':'not-authorized'},issues,
                    ['Internal preparation only; no client/public projection or publication approval.','Performance is a supplied reconciled time-weighted result, not independently recalculated from positions. Capital returns cannot substitute for time-weighted returns.','Disclosure requirements are supplied policy; this is not GIPS compliance or marketing-rule certification.'])

def validate(doc):return guard(compute,doc)
