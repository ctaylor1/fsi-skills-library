"""Linked normal-servicing plans. Settlement is never rolled back."""
from domain_support import difference, finding, number, object_list, row_fields, profile_review, scoped_policy, sources, total

SKILL = 'payment-servicing-planner'
ACTIONS = {'refund', 'void', 'reversal', 'return', 'cancel-recovery'}
STATES = {'draft', 'authorized', 'submitted', 'accepted', 'settled', 'posted', 'rejected', 'returned', 'unknown'}


def validate(data):
    if not isinstance(data, dict):
        return ['data must be an object']
    errors = []
    for key in ('original_payment', 'service_request', 'policy', 'card_profile'):
        if key in data and not isinstance(data[key], dict):
            errors.append(f'{key} must be an object')
    errors += object_list(data, 'prior_services')
    card = data.get('card_profile', {})
    for key in ('participants', 'actions'):
        if key in card and (not isinstance(card[key], list) or not all(isinstance(x, str) for x in card[key])):
            errors.append(f'card_profile.{key} must be a list of strings')
    if errors:
        return errors
    errors += row_fields([data.get('original_payment', {}), data.get('service_request', {})], ('payment_id', 'state', 'amount', 'currency', 'rail_profile_id', 'action', 'service_id', 'beneficiary_account_ref', 'originator_account_ref'))
    errors += row_fields(data.get('prior_services', []), ('payment_id', 'service_id', 'amount', 'currency', 'status', 'action'))
    policy = data.get('policy', {})
    for key in ('participants', 'profile_ids', 'approval_roles'):
        if key in policy and not isinstance(policy[key], list):
            errors.append(f'policy.{key} must be a list')
    errors += object_list(policy, 'permissions')
    for permission in policy.get('permissions', []):
        if 'original_states' in permission and not isinstance(permission['original_states'], list):
            errors.append('permissions.original_states must be a list')
    return errors


def analyze(request):
    data, findings = request['data'], []
    original, service, policy = data.get('original_payment', {}), data.get('service_request', {}), data.get('policy', {})
    pid, action, state = original.get('payment_id'), service.get('action'), original.get('state')
    original_amount, requested = number(original.get('amount'), True), number(service.get('amount'), True)
    currency = original.get('currency')
    findings.extend(profile_review(data, original, request, action))
    if not pid or state not in STATES or state == 'unknown' or not sources(original) or original_amount is None or not currency or not original.get('rail_profile_id') or not original.get('originator_account_ref') or not original.get('beneficiary_account_ref'):
        findings.append(finding('original-payment-incomplete', 'Original payment identity, evidenced lifecycle, amount/currency, accounts and rail are required.', original))
    if action not in ACTIONS or not service.get('service_id') or service.get('payment_id') != pid or requested is None or service.get('currency') != currency or not service.get('reason') or not sources(service):
        findings.append(finding('service-request-incomplete', 'One linked service request needs an explicit action, reason, amount/currency and evidence.', service))
    if service.get('authority_source') == 'repair' or data.get('repair_approval'):
        findings.append(finding('repair-authority-inapplicable', 'A repair approval cannot authorize normal servicing; independent action-specific authority is required.', service))
    if data.get('prior_service_ledger_complete') is not True or 'prior_services' not in data:
        findings.append(finding('service-history-unknown', 'Supply the complete prior and pending servicing ledger; an omitted history is not zero.', original))
    completed, pending, seen, valid_ledger = [], [], set(), True
    for item in data.get('prior_services', []):
        value = number(item.get('amount'), True)
        if not item.get('service_id') or item['service_id'] in seen or item.get('payment_id') != pid or item.get('currency') != currency or value is None or item.get('action') not in ACTIONS or item.get('status') not in {'completed', 'pending', 'failed', 'cancelled'} or not sources(item):
            findings.append(finding('service-ledger-invalid', 'Prior service identity, original link, status, amount/currency, action and evidence must be unique and complete.', item))
            valid_ledger = False
            continue
        seen.add(item['service_id'])
        if item['service_id'] == service.get('service_id'):
            findings.append(finding('duplicate-service', 'Requested service identifier already appears in the servicing ledger.', item))
        if item['status'] == 'completed':
            completed.append(value)
        elif item['status'] == 'pending':
            pending.append(value)
    used, reserved = total(completed), total(pending)
    history_usable = valid_ledger and isinstance(data.get('prior_services'), list) and data.get('prior_service_ledger_complete') is True
    remaining = difference(difference(original_amount, used), reserved) if original_amount is not None and history_usable else None
    if remaining is not None and (remaining < 0 or requested is not None and requested > remaining):
        findings.append(finding('service-amount-exceeds-remaining', 'Completed and pending services plus this request exceed the original payment amount.', service))
    if state in {'rejected', 'returned'}:
        findings.append(finding('no-new-service-on-closed-payment', 'Rejected or fully returned payment evidence requires investigation before another servicing instruction.', original))
    if action == 'void' and state not in {'draft', 'authorized'}:
        findings.append(finding('void-after-submission', 'This bounded void plan supports only unsubmitted draft/authorization states; submitted or settled payments require a distinct service.', original))
    if action in {'refund', 'return'} and state not in {'settled', 'posted'}:
        findings.append(finding('funds-movement-not-evidenced', 'Refund/return planning requires evidenced settlement or posting of the original funds.', original))
    if action == 'reversal' and state in {'settled', 'posted'} and service.get('requested_effect') == 'rollback':
        findings.append(finding('settled-rollback-prohibited', 'A settled payment cannot be rolled back. Any permitted reversal is a separately linked instruction under its own rule.', service))
    if service.get('requested_effect') == 'rollback':
        findings.append(finding('rollback-not-supported', 'No servicing action restores the original ledger state through a rollback in this planner.', service))
    if not scoped_policy(policy, request, original.get('rail_profile_id')):
        findings.append(finding('service-policy-unresolved', 'An active participant/jurisdiction/rail servicing policy with source evidence is required.', policy))
    permissions = [x for x in policy.get('permissions', []) if x.get('action') == action and x.get('currency') == currency]
    permission = permissions[0] if len(permissions) == 1 else {}
    maximum = number(permission.get('max_amount'), True)
    if not permission or state not in permission.get('original_states', []) or maximum is None or requested is None or requested > maximum or not sources(permission):
        findings.append(finding('service-permission-unresolved', 'The action, original state and requested amount must satisfy one sourced currency-specific permission.', permission))
    # Deadline is an explicitly supplied reviewed date, never an invented business-day clock.
    deadline = permission.get('deadline_date')
    from domain_support import day
    if not day(deadline) or day(request['as_of']) > day(deadline):
        findings.append(finding('service-window-unresolved', 'A reviewed action-specific deadline date is missing, malformed or elapsed; no universal return clock is inferred.', permission))
    expected_binding = {k: original.get(k) for k in ('payment_id', 'amount', 'currency', 'rail_profile_id', 'originator_account_ref', 'beneficiary_account_ref', 'state')} | {k: original[k] for k in ('rail_family', 'network', 'product') if k in original}
    if service.get('original_binding') != expected_binding:
        findings.append(finding('original-binding-mismatch', 'The requested plan must bind the exact original payment snapshot, including lifecycle state.', service))
    if service.get('destination_account_ref') != original.get('originator_account_ref') and action in {'refund', 'return', 'reversal'}:
        findings.append(finding('beneficiary-redirection', 'A different destination is a new-payee instruction requiring initiation controls; original servicing authority is insufficient.', service))
    if not policy.get('approval_roles'):
        findings.append(finding('service-approval-roles-missing', 'Applicable human approval roles must be explicit.', policy))
    if action in {'refund', 'return', 'reversal'}:
        effect = {'kind': 'new-linked-funds-movement', 'original_ledger_rolled_back': False, 'planned_amount': service.get('amount'), 'currency': currency, 'guaranteed_recovery': False}
    elif action == 'void':
        effect = {'kind': 'request-release-before-submission', 'original_ledger_rolled_back': False, 'planned_amount': service.get('amount'), 'currency': currency, 'guaranteed_recovery': False}
    else:
        effect = {'kind': 'cancellation-or-recovery-request', 'original_ledger_rolled_back': False, 'planned_amount': service.get('amount'), 'currency': currency, 'guaranteed_recovery': False, 'actual_financial_effect': 'unknown-until-counterparty-and-system-response'}
    return {'result': {'review': 'gaps' if findings else 'ready-for-human-review', 'service_id': service.get('service_id'), 'original_payment_id': pid, 'action': action, 'original_binding': expected_binding, 'completed_service_amount': str(used) if history_usable else None, 'pending_service_amount': str(reserved) if history_usable else None, 'remaining_serviceable_amount': str(remaining) if remaining is not None else None, 'expected_effect': effect, 'approval_roles': policy.get('approval_roles', []), 'execution_authorized': False, 'required_outcome_evidence': ['service response linked to original and service IDs', 'settlement/account posting if funds move', 'refreshed prior and pending service ledger']}, 'findings': findings, 'handoffs': [{'target_skill': 'payment-initiation-control-reviewer', 'reason': 'Review the exact new linked instruction and servicing authority before any funds-movement execution.', 'required_inputs': ['original_binding', 'service_request', 'policy', 'findings']}, {'target_skill': 'payment-lifecycle-diagnoser', 'reason': 'Interpret actual service and original payment events after an authorized operator acts.', 'required_inputs': ['original payment ID', 'service ID', 'event evidence']}]}
