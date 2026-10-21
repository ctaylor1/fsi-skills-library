"""Bounded supplied-evidence research; no source authentication or execution."""
from datetime import date, datetime, timezone
from copy import deepcopy
from statistics import median
from analysis_contract import validate_base, number, require, rows, unique, references, finish

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
    if lineage is None: lineage=[{'operation':'Within-estate collateral and general-priority waterfalls; equal-priority claims pro rata to remaining claim/cap','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
    return finish(doc,skill,result,issues=issues or [],lineage=lineage)

SKILL='credit-recovery-scenario-analyzer'
def validate_document(doc):
    base(doc); es=rows(doc.get('estates'),'estates',nonempty=True); unique(es,'estate_id','estates'); estate_ids={e.get('estate_id') for e in es}; pools={}
    for e in es:
        obj(e,'estate'); text(e.get('estate_id'),'estate_id'); text(e.get('currency'),'currency'); text(e.get('unit'),'unit'); amount(e,'unencumbered_value',minimum=0); amount(e,'estate_costs',minimum=0); cited(doc,e,'estate')
        ps=rows(e.get('collateral_pools'),'collateral_pools'); unique(ps,'pool_id','collateral_pools')
        for p in ps:
            text(p.get('pool_id'),'pool_id'); require(p['pool_id'] not in pools,'pool_id must be globally unique'); amount(p,'value',minimum=0); flag(p.get('release_surplus_to_estate'),'release_surplus_to_estate'); cited(doc,p,'pool'); pools[p['pool_id']]=e['estate_id']
    cs=rows(doc.get('claims'),'claims',nonempty=True); unique(cs,'claim_id','claims')
    for c in cs:
        obj(c,'claim'); text(c.get('claim_id'),'claim_id'); require(c.get('estate_id') in estate_ids,'claim estate unknown'); amount(c,'amount',minimum=0); require(type(c.get('priority')) is int and c['priority']>=1,'priority must be positive integer'); cited(doc,c,'claim')
        e=next(x for x in es if x['estate_id']==c['estate_id']); require(c.get('currency')==e['currency'] and c.get('unit')==e['unit'],'claim currency/unit differs from estate')
        if c.get('pool_id') is not None:
            require(pools.get(c['pool_id'])==c['estate_id'],'collateral pool outside claim estate'); amount(c,'collateral_cap',minimum=0); require(c['collateral_cap']<=c['amount'],'collateral cap exceeds claim'); require(type(c.get('collateral_priority')) is int and c['collateral_priority']>=1,'collateral_priority required')
            require(c.get('deficiency_allowed') is None or isinstance(c['deficiency_allowed'],bool),'deficiency_allowed must be boolean or unknown')
def compute(doc):
    validate_document(doc); issues=[]; estates=[]
    for e in doc['estates']:
        cs=[c for c in doc['claims'] if c['estate_id']==e['estate_id']]; paid={c['claim_id']:0. for c in cs}; cash=max(0,e['unencumbered_value']-e['estate_costs']); unrecovered_cost=max(0,e['estate_costs']-e['unencumbered_value']); pool_results=[]; unknown=False
        for p in e['collateral_pools']:
            available=p['value']; pc=[c for c in cs if c.get('pool_id')==p['pool_id']]
            for rank in sorted({c['collateral_priority'] for c in pc}):
                group=[c for c in pc if c['collateral_priority']==rank]; total=sum(c['collateral_cap'] for c in group); distributed=min(available,total)
                for c in group: paid[c['claim_id']]+=distributed*c['collateral_cap']/total if total else 0
                available-=distributed
            if p['release_surplus_to_estate']: cash+=available
            pool_results.append({'pool_id':p['pool_id'],'distributed':p['value']-available,'surplus':available,'surplus_released':p['release_surplus_to_estate']})
        # Costs on unencumbered estate assets only. A shortfall does not invade collateral without a supplied legal allocation.
        if unrecovered_cost: issues.append(e['estate_id']+': costs exceed unencumbered value; legal cost allocation unresolved'); unknown=True
        collateral_paid=dict(paid)
        unsecured=[]
        for c in cs:
            remaining=c['amount']-paid[c['claim_id']]
            if c.get('pool_id') is None or c.get('deficiency_allowed') is True: unsecured.append((c,remaining))
            elif c.get('deficiency_allowed') is None and remaining>1e-9: issues.append(c['claim_id']+': deficiency claim eligibility unknown; general-estate waterfall withheld'); unknown=True
        if not unknown:
            for rank in sorted({c['priority'] for c,_ in unsecured}):
                group=[(c,v) for c,v in unsecured if c['priority']==rank]; total=sum(v for _,v in group); distributed=min(cash,total)
                for c,v in group: paid[c['claim_id']]+=distributed*v/total if total else 0
                cash-=distributed
        recovery=[{'claim_id':c['claim_id'],'claim_amount':c['amount'],'recovery_amount':None if unknown else paid[c['claim_id']],'known_collateral_recovery_amount':collateral_paid[c['claim_id']],'recovery_pct':paid[c['claim_id']]/c['amount'] if c['amount']>0 and not unknown else None,'general_waterfall_status':'withheld' if unknown else 'computed-under-supplied-priorities'} for c in cs]
        estates.append({'estate_id':e['estate_id'],'currency':e['currency'],'unit':e['unit'],'claims':recovery,'collateral_pools':pool_results,'residual_unallocated':cash,'estate_costs_paid_from_unencumbered':min(e['estate_costs'],e['unencumbered_value'])})
    return done(doc,SKILL,{'estates':estates,'cross_estate_transfers':[],'guarantee_recoveries':'not-invented; separate supplied estate claims required','legal_outcome':'hypothetical-supplied-waterfall-only','recommendation':'not-made'},issues)
