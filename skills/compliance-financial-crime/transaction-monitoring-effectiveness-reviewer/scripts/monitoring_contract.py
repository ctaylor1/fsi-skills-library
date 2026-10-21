"""Local monitoring intake helpers; exact decimals and Foundation 2.0 claims."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation, localcontext
import re
from foundation_contract import validate_common, claim_value, text, strings, records, unique_ids, day

T = text
B = lambda v: isinstance(v, bool)
I = lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0
D = lambda v: day(v) is not None
L = lambda v: strings(v) and len(v) == len(set(v))


def exact(v):
    """No float or exponent admission for precision-bound input."""
    if not isinstance(v, str) or not re.fullmatch(r'(?:0|[1-9]\d*)(?:\.\d+)?', v):
        return False
    try:
        return Decimal(v).is_finite()
    except InvalidOperation:
        return False


def fraction(v):
    return exact(v) and Decimal(v) <= 1


def enum(*options):
    return lambda v: isinstance(v, str) and v in options


def validate_schema(doc, object_type, objects, collections):
    errors = validate_common(doc, {object_type})
    if not isinstance(doc, dict) or not isinstance(doc.get('data'), dict):
        return errors, []
    if set(doc) != {'request_id','object_id','object_type','as_of','knowledge_cutoff','workflow','sources','data'}:
        errors.append('native input must contain exactly declared top-level fields')
    data = doc['data']
    if set(data) != set(objects) | set(collections):
        errors.append('data must contain exactly declared domain objects and collections')

    def check(row, schema, label, id_key=None):
        if not isinstance(row, dict):
            errors.append(label + ': domain object required')
            return
        if set(row) != set(schema) | ({id_key} if id_key else set()):
            errors.append(label + ': undeclared or missing fields')
        for field, predicate in schema.items():
            c = row.get(field)
            if not isinstance(c, dict) or set(c) != {'value','source_refs','fact_ids'}:
                errors.append(label+'.'+field+': exact value/source_refs/fact_ids claim required')
                continue
            if not strings(c['source_refs']) or not strings(c['fact_ids']):
                errors.append(label+'.'+field+': source and fact references must be string lists')
            if c['value'] is not None and not predicate(c['value']):
                errors.append(label+'.'+field+': unsupported type, enum, duplicate identity or exact decimal string required')

    for label, schema in objects.items():
        check(data.get(label), schema, label)
    for label, (id_key,schema) in collections.items():
        rows = data.get(label)
        if not records(rows) or not unique_ids(rows,id_key):
            errors.append(label+': unique nonempty record IDs required')
            continue
        for row in rows:
            check(row,schema,label+'.'+row[id_key],id_key)
    return errors, []


def resolve(doc,row,schema,label,issues):
    resolved = {}
    for field in schema:
        resolved[field], gaps = claim_value(doc,row[field],label+'.'+field)
        issues.extend(gaps)
    return resolved


def raw(row,field):
    c = row.get(field)
    return c.get('value') if isinstance(c,dict) else None


def metric(numerator,denominator,unit='fraction'):
    if denominator == 0:
        return None
    with localcontext() as ctx:
        ctx.prec = max(40,len(str(numerator))+len(str(denominator))+20)
        value = Decimal(numerator)/Decimal(denominator)
        rendered = format(value.quantize(Decimal('0.000000000001')),'f')
    return {'numerator':numerator,'denominator':denominator,'unit':unit,
            'decimal':rendered,'display_rounding':'12 places, half-even; exact counts retained'}


def threshold_compare(numerator,denominator,threshold):
    if not denominator or threshold is None:
        return None
    # Decimal multiplication needs enough precision for arbitrary supplied strings.
    with localcontext() as ctx:
        ctx.prec = max(40,len(str(numerator))+len(str(denominator))+len(threshold)+10)
        return Decimal(numerator) >= Decimal(denominator)*Decimal(threshold)


def decimal_equal(a,b):
    return a is not None and b is not None and Decimal(a) == Decimal(b)
