"""Domain-owned, offline supplied-evidence method; no professional/action authority."""
from __future__ import annotations
from decimal import Decimal, localcontext
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, number, decimal, day, records, strings, unique_ids)

SKILL = "anti-bribery-corruption-reviewer"
OBJECT_TYPES = {'abc_engagement_review'}
METHOD = "benefit-service-payment-review/1.0"
T = text
B = lambda v: isinstance(v, bool)
N = number
I = lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0
D = lambda v: day(v) is not None
L = strings
OBJECT_SCHEMAS = {}
RECORD_SCHEMAS = {'engagements': ('engagement_id', {
    'benefit_type': lambda v: v in {'intermediary','gift','hospitality','donation','payment'},
    'recipient': T, 'services': T, 'delivered_services': T, 'amount': N,
    'benchmark_amount': N, 'currency': lambda v: text(v) and len(v) == 3 and v.isalpha() and v.isupper(),
    'benchmark_currency': lambda v: text(v) and len(v) == 3 and v.isalpha() and v.isupper(),
    'proportionality_limit': N, 'government_link': B,
    'due_diligence_complete': B, 'policy_applies': B, 'counterevidence': L})}

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
    issues, reviews = [], []
    if not doc['data']['engagements']:
        issues.append('No engagements supplied; benefit/payment assessment is unassessed')
    for row in doc['data']['engagements']:
        label = row['engagement_id']
        v = values(doc, row, RECORD_SCHEMAS['engagements'][1], label, issues)
        reasons, ratio, comparison = [], None, None
        if v['policy_applies'] is not True:
            reasons.append('applicable institutional ABC policy is missing or not established')
        if v['due_diligence_complete'] is not True:
            reasons.append('intermediary/recipient diligence is incomplete or unknown')
        if v['government_link'] is True:
            reasons.append('government link requires Legal/ABC review; it does not establish wrongdoing')
        if v['services'] is not None and v['delivered_services'] is not None and v['services'] != v['delivered_services']:
            reasons.append('delivered services differ from the contracted service description')
        required = ['amount','benchmark_amount','currency','benchmark_currency','proportionality_limit','policy_applies']
        if any(v[k] is None for k in required) or v['policy_applies'] is not True:
            reasons.append('proportionality comparison withheld pending criteria and comparable evidence')
        elif v['currency'] != v['benchmark_currency'] or v['benchmark_amount'] == 0:
            reasons.append('benchmark currency mismatch or zero benchmark prevents proportionality ratio')
        else:
            with localcontext() as context:
                context.prec = 1000
                raw_ratio = decimal(v['amount']) / decimal(v['benchmark_amount'])
                ratio = format(raw_ratio.quantize(Decimal('0.000000000001')), 'f')
                comparison = raw_ratio <= decimal(v['proportionality_limit'])
            if not comparison:
                reasons.append('compensation/benefit exceeds the supplied proportionality criterion')
        issues.extend(label + ': ' + reason for reason in reasons)
        reviews.append({'engagement_id': label, 'evidence': v, 'amount_to_benchmark_ratio': ratio,
            'ratio_precision': '12 decimal places', 'within_supplied_criterion': comparison,
            'review_state': 'needs-ABC-review' if reasons or any(x is None for x in v.values()) else 'evidence-reconciled-draft',
            'review_reasons': reasons, 'counterevidence': v['counterevidence'],
            'required_review': ['Confirm legitimate service/benefit rationale and actual recipient',
                'Resolve diligence, official links and contrary evidence with Legal/ABC owner'],
            'legal_guilt_determination': 'not-performed', 'payment_approved': False})
    return result(doc, SKILL, METHOD, {'engagement_reviews': reviews}, issues,
        ['Institutional policy/benchmark comparison is not an FCPA/FEPA legal determination.',
         'No default benefit limit, legal threshold, risk weight or payment approval.'],
        ['third-party-risk-assessor','procurement-sourcing-assistant','misconduct-investigation-assistant'])

