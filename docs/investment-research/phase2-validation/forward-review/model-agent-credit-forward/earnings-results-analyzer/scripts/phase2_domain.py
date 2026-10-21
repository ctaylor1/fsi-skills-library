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
    if lineage is None: lineage=[{'operation':'Reported actual less each frozen comparable baseline; difference divided by absolute nonzero baseline with supplied direction and tolerance','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
    return finish(doc,skill,result,issues=issues or [],lineage=lineage)

def validate_metrics(doc,preview):
    base(doc); release=stamp(doc.get('release_at'),'release_at'); cutoff=stamp(doc['knowledge_cutoff'],'knowledge_cutoff')
    require(cutoff<release if preview else cutoff>=release,'knowledge cutoff inconsistent with preview/results')
    ms=rows(doc.get('metrics'),'metrics',nonempty=True); unique(ms,'metric_id','metrics')
    for m in ms:
        obj(m,'metric'); text(m.get('metric_id'),'metric_id'); require(m.get('direction') in ('higher-is-better','lower-is-better'),'unsupported direction')
        if not preview:
            r=obj(m.get('reported'),'reported'); field_context(r,'reported'); amount(r,'value',nullable=True); stamp(r.get('known_at'),'reported.known_at'); cited(doc,r,'reported'); require(stamp(r['known_at'],'known_at')<=cutoff,'reported fact known after cutoff')
        bs=rows(m.get('baselines'),'baselines'); unique(bs,'kind','baselines')
        for b in bs:
            obj(b,'baseline'); require(b.get('kind') in ('consensus','whisper','guidance','model'),'unsupported baseline kind'); field_context(b,'baseline'); stamp(b.get('known_at'),'known_at'); cited(doc,b,'baseline')
            require(stamp(b['known_at'],'known_at')<release,'baseline must be frozen before release')
            if preview: require(stamp(b['known_at'],'known_at')<=cutoff,'baseline known after preview cutoff')
            if 'low' in b or 'high' in b:
                require(b['kind']=='guidance','only guidance range supported'); amount(b,'low',nullable=True); amount(b,'high',nullable=True)
                if b['low'] is not None and b['high'] is not None: require(b['low']<=b['high'],'guidance range reversed')
            else: amount(b,'value',nullable=True)
def baseline_value(b):
    if 'low' in b or 'high' in b: return (b['low']+b['high'])/2 if b.get('low') is not None and b.get('high') is not None else None
    return b.get('value')

SKILL='earnings-results-analyzer'
def validate_document(doc):
    validate_metrics(doc,False); amount(doc,'classification_tolerance',minimum=0); require(doc['classification_tolerance']<=1,'classification_tolerance exceeds one')
def compute(doc):
    validate_document(doc); issues=[]; results=[]
    for m in doc['metrics']:
        actual=m['reported']; comparisons=[]
        for b in m['baselines']:
            reason=None; v=baseline_value(b)
            if not comparable(actual,b): reason='fiscal period, accounting basis, consolidation scope, unit or currency mismatch'
            if actual['value'] is None or v is None: reason=reason or 'actual or baseline value/range incomplete'
            delta=None if reason else actual['value']-v; pct=None if reason or v==0 else delta/abs(v)
            effective=None if pct is None else pct*(1 if m['direction']=='higher-is-better' else -1)
            cls=None if effective is None else ('Beat' if effective>doc['classification_tolerance'] else 'Miss' if effective<-doc['classification_tolerance'] else 'In-line')
            if not reason and v==0: reason='zero baseline: absolute delta only; percent/classification withheld'
            comparisons.append({'baseline_kind':b['kind'],'baseline_value':v,'absolute_delta':delta,'surprise_fraction':pct,'classification':cls,
                'evidence_refs':deepcopy(actual['evidence_refs']+b['evidence_refs']),'reason':reason,'baseline_known_at':b['known_at']})
            if reason: issues.append(m['metric_id']+': '+b['kind']+': '+reason)
        if not comparisons: issues.append(m['metric_id']+': no frozen pre-event baseline')
        results.append({'metric_id':m['metric_id'],'reported':deepcopy(actual),'comparisons':comparisons})
    return done(doc,SKILL,{'release_at':doc['release_at'],'metric_results':results,'baseline_scope':'simultaneous consensus, whisper, guidance midpoint and supplied model; no substituted vintages','investment_call':'not-made'},issues)
