"""Source-bound supplied-evidence review; no action or legal adjudication (MIT)."""
from foundation_contract import *
from datetime import timedelta
from decimal import Decimal, localcontext

SKILL = "financial-crime-case-investigator"

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
    errors=validate_common(doc,{'financial_crime_case'})
    if errors: return errors,[]
    d=doc['data']; s=d.get('scope',{})
    if not isinstance(s,dict) or not day(s.get('start')) or not day(s.get('end')) or day(s['start'])>day(s['end']) or day(s['end'])>day(doc['as_of']): errors.append('valid case scope date range required')
    if not strings(s.get('currencies'),True): errors.append('explicit scope currencies required')
    ents=rows(d,'entities',errors); accounts=rows(d,'accounts',errors); ts=rows(d,'transactions',errors)
    ident(ents,'entity_id',errors); ident(accounts,'account_id',errors); ident(ts,'transaction_id',errors)
    for r in ents:
        claim(r.get('identity'),errors,'entity identity'); claim(r.get('id_evidence'),errors,'entity identity binding')
    entity_ids={r.get('entity_id') for r in ents}; account_ids={r.get('account_id') for r in accounts}
    for r in accounts:
        if r.get('entity_id') not in entity_ids: errors.append('account entity outside case scope')
        claim(r.get('identity'),errors,'account identity'); claim(r.get('id_evidence'),errors,'account identity binding'); claim(r.get('entity_evidence'),errors,'account-entity relationship')
    for r in ts:
        if not day(r.get('date')) or not day(s.get('start')) or not day(s['start'])<=day(r['date'])<=day(s['end']): errors.append('transaction outside scoped period')
        if r.get('currency') not in s.get('currencies',[]): errors.append('transaction currency outside scope')
        if not text(r.get('from_account')) or not text(r.get('to_account')) or not({r['from_account'],r['to_account']}&account_ids): errors.append('transaction must link a scoped account and explicit counterparties')
        claim(r.get('id_evidence'),errors,'transaction identity'); money(r.get('amount'),errors,'transaction amount'); claim(r.get('date_evidence'),errors,'transaction date')
        claim(r.get('currency_evidence'),errors,'transaction currency'); claim(r.get('from_evidence'),errors,'transaction origin'); claim(r.get('to_evidence'),errors,'transaction destination')
    mapped_ids=[tuple(r.get('id_evidence',{}).get('fact_ids',[])) for r in ts]
    if len(set(mapped_ids))!=len(mapped_ids): errors.append('duplicate transaction identity provenance; cannot count same transaction twice')
    hs=rows(d,'hypotheses',errors); validate_hypotheses(hs,errors)
    plan=rows(d,'investigative_plan',errors); ident(plan,'step_id',errors)
    for r in plan:
        if not text(r.get('question')) or not strings(r.get('hypothesis_ids'),True) or not set(r['hypothesis_ids'])<={h.get('hypothesis_id') for h in hs}: errors.append('plan must identify question and scoped hypotheses')
    for r in rows(d,'chronology',errors):
        if not day(r.get('date')) or day(r['date'])>day(doc['as_of']): errors.append('chronology date invalid/future')
        claim(r.get('event'),errors,'chronology event'); claim(r.get('date_evidence'),errors,'chronology date')
    for r in rows(d,'narrative_propositions',errors): claim(r,errors,'narrative proposition')
    return errors,[]

def _compute(doc):
    require_valid(doc,validate); d=doc['data']; issues=[]; scoped={a['account_id'] for a in d['accounts']}
    entities=[]; supported_entities=set(); accounts=[]; supported_accounts=set()
    for r in d['entities']:
        eid=cv(doc,r['id_evidence'],'entity identifier',issues); identity=cv(doc,r['identity'],'entity identity',issues)
        supported=eid==r['entity_id'] and identity is not None
        if not supported: issues.append('entity identity differs from scoped ID or is unknown')
        else: supported_entities.add(eid)
        entities.append({'scope_ref':r['entity_id'],'entity_id':eid if supported else None,'identity':identity if supported else None,'evidence_status':'supplied-unverified'})
    for r in d['accounts']:
        aid=cv(doc,r['id_evidence'],'account identifier',issues); eid=cv(doc,r['entity_evidence'],'account-entity relationship',issues); identity=cv(doc,r['identity'],'account identity',issues)
        supported=aid==r['account_id'] and eid==r['entity_id'] and eid in supported_entities and identity is not None
        if not supported: issues.append('account identity/entity relationship differs from scoped graph or is unknown')
        else: supported_accounts.add(aid)
        accounts.append({'scope_ref':r['account_id'],'account_id':aid if supported else None,'entity_id':eid if supported else None,'identity':identity if supported else None,'evidence_status':'supplied-unverified'})
    buckets={}; links=[]
    for r in d['transactions']:
        val=amount(doc,r['amount'],'transaction '+r['transaction_id'],issues)
        checks=[cv(doc,r[k],r['transaction_id']+'.'+k,issues) for k in ('date_evidence','from_evidence','to_evidence','currency_evidence','id_evidence')]
        if checks!=[r['date'],r['from_account'],r['to_account'],r['currency'],r['transaction_id']]: issues.append(r['transaction_id']+' date/flow endpoints differ from exact source facts'); val=None
        if ({r['from_account'],r['to_account']}&scoped)-supported_accounts: issues.append(r['transaction_id']+' depends on unsupported account/entity relationship'); val=None
        b=buckets.setdefault(r['currency'],{'external_inflow':Decimal(0),'external_outflow':Decimal(0),'internal_transfer':Decimal(0),'unique_turnover':Decimal(0),'unquantified_transactions':[]})
        if val is None: b['unquantified_transactions'].append(r['transaction_id'])
        else:
            b['unique_turnover']+=val
            k='internal_transfer' if r['from_account'] in scoped and r['to_account'] in scoped else 'external_inflow' if r['to_account'] in scoped else 'external_outflow'
            b[k]+=val
        links.append({'transaction_id':r['transaction_id'],'from':r['from_account'],'to':r['to_account'],'currency':r['currency'],'amount':str(val) if val is not None else None,'date':r['date'],'source_refs':r['amount']['source_refs']})
    chronology=[]
    for r in sorted(d['chronology'],key=lambda r:r['date']):
        event=cv(doc,r['event'],'chronology event',issues); when=cv(doc,r['date_evidence'],'chronology date',issues)
        if when!=r['date']: issues.append('chronology date differs from source fact')
        chronology.append({'date':when,'event':event})
    propositions=[cv(doc,r,'narrative proposition',issues) for r in d['narrative_propositions']]
    if not d['transactions']: issues.append('No transaction population supplied; flow cannot be assessed')
    totals={c:{k:(str(v) if isinstance(v,Decimal) else v) for k,v in b.items()} for c,b in buckets.items()}
    payload={'scope':d['scope'],'entities':entities,'accounts':accounts,'flow_links':links,'currency_totals':totals,'proceeds_amount':None,'proceeds_status':'unknown-no-tracing-or-illicit-origin-method','chronology':chronology,'hypotheses':hypotheses(doc,d['hypotheses'],issues),'investigative_plan':[{**r,'execution':'not_performed'} for r in d['investigative_plan']],'narrative_propositions':propositions,'disposition':'human-owned','reportability':'human-owned'}
    return result(doc,SKILL,'case-flow-evidence/1.0',payload,issues,limitations=['Distinct case investigation; not scenario replay. Turnover counts each supplied unique transaction once; internal transfers are not fresh proceeds. No FX conversion, tracing attribution, guilt or reportability conclusion.'],handoffs=['suspicious-activity-report-drafter','sanctions-exposure-reviewer','enhanced-due-diligence-assessor'])


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
