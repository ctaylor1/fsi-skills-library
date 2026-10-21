"""Institutional issue, service-action and reporting-cadence preparation."""
from datetime import timedelta
from foundation_contract import D,date_value,exact
from business_evidence import start,items,bound,num,text,flag,support,complete,guard,current,statement, observed
SKILL='investment-client-service-preparer'

@exact
def compute(doc):
    if isinstance(doc, dict) and 'mode' in doc: raise ValueError('this calculator has no selectable mode')
    start(doc,{'service_policy','issues','reports','messages'})
    issues=[];policy=bound(doc,doc.get('service_policy'),issues,'service policy',True)
    cases=items(doc,'issues',issues);reports=items(doc,'reports',issues);messages=items(doc,'messages',issues,True)
    policy_ok=bool(policy and current(policy,doc,issues,'service policy'));plans=[];calendar=[];drafts=[]
    for case in cases:
        status=case.get('status')
        if status not in {'open','in-progress','resolved'}:raise ValueError('unsupported service issue status')
        opened=date_value(case.get('opened_at'));due=date_value(case.get('due_at'))
        if not observed(doc,case,'opened_at') or due<opened:issues.append('service issue date inconsistency');continue
        severity=text(case,'severity');owner=text(case,'owner')
        if status=='resolved' and not flag(case,'resolution_evidence_recorded'):
            status='resolution-unverified';issues.append('claimed service resolution lacks supporting record')
        row={'id':case['id'],'status':status,'owner':owner,'severity':severity,'due_at':case['due_at'],'overdue':status!='resolved' and due<date_value(doc['as_of']),'evidence':support(case)}
        if policy_ok:
            sla=policy.get('sla_days',{}).get(severity)
            if isinstance(sla,bool) or not isinstance(sla,int) or sla<0:issues.append('service severity has no valid SLA');row['sla_due']=None
            else:
                sla_due=opened+timedelta(days=sla);row['sla_due']=sla_due.isoformat()
                row['sla_breached']=status!='resolved' and date_value(doc['as_of'])>sla_due
                if row['sla_breached']:issues.append('service issue exceeds supplied SLA')
        else:issues.append('current service policy unavailable')
        if row['overdue']:issues.append('service action overdue')
        row['proposed_action']='review-resolution-evidence' if row['status']=='resolution-unverified' else 'owner-follow-up' if status!='resolved' else 'retain-resolution-evidence'
        plans.append(row)
    for report in reports:
        last=date_value(report.get('last_delivered'));days=report.get('cadence_days')
        if type(days) is not int or not 1<=days<=366:raise ValueError('cadence_days must be1..366')
        if not observed(doc,report,'last_delivered'):issues.append('future delivery record omitted');continue
        next_date=last+timedelta(days=days)
        row={'id':report['id'],'owner':text(report,'owner'),'next_due':next_date.isoformat(),'overdue':next_date<date_value(doc['as_of']),'evidence':support(report)}
        if row['overdue']:issues.append('client reporting cadence overdue')
        calendar.append(row)
    for message in messages:
        if not current(message,doc,issues,'service content'):continue
        content=statement(message,issues,'service content')
        if content is not None:drafts.append({'id':message['id'],'text':content,'evidence':support(message)})
    if not cases and not reports:issues.append('no service issue or reporting evidence supplied')
    return complete(doc,SKILL,'institutional-service-sla-cadence',{'action_plan':plans,'reporting_calendar':calendar,'approved_content_draft':drafts,'client_contacted':False},issues,
                    ['Calendar days, not jurisdiction-specific business-day calendars.','Resolution and delivery evidence are supplied assertions; this packet cannot close issues, schedule work or contact clients.'])

def validate(doc):return guard(compute,doc)
