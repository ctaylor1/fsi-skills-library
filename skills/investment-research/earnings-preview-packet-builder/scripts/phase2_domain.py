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
    if lineage is None: lineage=[{'operation':'Comparable frozen baseline less frozen consensus; difference divided by absolute nonzero consensus','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
    return finish(doc,skill,result,issues=issues or [],lineage=lineage)

def row_knowledge(doc,row,release,baseline):
    asserted=stamp(row.get('known_at'),'row.known_at')
    index={s['source_id']:s for s in doc['sources']}
    for citation in row['evidence_refs']:
        known=stamp(index[citation['source_id']]['known_at'],'cited source known_at')
        require(known<=asserted,'cited source known after asserted observation vintage')
        if baseline: require(known<release,'baseline source must be frozen strictly before release')

def validate_metrics(doc,preview):
    base(doc); release=stamp(doc.get('release_at'),'release_at'); cutoff=stamp(doc['knowledge_cutoff'],'knowledge_cutoff')
    require(cutoff<release if preview else cutoff>=release,'knowledge cutoff inconsistent with preview/results')
    ms=rows(doc.get('metrics'),'metrics',nonempty=True); unique(ms,'metric_id','metrics')
    for m in ms:
        obj(m,'metric'); text(m.get('metric_id'),'metric_id'); require(m.get('direction') in ('higher-is-better','lower-is-better'),'unsupported direction')
        if not preview:
            r=obj(m.get('reported'),'reported'); field_context(r,'reported'); amount(r,'value',nullable=True); stamp(r.get('known_at'),'reported.known_at'); cited(doc,r,'reported'); require(release<=stamp(r['known_at'],'known_at')<=cutoff,'reported fact must be known at/after release and no later than cutoff'); row_knowledge(doc,r,release,False)
        bs=rows(m.get('baselines'),'baselines'); unique(bs,'kind','baselines')
        for b in bs:
            obj(b,'baseline'); require(b.get('kind') in ('consensus','whisper','guidance','model'),'unsupported baseline kind'); field_context(b,'baseline'); stamp(b.get('known_at'),'known_at'); cited(doc,b,'baseline')
            require(stamp(b['known_at'],'known_at')<release,'baseline must be frozen before release'); row_knowledge(doc,b,release,True)
            if preview: require(stamp(b['known_at'],'known_at')<=cutoff,'baseline known after preview cutoff')
            if 'low' in b or 'high' in b:
                require(b['kind']=='guidance','only guidance range supported'); amount(b,'low',nullable=True); amount(b,'high',nullable=True)
                if b['low'] is not None and b['high'] is not None: require(b['low']<=b['high'],'guidance range reversed')
            else: amount(b,'value',nullable=True)
def baseline_value(b):
    if 'low' in b or 'high' in b: return (b['low']+b['high'])/2 if b.get('low') is not None and b.get('high') is not None else None
    return b.get('value')

SKILL='earnings-preview-packet-builder'
def validate_document(doc): validate_metrics(doc,True)
def compute(doc):
    validate_document(doc); issues=[]; results=[]
    for m in doc['metrics']:
        baselines=deepcopy(m['baselines']); consensus=next((b for b in baselines if b['kind']=='consensus'),None); comparisons=[]
        for b in baselines:
            if b['kind']=='consensus': continue
            reason=None
            if consensus is None: reason='frozen consensus baseline missing'
            elif not comparable(b,consensus): reason='fiscal period, accounting basis, scope, unit or currency mismatch'
            a=baseline_value(b); c=baseline_value(consensus) if consensus else None
            if a is None or c is None: reason=reason or 'baseline value/range incomplete'
            comparisons.append({'baseline_kind':b['kind'],'versus':'consensus','delta':None if reason else a-c,'relative_gap':None if reason or c==0 else (a-c)/abs(c),'status':'withheld' if reason else 'prospective-setup-comparison','reason':reason})
            if reason: issues.append(m['metric_id']+': '+b['kind']+': '+reason)
        if not baselines: issues.append(m['metric_id']+': no frozen baselines')
        results.append({'metric_id':m['metric_id'],'frozen_baselines':baselines,'setup_comparisons':comparisons,'actual_surprise':'not-yet-observed'})
    return done(doc,SKILL,{'release_at':doc['release_at'],'freeze_cutoff':doc['knowledge_cutoff'],'metrics':results,'estimate_authorship':'supplied labeled baselines only; no house forecast invented','rating_or_target':'not-determined'},issues)
