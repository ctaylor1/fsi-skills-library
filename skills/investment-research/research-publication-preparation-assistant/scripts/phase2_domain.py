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
    if lineage is None: lineage=[{'operation':'Intended note scope matched to effective supplied policy profile, disclosure anchors, current restriction coverage and per-source distribution permissions','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
    return finish(doc,skill,result,issues=issues or [],lineage=lineage)

SKILL='research-publication-preparation-assistant'
def validate_document(doc):
    base(doc); n=obj(doc.get('note'),'note')
    for k in ('note_id','intended_audience','jurisdiction','research_type','institution'): text(n.get(k),'note.'+k)
    p=obj(doc.get('policy_profile'),'policy_profile')
    for k in ('profile_id','version','institution','jurisdiction','audience','research_type'): text(p.get(k),'policy_profile.'+k)
    day(p.get('effective_from'),'effective_from'); day(p.get('effective_to'),'effective_to'); cited(doc,p,'policy_profile'); require(p.get('applicability_status') in ('confirmed-supplied','unknown'),'unsupported applicability status')
    ds=rows(doc.get('disclosures'),'disclosures'); unique(ds,'disclosure_id','disclosures')
    for d in ds:
        obj(d,'disclosure'); text(d.get('disclosure_id'),'disclosure_id'); flag(d.get('required'),'required'); require(d.get('status') in ('present-supplied','absent','unknown'),'disclosure status invalid')
        if d['status']=='present-supplied': text(d.get('note_anchor'),'note_anchor'); text(d.get('supplied_text'),'supplied_text'); cited(doc,d,'disclosure')
    r=obj(doc.get('restricted_list_review'),'restricted_list_review'); require(r.get('status') in ('checked-supplied','unknown'),'restricted status invalid'); require(r.get('subject_restricted') is None or isinstance(r['subject_restricted'],bool),'subject_restricted boolean or null')
    if r['status']=='checked-supplied': day(r.get('snapshot_date'),'snapshot_date'); cited(doc,r,'restricted_list_review')
    rights=rows(doc.get('source_permissions'),'source_permissions'); unique(rights,'source_id','source_permissions'); known={s['source_id'] for s in doc['sources']}
    for r in rights:
        obj(r,'source_permission'); require(r.get('source_id') in known,'unknown licensed source'); require(r.get('status') in ('allowed-supplied','denied','unknown'),'permission status invalid'); day(r.get('valid_from'),'valid_from'); day(r.get('valid_to'),'valid_to')
        for k in ('audiences','purposes'):
            for x in rows(r.get(k),k): text(x,k)
        cited(doc,r,'source_permission')
def compute(doc):
    validate_document(doc); n=doc['note']; p=doc['policy_profile']; use=day(doc['use_on'],'use_on'); gaps=[]; checks=[]
    for a,b in (('institution','institution'),('jurisdiction','jurisdiction'),('intended_audience','audience'),('research_type','research_type')):
        if n[a]!=p[b]: gaps.append('policy profile '+b+' differs from intended note scope')
    if p['applicability_status']!='confirmed-supplied': gaps.append('applicability unresolved')
    if not day(p['effective_from'],'effective_from')<=use<=day(p['effective_to'],'effective_to'): gaps.append('policy profile not effective at requested use date')
    for d in doc['disclosures']:
        if d['required'] and d['status']!='present-supplied': gaps.append('required disclosure '+d['disclosure_id']+' absent or unknown')
        checks.append({'disclosure_id':d['disclosure_id'],'status':d['status'],'note_anchor':d.get('note_anchor'),'text_verified':False})
    if not doc['disclosures']: gaps.append('required disclosure inventory absent; completeness unestablished')
    r=doc['restricted_list_review']
    if r['status']!='checked-supplied' or r.get('subject_restricted') is None: gaps.append('restricted-list coverage unknown')
    elif r['subject_restricted']: gaps.append('subject on supplied restricted list; owner review required')
    elif day(r['snapshot_date'],'snapshot_date')!=use: gaps.append('restricted-list snapshot not current for requested use date')
    permissions={r['source_id']:r for r in doc['source_permissions']}; coverage=[]
    for s in doc['sources']:
        r=permissions.get(s['source_id']); ok=bool(r and r['status']=='allowed-supplied' and n['intended_audience'] in r['audiences'] and 'research-distribution' in r['purposes'] and day(r['valid_from'],'valid_from')<=use<=day(r['valid_to'],'valid_to'))
        coverage.append({'source_id':s['source_id'],'distribution_eligibility':'supplied-permission-match' if ok else 'not-established'})
        if not ok: gaps.append(s['source_id']+': intended distribution permission not established')
    return done(doc,SKILL,{'note_id':n['note_id'],'profile_id':p['profile_id'],'profile_version':p['version'],'disclosure_checks':checks,'source_permission_coverage':coverage,
        'gaps':gaps,'suggested_disposition':'ready-for-owner-review' if not gaps else 'gaps-for-owner-review','clearance_granted':False,'published':False,'distributed':False,
        'verification_scope':'supplied anchors/text and configuration assertions only; no authenticated legal applicability, actual note text or license verification'},gaps)
