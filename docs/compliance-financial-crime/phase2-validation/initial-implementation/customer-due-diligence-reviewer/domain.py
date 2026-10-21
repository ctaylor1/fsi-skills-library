"""Source-bound supplied-evidence review; no action or legal adjudication (MIT)."""
from foundation_contract import *
from datetime import timedelta
from decimal import Decimal, localcontext

SKILL = "customer-due-diligence-reviewer"

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
    errors=validate_common(doc,{'customer'})
    if errors: return errors,[]
    d=doc['data']
    if doc.get('mode')!='lifecycle': errors.append('Phase2 mode must be lifecycle')
    if d.get('lifecycle') not in ('onboarding','periodic','event-driven'): errors.append('CDD lifecycle context required')
    claim(d.get('anchor_date'),errors,'CDD review anchor')
    for k in ('current_record','prior_record'):
        if not isinstance(d.get(k),dict): errors.append(k+' must be explicit object'); continue
        for c in d[k].values(): claim(c,errors,k+' field')
    p=doc.get('policy_profile',{})
    if not strings(p.get('material_fields')) or not strings(p.get('required_fields'),True): errors.append('explicit material/required field policy required')
    claim(p.get('cadence_days'),errors,'policy cadence')
    if known(p.get('cadence_days',{}).get('value')) and (type(p['cadence_days']['value']) is not int or p['cadence_days']['value']<0): errors.append('CDD cadence must be nonnegative integer days')
    for k in ('ownership_coverage_target','activity_min','activity_max'): money(p.get(k),errors,k)
    for k in ('ownership_complete','control_coverage','expected_activity_currency','expected_activity_period_start','expected_activity_period_end'): claim(d.get(k),errors,k)
    rs=rows(d,'owners',errors); ident(rs,'owner_id',errors)
    for r in rs:
        claim(r.get('owner_evidence'),errors,'CDD owner identity')
        money(r.get('ownership_pct'),errors,'CDD ownership')
        if known(r.get('ownership_pct',{}).get('value')) and decimal(r['ownership_pct']['value'])>100: errors.append('ownership percentage exceeds100')
        claim(r.get('verified'),errors,'ownership verification')
    for r in rows(d,'observed_activity',errors):
        claim(r.get('currency_evidence'),errors,'activity currency evidence'); money(r.get('amount'),errors,'observed activity'); claim(r.get('date'),errors,'activity date')
        if not text(r.get('currency')): errors.append('activity currency required')
    pct_ids=[fid for r in rs for fid in r.get('ownership_pct',{}).get('fact_ids',[])]
    if len(set(pct_ids))!=len(pct_ids): errors.append('duplicate owner stake provenance; cannot count same ownership twice')
    cs=rows(d,'review_controls',errors); ident(cs,'control_id',errors)
    for r in cs: claim(r.get('evidence'),errors,'review control evidence')
    if not strings(p.get('required_controls'),True): errors.append('required review controls policy required')
    return errors,[]

def _compute(doc):
    require_valid(doc,validate); d=doc['data']; issues=[]; p=profile(doc,'policy_profile','cdd-lifecycle/1.0',issues)
    prior={k:cv(doc,c,'prior '+k,issues) for k,c in d['prior_record'].items()}; current={k:cv(doc,c,'current '+k,issues) for k,c in d['current_record'].items()}
    gaps=[]; changes=[]; due=None
    if p:
        for k in p['required_fields']:
            if current.get(k) is None: gaps.append('required current field '+k+' unknown')
        if d['lifecycle']!='onboarding' and not prior: gaps.append('prior record absent; material change comparison unknown')
        for k in p['material_fields']:
            if k not in prior or k not in current or prior[k] is None or current[k] is None:
                if d['lifecycle']!='onboarding': gaps.append('material field '+k+' comparison unknown')
            elif prior[k]!=current[k]: changes.append({'field':k,'prior':prior[k],'current':current[k],'basis':'supplied-policy-material-field'})
        anchor=day(cv(doc,d['anchor_date'],'CDD anchor',issues)); cadence=cv(doc,p['cadence_days'],'CDD cadence',issues)
        if anchor and anchor<=day(doc['as_of']) and type(cadence) is int: due=(anchor+timedelta(days=cadence)).isoformat()
        else: gaps.append('anchor/cadence missing/future; due date unknown')
    total=Decimal(0); quantified=True; unverified=[]
    for r in d['owners']:
        a=amount(doc,r['ownership_pct'],'CDD owner',issues); verified=cv(doc,r['verified'],'CDD owner verification',issues)
        owner=cv(doc,r['owner_evidence'],'CDD owner identity',issues)
        if a is None or owner!=r['owner_id']: quantified=False; issues.append('CDD owner identifier/stake unsupported')
        else: total+=a
        if verified is not True: unverified.append(r['owner_id'])
    if total>100: raise ValueError('declared ownership exceeds100')
    complete=cv(doc,d['ownership_complete'],'ownership completeness',issues); control=cv(doc,d['control_coverage'],'control coverage',issues)
    target=amount(doc,p['ownership_coverage_target'],'coverage target',issues) if p else None
    if target is not None and target>100: raise ValueError('ownership coverage target exceeds100')
    owner_status='supported-declared-coverage' if p and complete is True and control is True and quantified and d['owners'] and not unverified and target is not None and total>=target else 'coverage-gap-or-unknown'
    if owner_status!='supported-declared-coverage': gaps.append('ownership/control coverage incomplete or unverified')
    currency=cv(doc,d['expected_activity_currency'],'expected currency',issues); start=day(cv(doc,d['expected_activity_period_start'],'activity period start',issues)); end=day(cv(doc,d['expected_activity_period_end'],'activity period end',issues)); observed=Decimal(0); ac=True
    for r in d['observed_activity']:
        a=amount(doc,r['amount'],'observed activity',issues); rd=day(cv(doc,r['date'],'activity date',issues))
        rc=cv(doc,r['currency_evidence'],'activity currency',issues)
        if a is None or rc!=r['currency'] or r['currency']!=currency or not start or not end or not rd or not start<=rd<=end: ac=False
        else: observed+=a
    if not start or not end or start>end or end>day(doc['as_of']): ac=False; issues.append('expected activity period unknown/inconsistent/future')
    lo=amount(doc,p['activity_min'],'expected minimum',issues) if p else None; hi=amount(doc,p['activity_max'],'expected maximum',issues) if p else None
    if lo is not None and hi is not None and lo>hi: raise ValueError('expected activity bounds inverted')
    activity='within-supplied-expectation' if ac and d['observed_activity'] and lo is not None and hi is not None and lo<=observed<=hi else 'outside-supplied-expectation' if ac and d['observed_activity'] and lo is not None and hi is not None else 'unknown'
    if activity=='unknown': gaps.append('expected/observed activity assessment unknown')
    controls={r['control_id']:cv(doc,r['evidence'],'review control '+r['control_id'],issues) for r in d['review_controls']}
    if p:
        for k in p['required_controls']:
            if controls.get(k) is not True: gaps.append('review control '+k+' evidence gap')
    issues.extend(gaps)
    proposals=[]
    if changes: proposals.append({'proposal':'analyst review material changes and refresh scoped evidence','execution':'not_performed'})
    if gaps: proposals.append({'proposal':'obtain missing scoped evidence using separately authorized remediation','execution':'not_performed'})
    if activity=='outside-supplied-expectation': proposals.append({'proposal':'investigate actual-versus-expected activity','execution':'not_performed'})
    return result(doc,SKILL,'cdd-lifecycle/1.0',{'lifecycle':d['lifecycle'],'review_due_date':due,'review_overdue':due<doc['as_of'] if due else None,'material_changes':changes,'current_record':current,'ownership_pct':str(total) if quantified else None,'ownership_control_review':owner_status,'unverified_owner_ids':unverified,'expected_activity_review':activity,'observed_activity_total':str(observed) if ac else None,'review_controls':controls,'remediation_proposals':proposals,'customer_decision':'human-owned'},issues,limitations=['CDD lifecycle supplied-policy review; no invented review cadence, onboarding decision, account action, BO legal determination or contact. Actual/prior records and source claims remain supplied-unverified.'],handoffs=['enhanced-due-diligence-assessor','beneficial-ownership-analyzer','financial-crime-case-investigator'])


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
