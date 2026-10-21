"""Domain-owned, offline supplied-evidence method; no professional/action authority."""
from __future__ import annotations
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, number, day, records, strings, unique_ids)

SKILL = "financial-promotion-reviewer"
OBJECT_TYPES = {'financial_promotion'}
METHOD = "content-context-claim-review/1.0"
T = text
B = lambda v: isinstance(v, bool)
N = number
I = lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0
D = lambda v: day(v) is not None
L = strings
OBJECT_SCHEMAS = {
 'promotion': {'content_id': T, 'content_version': T, 'content': T, 'sector': T, 'product': T,
  'channel': T, 'audience': T, 'jurisdiction': T, 'perimeter': lambda v: v in {'applicable','not-applicable','unknown'},
  'profile_id': T, 'profile_supported': B, 'profile_authority': T, 'profile_basis': T,
  'use_from': D, 'use_to': D},
 'approval': {'actor': T, 'actor_authorized': B, 'content_id': T, 'content_version': T, 'audience': T,
  'product': T, 'sector': T, 'jurisdiction': T, 'channel': T, 'profile_id': T,
  'authority_scope': L, 'approved_on': D, 'use_from': D, 'use_to': D}}
RECORD_SCHEMAS = {
 'claims': ('claim_id', {'text': T, 'substantiation': T, 'substantiation_state': lambda v: v in {'supported','unsupported','unknown'}, 'risk_balance': B}),
 'disclosures': ('disclosure_id', {'text': T, 'required': B, 'present': B, 'visible': B, 'conditions_met': B})}
SUPPORTED_METHOD_PROFILES = {'institution-content-review/1.0','uk-fca-content-review/1.0','us-finra-member-content-review/1.0'}


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
    for name in ['approval','promotion']:
        row = data.get(name, {})
        if isinstance(row, dict):
            start, end = row.get('use_from'), row.get('use_to')
            a = start.get('value') if isinstance(start, dict) else None
            b = end.get('value') if isinstance(end, dict) else None
            if day(a) and day(b) and day(a) > day(b):
                errors.append(name + ' use period ends before start')
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
    p = values(doc, doc['data']['promotion'], OBJECT_SCHEMAS['promotion'], 'promotion', issues)
    a = values(doc, doc['data']['approval'], OBJECT_SCHEMAS['approval'], 'approval', issues)
    profile_ok = all(v is not None for v in p.values()) and p['profile_supported'] is True and p['profile_id'] in SUPPORTED_METHOD_PROFILES
    if p['profile_id'] == 'uk-fca-content-review/1.0' and p['jurisdiction'] != 'UK':
        profile_ok = False
    if p['profile_id'] == 'us-finra-member-content-review/1.0' and (p['jurisdiction'] != 'US' or p['sector'] != 'FINRA-member'):
        profile_ok = False
    if p['jurisdiction'] != doc['workflow']['context']['jurisdiction']:
        profile_ok = False
    if not profile_ok:
        issues.append('Unsupported or incomplete sector/product/perimeter profile; no legal applicability inferred')
    if p['perimeter'] != 'applicable':
        issues.append('Promotion perimeter not established as applicable; Legal review required')
    comparisons = []
    for row in doc['data']['claims']:
        v = values(doc, row, RECORD_SCHEMAS['claims'][1], row['claim_id'], issues)
        reasons = []
        matches = None
        if p['content'] is not None and v['text'] is not None:
            if v['text'] not in p['content']:
                reasons.append('claim text not present in the exact supplied content')
        else:
            reasons.append('content/claim statement unavailable')
        if v['text'] is not None and v['substantiation'] is not None:
            matches = v['text'] == v['substantiation']
            if not matches:
                reasons.append('promotion claim differs from the exact supplied substantiation statement')
        if v['substantiation_state'] != 'supported':
            reasons.append('claim support has not been established by the supplied reviewer evidence')
        if v['risk_balance'] is not True:
            reasons.append('supplied risk/benefit balance review is negative or unknown')
        issues.extend(row['claim_id'] + ': ' + reason for reason in reasons)
        comparisons.append({'claim_id': row['claim_id'], 'evidence': v, 'source_statement_matches': matches,
            'review_issues': reasons, 'remediation': ['Replace unsupported wording with a source-bound statement and required conditions',
                'Have the appropriate product/promotions owner review risk prominence and audience comprehension'] if reasons else []})
    if not comparisons:
        issues.append('No claim inventory supplied; content completeness unassessed')
    disclosures = []
    for row in doc['data']['disclosures']:
        v = values(doc, row, RECORD_SCHEMAS['disclosures'][1], row['disclosure_id'], issues)
        reasons = []
        if v['required'] is None:
            reasons.append('applicability of this disclosure is unknown')
        if v['required'] is True and (v['present'] is not True or v['visible'] is not True or v['conditions_met'] is not True):
            reasons.append('required disclosure is absent, obscured, conditionality unmet or unknown')
        if v['present'] is True and (p['content'] is None or v['text'] is None or v['text'] not in p['content']):
            reasons.append('disclosure presence claim conflicts with exact content')
        issues.extend(row['disclosure_id'] + ': ' + reason for reason in reasons)
        disclosures.append({'disclosure_id': row['disclosure_id'], 'evidence': v, 'review_issues': reasons,
            'remediation': 'Insert the source-backed applicable wording visibly in this channel and resolve conditions with product owner' if reasons else None})
    if not disclosures:
        issues.append('No disclosure inventory supplied; required disclosure completeness unassessed')
    authority_reasons = []
    for key in ['content_id','content_version','audience','product','sector','jurisdiction','channel','profile_id']:
        if a[key] is None or p[key] is None or a[key] != p[key]:
            authority_reasons.append('approval differs or lacks exact ' + key)
    if a['actor_authorized'] is not True or a['actor'] is None or a['authority_scope'] is None or 'approve-financial-promotion' not in a['authority_scope']:
        authority_reasons.append('approval actor authority is unknown or inconsistent')
    if any(v is None for v in [a['use_from'],a['use_to'],p['use_from'],p['use_to']]) or not (day(a['use_from']) <= day(p['use_from']) <= day(p['use_to']) <= day(a['use_to'])):
        authority_reasons.append('approval evidence does not cover the exact proposed use period')
    if a['approved_on'] is None:
        authority_reasons.append('approval date is unknown')
    else:
        receipts = [day(s['received_at']) for s in doc['sources'] if s['source_ref'] in doc['data']['approval']['approved_on']['source_refs']]
        if day(a['approved_on']) > min([day(doc['as_of']),day(doc['knowledge_cutoff'])] + receipts):
            authority_reasons.append('asserted approval is dated after assessment/cutoff/source receipt')
    issues.extend('approval: ' + reason for reason in authority_reasons)
    return result(doc, SKILL, METHOD, {'content_context': p, 'profile_method_supported': profile_ok,
        'claim_reviews': comparisons, 'disclosure_reviews': disclosures, 'supplied_approval_evidence': a,
        'approval_scope_consistent': not authority_reasons, 'approval_issues': authority_reasons,
        'approval_granted': False, 'dissemination': 'not-performed',
        'decision_points': ['Legal confirms jurisdiction, sector/product perimeter, exceptions and sourcebook',
            'Authorized promotions reviewer decides approval for this exact content, audience and use period']}, issues,
        ['Native profiles support exact supplied criteria/content comparison, not complete sector legal-rule coverage.',
         'Source statement matching does not independently establish semantic substantiation or disclosure sufficiency.'],
        ['communications-compliance-reviewer','customer-conduct-outcomes-reviewer','regulatory-obligation-control-mapper'])
