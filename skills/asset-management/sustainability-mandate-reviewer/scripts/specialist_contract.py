"""Bounded supplied-engine result challenge for AM specialist reviews (MIT).

No pricing engine is invoked. A passing comparison is not institutional approval.
"""
from foundation_contract import D, date_value, exact, require_sources, text, validate_actual_date
from native_integrity import canonical_hash

def validate_specialist_common(doc):
    """Phase4 financial inputs preserve decimal lexemes; earlier schemas unchanged."""
    from foundation_contract import validate_common
    errors = validate_common(doc)
    if errors: return errors
    def inspect(value):
        if isinstance(value, float):
            raise ValueError('specialist numeric inputs require exact decimal strings or integers, not JSON floats')
        if isinstance(value, dict):
            for child in value.values(): inspect(child)
        elif isinstance(value, list):
            for child in value: inspect(child)
    try: inspect(doc)
    except ValueError as exc: errors.append(str(exc))
    return errors


VERSION = 'investment-specialist-engine/1.0'
PIN_FIELDS = ('engine_id', 'engine_version', 'method_id', 'method_version', 'model_version')
CONTEXT_FIELDS = ('object_id', 'as_of', 'knowledge_cutoff', 'currency')


def _pinned(value):
    return text(value) and value.strip().lower() not in {'latest', 'unknown', 'n/a'}


def _metrics(values, *, benchmark=False):
    if not isinstance(values, list) or not values or len(values) > 10000:
        raise ValueError('nonempty bounded engine metric list required')
    result = {}
    for row in values:
        if not isinstance(row, dict) or not text(row.get('id')) or not text(row.get('unit')) or row['id'] in result:
            raise ValueError('engine metrics require unique identity and explicit unit')
        if 'value' in row:
            # Preserve source lexical precision for financial engine comparisons.
            if not isinstance(row['value'], (str, int)) or isinstance(row['value'], bool):
                raise ValueError('engine values must be exact decimal strings or integers')
            D(row['value'])
        if benchmark:
            if not isinstance(row.get('tolerance'), (str, int)) or isinstance(row['tolerance'], bool) or D(row['tolerance']) < 0:
                raise ValueError('nonnegative exact benchmark tolerance required')
        result[row['id']] = row
    return result


@exact
def review_engine(doc, request, record, benchmark):
    """Bind full engine request, versions, coverage and independent supplied challenge.

    request: PIN_FIELDS, CONTEXT_FIELDS, purpose, source_ref, acceptance_ref,
    input(object), expected_metrics[{id,unit}]. record: same pins/context,
    request_hash, status, source_ref, observed_on, values[{id,unit,value}],
    unresolved_issues. benchmark: request_hash, benchmark_id, version, method,
    independent_from_engine:true, source_ref, observed_on,
    values[{id,unit,value,tolerance}]. Missing records return unavailable, never
    an alternative price. Every result remains supplied-unverified.
    """
    if not isinstance(request, dict):
        raise ValueError('explicit engine request required')
    if any(not _pinned(request.get(k)) for k in PIN_FIELDS + ('purpose',)):
        raise ValueError('engine identity, method and model versions must be pinned')
    if any(request.get(k) != doc.get(k) for k in CONTEXT_FIELDS):
        raise ValueError('engine request context differs from review')
    if not isinstance(request.get('input'), dict) or not request['input']:
        raise ValueError('detached outcome-relevant engine input required')
    require_sources(doc, [request.get('source_ref'), request.get('acceptance_ref')])
    expected = _metrics(request.get('expected_metrics'))
    if any('value' in row for row in expected.values()):
        raise ValueError('expected metric inventory must not supply engine result values')
    digest = canonical_hash(request)
    result = {'contract_version': VERSION, 'request_hash': digest, 'status': 'unavailable',
              'comparisons': [], 'values': None, 'eligible_for_review': False,
              'engine_invoked': False, 'engine_approval_authenticated': False,
              'benchmark_independence_authenticated': False, 'issues': []}
    if record is None or benchmark is None:
        result['issues'] = ['Complete engine result and independent benchmark are both required; no fallback calculation.']
        return result
    if not isinstance(record, dict) or not isinstance(benchmark, dict):
        raise ValueError('engine result and benchmark must be objects or null')
    for pair in (record, benchmark):
        require_sources(doc, [pair.get('source_ref')])
        validate_actual_date(doc, pair.get('observed_on'), pair['source_ref'])
        if pair.get('request_hash') != digest:
            raise ValueError('engine or benchmark input hash differs from full request')
        if date_value(pair['observed_on']) < date_value(request['as_of']):
            raise ValueError('engine observation predates its valuation date')
    if any(record.get(k) != request[k] for k in PIN_FIELDS + CONTEXT_FIELDS):
        raise ValueError('engine result model/method/version or scope differs from request')
    if record.get('status') not in {'complete', 'partial', 'unsupported', 'unavailable', 'failed'}:
        raise ValueError('unsupported engine result status')
    if not isinstance(record.get('unresolved_issues'), list) or any(not text(v) for v in record['unresolved_issues']):
        raise ValueError('engine unresolved_issues must be explicit strings')
    if any(not _pinned(benchmark.get(k)) for k in ('benchmark_id', 'version', 'method')):
        raise ValueError('independent benchmark identity/version/method required')
    if benchmark.get('independent_from_engine') is not True or benchmark['source_ref'] == record['source_ref']:
        raise ValueError('separate independently designated benchmark evidence required')
    issues = list(record['unresolved_issues'])
    if record['status'] != 'complete':
        result.update(status=record['status'], issues=issues + ['Engine result is not complete; dependent values withheld.'])
        return result
    actual = _metrics(record.get('values'))
    check = _metrics(benchmark.get('values'), benchmark=True)
    if set(actual) != set(expected) or set(check) != set(expected):
        raise ValueError('engine/benchmark coverage differs from expected inventory')
    for identity, spec in expected.items():
        left, right = actual[identity], check[identity]
        if left['unit'] != spec['unit'] or right['unit'] != spec['unit']:
            raise ValueError('engine/benchmark units differ; no implicit conversion')
        delta = D(left.get('value')) - D(right.get('value'))
        within = abs(delta) <= D(right['tolerance'])
        if not within:
            issues.append('Independent benchmark tolerance breached: ' + identity)
        result['comparisons'].append({'id': identity, 'unit': spec['unit'], 'difference': str(delta), 'within_tolerance': within})
    result.update(status='needs-review' if issues else 'complete', issues=issues,
                  eligible_for_review=not issues, values=record['values'] if not issues else None)
    return result
