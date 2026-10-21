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
    if lineage is None: lineage=[{'operation':'Signed numerator and denominator component sums; maximum threshold-ratio or minimum ratio-threshold; headroom times positive denominator','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
    return finish(doc,skill,result,issues=issues or [],lineage=lineage)

SKILL='covenant-headroom-analyzer'
def validate_document(doc):
    base(doc); ts=rows(doc.get('tests'),'tests',nonempty=True); unique(ts,'test_id','tests')
    for t in ts:
        obj(t,'test')
        for k in ('test_id','instrument_id','document_id','document_version','definition_id','accounting_basis','currency','unit'): text(t.get(k),'test.'+k)
        d=day(t.get('test_date'),'test_date'); require(d<=day(doc['as_of'],'as_of'),'future test date'); require(day(t.get('effective_from'),'effective_from')<=d,'test definition not yet effective')
        if t.get('effective_to') is not None: require(d<=day(t['effective_to'],'effective_to'),'test definition expired')
        require(t.get('application_status') in ('applicable-supplied','not-applicable-supplied','unknown'),'application_status invalid'); flag(t.get('definition_reviewed'),'definition_reviewed')
        require(t.get('operator') in ('maximum','minimum'),'operator must be maximum/minimum'); amount(t,'threshold',minimum=0); cited(doc,t,'test')
        for side in ('numerator','denominator'):
            z=obj(t.get(side),side); text(z.get('definition'),side+'.definition'); require(z.get('period')==t.get('period'),side+' period mismatch')
            p=obj(z.get('period'),'period'); require(day(p.get('start'),'period.start')<=day(p.get('end'),'period.end')<=d,'period reversed or after test date')
            rs=rows(z.get('components'),side+'.components',nonempty=True); unique(rs,'component_id',side)
            for r in rs:
                obj(r,'component'); text(r.get('component_id'),'component_id'); amount(r,'amount',nullable=True); require(type(r.get('sign')) is int and r['sign'] in (-1,1),'component sign must be -1/1'); cited(doc,r,'component')
def compute(doc):
    validate_document(doc); findings=[]; issues=[]
    for t in doc['tests']:
        gaps=[]; values={}
        if not t['definition_reviewed']: gaps.append('definition not reviewed')
        if t['application_status']!='applicable-supplied': gaps.append('test applicability not established or not applicable')
        for side in ('numerator','denominator'):
            rs=t[side]['components']; values[side]=sum(r['amount']*r['sign'] for r in rs) if all(r['amount'] is not None for r in rs) else None
        n,d=values['numerator'],values['denominator']
        if n is None or d is None: gaps.append('component value unknown')
        if d is not None and d<=0: gaps.append('nonpositive denominator; ratio and headroom withheld')
        ratio=None if gaps else n/d
        headroom=None if gaps else (t['threshold']-ratio if t['operator']=='maximum' else ratio-t['threshold'])
        amount_headroom=None if headroom is None else headroom*d
        findings.append({'test_id':t['test_id'],'instrument_id':t['instrument_id'],'document_id':t['document_id'],'document_version':t['document_version'],
            'definition_id':t['definition_id'],'test_date':t['test_date'],'period':t['period'],'operator':t['operator'],'threshold':t['threshold'],**values,
            'ratio_x':ratio,'ratio_headroom_x':headroom,'numerator_headroom_amount':amount_headroom,
            'indicative_result':'not-evaluable' if ratio is None else ('within-supplied-threshold' if headroom>=0 else 'outside-supplied-threshold'),
            'legal_compliance':'not-determined','evidence_refs':deepcopy(t['evidence_refs']),'unresolved_issues':gaps})
        issues.extend(t['test_id']+': '+g for g in gaps)
    return done(doc,SKILL,{'tests':findings,'legal_compliance_determined':False,'waiver_or_cure_effect':'not-evaluated'},issues)
