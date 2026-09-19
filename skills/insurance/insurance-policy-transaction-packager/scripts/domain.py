"""Prepare one evidenced policy change; no policy state is changed."""
from insurance_contract import iso_date, stable_hash
from insurance_foundation import number, profile_issues, sources_for

SKILL = 'insurance-policy-transaction-packager'
ACTIONS = {'issue', 'endorsement', 'renewal', 'cancellation', 'nonrenewal', 'reinstatement'}


def validate(doc):
    data, errors = doc.get('data', {}), []
    for key in ('policy', 'request', 'authority', 'premium_effect', 'rule_profile'):
        if key in data and not isinstance(data[key], dict):
            errors.append(f'data.{key} must be an object')
    for key in ('documents', 'notices', 'pending_transactions'):
        if key in data and (not isinstance(data[key], list) or any(not isinstance(x, dict) for x in data[key])):
            errors.append(f'data.{key} must be a list of objects')
    request = data.get('request', {})
    if isinstance(request, dict):
        for key in ('transaction_type', 'policy_id', 'request_id', 'requested_by', 'expected_policy_version'):
            if key in request and request[key] is not None and not isinstance(request[key], str):
                errors.append(f'request.{key} must be a string or null')
    if isinstance(request, dict) and 'changes' in request and (not isinstance(request['changes'], list) or any(not isinstance(x, dict) for x in request['changes'])):
        errors.append('request.changes must be a list of objects')
    policy = data.get('policy', {})
    if isinstance(policy, dict) and 'values' in policy and not isinstance(policy['values'], dict):
        errors.append('policy.values must be an object')
    profile = data.get('rule_profile', {})
    if isinstance(profile, dict):
        actions = profile.get('transactions', {})
        if not isinstance(actions, dict) or any(not isinstance(v, dict) for v in actions.values()):
            errors.append('rule_profile.transactions must map actions to rule objects')
        else:
            for rules in actions.values():
                for key in ('allowed_statuses', 'allowed_fields', 'required_documents', 'required_recipients'):
                    if key in rules and (not isinstance(rules[key], list) or any(not isinstance(x, str) for x in rules[key])):
                        errors.append(f'transaction rules {key} must be a list of strings')
                n = rules.get('minimum_notice_days')
                if n is not None and (isinstance(n, bool) or not isinstance(n, int) or n < 0):
                    errors.append('minimum_notice_days must be a nonnegative integer or null')
    authority = data.get('authority', {})
    if isinstance(authority, dict) and 'actions' in authority and (not isinstance(authority['actions'], list) or any(not isinstance(x, str) for x in authority['actions'])):
        errors.append('authority.actions must be a list of strings')
    premium = data.get('premium_effect', {})
    if isinstance(premium, dict):
        try:
            number(premium.get('amount'))
        except ValueError as exc:
            errors.append('premium_effect.amount: ' + str(exc))
    return errors


def evaluate(doc):
    data, findings = doc['data'], []
    policy, request = data.get('policy', {}), data.get('request', {})
    authority, profile = data.get('authority', {}), data.get('rule_profile', {})
    action = request.get('transaction_type')

    def add(code, message, row=None, severity='gap'):
        refs = (row or {}).get('source_refs', [])
        findings.append({'code': code, 'message': message, 'severity': severity,
                         'source_refs': refs if isinstance(refs, list) and all(isinstance(x, str) and x for x in refs) else []})

    def evidence(row, label):
        issues = sources_for(doc, row.get('source_refs'))
        if issues:
            add(label + '-evidence', '; '.join(issues), row)

    for label, row in [('policy', policy), ('request', request), ('authority', authority)]:
        evidence(row, label)
    if not policy.get('policy_id') or policy.get('policy_id') != doc['context']['object_id'] or request.get('policy_id') != policy.get('policy_id'):
        add('policy-identity', 'Policy, request and context must identify the same policy.', request)
    if not policy.get('version') or request.get('expected_policy_version') != policy.get('version'):
        add('policy-version-conflict', 'Request must bind the exact current policy version; refresh a stale request.', request)
    if policy.get('jurisdiction') != doc['context']['jurisdiction'] or policy.get('line_of_business') != doc['context']['line_of_business']:
        add('policy-scope', 'Policy jurisdiction and line must match the requested scope.', policy)
    if doc['context']['line_of_business'] not in {'pc', 'life', 'annuity'}:
        add('line-profile-unavailable', 'This policy transaction preparer requires a reviewed P&C or life/annuity administrative profile.')
    if action not in ACTIONS or not request.get('request_id'):
        add('transaction-identity', 'A unique request ID and supported transaction type are required.', request)
    rules = profile.get('transactions', {}).get(action, {})
    for issue in profile_issues(doc, profile):
        add('profile-applicability', issue, profile)
    if not rules or policy.get('status') not in rules.get('allowed_statuses', []):
        add('policy-state-ineligible', 'The supplied transaction profile must allow this current policy state.', policy, 'review')
    if not request.get('requested_by') or authority.get('actor_id') != request.get('requested_by') or authority.get('policy_id') != policy.get('policy_id') or action not in authority.get('actions', []):
        add('request-authority', 'Evidence must establish this requester, policy and specific administrative action.', authority)
    try:
        if not iso_date(authority.get('effective_from')) <= iso_date(doc['as_of']) <= iso_date(authority.get('effective_to')):
            add('authority-not-current', 'Request authority is not current at the review date.', authority, 'review')
    except (ValueError, TypeError):
        add('authority-dates', 'Authority effective dates are missing or invalid.', authority)
    effective = None
    try:
        effective = iso_date(request.get('effective_date'))
        start, end = iso_date(policy.get('effective_from')), iso_date(policy.get('effective_to'))
        if start >= end:
            add('policy-period', 'Policy dates do not form a positive coverage period.', policy)
        if action in {'endorsement', 'cancellation'} and not start <= effective < end:
            add('transaction-date-outside-term', 'Midterm change date must be within the supplied policy period.', request, 'review')
        if action in {'renewal', 'nonrenewal'} and effective != end:
            add('term-boundary-mismatch', 'Renewal/nonrenewal date differs from supplied expiration; obtain a reviewed term mapping.', request, 'review')
        if effective < iso_date(doc['as_of']) and rules.get('backdating_permitted') is not True:
            add('backdating-unresolved', 'Retrospective effective date requires explicitly sourced permission and specialist review.', request, 'review')
    except (ValueError, TypeError):
        add('transaction-dates', 'Valid policy and requested effective dates are required.', request)
    changes, seen = [], set()
    for change in request.get('changes', []):
        field = change.get('field')
        evidence(change, 'change')
        if not isinstance(field, str) or not field or field in seen or field not in rules.get('allowed_fields', []):
            add('change-field', 'Each change must identify one unique permitted field.', change, 'review')
        if isinstance(field, str):
            seen.add(field)
            if field not in policy.get('values', {}) or 'before' not in change or change.get('before') != policy.get('values', {}).get(field):
                add('before-value-conflict', f'Current value for {field} does not match the proposed before value.', change, 'review')
        if 'after' not in change:
            add('after-value-missing', 'Explicit proposed after value is required, including null for deletion.', change)
        current_known = isinstance(field, str) and field in policy.get('values', {})
        changes.append({'field': field,
                        'before': policy['values'][field] if current_known else None,
                        'before_known': current_known, 'requested_before': change.get('before'),
                        'before_matches_request': current_known and 'before' in change and change['before'] == policy['values'][field],
                        'after': change.get('after'), 'source_refs': change.get('source_refs', []),
                        'policy_source_refs': policy.get('source_refs', [])})
    if action == 'endorsement' and not changes:
        add('changes-missing', 'An endorsement requires an explicit source-backed before/after change list.', request)
    if data.get('pending_inventory_complete') is not True or 'pending_transactions' not in data:
        add('pending-history-unknown', 'An omitted pending transaction inventory does not establish no conflicting change.')
    for pending in data.get('pending_transactions', []):
        evidence(pending, 'pending')
        if pending.get('policy_id') != policy.get('policy_id'):
            add('pending-policy-conflict', 'Pending transaction belongs to another policy.', pending)
        if pending.get('request_id') == request.get('request_id'):
            add('duplicate-request', 'This request ID already exists; do not prepare a duplicate instruction.', pending, 'review')
        elif pending.get('status') in {'pending', 'approved'}:
            add('concurrent-policy-change', 'A pending/approved change may invalidate this policy snapshot; resolve sequencing.', pending, 'review')
        elif pending.get('status') not in {'completed', 'rejected', 'cancelled'}:
            add('pending-state-unknown', 'Transaction history status is unknown.', pending)
    document_matrix = []
    for kind in rules.get('required_documents', []):
        matches = [x for x in data.get('documents', []) if x.get('kind') == kind and x.get('policy_id') == policy.get('policy_id') and x.get('policy_version') == policy.get('version') and x.get('version') and not sources_for(doc, x.get('source_refs'))]
        document_matrix.append({'kind': kind, 'matched_document_ids': [x.get('document_id') for x in matches], 'status': 'supplied' if matches else 'missing'})
        if not matches:
            add('required-document', f'{kind} needs a versioned document for this policy snapshot.')
    notice_plan = []
    if 'required_recipients' not in rules or 'minimum_notice_days' not in rules:
        add('notice-rules-unknown', 'Supply applicable recipients and calendar notice-day convention; explicit empty/zero is distinct from missing.', profile)
    for recipient in rules.get('required_recipients', []):
        candidates = [n for n in data.get('notices', []) if n.get('recipient') == recipient]
        notice = candidates[0] if len(candidates) == 1 else {}
        evidence(notice, 'notice')
        lead = None
        try:
            send_date = iso_date(notice.get('planned_send_date'))
            lead = (effective - send_date).days if effective else None
            if send_date < iso_date(doc['as_of']):
                add('notice-plan-in-past', 'A planned notice cannot stand in for evidence of an already delivered notice.', notice, 'review')
        except (ValueError, TypeError):
            add('notice-date', f'A unique dated notice plan is required for {recipient}.', notice)
        minimum = rules.get('minimum_notice_days')
        if rules.get('notice_day_basis') != 'calendar' or minimum is None:
            add('notice-convention', 'Only an explicitly supplied calendar-day notice profile is computed.', profile)
        elif lead is not None and lead < minimum:
            add('insufficient-notice', f'{recipient}: planned interval {lead} days is below supplied minimum {minimum}.', notice, 'review')
        notice_plan.append({'recipient': recipient, 'planned_send_date': notice.get('planned_send_date'), 'lead_calendar_days': lead, 'delivered': False})
    premium = data.get('premium_effect', {})
    evidence(premium, 'premium')
    amount = number(premium.get('amount'))
    if amount is None or not policy.get('currency') or premium.get('currency') != policy.get('currency') or premium.get('basis') != 'written-premium-change':
        add('premium-effect-unknown', 'Supply the sourced signed written-premium effect in policy currency; no prorata/refund formula is inferred.', premium)
        amount = None
    if doc['context']['line_of_business'] in {'life', 'annuity'} and any(c.get('field') in {'beneficiary', 'owner', 'withdrawal', 'surrender', 'loan', 'death_benefit'} for c in changes):
        add('life-value-rights-review', 'Life value or rights changes require the life/annuity contract-service review before this administrative package.', request, 'review')
    gaps = any(f['severity'] == 'gap' for f in findings)
    return {'status': 'needs-data' if gaps else 'needs-review' if findings else 'ready-for-review',
            'findings': findings, 'completeness': 'partial' if gaps else 'complete',
            'evaluability': 'partial' if gaps else 'evaluable',
            'results': {'transaction_type': action, 'request_id': request.get('request_id'),
                        'policy_binding': policy, 'policy_snapshot_hash': stable_hash(policy),
                        'proposed_changes': changes, 'requested_effective_date': request.get('effective_date'),
                        'document_matrix': document_matrix, 'notice_plan': notice_plan,
                        'premium_effect': {'amount': amount, 'currency': premium.get('currency'), 'basis': 'written-premium-change'},
                        'instruction_status': 'draft', 'resulting_policy_state': 'not-established',
                        'execution_authorized': False}}
