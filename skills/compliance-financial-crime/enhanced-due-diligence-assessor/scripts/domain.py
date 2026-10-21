"""Source-bound supplied-evidence review; no action or legal adjudication (MIT)."""
from foundation_contract import *
from datetime import timedelta
from decimal import Decimal, localcontext

SKILL = "enhanced-due-diligence-assessor"

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
    if doc.get('mode')!='substantive': errors.append('Phase2 mode must be substantive')
    rs=rows(d,'wealth_funds_claims',errors); ident(rs,'claim_id',errors)
    for r in rs:
        if r.get('kind') not in ('source_of_funds','source_of_wealth') or not text(r.get('currency')): errors.append('SoF/SoW claim kind/currency required')
        claim(r.get('currency_evidence'),errors,'claim currency')
        for key in ('economic_activity','capacity_basis','capacity_currency'): claim(r.get(key),errors,'plausibility '+key)
        money(r.get('economic_capacity'),errors,'economic capacity')
        money(r.get('claimed_amount'),errors,'claimed wealth/funds'); claim(r.get('claim_date'),errors,'claim date')
        cs=r.get('corroboration')
        if not records(cs): errors.append('corroboration must be list'); continue
        ident(cs,'evidence_id',errors)
        if r.get('additivity') is not None: claim(r['additivity'],errors,'economic-event additivity')
        for c in cs:
            claim(c.get('currency_evidence'),errors,'corroboration currency'); money(c.get('amount'),errors,'corroboration amount'); claim(c.get('date'),errors,'corroboration date'); claim(c.get('description'),errors,'corroboration description')
            if not text(c.get('currency')): errors.append('corroboration currency required')
            if c.get('economic_event') is not None: claim(c['economic_event'],errors,'economic-event identity')
        for c in r.get('counterevidence',[]): claim(c,errors,'claim counterevidence')
        if not isinstance(r.get('counterevidence'),list): errors.append('counterevidence must be explicit list')
    hs=rows(d,'hypotheses',errors); validate_hypotheses(hs,errors)
    cs=rows(d,'controls',errors); ident(cs,'control_id',errors)
    for r in cs:
        claim(r.get('id_evidence'),errors,'control identity')
        for k in ('design_assessed','operating_assessed','assessor','period_start','period_end','sample_size','failures'): claim(r.get(k),errors,'control '+k)
    if not records(d.get('chronology')): errors.append('EDD chronology required')
    else:
        for r in d['chronology']: claim(r.get('date'),errors,'EDD chronology date'); claim(r.get('event'),errors,'EDD chronology event')
    return errors,[]

def _compute(doc):
    require_valid(doc,validate); d=doc['data']; issues=[]; assessments=[]
    p=profile(doc,'method_profile','edd-reconciliation/1.0',issues)
    tolerance=amount(doc,p.get('tolerance'),'reconciliation tolerance',issues) if p else None
    for r in d['wealth_funds_claims']:
        rowissues=[]; claim_currency=cv(doc,r['currency_evidence'],'claim currency',rowissues); target=amount(doc,r['claimed_amount'],'claim '+r['claim_id'],rowissues); cday=day(cv(doc,r['claim_date'],'claim date',rowissues)); total=Decimal(0); complete=True; chronological=True; evid=[]
        events={}; monetary_provenance={}; conflicts=set()
        for c in r['corroboration']:
            a=amount(doc,c['amount'],'corroboration '+c['evidence_id'],rowissues); when=day(cv(doc,c['date'],'corroboration date',rowissues)); descr=cv(doc,c['description'],'corroboration description',rowissues)
            ec=cv(doc,c['currency_evidence'],'corroboration currency',rowissues)
            if a is None or ec!=c['currency'] or claim_currency!=r['currency'] or c['currency']!=r['currency']: complete=False; rowissues.append('corroboration amount/currency cannot reconcile without FX')
            if not when or not cday or when>cday or cday>day(doc['as_of']): chronological=False; rowissues.append('corroboration chronology inconsistent/unknown')
            identity=cv(doc,c.get('economic_event'),'economic event for '+c['evidence_id'],rowissues)
            event_id=identity.get('event_id') if isinstance(identity,dict) else None
            identified=bool(isinstance(identity,dict) and text(event_id) and known(event_id)
                and identity.get('claim_id')==r['claim_id'] and identity.get('amount')==c['amount']['value']
                and identity.get('currency')==c['currency'] and identity.get('date')==c['date']['value']
                and a is not None and ec==c['currency'] and when is not None)
            if not identified:
                complete=False; rowissues.append(c['evidence_id']+' economic-event identity/amount/currency/date/scope is missing or ambiguous')
                event_id=None
            else:
                signature=(a,ec,when.isoformat())
                if event_id in events and events[event_id]['signature']!=signature:
                    conflicts.add(event_id); complete=False
                    rowissues.append('economic event '+event_id+' has conflicting amount/currency/date versions; dependent total withheld')
                event=events.setdefault(event_id,{'signature':signature,'documents':[]})
                event['documents'].append(c['evidence_id'])
                for fact_id in c['amount']['fact_ids']:
                    monetary_provenance.setdefault(fact_id,set()).add(event_id)
            evid.append({'evidence_id':c['evidence_id'],'economic_event_id':event_id,
                'amount':str(a) if a is not None else None,'date':when.isoformat() if when else None,
                'description':descr,'counting_status':'withheld-pending-economic-event-review'})
        if not r['corroboration']: complete=False; rowissues.append('no corroboration records')
        if any(len(ids)>1 for ids in monetary_provenance.values()):
            complete=False; rowissues.append('same monetary fact is attributed to different economic events; distinctness unresolved')
        additive=cv(doc,r.get('additivity'),'economic-event additivity for '+r['claim_id'],rowissues)
        expected_basis='distinct_funds_receipts' if r['kind']=='source_of_funds' else 'disjoint_wealth_components'
        additive_ids=additive.get('event_ids') if isinstance(additive,dict) else None
        additive_supported=bool(p and isinstance(additive,dict) and additive.get('claim_id')==r['claim_id']
            and additive.get('basis')==expected_basis and strings(additive_ids,True)
            and len(set(additive_ids))==len(additive_ids) and set(additive_ids)==set(events))
        if not additive_supported:
            complete=False; rowissues.append('distinct economic-event additivity is not supported by an applicable method and exact scoped source facts; total withheld')
        if complete:
            total=sum((event['signature'][0] for event in events.values()),Decimal(0))
            first_documents={event['documents'][0] for event in events.values()}
            for evidence in evid:
                evidence['counting_status']='counted-once' if evidence['evidence_id'] in first_documents else 'duplicate-document-not-additional-funds'
        economic_events=[{'event_id':eid,'amount':str(event['signature'][0]) if eid not in conflicts else None,
            'currency':event['signature'][1] if eid not in conflicts else None,
            'date':event['signature'][2] if eid not in conflicts else None,
            'document_evidence_ids':event['documents'],'consistency':'conflicting-versions' if eid in conflicts else 'consistent-supplied-event'}
            for eid,event in events.items()]
        counter=[cv(doc,c,'SoF/SoW counterevidence',rowissues) for c in r['counterevidence']]
        economic_activity=cv(doc,r['economic_activity'],'economic activity',rowissues); capacity_basis=cv(doc,r['capacity_basis'],'capacity basis',rowissues); capacity_currency=cv(doc,r['capacity_currency'],'capacity currency',rowissues); capacity=amount(doc,r['economic_capacity'],'economic capacity',rowissues)
        capacity_review=None if target is None or capacity is None or capacity_currency!=r['currency'] or economic_activity is None or capacity_basis is None else target<=capacity
        if capacity_review is not True: rowissues.append('claimed funds/wealth exceed or cannot be compared with sourced economic capacity; investigate plausibility')
        difference=target-total if target is not None and complete else None
        reconciled=None if not p or tolerance is None or difference is None else abs(difference)<=tolerance
        status='quantitatively-reconciled-supplied-evidence' if reconciled and chronological and not rowissues else 'reconciliation-gap' if reconciled is False else 'unknown-or-chronology-gap'
        if status!='quantitatively-reconciled-supplied-evidence': rowissues.append('SoF/SoW reconciliation requires further investigation')
        if counter: rowissues.append('counterevidence supplied; substantive plausibility remains contested')
        issues.extend(r['claim_id']+': '+x for x in rowissues)
        assessments.append({'claim_id':r['claim_id'],'kind':r['kind'],'currency':r['currency'],'claimed_amount':str(target) if target is not None else None,'corroborated_amount':str(total) if complete else None,'difference':str(difference) if difference is not None else None,'economic_event_aggregation':{'status':'supported-supplied-event-additivity' if complete else 'unknown-total-withheld','basis':expected_basis if additive_supported else None,'unique_event_count':len(events),'events':economic_events},'quantitative_review':status,'plausibility':'human-assessment-required','economic_activity':economic_activity,'capacity_basis':capacity_basis,'economic_capacity':str(capacity) if capacity is not None else None,'capacity_review':'within-supplied-economic-capacity' if capacity_review is True else 'exceeds-supplied-economic-capacity' if capacity_review is False else 'unknown','corroboration':evid,'counterevidence':counter})
    if not assessments: issues.append('no substantive SoF/SoW claims supplied')
    controls=[]; effective=True
    for r in d['controls']:
        v={k:cv(doc,r[k],'control '+r['control_id']+'.'+k,issues) for k in ('design_assessed','operating_assessed','assessor','period_start','period_end','sample_size','failures')}
        start,end=day(v['period_start']),day(v['period_end'])
        cid=cv(doc,r['id_evidence'],'control identity',issues)
        supported=cid==r['control_id'] and v['design_assessed'] is True and v['operating_assessed'] is True and v['assessor'] is not None and start and end and start<=end<=day(doc['as_of']) and type(v['sample_size']) is int and v['sample_size']>0 and type(v['failures']) is int and 0<=v['failures']<=v['sample_size']
        effective=effective and bool(supported)
        if not supported: issues.append('control '+r['control_id']+' operating assessment evidence insufficient')
        controls.append({'control_id':r['control_id'],**v,'operating_assessment_supported':bool(supported)})
    reviewed_hypotheses=hypotheses(doc,d['hypotheses'],issues)
    chronology=[]
    for r in d['chronology']:
        when=cv(doc,r['date'],'EDD chronology date',issues); event=cv(doc,r['event'],'EDD chronology event',issues)
        if not day(when) or day(when)>day(doc['as_of']): issues.append('EDD chronology unknown/future')
        chronology.append({'date':when,'event':event})
    issues.extend(doc['workflow']['unresolved_issues'])
    residual={'band':'Unknown','score':None,'status':'unknown'}
    risk=doc.get('risk_method')
    if risk:
        rp=profile(doc,'risk_method','edd-residual/1.0',issues)
        if rp:
            inherent=amount(doc,rp.get('inherent_score'),'inherent risk',issues); effectiveness=amount(doc,rp.get('control_effectiveness'),'control effectiveness',issues)
            bands=rp.get('bands',[]); boundaries=[]
            for b in bands:
                maximum=amount(doc,b.get('maximum'),'risk band maximum',issues)
                label=cv(doc,b.get('band_evidence'),'risk band label',issues)
                if maximum is not None and label==b.get('band') and text(label): boundaries.append((maximum,label))
                else: issues.append('risk band label/maximum not source-bound')
            required=rp.get('required_controls',[])
            recorded_required=cv(doc,rp.get('required_controls_evidence'),'required risk controls',issues)
            if recorded_required!=required: issues.append('required risk control IDs differ from accepted method evidence')
            accepted=bool(required and strings(required,True) and set(required)<={r['control_id'] for r in controls} and effective and d['controls'] and not issues and inherent is not None and effectiveness is not None and effectiveness<=1 and boundaries and boundaries==sorted(boundaries) and len({x[0] for x in boundaries})==len(boundaries))
            if accepted:
                score=inherent*(1-effectiveness); band=next((label for maximum,label in boundaries if score<=maximum),None)
                if band: residual={'band':band,'score':str(score),'status':'supplied-accepted-method-assessed-operating-evidence-human-review-required'}
                else: issues.append('risk bands do not cover calculated score')
            else: issues.append('residual method/control evidence insufficient; Unknown retained')
    else: issues.append('no accepted residual-risk method; Unknown retained')
    return result(doc,SKILL,'edd-reconciliation/1.0',{'wealth_funds_assessments':assessments,'chronology':sorted(chronology,key=lambda r:r['date'] or ''),'hypotheses':reviewed_hypotheses,'control_assessments':controls,'residual_risk':residual,'recommendation':'human-adjudication-required','customer_decision':'human-owned'},issues,limitations=['Quantitative reconciliation supports plausibility review, not proof of lawful origin or complete net worth. No currency conversion, fabricated income chronology, residual downgrade without explicit method and assessed operating evidence, adjudication, customer action or filing.'],handoffs=['financial-crime-case-investigator','sanctions-exposure-reviewer','customer-risk-rating-reviewer'])


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
