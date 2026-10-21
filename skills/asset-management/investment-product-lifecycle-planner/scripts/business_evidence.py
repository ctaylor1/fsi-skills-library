"""Claim-level evidence support for bounded AM business methods; no source authentication."""
from copy import deepcopy
from decimal import Decimal, Context, localcontext
import re
from foundation_contract import D, date_value, validate_common, source_issues, finish, ratio, validate_actual_date
from native_integrity import canonical_hash

COMMON = {'request_id','object_id','as_of','knowledge_cutoff','currency','audience','sources','mode','unresolved_issues'}


def start(doc, fields):
    errors = validate_common(doc)
    if errors: raise ValueError('; '.join(errors))
    extra = set(doc) - COMMON - set(fields)
    if extra: raise ValueError('unsupported input fields: ' + ', '.join(sorted(extra)))


def bound(doc, row, issues, label, approved=False):
    """Withhold the whole row before copying identifiers, values or provenance."""
    if not isinstance(row, dict) or set(row) != {'source_ref','claim_id','data'} or not isinstance(row.get('data'), dict):
        issues.append(label + ': missing structured evidence'); return None
    source = next((s for s in doc['sources'] if s.get('source_ref') == row['source_ref']), None)
    if not source or source.get('object_id') != doc['object_id'] or source.get('currency') != doc['currency']:
        issues.append(label + ': evidence scope unavailable'); return None
    if not isinstance(source.get('permitted_audiences'), list) or doc['audience'] not in source['permitted_audiences']:
        issues.append(label + ': restricted evidence omitted'); return None
    if source_issues(doc, row['source_ref']):
        issues.append(label + ': evidence timing or provenance unresolved'); return None
    if date_value(source['as_of']) > date_value(doc['as_of']):
        issues.append(label + ': future evidence omitted'); return None
    if approved:
        if source.get('approval_status') != 'approved':
            issues.append(label + ': approval evidence unavailable'); return None
        try:
            if not date_value(source['effective_from']) <= date_value(doc['as_of']) <= date_value(source['expires']):
                raise ValueError('outside effective interval')
        except (KeyError, ValueError, TypeError):
            issues.append(label + ': approved evidence is not current'); return None
    claims = source.get('claims')
    if not isinstance(claims, dict) or row['claim_id'] not in claims or canonical_hash(claims[row['claim_id']]) != canonical_hash(row['data']):
        issues.append(label + ': claim content not supported by supplied source'); return None
    data = deepcopy(row['data'])
    if '_evidence' in data: raise ValueError('reserved evidence field')
    data['_evidence'] = {'source_ref': row['source_ref'], 'claim_id': row['claim_id'], 'version': source['version'], 'as_of': source['as_of'], 'known_at': source['known_at'], 'source_truth': 'unverified'}
    return data


def items(doc, key, issues, approved=False):
    rows = doc.get(key)
    if not isinstance(rows, list): raise ValueError(key + ' must be a list')
    result = []
    ids = set()
    for i, row in enumerate(rows):
        data = bound(doc, row, issues, f'{key}[{i}]', approved)
        if data is None: continue
        identifier = text(data, 'id')
        if identifier in ids: raise ValueError(key + ': duplicate source-backed IDs')
        ids.add(identifier); result.append(data)
    return result


def text(data, field):
    value = data.get(field)
    if not isinstance(value, str) or not value.strip(): raise ValueError(field + ' must be nonempty text')
    return value


def num(data, field, low=None, high=None):
    value = D(data.get(field))
    if low is not None and value < D(low) or high is not None and value > D(high): raise ValueError(field + ' outside supported range')
    return value


def flag(data, field):
    value = data.get(field)
    if type(value) is not bool: raise ValueError(field + ' must be explicit boolean')
    return value


def values(data, field):
    value = data.get(field)
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value): raise ValueError(field + ' must be a list of nonempty strings')
    return value


def F(value):
    if value is None: return None
    with localcontext(Context(prec=256)):
        return format(value.quantize(Decimal('0.000001')), 'f')


def observed(doc, data, field):
    """A completed observation must exist by review, cutoff and source knowledge."""
    try:
        validate_actual_date(doc, data.get(field), data['_evidence']['source_ref'])
        return True
    except ValueError:
        return False


def current(data, doc, issues, label):
    try:
        okay = date_value(data['effective_from']) <= date_value(doc['as_of']) <= date_value(data['expires'])
    except (KeyError, ValueError, TypeError): okay = False
    if not okay: issues.append(label + ': policy/content effective dates unresolved')
    return okay


def statement(data, issues, label):
    value = text(data, 'text')
    if re.search(r'guarantee(?:d|s)?\s+(?:a\s+\S+\s+)?(?:return|outperformance)|risk[- ]free', value, re.I):
        issues.append(label + ': prohibited investment guarantee withheld'); return None
    return value


def support(data):
    return deepcopy(data['_evidence'])


def complete(doc, skill, method, results, issues, limitations, handoffs=()):
    output = finish(doc, skill, method, results, issues, limitations, handoffs)
    used = set()
    def visit(value):
        if isinstance(value, dict):
            if 'source_ref' in value and 'claim_id' in value: used.add(value['source_ref'])
            for child in value.values(): visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
    visit(results)
    output['source_refs'] = sorted(used)
    if 'mode' in doc: output['mode'] = doc['mode']
    return output


def guard(compute, doc):
    try: compute(doc); return []
    except (ValueError, TypeError, KeyError, IndexError, ArithmeticError) as exc: return ['invalid business input: ' + str(exc)]


def compare(value, operator, threshold):
    if value is None: return 'unknown'
    if operator=='equals': return 'met' if type(value) is type(threshold) and value==threshold else 'not-met'
    if operator=='documented': return 'met' if value is True else 'not-met' if value is False else 'unknown'
    if operator not in {'minimum','maximum'}:raise ValueError('unsupported policy comparator')
    try: actual=D(value); target=D(threshold)
    except (ValueError,ArithmeticError):return 'unknown'
    return 'met' if (actual>=target if operator=='minimum' else actual<=target) else 'not-met'
