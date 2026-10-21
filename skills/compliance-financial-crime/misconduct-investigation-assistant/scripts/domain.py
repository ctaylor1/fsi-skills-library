"""Domain-owned, offline supplied-evidence method; no professional/action authority."""
from __future__ import annotations
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, number, day, records, strings, unique_ids)

SKILL = "misconduct-investigation-assistant"
OBJECT_TYPES = {'misconduct_investigation'}
METHOD = "mandated-allegation-evidence-plan/1.0"
T = text
B = lambda v: isinstance(v, bool)
N = number
I = lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0
D = lambda v: day(v) is not None
L = strings
OBJECT_SCHEMAS = {'mandate': {'authorized': B, 'allegation_ids': L, 'allowed_evidence_types': L, 'legal_owner': T, 'hr_owner': T}}
RECORD_SCHEMAS = {
    'allegations': ('allegation_id', {'description': T}),
    'events': ('event_id', {'allegation_id': T, 'occurred_on': D, 'proposition': T, 'evidence_type': T,
        'hypothesis': T, 'polarity': lambda v: v in {'supports','contradicts','neutral','unknown'}}),
    'plans': ('plan_id', {'allegation_id': T, 'evidence_type': T, 'purpose': T})}


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
    pass
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
    m = values(doc, doc['data']['mandate'], OBJECT_SCHEMAS['mandate'], 'mandate', issues)
    supplied_ids = [a['allegation_id'] for a in doc['data']['allegations']]
    mandate_ok = all(v is not None for v in m.values()) and m['authorized'] is True and set(supplied_ids).issubset(m['allegation_ids'])
    if not supplied_ids:
        issues.append('No actual allegation supplied; investigation is unassessed')
        mandate_ok = False
    if not mandate_ok:
        issues.append('Exact supplied investigation mandate is missing, unauthorized or excludes an allegation')
    allegations = []
    for row in doc['data']['allegations']:
        v = values(doc, row, RECORD_SCHEMAS['allegations'][1], row['allegation_id'], issues)
        allegations.append({'allegation_id': row['allegation_id'], 'description': v['description'], 'status': 'allegation-only'})
    events, hypothesis_map = [], {}
    for row in doc['data']['events']:
        v = values(doc, row, RECORD_SCHEMAS['events'][1], row['event_id'], issues)
        reasons = []
        if not mandate_ok or v['allegation_id'] not in supplied_ids or (m['allowed_evidence_types'] is not None and v['evidence_type'] not in m['allowed_evidence_types']):
            reasons.append('event outside exact supplied mandate/allegation/evidence scope')
        if v['occurred_on'] is not None:
            refs = row['occurred_on']['source_refs']
            receipt_dates = [day(s['received_at']) for s in doc['sources'] if s['source_ref'] in refs]
            if day(v['occurred_on']) > min([day(doc['as_of']),day(doc['knowledge_cutoff'])] + receipt_dates):
                reasons.append('observed event exceeds assessment, cutoff or source receipt date')
        if any(x is None for x in v.values()):
            reasons.append('event has unsupported/unknown material fields')
        issues.extend(row['event_id'] + ': ' + reason for reason in reasons)
        eligible = mandate_ok and not reasons
        events.append({'event_id': row['event_id'], 'evidence': v if mandate_ok else None,
            'eligible_for_timeline': eligible, 'issues': reasons})
        if eligible:
            key = (v['allegation_id'],v['hypothesis'])
            h = hypothesis_map.setdefault(key, {'allegation_id': key[0], 'hypothesis': key[1], 'supports': [], 'contradicts': [], 'neutral': []})
            h[v['polarity']].append(row['event_id'])
    events.sort(key=lambda e: ((e['evidence'] or {}).get('occurred_on') or '9999-12-31', e['event_id']))
    hypotheses = list(hypothesis_map.values())
    for h in hypotheses:
        h['contradiction_unresolved'] = bool(h['supports'] and h['contradicts'])
        h['conclusion'] = 'not-adjudicated'
        if h['contradiction_unresolved']:
            issues.append(h['allegation_id'] + ': hypothesis has both support and counterevidence: ' + h['hypothesis'])
    plans = []
    for row in doc['data']['plans']:
        v = values(doc, row, RECORD_SCHEMAS['plans'][1], row['plan_id'], issues)
        scoped = mandate_ok and all(x is not None for x in v.values()) and v['allegation_id'] in supplied_ids and v['evidence_type'] in m['allowed_evidence_types']
        if not scoped:
            issues.append(row['plan_id'] + ': proposed evidence/interview request is outside or lacks exact mandate')
        plans.append({'plan_id': row['plan_id'], 'proposed_request': v if mandate_ok else None,
            'within_supplied_mandate': scoped, 'execution': 'not-performed',
            'owner_review': 'Legal/HR confirms collection, privilege, confidentiality, whistleblower protection and interview approach'})
    if mandate_ok and not any(e['eligible_for_timeline'] for e in events):
        issues.append('No supported timeline evidence; allegations cannot become findings')
    if mandate_ok and not plans:
        issues.append('No scoped evidence/interview plan supplied; investigation planning is unassessed')
    return result(doc, SKILL, METHOD, {'mandate_evidence_consistent': mandate_ok, 'allegations': allegations,
        'timeline': events, 'hypotheses': hypotheses, 'evidence_interview_plan': plans,
        'legal_or_HR_adjudication': 'not-performed', 'external_contacts': 'not-performed'}, issues,
        ['Timeline and hypothesis comparison is scoped to supplied evidence; no guilt, privilege or employment determination.'],
        ['anti-bribery-corruption-reviewer','privacy-impact-assessment-assistant','compliance-remediation-evidence-reviewer'])
