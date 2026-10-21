"""Source-bound supplied-evidence review; no action or legal adjudication (MIT)."""
from foundation_contract import *
from datetime import timedelta
from decimal import Decimal, localcontext

SKILL = "sanctions-exposure-reviewer"

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
    errors=validate_common(doc,{'sanctions_exposure'})
    if errors: return errors,[]
    d=doc['data']
    for k in ('regime','regime_type','activity','perimeter','ownership_complete_evidence','indirect_exposure_evidence'): claim(d.get(k),errors,k)
    os=rows(d,'direct_owners',errors); ident(os,'owner_id',errors)
    for r in os:
        claim(r.get('owner_evidence'),errors,'owner identity'); money(r.get('ownership_pct'),errors,'ownership percentage'); claim(r.get('blocked'),errors,'blocked status')
        v=r.get('ownership_pct',{}).get('value')
        if known(v) and decimal(v)>100: errors.append('ownership percentage exceeds100')
    pct_ids=[fid for r in os for fid in r.get('ownership_pct',{}).get('fact_ids',[])]
    if len(set(pct_ids))!=len(pct_ids): errors.append('duplicate ownership monetary provenance; cannot count same stake twice')
    if not isinstance(d.get('ownership_complete'),bool) or not isinstance(d.get('indirect_exposure'),bool): errors.append('explicit ownership completeness/indirect exposure required')
    rs=rows(d,'activity_conditions',errors); ident(rs,'condition_id',errors)
    for r in rs:
        claim(r.get('observed'),errors,'condition observed'); claim(r.get('required'),errors,'condition requirement')
    auth=d.get('authorization')
    if auth is not None:
        if not isinstance(auth,dict): errors.append('authorization must be object'); return errors,[]
        for k in ('regime','activity','perimeter','valid_from','valid_until','authority'): claim(auth.get(k),errors,'authorization '+k)
        for r in rows(auth,'conditions',errors): claim(r.get('observed'),errors,'authorization observed'); claim(r.get('required'),errors,'authorization required')
    return errors,[]

def _compute(doc):
    require_valid(doc,validate); d=doc['data']; issues=[]
    regime=cv(doc,d['regime'],'regime',issues); rtype=cv(doc,d['regime_type'],'regime type',issues)
    activity=cv(doc,d['activity'],'activity',issues); perimeter=cv(doc,d['perimeter'],'perimeter',issues)
    method=profile(doc,'method_profile','ofac-direct-ownership/1.0',issues)
    total=Decimal(0); all_known=True; ownership_total=Decimal(0)
    for r in d['direct_owners']:
        pct=amount(doc,r['ownership_pct'],'owner '+r['owner_id'],issues); blocked=cv(doc,r['blocked'],'owner blocked status',issues)
        owner=cv(doc,r['owner_evidence'],'owner identity',issues)
        if owner!=r['owner_id']: issues.append('direct owner identifier differs from sourced ownership record')
        if pct is None or owner!=r['owner_id'] or type(blocked) is not bool: all_known=False; issues.append('owner evidence unknown'); continue
        ownership_total+=pct
        if blocked: total+=pct
    if ownership_total>100: raise ValueError('declared ownership exceeds100; duplicate or invalid population')
    complete_fact=cv(doc,d['ownership_complete_evidence'],'ownership population completeness',issues); indirect_fact=cv(doc,d['indirect_exposure_evidence'],'indirect exposure scope',issues)
    if complete_fact!=d['ownership_complete'] or indirect_fact!=d['indirect_exposure']: issues.append('ownership completeness/indirect scope differs from source facts')
    supported=bool(method and indirect_fact is False and regime=='OFAC' and rtype=='blocking' and not d['indirect_exposure'])
    if not supported: issues.append('only explicit approved OFAC direct blocking ownership aggregation supported; indirect/foreign/sectoral interpretation unknown')
    complete=all_known and complete_fact is True and d['ownership_complete'] and bool(d['direct_owners'])
    if not complete: issues.append('direct ownership population incomplete; below-threshold inference unavailable')
    outcome='threshold-met-in-supplied-direct-records' if supported and all_known and total>=50 else 'threshold-not-met-in-complete-supplied-direct-records' if supported and complete else 'unknown'
    conditions=[]
    for r in d['activity_conditions']:
        ob=cv(doc,r['observed'],'activity condition',issues); req=cv(doc,r['required'],'regime condition requirement',issues)
        conditions.append({'condition_id':r['condition_id'],'match':None if ob is None or req is None else ob==req,'observed':ob,'required':req})
    if not conditions: issues.append('regime-specific activity/prohibition conditions absent')
    auth_status='unknown'; auth=d.get('authorization')
    if auth:
        values={k:cv(doc,auth[k],'authorization '+k,issues) for k in ('regime','activity','perimeter','valid_from','valid_until','authority')}
        checks=[]
        for r in auth['conditions']:
            ob=cv(doc,r['observed'],'authorization condition',issues); req=cv(doc,r['required'],'authorization requirement',issues); checks.append(ob is not None and req is not None and ob==req)
        start,end=day(values['valid_from']),day(values['valid_until'])
        matched=all(v is not None for v in values.values()) and values['regime']==regime and values['activity']==activity and values['perimeter']==perimeter and start and end and start<=day(doc['as_of'])<=end and all(checks) and bool(checks)
        auth_status='supplied-scope-date-conditions-match-human-review-required' if matched else 'scope-date-condition-gap'
        if not matched: issues.append('authorization scope/date/conditions not supported by supplied facts')
    else: issues.append('authorization/exemption applicability unassessed')
    return result(doc,SKILL,'ofac-direct-ownership/1.0',{'regime':regime,'regime_type':rtype,'activity':activity,'perimeter':perimeter,'direct_blocked_ownership_pct':str(total) if supported and all_known else None,'ownership_result':outcome,'activity_conditions':conditions,'authorization_review':auth_status,'legal_status':'human-owned','transaction_clearance':False},issues,limitations=['No universal sanctions rule, indirect look-through, foreign control/ownership method, designation validation or permission to process/block/reject. Direct arithmetic is only a supplied-record review.'],handoffs=['sanctions-match-investigator','beneficial-ownership-analyzer','financial-crime-reporting-reviewer'])


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
