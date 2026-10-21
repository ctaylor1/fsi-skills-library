"""Source-bound supplied-evidence review; no action or legal adjudication (MIT)."""
from foundation_contract import *
from datetime import timedelta
from decimal import Decimal, localcontext

SKILL = "compliance-regulatory-notification-reviewer"

def rows(d,key,errors,required=True):
    v=d.get(key)
    if v is None and not required: return []
    if not records(v): errors.append('data.'+key+' must be list of objects'); return []
    return v

def ident(rs,key,errors):
    if not unique_ids(rs,key): errors.append('unique nonempty '+key+' values required')

def claim(v,errors,label):
    if not isinstance(v,dict) or not {'value','source_refs','fact_ids'}<=set(v): errors.append(label+' requires value/source_refs/fact_ids'); return
    if not strings(v['source_refs']) or not strings(v['fact_ids']): errors.append(label+' source_refs/fact_ids must be string lists')

def money(v,errors,label):
    claim(v,errors,label)
    if isinstance(v,dict) and known(v.get('value')):
        try:
            if not isinstance(v['value'],str) or decimal(v['value'])<0: raise ValueError()
        except (ValueError,TypeError): errors.append(label+' must contain a nonnegative exact decimal string')

def cv(doc,v,label,issues):
    value,gaps=claim_value(doc,v,label); issues.extend(gaps); return value

def amount(doc,v,label,issues):
    value=cv(doc,v,label,issues)
    return decimal(value) if value is not None else None

def profile(doc,kind,method,issues):
    p=doc.get(kind)
    if not isinstance(p,dict): issues.append(kind+' missing; no method default'); return None
    required=('version','jurisdiction','institution_type','purpose','effective_date','review_due_date','approval_status','approval')
    if any(k not in p for k in required): issues.append(kind+' missing applicable authority/date metadata'); return None
    if p.get('method')!=method: issues.append('unsupported '+kind+' method; specialist method required'); return None
    if p.get('jurisdiction')!=doc['workflow']['context']['jurisdiction'] or not known(p.get('institution_type')) or p.get('purpose')!=doc['workflow']['context']['purpose']:
        issues.append(kind+' institution/jurisdiction/purpose context mismatch'); return None
    start,end=day(p.get('effective_date')),day(p.get('review_due_date'))
    if not start or not end or not start<=day(doc['as_of'])<=end: issues.append(kind+' is not effective/review-current'); return None
    status=p.get('approval_status')
    if status!='approved' and not(status=='test-only' and doc.get('execution_context')=='test'):
        issues.append(kind+' not accepted for this execution context'); return None
    acceptance=cv(doc,p.get('approval'),kind+'.approval',issues)
    expected={k:p[k] for k in ('method','version','jurisdiction','institution_type','purpose','effective_date','review_due_date','approval_status')}
    if acceptance!=expected: issues.append(kind+' accepted status/scope/version/dates differ from source facts'); return None
    return p

def hypotheses(doc,rs,issues):
    out=[]
    for r in rs:
        support=[cv(doc,x,r['hypothesis_id']+'.support',issues) for x in r['support']]
        counter=[cv(doc,x,r['hypothesis_id']+'.counterevidence',issues) for x in r['counterevidence']]
        if not r['support']: issues.append(r['hypothesis_id']+' has no sourced support')
        if not r['counterevidence']: issues.append(r['hypothesis_id']+' counterevidence not supplied')
        out.append({'hypothesis_id':r['hypothesis_id'],'proposition':r['proposition'],'proposition_status':'analyst-hypothesis','support':support,'counterevidence':counter,'conclusion':'human-assessment-required'})
    return out

def validate_hypotheses(rs,errors):
    ident(rs,'hypothesis_id',errors)
    for r in rs:
        if not text(r.get('proposition')): errors.append('hypothesis proposition required')
        for k in ('support','counterevidence'):
            if not isinstance(r.get(k),list): errors.append(k+' must be list'); continue
            for c in r[k]: claim(c,errors,k)

def validate(doc):
    errors=validate_common(doc,{'regulatory_notification'})
    if errors: return errors,[]
    d=doc['data']
    for k in ('regulated_entity','regulated_activity','event','event_date','awareness_date'): claim(d.get(k),errors,k)
    rs=rows(d,'obligations',errors); ident(rs,'obligation_id',errors)
    for r in rs:
        claim(r.get('timing_evidence'),errors,'notification timing'); claim(r.get('materiality_method_evidence'),errors,'notification materiality method')
        for k in ('entity','activity','rule','channel','due_date'): claim(r.get(k),errors,'notification '+k)
        if r.get('timing') not in ('immediate','fixed_date','unknown'): errors.append('notification timing must be explicit')
        if r.get('materiality_method') not in ('all','any','unknown'): errors.append('materiality method explicit')
        cs=r.get('criteria')
        if not records(cs): errors.append('materiality criteria must be list'); continue
        ident(cs,'criterion_id',errors)
        for c in cs: claim(c.get('observed'),errors,'materiality fact'); claim(c.get('expected'),errors,'materiality rule criterion')
    for r in rows(d,'exhibits',errors): claim(r,errors,'exhibit')
    return errors,[]

def _compute(doc):
    require_valid(doc,validate); d=doc['data']; issues=[]; method=profile(doc,'method_profile','entity-activity-event-notification/1.0',issues)
    v={k:cv(doc,d[k],k,issues) for k in ('regulated_entity','regulated_activity','event','event_date','awareness_date')}
    event_day,awareness=day(v['event_date']),day(v['awareness_date'])
    if not event_day or not awareness or event_day>awareness or awareness>day(doc['as_of']): issues.append('event/awareness chronology unknown or inconsistent')
    reviews=[]
    for r in d['obligations']:
        gaps=[]; ov={k:cv(doc,r[k],r['obligation_id']+'.'+k,gaps) for k in ('entity','activity','rule','channel','due_date')}; checks=[]
        for c in r['criteria']:
            obs=cv(doc,c['observed'],'materiality observed',gaps); exp=cv(doc,c['expected'],'materiality expected',gaps)
            checks.append({'criterion_id':c['criterion_id'],'observed':obs,'expected':exp,'match':None if obs is None or exp is None else obs==exp})
        timing=cv(doc,r['timing_evidence'],'notification timing',gaps); materiality_method=cv(doc,r['materiality_method_evidence'],'materiality method',gaps)
        if timing!=r['timing'] or materiality_method!=r['materiality_method']: gaps.append('timing/materiality method differs from sourced rule method')
        applicable=None if not method or ov['entity'] is None or ov['activity'] is None or v['regulated_entity'] is None or v['regulated_activity'] is None else ov['entity']==v['regulated_entity'] and ov['activity']==v['regulated_activity']
        material=None if not checks or r['materiality_method']=='unknown' or any(x['match'] is None for x in checks) else all(x['match'] for x in checks) if r['materiality_method']=='all' else any(x['match'] for x in checks)
        if applicable is not True: gaps.append('entity/activity applicability unknown or outside supplied scope')
        if material is None: gaps.append('materiality cannot be assessed without sourced explicit criteria')
        due=day(ov['due_date'])
        if r['timing']=='fixed_date' and not due: gaps.append('fixed deadline missing; no invented business-day calendar')
        if r['timing']=='unknown': gaps.append('timing unassessed')
        if ov['channel'] is None: gaps.append('notification channel/form not evidenced')
        state='unknown' if gaps or issues else 'urgent-human-notification-review' if applicable and material and r['timing']=='immediate' else 'overdue-human-review' if applicable and material and due and due<day(doc['as_of']) else 'draft-for-human-notification-review' if applicable and material else 'criteria-not-met-in-supplied-scope'
        issues.extend(r['obligation_id']+': '+x for x in gaps)
        reviews.append({'obligation_id':r['obligation_id'],'rule':ov['rule'],'applicable':applicable,'materiality':material,'criteria':checks,'timing':r['timing'],'due_date':ov['due_date'],'channel':ov['channel'],'review_state':state})
    exhibits=[cv(doc,c,'notification exhibit',issues) for c in d['exhibits']]
    if not reviews: issues.append('notification obligations absent')
    return result(doc,SKILL,'entity-activity-event-notification/1.0',{'event_facts':v,'notification_reviews':reviews,'draft_exhibits':exhibits,'notification_taken':False,'legal_materiality_decision':'human-owned'},issues,limitations=['Supplied applicable notification facts/method only. Immediate remains urgent human review, never converted to an invented date. Prudential/payment incident reporting, exam responses and statutory financial-crime filing retain separate owners.'],handoffs=['regulatory-exam-response-packager','operational-resilience-reporter','regulatory-reporting-data-validator'])


def compute(doc):
    """Use an exact Decimal context sized for every supplied coefficient/exponent."""
    digit_span=28; population=0
    def scan(v):
        nonlocal digit_span,population
        if isinstance(v,dict):
            for x in v.values(): scan(x)
        elif isinstance(v,list):
            for x in v: scan(x)
        elif isinstance(v,str):
            try:
                n=decimal(v); tup=n.as_tuple()
                digit_span=max(digit_span,len(tup.digits)+abs(tup.exponent)); population+=1
            except (ValueError,TypeError): pass
    scan(doc)
    with localcontext() as context:
        context.prec=2*digit_span+len(str(population+1))+8
        return _compute(doc)
