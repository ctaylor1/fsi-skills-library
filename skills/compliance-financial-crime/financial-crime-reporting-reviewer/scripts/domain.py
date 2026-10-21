"""Source-bound supplied-evidence review; no action or legal adjudication (MIT)."""
from foundation_contract import *
from datetime import timedelta
from decimal import Decimal, localcontext

SKILL = "financial-crime-reporting-reviewer"

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
    errors=validate_common(doc,{'financial_crime_reporting'})
    if errors: return errors,[]
    d=doc['data']; es=rows(d,'events',errors); os=rows(d,'obligations',errors)
    ident(es,'event_id',errors); ident(os,'obligation_id',errors)
    for r in es:
        if not day(r.get('date')) or day(r['date'])>day(doc['as_of']): errors.append('event date invalid/future')
        if not text(r.get('currency')): errors.append('event currency required')
        claim(r.get('id_evidence'),errors,'event identity'); money(r.get('amount'),errors,'reporting event amount'); claim(r.get('date_evidence'),errors,'event date'); claim(r.get('type'),errors,'event type'); claim(r.get('currency_evidence'),errors,'event currency')
    for r in os:
        if r.get('kind') not in ('ctr','blocked_property','rejected_transaction','fbar','other_non_sar'): errors.append('nonSAR obligation type required; SAR routes to SAR drafter')
        if not strings(r.get('event_ids'),True) or not set(r['event_ids'])<={x['event_id'] for x in es}: errors.append('obligation event membership must identify supplied events')
        claim(r.get('scope_evidence'),errors,'obligation population/method scope')
        if len(set(r.get('event_ids',[])))!=len(r.get('event_ids',[])): errors.append('duplicate event membership cannot double count amounts')
        for k in ('applicable','obligation','period_start','period_end','due_date','channel'): claim(r.get(k),errors,'obligation '+k)
        money(r.get('threshold'),errors,'threshold')
        if r.get('comparison') not in ('gt','gte','event_required'): errors.append('explicit threshold comparison/method required')
        if not text(r.get('currency')): errors.append('obligation currency required; no FX assumed')
        if r.get('expected_event_type') is None: errors.append('expected event type required')
        if not records(r.get('exceptions')) or not records(r.get('acknowledgments')): errors.append('explicit exceptions/acknowledgments ledgers required')
        for x in r.get('exceptions',[]): claim(x.get('valid'),errors,'exception valid'); claim(x.get('basis'),errors,'exception basis'); claim(x.get('obligation_id'),errors,'exception obligation scope')
        for x in r.get('acknowledgments',[]):
            if x.get('status') not in ('accepted','rejected','pending'): errors.append('acknowledgment status invalid')
            claim(x.get('status_evidence'),errors,'acknowledgment status evidence')
            for k in ('receipt','date','obligation_id'): claim(x.get(k),errors,'acknowledgment '+k)
    return errors,[]

def _compute(doc):
    require_valid(doc,validate); d=doc['data']; issues=[]; method=profile(doc,'method_profile','typed-nonsar-obligation-review/1.0',issues); events={r['event_id']:r for r in d['events']}; out=[]
    for r in d['obligations']:
        rowissues=[]; v={k:cv(doc,r[k],r['obligation_id']+'.'+k,rowissues) for k in ('applicable','obligation','period_start','period_end','due_date','channel')}
        start,end,due=day(v['period_start']),day(v['period_end']),day(v['due_date'])
        if not start or not end or start>end: rowissues.append('reporting period unknown/inconsistent')
        if not due: rowissues.append('deadline unknown; no calendar or legal default')
        scope=cv(doc,r['scope_evidence'],'obligation population/method scope',rowissues)
        exactscope={k:r[k] for k in ('kind','event_ids','currency','comparison','expected_event_type')}
        complete=scope==exactscope
        if not complete: rowissues.append('obligation population/method differs from exact sourced scope')
        total=Decimal(0)
        for eid in r['event_ids']:
            e=events[eid]; a=amount(doc,e['amount'],'event '+eid,rowissues); ed=cv(doc,e['date_evidence'],'event date',rowissues); et=cv(doc,e['type'],'event type',rowissues); currency=cv(doc,e['currency_evidence'],'event currency',rowissues); sourced_id=cv(doc,e['id_evidence'],'event identity',rowissues)
            if sourced_id!=eid or currency!=e['currency'] or e['currency']!=r['currency'] or not start or not end or not ed or ed!=e['date'] or not start<=day(ed)<=end or et!=r['expected_event_type']: rowissues.append('event currency/type/date outside obligation method scope'); complete=False
            if a is None: complete=False
            else: total+=a
        threshold=amount(doc,r['threshold'],'reporting threshold',rowissues)
        exceptions=[{'valid':cv(doc,x['valid'],'exception applicability',rowissues),'basis':cv(doc,x['basis'],'exception basis',rowissues),'obligation_id':cv(doc,x['obligation_id'],'exception obligation scope',rowissues)} for x in r['exceptions']]
        if any(x['valid'] is None or x['basis'] is None or x['obligation_id']!=r['obligation_id'] for x in exceptions): rowissues.append('exception evidence unknown')
        exception=any(x['valid'] is True and x['basis'] is not None and x['obligation_id']==r['obligation_id'] for x in exceptions)
        trigger=None if not method or not complete or v['applicable'] is not True or threshold is None else (True if r['comparison']=='event_required' else total>threshold if r['comparison']=='gt' else total>=threshold)
        if v['applicable'] is not True: rowissues.append('obligation applicability requires human confirmation or is out of supplied scope')
        acknowledgments=[]
        for x in r['acknowledgments']:
            av={k:cv(doc,x[k],'acknowledgment '+k,rowissues) for k in ('receipt','date','obligation_id')}
            if av['obligation_id']!=r['obligation_id'] or not day(av['date']) or day(av['date'])>day(doc['as_of']): rowissues.append('acknowledgment identity/date mismatch')
            status=cv(doc,x['status_evidence'],'acknowledgment status',rowissues)
            if status!=x['status']: rowissues.append('acknowledgment status differs from source fact')
            acknowledgments.append({**av,'status':status,'assurance':'supplied-unverified'})
        accepted=any(x['status']=='accepted' and x['receipt'] is not None and x['obligation_id']==r['obligation_id'] and day(x['date']) and day(x['date'])<=day(doc['as_of']) for x in acknowledgments)
        state='unknown' if trigger is None or rowissues else 'exception-for-human-review' if exception else 'acknowledgment-recorded-unverified' if accepted else 'overdue-review' if trigger and due<day(doc['as_of']) else 'draft-obligation-review' if trigger else 'threshold-not-met-in-supplied-scope'
        issues.extend(r['obligation_id']+': '+x for x in rowissues)
        out.append({'obligation_id':r['obligation_id'],'kind':r['kind'],'obligation':v['obligation'],'event_ids':r['event_ids'],'currency':r['currency'],'amount':str(total) if complete else None,'threshold':str(threshold) if threshold is not None else None,'trigger_observed':trigger,'period_start':v['period_start'],'period_end':v['period_end'],'due_date':v['due_date'],'channel':v['channel'],'review_state':state,'exceptions':exceptions,'acknowledgments':acknowledgments})
    if not out: issues.append('no typed obligations supplied')
    return result(doc,SKILL,'typed-nonsar-obligation-review/1.0',{'obligation_reviews':out,'filing_performed':False,'sar_substitution':False},issues,limitations=['NonSAR supplied-obligation review only. Event membership, threshold and deadline must be explicit approved applicable method. No universal CTR/OFAC/FBAR deadlines, FX, filing, exemption adjudication or acknowledgment authentication.'],handoffs=['suspicious-activity-report-drafter','sanctions-exposure-reviewer','regulatory-reporting-data-validator'])


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
