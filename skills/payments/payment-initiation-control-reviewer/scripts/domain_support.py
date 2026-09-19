"""Small local domain primitives; no account, source, or actor authentication."""
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext


def number(value, positive=False):
    if not isinstance(value, str):
        return None
    try:
        result = Decimal(value)
        if not result.is_finite() or result < 0 or (positive and result == 0):
            return None
        return result
    except InvalidOperation:
        return None


def total(values):
    with localcontext() as ctx:
        ctx.prec = max(50, sum(len(str(v)) for v in values) + 5)
        return sum(values, Decimal(0))


def difference(a, b):
    with localcontext() as ctx:
        ctx.prec = max(50, len(str(a)) + len(str(b)) + 5)
        return a - b


def day(value):
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def sources(row):
    value = row.get('source_ids', []) if isinstance(row, dict) else []
    return value if isinstance(value, list) and all(isinstance(x, str) for x in value) else []


def finding(code, message, row=None, severity='gap'):
    return {'code': code, 'message': message, 'source_ids': sources(row or {}), 'severity': severity}


def active(row, as_of):
    start, end, now = day(row.get('effective_from')), day(row.get('effective_until')), day(as_of)
    return bool(start and end and now and start <= now <= end and row.get('revoked') is False)


def object_list(data, name, required=False):
    value = data.get(name)
    if value is None and not required:
        return []
    if not isinstance(value, list) or not all(isinstance(x, dict) for x in value):
        return [f'{name} must be a list of objects']
    return []


def row_fields(rows, fields):
    errors = []
    for index, row in enumerate(rows):
        for key in fields:
            if key in row and not isinstance(row[key], str):
                errors.append(f'row {index}.{key} must be a string when supplied')
        if 'source_ids' in row and (not isinstance(row['source_ids'], list) or not all(isinstance(x, str) for x in row['source_ids'])):
            errors.append(f'row {index}.source_ids must be a list of strings')
    return errors


def scoped_policy(policy, request, profile_id=None):
    return bool(policy and sources(policy) and active(policy, request['as_of'])
                and policy.get('jurisdiction') == request['jurisdiction']
                and request['participant'] in policy.get('participants', [])
                and (profile_id is None or profile_id in policy.get('profile_ids', [])))


def profile_review(data, payment, request, action):
    from payment_foundation import load_rail_profile
    profile_id = payment.get('rail_profile_id')
    if payment.get('rail_family') == 'card':
        profile = data.get('card_profile', {})
        policy = data.get('policy', {})
        exact = all(payment.get(k) and profile.get(k) == payment.get(k) and policy.get(k) == payment.get(k) for k in ('network', 'product'))
        dates = day(profile.get('reviewed_on')) and day(profile.get('review_due')) and day(profile['reviewed_on']) <= day(request['as_of']) <= day(profile['review_due'])
        valid = exact and profile.get('profile_id') == profile_id and active(profile, request['as_of']) and profile.get('jurisdiction') == request['jurisdiction'] and request['participant'] in profile.get('participants', []) and action in profile.get('actions', []) and profile.get('source_version') and dates and sources(profile)
        return [] if valid else [finding('card-profile-unresolved', 'Card scope requires a supplied versioned, currently reviewed network/product/participant/jurisdiction/action profile and matching policy.', profile)]
    profile = load_rail_profile(profile_id)
    if not profile:
        return [finding('native-profile-unresolved', 'The bank rail profile does not resolve; a generic rail label cannot supply scheme rules.', payment)]
    dates = day(profile.get('reviewed_on')) and day(profile.get('review_due')) and day(profile['reviewed_on']) <= day(request['as_of']) <= day(profile['review_due'])
    if not dates or profile.get('jurisdiction') != request['jurisdiction'] or payment.get('currency') not in profile.get('currencies', []):
        return [finding('native-profile-scope', 'Native profile date, jurisdiction or currency does not apply to the proposed payment.', payment)]
    if payment.get('direction') is not None and payment.get('direction') not in profile.get('directions', []):
        return [finding('native-profile-direction', 'The selected native rail does not support this payment direction.', payment)]
    return []
