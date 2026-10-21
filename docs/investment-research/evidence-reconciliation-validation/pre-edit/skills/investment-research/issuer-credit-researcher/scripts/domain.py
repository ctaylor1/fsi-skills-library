"""Bounded supplied-evidence research; no source authentication or execution."""
from datetime import date, datetime, timezone
from copy import deepcopy
from statistics import median
from analysis_contract import validate_base, number, require, rows, unique, references, finish
from research_runtime import temporal

def text(v,label):
    require(isinstance(v,str) and bool(v.strip()),label+' must be a non-empty string')
    return v
def obj(v,label):
    require(isinstance(v,dict),label+' must be an object'); return v
def day(v,label):
    text(v,label); require(len(v)==10,label+' must be YYYY-MM-DD'); return date.fromisoformat(v)
def stamp(v,label):
    text(v,label); require('T' in v,label+' must contain an intraday time')
    d=datetime.fromisoformat(v.replace('Z','+00:00')); require(d.tzinfo is not None,label+' requires timezone'); return d
def flag(v,label):
    require(isinstance(v,bool),label+' must be boolean'); return v
def amount(row,key,nullable=False,minimum=None):
    number(row.get(key),key,nullable=nullable,minimum=minimum); return row.get(key)
def cited(doc,row,label):
    require(isinstance(row.get('evidence_refs'),list) and bool(row['evidence_refs']),label+' requires nonempty evidence_refs')
    references(doc,row.get('evidence_refs'),label+'.evidence_refs')
def field_context(row,label):
    for k in ('currency','unit','accounting_basis','consolidation_scope'): text(row.get(k),label+'.'+k)
    p=obj(row.get('period'),label+'.period'); text(p.get('fiscal_calendar_id'),label+'.fiscal_calendar_id')
    a=day(p.get('start'),label+'.period.start'); b=day(p.get('end'),label+'.period.end'); require(a<=b,label+' period reversed')
def comparable(a,b):
    return all(a.get(k)==b.get(k) for k in ('currency','unit','accounting_basis','consolidation_scope','period'))
def base(doc):
    validate_base(doc,subject_types=('issuer','security'))
    require(doc.get('schema_version')=='ir-phase2/1.0','unsupported Phase 2 schema_version')
def done(doc,skill,result,issues=None,lineage=None):
    if lineage is None: lineage=[{'operation':'Debt/positive EBITDA; (debt-unrestricted cash)/positive EBITDA; EBITDA/positive interest; operating cash flow-capex; FFO/positive debt','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
    return finish(doc,skill,result,issues=issues or [],lineage=lineage)

SKILL='issuer-credit-researcher'
def validate_document(doc):
    base(doc); require(doc.get('issuer_profile')=='nonfinancial-corporate','only nonfinancial-corporate EBITDA analysis supported')
    f=obj(doc.get('financials'),'financials'); field_context(f,'financials'); cited(doc,f,'financials')
    cutoff=temporal(doc['knowledge_cutoff'])[1]
    cutoff_date=cutoff.date() if isinstance(cutoff,datetime) else cutoff
    require(day(f['period']['end'],'financials.period.end')<=min(day(doc['as_of'],'as_of'),cutoff_date),
            'financials reported period must end on or before as_of and knowledge_cutoff; forecast/scenario financials unsupported')
    for k in ('ebitda','gross_debt','unrestricted_cash','interest_expense','operating_cash_flow','capex','funds_from_operations'):
        amount(f,k,nullable=True,minimum=0 if k in ('gross_debt','unrestricted_cash','interest_expense','capex') else None)
    ins=rows(doc.get('instruments'),'instruments',nonempty=True); unique(ins,'instrument_id','instruments')
    for i,r in enumerate(ins):
        obj(r,'instrument');
        for k in ('instrument_id','issuer_id','estate_id','seniority','currency'): text(r.get(k),'instrument.'+k)
        amount(r,'principal',nullable=True,minimum=0); cited(doc,r,'instrument')
        gs=rows(r.get('guarantor_ids'),'guarantor_ids')
        for g in gs: text(g,'guarantor_id')
        require(len(gs)==len(set(gs)),'duplicate guarantor_id')
    adjustments=rows(doc.get('ebitda_adjustments',[]),'ebitda_adjustments')
    unique(adjustments,'adjustment_id','ebitda_adjustments')
    for a in adjustments:
        obj(a,'adjustment'); text(a.get('adjustment_id'),'adjustment_id'); text(a.get('rationale'),'rationale'); amount(a,'amount'); cited(doc,a,'adjustment')
    for r in rows(doc.get('risk_observations',[]),'risk_observations'):
        obj(r,'risk'); text(r.get('risk_id'),'risk_id'); text(r.get('category'),'risk.category'); text(r.get('observation'),'risk.observation'); cited(doc,r,'risk')
def compute(doc):
    validate_document(doc); f=doc['financials']; issues=[]
    e=f['ebitda']; adjusted=None if e is None else e+sum(x['amount'] for x in doc.get('ebitda_adjustments',[]))
    metrics={}
    for label,den in [('reported_ebitda',e),('analyst_adjusted_ebitda',adjusted)]:
        metrics[label]={'ebitda':den,'gross_leverage_x':f['gross_debt']/den if den is not None and den>0 and f['gross_debt'] is not None else None,
            'net_leverage_x':(f['gross_debt']-f['unrestricted_cash'])/den if den is not None and den>0 and f['gross_debt'] is not None and f['unrestricted_cash'] is not None else None,
            'interest_coverage_x':den/f['interest_expense'] if den is not None and f['interest_expense'] is not None and f['interest_expense']>0 else None}
        if any(v is None for v in metrics[label].values()): issues.append(label+': missing or nonpositive denominator; dependent ratios withheld')
    debt=f['gross_debt']; cash_flow={'free_cash_flow':f['operating_cash_flow']-f['capex'] if f['operating_cash_flow'] is not None and f['capex'] is not None else None,
        'ffo_to_debt':f['funds_from_operations']/debt if f['funds_from_operations'] is not None and debt is not None and debt>0 else None}
    structural=[]; subject=doc['subject'].get('issuer_id',doc['subject']['id'])
    for r in doc['instruments']:
        if r['issuer_id']!=subject and subject not in r['guarantor_ids']:
            structural.append({'instrument_id':r['instrument_id'],'issue':'separate legal issuer; no supplied upstream guarantee to subject','estate_id':r['estate_id'],'evidence_refs':r['evidence_refs']})
        if r['seniority']=='unknown': issues.append(r['instrument_id']+': legal priority unresolved')
    result={'financial_context':{k:f[k] for k in ('currency','unit','period','accounting_basis','consolidation_scope')},'credit_metrics':metrics,'cash_flow':cash_flow,
        'structural_risks':structural,'risk_observations':deepcopy(doc.get('risk_observations',[])),'ebitda_adjustments':deepcopy(doc.get('ebitda_adjustments',[])),
        'rating_assigned':False,'credit_decision':'not-made','legal_priority':'supplied-assertions-only'}
    return done(doc,SKILL,result,issues,[{'metric':'gross_leverage_x','formula':'gross_debt / EBITDA; positive EBITDA required','evidence_refs':f['evidence_refs']}])
