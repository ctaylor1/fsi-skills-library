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
    if lineage is None: lineage=[{'operation':'Unweighted median of eligible matched peer spreads; target spread minus median','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
    return finish(doc,skill,result,issues=issues or [],lineage=lineage)

SKILL='credit-relative-value-analyzer'
def validate_document(doc):
    base(doc); require(obj(doc.get('target'),'target').get('issuer_id')==doc['subject'].get('issuer_id',doc['subject']['id']),'target issuer differs from subject'); amount(doc,'duration_tolerance',minimum=0); amount(doc,'max_price_age_days',minimum=0)
    require(type(doc['max_price_age_days']) is int,'max_price_age_days must be integer')
    allrows=[obj(doc.get('target'),'target')]+rows(doc.get('peers'),'peers',nonempty=True); unique(allrows,'security_id','securities')
    for r in allrows:
        for k in ('security_id','issuer_id','currency','option_profile','rating_group','spread_basis','unit'): text(r.get(k),'security.'+k)
        require(r['unit']=='bps','spread unit must be bps'); amount(r,'spread_bps',nullable=True); amount(r,'duration',nullable=True,minimum=0); day(r.get('price_date'),'price_date'); stamp(r.get('known_at'),'known_at'); cited(doc,r,'security')
def compute(doc):
    validate_document(doc); target=doc['target']; included=[]; excluded=[]; issues=[]; cut=stamp(doc['knowledge_cutoff'],'knowledge_cutoff'); asof=day(doc['as_of'],'as_of')
    def timing(r):
        return (asof-day(r['price_date'],'price_date')).days<0 or (asof-day(r['price_date'],'price_date')).days>doc['max_price_age_days'] or stamp(r['known_at'],'known_at')>cut
    target_ok=not timing(target) and target['spread_bps'] is not None and target['duration'] is not None
    if not target_ok: issues.append('target spread/duration absent or price stale/future; relative comparison withheld')
    for r in doc['peers']:
        reasons=[k+' mismatch' for k in ('currency','option_profile','rating_group','spread_basis') if r[k]!=target[k]]
        if timing(r): reasons.append('stale/future price or knowledge beyond cutoff')
        if r['spread_bps'] is None or r['duration'] is None: reasons.append('spread/duration unknown')
        elif target['duration'] is not None and abs(r['duration']-target['duration'])>doc['duration_tolerance']: reasons.append('outside supplied duration tolerance')
        if r['issuer_id']==target['issuer_id']: reasons.append('same issuer excluded from independent peer median')
        if reasons: excluded.append({'security_id':r['security_id'],'reasons':reasons})
        else: included.append(deepcopy(r))
    m=median([r['spread_bps'] for r in included]) if included and target_ok else None
    if m is None: issues.append('no eligible target/peer comparison')
    return done(doc,SKILL,{'target_security_id':target['security_id'],'included_peers':included,'excluded_peers':excluded,'peer_median_spread_bps':m,
        'target_minus_peer_median_bps':None if m is None else target['spread_bps']-m,'assessment':'descriptive-spread-difference-only','rating_assigned':False,'investment_recommendation':'not-made',
        'duration_method':'eligibility tolerance; no curve interpolation or option model'},issues)
