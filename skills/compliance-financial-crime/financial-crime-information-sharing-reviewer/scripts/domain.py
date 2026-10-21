"""Source-bound supplied-evidence review; no action or legal adjudication (MIT)."""
from foundation_contract import *
from datetime import timedelta
from decimal import Decimal, localcontext

SKILL = "financial-crime-information-sharing-reviewer"

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
    errors=validate_common(doc,{'information_sharing_review'})
    if errors: return errors,[]
    d=doc['data']
    for k in ('recipient_id','recipient_type','purpose','legal_basis'): claim(d.get(k),errors,k)
    items=rows(d,'items',errors); ident(items,'item_id',errors)
    for r in items:
        if r.get('kind') not in ('underlying_fact','sar_material','sar_existence'): errors.append('typed information kind required')
        claim(r.get('content'),errors,'sharing content'); claim(r.get('kind_evidence'),errors,'content kind evidence')
        if not isinstance(r.get('necessary'),bool): errors.append('content minimization necessity must be explicit')
    ps=rows(d,'permissions',errors); ident(ps,'permission_id',errors)
    for r in ps:
        for k in ('recipient_id','purpose','legal_basis','authority','valid_from','valid_until'): claim(r.get(k),errors,'permission '+k)
        if not strings(r.get('item_ids'),True) or not strings(r.get('permitted_kinds'),True): errors.append('permission requires exact content scope and kinds')
        claim(r.get('scope'),errors,'content-bound permission scope')
        if r.get('status') not in ('approved','pending','refused'): errors.append('permission approval status required')
    for k in ('sender_registration','recipient_registration','recipient_eligibility','security_controls','joint_sar_participant'):
        claim(d.get(k),errors,k)
    return errors,[]

def _compute(doc):
    require_valid(doc,validate); d=doc['data']; issues=[]
    values={k:cv(doc,d[k],k,issues) for k in ('recipient_id','recipient_type','purpose','legal_basis','sender_registration','recipient_registration','recipient_eligibility','security_controls','joint_sar_participant')}
    method=profile(doc,'method_profile','content-bound-disclosure-review/1.0',issues)
    permissions=[]
    for r in d['permissions']:
        v={k:cv(doc,r[k],'permission '+k,issues) for k in ('recipient_id','purpose','legal_basis','authority','valid_from','valid_until')}
        start,end=day(v['valid_from']),day(v['valid_until'])
        scope=cv(doc,r['scope'],'content-bound permission scope',issues)
        scope_matches=scope=={k:r[k] for k in ('item_ids','permitted_kinds','status')}
        if not scope_matches: issues.append('permission scope differs from sourced content IDs/kinds/status')
        applies=bool(method and scope_matches and r['status']=='approved' and all(x is not None for x in v.values()) and v['recipient_id']==values['recipient_id'] and v['purpose']==values['purpose'] and v['legal_basis']==values['legal_basis'] and start and end and start<=day(doc['as_of'])<=end)
        permissions.append((r,applies))
    out=[]
    for r in d['items']:
        val=cv(doc,r['content'],'sharing item '+r['item_id'],issues)
        reasons=[]
        kind=cv(doc,r['kind_evidence'],'content kind',issues)
        if kind!=r['kind']: reasons.append('content kind differs from source-bound classification')
        matches=[p['permission_id'] for p,applies in permissions if applies and r['item_id'] in p['item_ids'] and r['kind'] in p['permitted_kinds']]
        if val is None: reasons.append('content evidence unknown')
        if not r['necessary']: reasons.append('minimize-remove-unnecessary-content')
        if not matches: reasons.append('no current recipient-purpose-basis-content-bound authority')
        if values['legal_basis']=='US_314b':
            if not all(values[k] is True for k in ('sender_registration','recipient_registration','recipient_eligibility','security_controls')): reasons.append('314b eligibility-registration-security evidence incomplete')
            if values['purpose'] not in ('identify_money_laundering','identify_terrorist_financing'): reasons.append('314b purpose not supported')
            if r['kind']!='underlying_fact': reasons.append('ordinary314b does not authorize SAR material/existence; jointSAR needs distinct legal basis review')
        if r['kind']!='underlying_fact' and (doc['workflow']['classification']!='sar_restricted' or doc['workflow']['audience']!='authorized_fiu'): reasons.append('actual SAR material requires restricted FIU native handling')
        if r['kind']!='underlying_fact' and not (values['legal_basis']=='US_joint_SAR' and values['joint_sar_participant'] is True): reasons.append('SAR material requires specific lawful SAR-sharing authority and actual joint participant evidence')
        if values['security_controls'] is not True: reasons.append('security evidence incomplete')
        issues.extend(r['item_id']+': '+x for x in reasons)
        out.append({'item_id':r['item_id'],'kind':r['kind'],'content':val if not reasons else None,'review_status':'supported-for-authorized-human-disclosure-review' if not reasons else 'withheld-pending-review','matched_permissions':matches,'issues':reasons})
    if not d['items']: issues.append('sharing content population absent')
    return result(doc,SKILL,'content-bound-disclosure-review/1.0',{'recipient_id':values['recipient_id'],'recipient_type':values['recipient_type'],'purpose':values['purpose'],'legal_basis':values['legal_basis'],'item_reviews':out,'send_authorized':False,'disclosure_taken':False},issues,limitations=['Specific supplied content/recipient/purpose review; no send or safe-harbor/legal conclusion. Source labels cannot replace actual SAR material classification or disclosure authority. Joint SAR discussions are a separate basis, not a generic314b exception.'],handoffs=['privacy-impact-assessment-assistant','suspicious-activity-report-drafter'])


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
