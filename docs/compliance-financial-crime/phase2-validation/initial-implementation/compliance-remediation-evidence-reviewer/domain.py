"""Domain-owned, offline supplied-evidence method; no professional/action authority."""
from __future__ import annotations
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, number, day, records, strings, unique_ids)

SKILL = "compliance-remediation-evidence-reviewer"
OBJECT_TYPES = {'compliance_remediation_review'}
METHOD = "finding-criterion-retest-sustainability/1.0"
T = text
B = lambda v: isinstance(v, bool)
N = number
I = lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0
D = lambda v: day(v) is not None
L = strings
OBJECT_SCHEMAS = {'finding': {'finding_id': T, 'version': T, 'accepted': B, 'affected_scope': L,
    'closure_criterion_ids': L, 'closure_owner': T, 'closure_authority': B}}
RECORD_SCHEMAS = {
 'criteria': ('criterion_id', {'finding_id': T, 'finding_version': T, 'required_scope': L,
    'required_operation_from': D, 'required_operation_to': D, 'minimum_observations': I}),
 'evidence': ('evidence_id', {'criterion_id': T, 'finding_id': T, 'finding_version': T, 'scope': L,
    'type': lambda v: v in {'design','implementation','retest','sustained-operation'},
    'operation_from': D, 'operation_to': D, 'observations': I, 'failures': I, 'evidence_complete': B})}


def validate(doc):
    errors = validate_common(doc, OBJECT_TYPES)
    if not isinstance(doc, dict) or not isinstance(doc.get('data'), dict):
        return errors, []
    if set(doc) - {'request_id','object_id','object_type','as_of','knowledge_cutoff','workflow','sources','data'}:
        errors.append('undeclared native top-level fields')
    data = doc['data']
    if set(data) != set(OBJECT_SCHEMAS) | set(RECORD_SCHEMAS):
        errors.append('data must contain exactly the declared domain collections/objects')
    for collection, (id_key, schema) in RECORD_SCHEMAS.items():
        rows = data.get(collection)
        if not records(rows) or not unique_ids(rows, id_key):
            errors.append(collection + ': distinct nonempty record IDs required')
            continue
        for row in rows:
            if set(row) != {id_key} | set(schema):
                errors.append(collection + ': undeclared or missing record fields')
            for field, predicate in schema.items():
                claim = row.get(field)
                if not isinstance(claim, dict) or set(claim) != {'value','source_refs','fact_ids'}:
                    errors.append(collection + '.' + field + ': exact claim object required')
                    continue
                if not strings(claim['source_refs']) or not strings(claim['fact_ids']):
                    errors.append(collection + '.' + field + ': reference lists must contain strings')
                if claim['value'] is not None and not predicate(claim['value']):
                    errors.append(collection + '.' + field + ': unsupported value type or enum')
    for name, schema in OBJECT_SCHEMAS.items():
        row = data.get(name)
        if not isinstance(row, dict):
            errors.append(name + ': domain object required')
            continue
        if set(row) != set(schema):
            errors.append(name + ': undeclared or missing fields')
        for field, predicate in schema.items():
            claim = row.get(field)
            if not isinstance(claim, dict) or set(claim) != {'value','source_refs','fact_ids'}:
                errors.append(name + '.' + field + ': exact claim object required')
                continue
            if not strings(claim['source_refs']) or not strings(claim['fact_ids']):
                errors.append(name + '.' + field + ': reference lists must contain strings')
            if claim['value'] is not None and not predicate(claim['value']):
                errors.append(name + '.' + field + ': unsupported value type or enum')
    if errors:
        return errors, []
    for name, start, end in [('criteria','required_operation_from','required_operation_to'),('evidence','operation_from','operation_to')]:
        for row in data.get(name, []) if records(data.get(name)) else []:
            a, b = row.get(start, {}).get('value'), row.get(end, {}).get('value')
            if day(a) and day(b) and day(a) > day(b):
                errors.append(name + ': operating period ends before start')
    for row in data.get('evidence', []) if records(data.get('evidence')) else []:
        o, f = row.get('observations', {}).get('value'), row.get('failures', {}).get('value')
        if isinstance(o, int) and isinstance(f, int) and f > o:
            errors.append('retest failures exceed observed items')
    return errors, []

def values(doc, row, fields, label, issues):
    resolved = {}
    for field in fields:
        resolved[field], gaps = claim_value(doc, row[field], label + '.' + field)
        issues.extend(gaps)
    return resolved

def compute(doc):
    require_valid(doc, validate)
    issues = []
    f = values(doc, doc['data']['finding'], OBJECT_SCHEMAS['finding'], 'finding', issues)
    supplied_criterion_ids = [row['criterion_id'] for row in doc['data']['criteria']]
    original_criterion_inventory_complete = f['closure_criterion_ids'] is not None and bool(f['closure_criterion_ids']) and len(f['closure_criterion_ids']) == len(set(f['closure_criterion_ids'])) and set(f['closure_criterion_ids']) == set(supplied_criterion_ids)
    accepted_finding = all(v is not None for v in f.values()) and f['accepted'] is True and f['closure_authority'] is True and bool(f['affected_scope']) and original_criterion_inventory_complete
    if not original_criterion_inventory_complete:
        issues.append('Original closure-criterion inventory is missing or does not match every supplied criterion')
    if not accepted_finding:
        issues.append('Original accepted finding, affected scope, closure owner or authority evidence missing/inconsistent')
    criteria = []
    for row in doc['data']['criteria']:
        c = values(doc, row, RECORD_SCHEMAS['criteria'][1], row['criterion_id'], issues)
        reasons = []
        linkage = all(c[k] is not None for k in c) and c['finding_id'] == f['finding_id'] and c['finding_version'] == f['version'] and f['affected_scope'] is not None and set(c['required_scope']).issubset(f['affected_scope']) and bool(c['required_scope']) and c['minimum_observations'] > 0
        if not linkage:
            reasons.append('criterion lacks exact finding/version, affected scope, period or positive observation requirement')
        if c['required_operation_to'] is not None and day(c['required_operation_to']) > min(day(doc['as_of']),day(doc['knowledge_cutoff'])):
            reasons.append('required sustained-operation window is not yet observable')
        matched, retest_ok, sustained_ok = [], False, False
        for erow in doc['data']['evidence']:
            base_fields = ['criterion_id','finding_id','finding_version','scope','type','evidence_complete']
            e = values(doc, erow, base_fields, erow['evidence_id'], issues)
            operating_type = e['type'] in {'retest','sustained-operation'}
            operation_fields = ['operation_from','operation_to','observations','failures']
            if operating_type:
                e.update(values(doc, erow, operation_fields, erow['evidence_id'], issues))
            else:
                # Design/implementation artifacts make no operating observation claim.
                # Their unused operating fields stay detached and are never evidence.
                e.update({key: None for key in operation_fields})
            if e['criterion_id'] != row['criterion_id']:
                continue
            gaps = []
            aligned = linkage and all(e[key] is not None for key in base_fields) and e['finding_id'] == f['finding_id'] and e['finding_version'] == f['version'] and set(e['scope']) == set(c['required_scope'])
            if not aligned:
                gaps.append('evidence finding/version/scope or material fields do not match exact criterion')
            if e['evidence_complete'] is not True:
                gaps.append('evidence completeness is negative or unknown')
            if operating_type and (e['failures'] is None or e['failures'] > 0):
                gaps.append('retest/operation failures unresolved or unknown')
            if operating_type and linkage and (e['observations'] is None or e['observations'] < c['minimum_observations']):
                gaps.append('insufficient observed items for supplied criterion')
            if e['operation_to'] is not None:
                receipts = [day(s['received_at']) for s in doc['sources'] if s['source_ref'] in erow['operation_to']['source_refs']]
                if day(e['operation_to']) > min([day(doc['as_of']),day(doc['knowledge_cutoff'])] + receipts):
                    gaps.append('actual operating evidence extends beyond assessment/cutoff/receipt')
            if operating_type and (e['operation_from'] is None or e['operation_to'] is None):
                gaps.append('actual operating evidence dates are missing or unsupported')
            operating = operating_type and aligned and not gaps
            covers_window = operating and day(e['operation_from']) <= day(c['required_operation_from']) and day(e['operation_to']) >= day(c['required_operation_to'])
            if e['type'] == 'retest' and operating:
                retest_ok = True
            if e['type'] == 'sustained-operation' and covers_window:
                sustained_ok = True
            if e['type'] == 'sustained-operation' and not covers_window:
                gaps.append('sustained evidence does not cover the full supplied operating window')
            issues.extend(erow['evidence_id'] + ': ' + gap for gap in gaps)
            matched.append({'evidence_id':erow['evidence_id'], 'evidence':e, 'criterion_aligned':aligned,
                'operating_evidence_eligible':operating, 'covers_required_window':covers_window, 'issues':gaps,
                'stage_limitation': 'Design/implementation does not establish retest or sustained operation; operating fields are not applied' if e['type'] in {'design','implementation'} else None})
        if not retest_ok:
            reasons.append('no supported successful retest against exact original criterion')
        if not sustained_ok:
            reasons.append('no supported sustained-operation evidence over full criterion window')
        ready = accepted_finding and not reasons and retest_ok and sustained_ok
        issues.extend(row['criterion_id'] + ': ' + reason for reason in reasons)
        criteria.append({'criterion_id':row['criterion_id'], 'criterion':c, 'evidence_reviews':matched,
            'successful_retest_evidenced':retest_ok, 'sustained_operation_evidenced':sustained_ok,
            'criterion_evidence_sufficient_for_owner_review':ready, 'review_issues':reasons})
    actual_criteria = {row['criterion_id'] for row in doc['data']['criteria']}
    for erow in doc['data']['evidence']:
        ref, gaps = claim_value(doc, erow['criterion_id'], erow['evidence_id'] + '.criterion_id')
        issues.extend(gaps)
        if ref not in actual_criteria:
            issues.append(erow['evidence_id'] + ': evidence is not linked to an original criterion')
    if not criteria:
        issues.append('No original closure criteria supplied; closure evidence unassessed')
    ready = accepted_finding and bool(criteria) and all(c['criterion_evidence_sufficient_for_owner_review'] for c in criteria) and not issues and not doc['workflow']['unresolved_issues']
    return result(doc, SKILL, METHOD, {'original_finding':f, 'original_finding_evidence_consistent':accepted_finding,
        'original_criterion_inventory_complete':original_criterion_inventory_complete,
        'criterion_reviews':criteria, 'closure_evidence_sufficient_for_owner_review':ready,
        'finding_closed':False, 'required_review':['Original finding owner accepts exact criteria and scope',
            'Authorized closure reviewer independently assesses retest, sustained operation, failures and coverage']}, issues,
        ['Document freshness/design improvement does not demonstrate operating effectiveness or close a finding.',
         'Supplied closure authority is unverified; no actual closure or system-of-record update.'],
        ['compliance-control-testing-assistant','regulatory-exam-response-packager','policy-procedure-gap-analyzer'])
