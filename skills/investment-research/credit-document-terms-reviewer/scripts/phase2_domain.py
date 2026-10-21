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
    if lineage is None: lineage=[{'operation':'Effective executed predecessor chain; reviewed add/replace/delete with original value hash matching','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
    return finish(doc,skill,result,issues=issues or [],lineage=lineage)

SKILL='credit-document-terms-reviewer'
def validate_document(doc):
    base(doc); flag(doc.get('document_inventory_complete'),'document_inventory_complete'); text(doc.get('instrument_id'),'instrument_id'); ds=rows(doc.get('documents'),'documents',nonempty=True); unique(ds,'version','documents')
    for d in ds:
        obj(d,'document')
        for k in ('document_id','version'): text(d.get(k),k)
        day(d.get('effective_date'),'effective_date'); flag(d.get('executed'),'executed'); cited(doc,d,'document')
        if d.get('supersedes_version') is not None: text(d['supersedes_version'],'supersedes_version')
        ts=rows(d.get('terms'),'terms'); unique(ts,'term_id','terms')
        for t in ts:
            obj(t,'term'); text(t.get('term_id'),'term_id'); text(t.get('field'),'field'); text(t.get('raw_text'),'raw_text'); require(t.get('interpretation_status') in ('reviewed-explicit','unresolved'),'interpretation_status invalid'); cited(doc,t,'term')
        cs=rows(d.get('changes'),'changes'); unique(cs,'term_id','changes')
        for c in cs:
            obj(c,'change'); text(c.get('term_id'),'term_id'); require(c.get('action') in ('replace','delete','add'),'invalid change action'); flag(c.get('reviewed'),'reviewed'); cited(doc,c,'change')
            if c['action'] in ('replace','delete'): text(c.get('prior_value_hash'),'prior_value_hash')
            if c['action']!='delete':
                n=obj(c.get('new_term'),'new_term'); require(n.get('term_id')==c['term_id'],'new_term identity differs'); text(n.get('field'),'field'); text(n.get('raw_text'),'raw_text'); require(n.get('interpretation_status') in ('reviewed-explicit','unresolved'),'interpretation_status invalid'); cited(doc,n,'new_term')
def compute(doc):
    from native_integrity import canonical_hash
    validate_document(doc); active={}; issues=[] if doc['document_inventory_complete'] else ['supplied governing document inventory incomplete']; chain=[]; seen=set(); previous=None; chain_gap=False; asof=day(doc['as_of'],'as_of')
    for d in sorted(doc['documents'],key=lambda x:(x['effective_date'],x['version'])):
        if day(d['effective_date'],'effective_date')>asof: issues.append(d['version']+': not effective at as_of; not applied'); continue
        if not d['executed']: issues.append(d['version']+': unexecuted document not applied'); continue
        if previous is not None and d.get('supersedes_version')!=previous: issues.append(d['version']+': governing version chain unresolved; no changes applied'); chain_gap=True; continue
        if previous is None and d.get('supersedes_version') is not None: issues.append(d['version']+': missing predecessor document'); chain_gap=True; continue
        if previous is not None and d['terms']: issues.append(d['version']+': amendment supplied with base terms; use explicit change log'); continue
        for t in d['terms']:
            active[t['term_id']]={'term':deepcopy(t),'document_id':d['document_id'],'document_version':d['version'],'status':t['interpretation_status']}
        for c in d['changes']:
            current=active.get(c['term_id']); reason=None
            if not c['reviewed']: reason='change log not reviewed'
            elif c['action']=='add' and current: reason='add collides with existing term'
            elif c['action'] in ('replace','delete') and not current: reason='prior term absent'
            elif c['action'] in ('replace','delete') and canonical_hash(current['term'].get('value'))!=c['prior_value_hash']: reason='prior value hash mismatch'
            if reason:
                issues.append(c['term_id']+': '+reason)
                if current: current['status']='unresolved-amendment'
                else: active[c['term_id']]={'term':{'term_id':c['term_id'],'field':'unknown','raw_text':'unresolved supplied change','value':None,'evidence_refs':c['evidence_refs']},'document_id':d['document_id'],'document_version':d['version'],'status':'unresolved-amendment'}
                continue
            if c['action']=='delete': del active[c['term_id']]
            else: active[c['term_id']]={'term':deepcopy(c['new_term']),'document_id':d['document_id'],'document_version':d['version'],'status':c['new_term']['interpretation_status']}
        chain.append({'document_id':d['document_id'],'version':d['version'],'effective_date':d['effective_date'],'evidence_refs':d['evidence_refs']}); previous=d['version']; seen.add(previous)
    terms=[]
    for key,r in sorted(active.items()):
        v=deepcopy(r); v['term']['value']=v['term'].get('value') if r['status']=='reviewed-explicit' and not chain_gap else None
        if r['status']!='reviewed-explicit' or chain_gap: issues.append(key+': legal interpretation unresolved; normalized value withheld')
        terms.append(v)
    if not chain: issues.append('no eligible executed governing document chain')
    return done(doc,SKILL,{'document_inventory_complete':doc['document_inventory_complete'],'instrument_id':doc['instrument_id'],'governing_version':None if chain_gap else previous,'applied_version_chain':chain,'effective_terms':terms,
        'consolidation_method':'supplied reviewed explicit changes with prior-value hashes','legal_effect_established':False,'covenant_compliance':'not-tested'},issues)
