"""Domain-owned, offline supplied-evidence method; no professional/action authority."""
from __future__ import annotations
from decimal import Decimal
from fractions import Fraction
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, number, day, records, strings, unique_ids)

SKILL = "customer-conduct-outcomes-reviewer"
OBJECT_TYPES = {'customer_conduct_review'}
METHOD = "cohort-harm-coverage-review/1.0"
T = text
B = lambda v: isinstance(v, bool)
N = number
I = lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0
D = lambda v: day(v) is not None
L = strings
OBJECT_SCHEMAS = {'review': {'product': T, 'distribution_role': T, 'window_from': D, 'window_to': D,
    'metric': T, 'numerator_definition': T, 'denominator_definition': T, 'segmentation_basis': T,
    'vulnerability_method': T, 'expected_cohorts': L}}
UNIT_FIELDS = ('population_unit', 'numerator_unit', 'denominator_unit')
RECORD_SCHEMAS = {'cohorts': ('cohort_id', {'population': I, 'observed': I, 'harms': I, 'vulnerable': B,
    'value_barriers': L, 'support_barriers': L, 'threshold_rate': lambda v: number(v, high=1)})}


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
        allowed = set(schema) | (set(UNIT_FIELDS) if name == 'review' else set())
        if not set(schema).issubset(row) or set(row) - allowed:
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
        for field in UNIT_FIELDS if name == 'review' else ():
            if field not in row:
                continue
            claim = row[field]
            if not isinstance(claim, dict) or set(claim) != {'value','source_refs','fact_ids'} or not strings(claim.get('source_refs')) or not strings(claim.get('fact_ids')) or (claim.get('value') is not None and not text(claim['value'])):
                errors.append(name + '.' + field + ': sourced unit claim required')
    if errors:
        return errors, []
    row = data.get('review', {})
    if isinstance(row, dict):
        start, end = row.get('window_from'), row.get('window_to')
        a = start.get('value') if isinstance(start, dict) else None
        b = end.get('value') if isinstance(end, dict) else None
        if day(a) and day(b) and day(a) > day(b):
            errors.append('observation window ends before start')
    for row in data.get('cohorts', []) if records(data.get('cohorts')) else []:
        p = row['population']['value'] if isinstance(row.get('population'), dict) else None
        o = row['observed']['value'] if isinstance(row.get('observed'), dict) else None
        h = row['harms']['value'] if isinstance(row.get('harms'), dict) else None
        if isinstance(p, int) and isinstance(o, int) and o > p:
            errors.append('observed denominator exceeds eligible cohort population')
        if isinstance(o, int) and isinstance(h, int) and h > o:
            errors.append('harm numerator exceeds observed denominator')
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
    review = values(doc, doc['data']['review'], OBJECT_SCHEMAS['review'], 'review', issues)
    for field in UNIT_FIELDS:
        review[field], gaps = claim_value(doc, doc['data']['review'].get(field), 'review.' + field)
        issues.extend(gaps)
    metric_scope_ok = all(v is not None for v in review.values()) and bool(review['expected_cohorts'])
    units_ok = all(review[field] == 'unique-customers' for field in UNIT_FIELDS)
    if not units_ok:
        issues.append('Supported harm/coverage proportions require source-bound unique-customers units for numerator, observed denominator and population; mixed event/customer or other units are unsupported')
        metric_scope_ok = False
    if review['window_to'] is not None and day(review['window_to']) > min(day(doc['as_of']),day(doc['knowledge_cutoff'])):
        issues.append('Observation window extends beyond assessment/cutoff; actual outcomes incomplete')
        metric_scope_ok = False
    if not metric_scope_ok:
        issues.append('Metric, numerator/denominator, segmentation/vulnerability method or complete observation window unestablished')
    actual_ids = [r['cohort_id'] for r in doc['data']['cohorts']]
    missing = None if review['expected_cohorts'] is None else sorted(set(review['expected_cohorts']) - set(actual_ids))
    if missing:
        issues.append('Expected cohorts have no observations: ' + ', '.join(missing))
    unexpected = None if review['expected_cohorts'] is None else sorted(set(actual_ids) - set(review['expected_cohorts']))
    if unexpected:
        issues.append('Cohorts outside supplied population definition: ' + ', '.join(unexpected))
    cohorts = []
    for row in doc['data']['cohorts']:
        v = values(doc, row, RECORD_SCHEMAS['cohorts'][1], row['cohort_id'], issues)
        harm_rate, coverage, within_threshold = None, None, None
        reasons = []
        if not metric_scope_ok or v['observed'] is None or v['observed'] == 0 or v['harms'] is None:
            reasons.append('missing/zero observed denominator or missing numerator; harm rate withheld')
        else:
            harm_rate = v['harms'] / v['observed']
            if v['threshold_rate'] is not None:
                within_threshold = Fraction(v['harms'], v['observed']) <= Fraction(Decimal(str(v['threshold_rate'])))
                if not within_threshold:
                    reasons.append('observed harm rate exceeds supplied criterion')
        if not metric_scope_ok or v['population'] is None or v['population'] == 0 or v['observed'] is None:
            reasons.append('population/observation coverage unavailable; zero population is not good outcomes')
        else:
            coverage = v['observed'] / v['population']
            if v['observed'] < v['population']:
                reasons.append('partial observations; remaining eligible customers unassessed')
        if v['value_barriers']:
            reasons.append('supplied value barriers require product/value-owner review')
        if v['support_barriers']:
            reasons.append('supplied support barriers require customer-support review')
        issues.extend(row['cohort_id'] + ': ' + reason for reason in reasons)
        cohorts.append({'cohort_id': row['cohort_id'], 'evidence': v, 'observed_harm_rate': harm_rate,
            'observation_coverage': coverage, 'within_supplied_harm_criterion': within_threshold,
            'vulnerable_customer_segment': v['vulnerable'], 'review_issues': reasons,
            'review_action': 'Review this segment, missing outcomes and value/support barriers with product/conduct owners',
            'population_good_outcomes_conclusion': 'not-established'})
    if not cohorts:
        issues.append('No cohort outcomes supplied; thematic conduct is unassessed')
    return result(doc, SKILL, METHOD, {'review_scope': review, 'cohort_metrics': cohorts,
        'metric_definition_evidence_consistent':metric_scope_ok,
        'missing_expected_cohorts': missing, 'cohorts_outside_defined_population': unexpected,
        'aggregation': 'separate cohort metrics; overlapping cohorts are not summed',
        'individual_complaint_resolution': 'not-performed'}, issues,
        ['Rates describe supplied observed outcomes; sampling/selection bias and causal harm are not resolved.',
         'No default metric, universal conduct threshold, weights, value model or population extrapolation.'],
        ['complaint-resolution-assistant','financial-promotion-reviewer','compliance-remediation-evidence-reviewer'])
