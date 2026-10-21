"""Supplied-policy contract. Metadata is an assertion, not authenticated approval."""
from datetime import date
import math
from native_integrity import canonical_hash


def text(value):
    return isinstance(value, str) and bool(value.strip())


def number(value, low=0, high=None):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= low and (high is None or value <= high))


def day(value):
    try:
        return date.fromisoformat(value) if isinstance(value, str) and len(value) == 10 else None
    except ValueError:
        return None


def records(value):
    return isinstance(value, list) and all(isinstance(x, dict) for x in value)


def strings(value, nonempty=False):
    return isinstance(value, list) and (bool(value) or not nonempty) and all(text(x) for x in value)


def base_errors(doc, version_key, date_key, config_key=None, config_keys=()):
    errors=[]
    if not isinstance(doc, dict):
        return ['input must be an object']
    try:
        canonical_hash(doc)
    except (ValueError, TypeError) as exc:
        errors.append(str(exc))
    asof=day(doc.get(date_key))
    if asof is None:
        errors.append(date_key + ' must be a valid YYYY-MM-DD date')
    if not text(doc.get(version_key)):
        errors.append(version_key + ' is required')
    profile=doc.get('policy_profile')
    if not isinstance(profile, dict):
        errors.append('policy_profile is required; no approved policy defaults are bundled')
        profile={}
    for key in ('version','jurisdiction','institution_type','purpose','authority','approval_ref'):
        if not text(profile.get(key)):
            errors.append('policy_profile.'+key+' is required')
    if profile.get('version') != doc.get(version_key):
        errors.append('policy_profile.version must match '+version_key)
    effective, review=day(profile.get('effective_date')), day(profile.get('review_due_date'))
    if not effective or not review or (asof and not effective <= asof <= review):
        errors.append('policy_profile dates must cover the assessment date')
    mode=doc.get('execution_context')
    if mode not in ('review','test'):
        errors.append('execution_context must be review or test')
    allowed=('approved','test-only') if mode == 'test' else ('approved',)
    if profile.get('approval_status') not in allowed:
        errors.append('policy_profile must assert approved status for review; test-only requires test context')
    if doc.get('jurisdiction') and profile.get('jurisdiction') != doc['jurisdiction']:
        errors.append('policy_profile jurisdiction differs from case jurisdiction')
    if config_key:
        cfg=doc.get(config_key)
        if not isinstance(cfg, dict):
            errors.append(config_key+' must be supplied explicitly')
            cfg={}
        for key in config_keys:
            if key not in cfg:
                errors.append(config_key+'.'+key+' must be supplied explicitly')
    return errors


def require_valid(doc, validator):
    errors, _ = validator(doc)
    if errors:
        raise ValueError('; '.join(errors))


def limitations():
    return ['Supplied source records and policy approval metadata are unverified assertions.',
            'Input binding establishes reproducibility, not source truth or authorization.',
            'No system action, legal determination, customer decision, or approval is performed.']
