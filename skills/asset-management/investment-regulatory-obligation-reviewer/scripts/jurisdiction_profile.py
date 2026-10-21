"""Supplied reviewed jurisdiction profiles; no legal inference or filings."""
from collections import defaultdict
from urllib.parse import urlsplit
from foundation_contract import date_value, finish, require_sources, text, validate_actual_date, validate_common
from specialist_contract import validate_specialist_common as validate_common

EXTENSION = 'jurisdiction-profile-comparison'
SCOPE_FIELDS = ('entity_type', 'activity', 'product_type', 'investor_type', 'home_jurisdiction', 'host_jurisdiction')


def fields(row, *keys):
    if not isinstance(row, dict) or any(not text(row.get(k)) for k in keys):
        raise ValueError('nonempty text required: ' + ', '.join(keys))


def rows(doc, key, identity):
    value = doc.get(key)
    if not isinstance(value, list) or not value or len(value) > 10000:
        raise ValueError(key + ' requires 1..10000 rows')
    seen = set()
    for row in value:
        fields(row, identity, 'source_ref')
        if row[identity] in seen: raise ValueError('duplicate ' + identity)
        seen.add(row[identity]); require_sources(doc, [row['source_ref']])
    return value


def compute(doc):
    errors = validate_common(doc)
    if errors: raise ValueError('; '.join(errors))
    if doc.get('extension') != EXTENSION: raise ValueError('unsupported regulatory extension')
    if doc.get('requested_action', 'review') not in {'review', 'draft'}: raise ValueError('legal certification, approval and filing unsupported')
    scopes = rows(doc, 'review_scopes', 'scope_id'); profiles = rows(doc, 'jurisdiction_profiles', 'profile_id')
    issues = []; results = []; day = date_value(doc['as_of']); source_map = {s['source_ref']: s for s in doc['sources']}
    for scope in scopes:
        fields(scope, 'entity_id', 'owner')
        for key in SCOPE_FIELDS:
            if key not in scope or scope[key] is not None and not text(scope[key]):
                raise ValueError('scope fields must be text or explicit null: ' + key)
        if scope['entity_id'] != doc['object_id']: raise ValueError('review scope entity differs from request object')
    for profile in profiles:
        fields(profile, 'obligation_key', 'jurisdiction', 'version', 'reviewer', 'owner', 'requirement_summary', 'treatment')
        if profile['treatment'] not in {'required', 'prohibited', 'conditional'}: raise ValueError('profile treatment unsupported')
        if profile.get('status') not in {'final', 'proposed', 'withdrawn', 'superseded'}: raise ValueError('profile lifecycle unsupported')
        if profile.get('territorial_basis') not in {'home', 'host', 'either'}: raise ValueError('territorial basis must be home/host/either')
        if not isinstance(profile.get('cross_border_only'), bool): raise ValueError('cross_border_only must be explicit boolean')
        start = date_value(profile.get('effective_from')); end = date_value(profile.get('effective_to')) if profile.get('effective_to') else None
        if end is not None and start > end: raise ValueError('profile effective interval inverted')
        validate_actual_date(doc, profile.get('reviewed_on'), profile['source_ref'])
        authority = profile.get('primary_authority'); fields(authority, 'authority', 'title', 'url', 'provision', 'version', 'source_ref')
        require_sources(doc, [authority['source_ref']])
        parsed = urlsplit(authority['url'])
        if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError('primary authority needs an explicit HTTPS source URL')
        registered = source_map[authority['source_ref']]
        if registered.get('locator') != authority['url'] or registered['version'] != authority['version']:
            raise ValueError('primary authority locator/version differs from registered evidence')
        validate_actual_date(doc, authority.get('retrieved_on'), authority['source_ref'])
        conditions = profile.get('scope_conditions')
        if not isinstance(conditions, dict) or set(conditions) != set(SCOPE_FIELDS[:4]):
            raise ValueError('profile needs reviewed entity/activity/product/investor scope conditions')
        for key, value in conditions.items():
            if not isinstance(value, list) or not value or any(not text(x) for x in value) or len(value) != len(set(value)):
                raise ValueError('scope conditions require unique explicit accepted values: ' + key)
        deadline = profile.get('deadline')
        if not isinstance(profile.get('deadline_required'), bool): raise ValueError('deadline_required must be boolean')
        if deadline is not None:
            fields(deadline, 'basis', 'source_ref'); require_sources(doc, [deadline['source_ref']])
            trigger = validate_actual_date(doc, deadline.get('trigger_date'), deadline['source_ref'])
            due = date_value(deadline.get('due_date'))
            if due < trigger: raise ValueError('supplied deadline predates its trigger')
        for scope in scopes:
            missing = [key for key in SCOPE_FIELDS if scope[key] is None]
            state = 'undetermined'; reasons = []
            if profile.get('review_status') != 'reviewed': reasons.append('profile review not established')
            elif profile['status'] != 'final': state = 'not-binding'; reasons.append('profile lifecycle is ' + profile['status'])
            elif not (start <= day and (end is None or day <= end)): state = 'not-effective'; reasons.append('outside supplied effective interval')
            else:
                known_tests = [scope[k] in accepted for k, accepted in conditions.items() if scope[k] is not None]
                territory_fields = ['home_jurisdiction'] if profile['territorial_basis'] == 'home' else ['host_jurisdiction'] if profile['territorial_basis'] == 'host' else ['home_jurisdiction', 'host_jurisdiction']
                territory_known = all(scope[k] is not None for k in territory_fields)
                if territory_known: known_tests.append(profile['jurisdiction'] in [scope[k] for k in territory_fields])
                if profile['cross_border_only'] and scope['home_jurisdiction'] is not None and scope['host_jurisdiction'] is not None:
                    known_tests.append(scope['home_jurisdiction'] != scope['host_jurisdiction'])
                if False in known_tests: state = 'not-applicable'; reasons.append('explicit reviewed scope condition not met')
                elif missing: reasons.append('scope facts missing: ' + ', '.join(missing))
                else: state = 'applicable-under-supplied-profile'; reasons.append('all supplied entity/activity/product/investor/territorial conditions met')
            applicable = state == 'applicable-under-supplied-profile'
            due_date = deadline['due_date'] if deadline is not None else None
            overdue = applicable and due_date is not None and date_value(due_date) < day
            days_until = (date_value(due_date) - day).days if applicable and due_date is not None else None
            if applicable and profile['deadline_required'] and deadline is None:
                issues.append(scope['scope_id'] + '/' + profile['profile_id'] + ': reviewed deadline evidence missing')
            if overdue: issues.append(scope['scope_id'] + '/' + profile['profile_id'] + ': supplied obligation overdue')
            if state == 'undetermined': issues.append(scope['scope_id'] + '/' + profile['profile_id'] + ': applicability undetermined')
            results.append({'scope_id': scope['scope_id'], 'profile_id': profile['profile_id'], 'obligation_key': profile['obligation_key'],
                'jurisdiction': profile['jurisdiction'], 'version': profile['version'], 'state': state, 'reasons': reasons,
                'treatment': profile['treatment'], 'requirement_summary': profile['requirement_summary'],
                'due_date': due_date, 'days_until_due_calendar': days_until, 'overdue_under_supplied_deadline': overdue,
                'owner': profile['owner'], 'source_ref': profile['source_ref'], 'primary_authority': authority,
                'discharge_confirmed': False})
    groups = defaultdict(list)
    for row in results:
        if row['state'] == 'applicable-under-supplied-profile': groups[(row['scope_id'], row['obligation_key'])].append(row)
    comparisons = []
    for (scope_id, obligation), active in groups.items():
        if len(active) < 2: continue
        overlap = len({r['jurisdiction'] for r in active}) < len(active)
        differing = len({(r['treatment'], r['requirement_summary'], r['due_date']) for r in active}) > 1
        unresolved = differing or overlap
        if unresolved: issues.append(scope_id + '/' + obligation + ': overlapping or differing reviewed profiles need legal-owner resolution')
        comparisons.append({'scope_id': scope_id, 'obligation_key': obligation, 'profile_ids': [r['profile_id'] for r in active],
            'different_requirements_or_deadlines': differing, 'overlapping_jurisdiction_versions': overlap,
            'potential_conflict_requires_review': unresolved, 'resolution': None, 'stricter_rule_automatically_selected': False})
    return finish(doc, 'investment-regulatory-obligation-reviewer', 'jurisdiction-profile-comparison/1', {
        'extension': EXTENSION, 'profile_comparisons': comparisons, 'obligations': results,
        'legal_conclusion': None, 'market_access_authorized': False, 'compliance_certified': False,
        'rule_coverage': 'Only the supplied reviewed profiles and explicit entity/activity/product/investor scope',
    }, issues, limitations=[
        'Geography alone never determines applicability; every profile supplies reviewed entity, activity, product and investor conditions.',
        'Primary URLs and version links are supplied provenance, not authenticated authority or legal interpretation. No universal jurisdiction pack is bundled.',
        'Deadlines are supplied absolute dates; calendar days are descriptive. Business-day calendars, transition relief and discharge require the legal owner.',
        'Different or overlapping profiles are exposed for review; no precedence, extraterritorial rule or stricter standard is inferred.',
    ])


def validate(doc):
    try: compute(doc); return []
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc: return [str(exc)]
