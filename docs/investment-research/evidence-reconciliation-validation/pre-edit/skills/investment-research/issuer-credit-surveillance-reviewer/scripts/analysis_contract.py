"""Phase 2 supplied-evidence guards. No authentication or action authority (MIT)."""
from __future__ import annotations
import copy, math, json
from native_integrity import attach_source, canonical_hash
from research_runtime import (require, text, calendar_date, temporal, validate_context,
                              validate_dossier, source_reasons)

VERSION = '2.0.0'

def load_json(raw):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'duplicate JSON object key: '+key);result[key]=value
        return result
    def constant(value):raise ValueError('non-finite JSON constant: '+value)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)

def number(value, label, nullable=False, minimum=None):
    if value is None and nullable: return None
    require(not isinstance(value, bool) and isinstance(value, (int,float)) and math.isfinite(value), label+' must be a finite JSON number')
    if minimum is not None: require(value>=minimum,label+' is below minimum')
    return value

def rows(value, label, nonempty=False):
    require(isinstance(value,list),label+' must be a list')
    if nonempty:require(bool(value),label+' must not be empty')
    return value

def unique(records, key, label):
    seen=set()
    for row in records:
        require(isinstance(row,dict) and text(row.get(key)),label+' requires '+key)
        require(row[key] not in seen,label+' duplicate '+key)
        seen.add(row[key])
    return records

def references(doc, refs, label='evidence_refs'):
    rows(refs,label)
    known={s['source_id'] for s in doc['sources']};seen=set()
    for ref in refs:
        require(isinstance(ref,dict) and text(ref.get('source_id')) and text(ref.get('locator')),label+' needs source_id and precise locator')
        require(ref['source_id'] in known,label+' unknown source_id')
        pair=(ref['source_id'],ref['locator']);require(pair not in seen,label+' duplicate citation');seen.add(pair)
    declared={(r.get('source_id'),r.get('locator')) for r in doc.get('evidence_refs',[]) if isinstance(r,dict)}
    require(seen<=declared,label+' references must appear in top-level evidence_refs for permission gating')
    return refs

def validate_base(doc, subject_types=('issuer','security')):
    validate_context(doc)
    def basis_guard(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key in {'currency','unit','units','accounting_basis','consolidation_scope'} and isinstance(item,str):
                    require(item.strip().lower()!='unknown','unknown '+key+' cannot support analytical calculations')
                basis_guard(item)
        elif isinstance(value,list):
            for item in value:basis_guard(item)
    basis_guard(doc)
    if subject_types is not None: require(doc['subject']['type'] in subject_types,'unsupported analysis subject type')
    calendar_date(doc.get('use_on'))
    # Reuse the maintained source schema and permission/date validation without
    # pretending every analytical method is a dossier or discarding input fields.
    projection={k:copy.deepcopy(doc[k]) for k in ('request_id','purpose','audience','subject','as_of','use_on','knowledge_cutoff','information_barrier','sources') if k in doc}
    projection['subject']={'type':'issuer','id':doc['subject']['id']}
    for key in ('event_time','pre_event','unresolved_issues'):
        if key in doc:projection[key]=copy.deepcopy(doc[key])
    projection.update(claims=[],coverage=[],contradictions=[])
    validate_dossier(projection)
    references(doc,doc.get('evidence_refs'), 'evidence_refs')
    return doc

def evidence_gaps(doc):
    refs=doc['evidence_refs'];sources={s['source_id']:s for s in doc['sources']}
    gaps=[]
    if not refs:gaps.append('No evidence references supplied for analytical inputs')
    for ref in refs:
        for reason in source_reasons(sources[ref['source_id']],doc):
            gaps.append(ref['source_id']+': '+reason)
    return sorted(set(gaps))

def finish(doc, skill, results, issues=None, lineage=None):
    validate_base(doc,subject_types=None)
    gaps=evidence_gaps(doc)
    issues=list(doc.get('unresolved_issues',[]))+list(issues or [])+gaps
    require(all(text(x) for x in issues),'issues must be nonempty strings')
    canonical_hash(results);canonical_hash(lineage or [])
    used={r['source_id'] for r in doc['evidence_refs']}
    output={'schema_version':'ir-analysis/2.0','method_id':skill,'method_version':VERSION,
        'request_id':doc['request_id'],'subject':copy.deepcopy(doc['subject']),
        'as_of':doc['as_of'],'knowledge_cutoff':doc['knowledge_cutoff'],'use_on':doc['use_on'],
        'purpose':doc['purpose'],'audience':doc['audience'],
        'results':None if gaps else copy.deepcopy(results),'status':'partial' if issues else 'complete-for-supplied-scope',
        'calculation_lineage':[] if gaps else copy.deepcopy(lineage or []),
        'unresolved_issues':sorted(set(issues)),
        'evidence_refs':[] if gaps else copy.deepcopy(doc['evidence_refs']),
        'source_register':[] if gaps else [{k:copy.deepcopy(s[k]) for k in ('source_id','version','known_at','locator','kind')} for s in doc['sources'] if s['source_id'] in used],
        'source_assurance':'supplied-not-authenticated','coverage_assurance':'supplied-inventory-only',
        'professional_acceptance':'not-established','authority_granted':False,'action_taken':False,
        'approval':'not_requested','execution':'not_performed'}
    return attach_source(output,doc)
