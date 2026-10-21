"""Domain-owned, offline supplied-evidence method; no professional/action authority."""
from __future__ import annotations
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, number, day, records, strings, unique_ids)

SKILL = "information-barrier-reviewer"
OBJECT_TYPES = {'information_barrier_review'}
METHOD = "exact-wall-crossing-scope/1.0"
T = text
B = lambda v: isinstance(v, bool)
N = number
I = lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0
D = lambda v: day(v) is not None
L = strings
OBJECT_SCHEMAS = {}
RECORD_SCHEMAS = {'requests': ('request_id', {
    'operation': lambda v: v in {'wall-crossing','access','list-change'},
    'person_id': T, 'information_ids': L,
    'classification': lambda v: v in {'public','confidential','MNPI','unknown'},
    'purpose': T, 'need_to_know': B, 'starts_on': D, 'ends_on': D,
    'authority_person_id': T, 'authority_information_ids': L, 'authority_purpose': T,
    'authority_starts_on': D, 'authority_ends_on': D, 'authority_scope': L,
    'restrictions': L, 'list_changes': L})}

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
    for row in data.get('requests', []) if records(data.get('requests')) else []:
        if row.get('classification', {}).get('value') == 'MNPI' and doc['workflow']['classification'] != 'mnpi':
            errors.append('MNPI request requires mnpi workflow classification')
        for start, end in [('starts_on','ends_on'),('authority_starts_on','authority_ends_on')]:
            a, b = row.get(start, {}).get('value'), row.get(end, {}).get('value')
            if day(a) and day(b) and day(a) > day(b):
                errors.append('request/authority period ends before it starts')
    return errors, []

def values(doc, row, fields, label, issues):
    resolved = {}
    for field in fields:
        resolved[field], gaps = claim_value(doc, row[field], label + '.' + field)
        issues.extend(gaps)
    return resolved

def compute(doc):
    require_valid(doc, validate)
    issues, reviews = [], []
    if not doc['data']['requests']:
        issues.append('No requests supplied; wall-crossing/access scope is unassessed')
    for row in doc['data']['requests']:
        label = row['request_id']
        v = values(doc, row, RECORD_SCHEMAS['requests'][1], label, issues)
        unknown = [key for key, value in v.items() if value is None]
        mismatches = []
        if not unknown:
            if v['person_id'] != v['authority_person_id']:
                mismatches.append('actor differs from supplied authority actor')
            if v['purpose'] != v['authority_purpose']:
                mismatches.append('purpose differs from supplied authority purpose')
            if not set(v['information_ids']).issubset(v['authority_information_ids']) or not v['information_ids']:
                mismatches.append('information set is empty or outside supplied authority')
            if v['operation'] not in v['authority_scope']:
                mismatches.append('operation outside supplied authority scope')
            if not (day(v['authority_starts_on']) <= day(v['starts_on']) <= day(v['ends_on']) <= day(v['authority_ends_on'])):
                mismatches.append('requested dates outside supplied authority period')
            if v['need_to_know'] is not True:
                mismatches.append('need-to-know is not established')
            if v['classification'] != 'public' and not v['restrictions']:
                mismatches.append('nonpublic information has no supplied restrictions')
            if v['operation'] == 'list-change' and not v['list_changes']:
                mismatches.append('list-change request has no exact proposed list changes')
        reasons = mismatches + ['unsupported or missing ' + field for field in unknown]
        issues.extend(label + ': ' + reason for reason in mismatches)
        reviews.append({'request_id': label, 'scope': v, 'scope_consistent_with_supplied_authority': None if unknown else not mismatches,
            'review_state': 'needs-control-room-review' if reasons else 'scope-consistent-draft',
            'reasons': reasons, 'decision_points': ['Control room reviews materiality/nonpublic classification and current restrictions',
                'Authorized owner adjudicates this exact actor, information set, purpose and period'], 'access_granted': False, 'list_changed': False})
    return result(doc, SKILL, METHOD, {'request_reviews': reviews}, issues,
        ['Comparison is against supplied authority, not authenticated access permission or legal materiality.'],
        ['employee-trading-preclearance-reviewer','market-surveillance-alert-investigator','conflicts-of-interest-reviewer'])

