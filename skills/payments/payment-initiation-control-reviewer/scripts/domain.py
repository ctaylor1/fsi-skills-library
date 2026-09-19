"""Exact payment-intent, batch and mandate review. No execution or authentication."""
from domain_support import active, day, finding, number, object_list, row_fields, profile_review, scoped_policy, sources, total

SKILL = 'payment-initiation-control-reviewer'
BINDING = ('instruction_id', 'payer_account_ref', 'payee_ref', 'payee_account_ref', 'amount', 'currency', 'rail_profile_id', 'execution_date', 'direction', 'principal_ref')


def validate(data):
    if not isinstance(data, dict):
        return ['data must be an object']
    errors = []
    for name in ('instructions', 'intents', 'mandates', 'screenings', 'account_verifications', 'delegations'):
        errors += object_list(data, name, name == 'instructions')
    for name in ('policy', 'batch_controls', 'card_profile'):
        if name in data and not isinstance(data[name], dict):
            errors.append(f'{name} must be an object')
    if 'prior_instruction_ids' in data and (not isinstance(data['prior_instruction_ids'], list) or not all(isinstance(x, str) for x in data['prior_instruction_ids'])):
        errors.append('prior_instruction_ids must be a list of strings')
    card = data.get('card_profile', {})
    for key in ('participants', 'actions'):
        if key in card and (not isinstance(card[key], list) or not all(isinstance(x, str) for x in card[key])):
            errors.append(f'card_profile.{key} must be a list of strings')
    if errors:
        return errors
    errors += row_fields(data['instructions'], BINDING + ('intent_id', 'mandate_id', 'submitter_ref', 'principal_ref'))
    for name in ('intents', 'mandates', 'screenings', 'account_verifications', 'delegations'):
        errors += row_fields(data.get(name, []), ('instruction_id', 'intent_id', 'mandate_id', 'effective_from', 'effective_until'))
    for key in ('participants', 'profile_ids', 'approval_roles', 'authorized_submitter_refs'):
        if key in data.get('policy', {}) and not isinstance(data['policy'][key], list):
            errors.append(f'policy.{key} must be a list')
    errors += object_list(data.get('policy', {}), 'currency_limits')
    errors += object_list(data, 'prior_instruction_bindings')
    errors += row_fields(data.get('prior_instruction_bindings', []), BINDING)
    controls = data.get('batch_controls', {})
    if 'totals_by_currency' in controls and not isinstance(controls['totals_by_currency'], dict):
        errors.append('batch_controls.totals_by_currency must be an object')
    for collection in ('screenings', 'intents'):
        for row in data.get(collection, []):
            if 'binding' in row and not isinstance(row['binding'], dict):
                errors.append(f'{collection}.binding must be an object')
    return errors


def binding(row):
    return {key: row.get(key) for key in BINDING} | {key: row[key] for key in ('mandate_id', 'rail_family', 'network', 'product') if key in row}


def matches(bound, instruction):
    return isinstance(bound, dict) and bound == binding(instruction) and all(instruction.get(key) is not None for key in BINDING)


def analyze(request):
    data = request['data']
    findings, results, totals, seen_ids, seen_fingerprints = [], [], {}, set(), set()
    instructions = data['instructions']
    policy = data.get('policy', {})
    prior = data.get('prior_instruction_ids')
    if not instructions:
        findings.append(finding('empty-batch', 'At least one proposed instruction is needed.'))
    if prior is None or 'prior_instruction_bindings' not in data or data.get('prior_instruction_ledger_complete') is not True:
        findings.append(finding('duplicate-history-unknown', 'Prior-submission history is not declared complete; retry or duplicate safety is unresolved.'))
    duplicate_ids, duplicate_fingerprints = set(), set()
    for item in instructions:
        identity = item.get('instruction_id')
        fingerprint = tuple(item.get(key) for key in BINDING if key != 'instruction_id')
        if identity in seen_ids:
            duplicate_ids.add(identity)
        if fingerprint in seen_fingerprints:
            duplicate_fingerprints.add(fingerprint)
        seen_ids.add(identity)
        seen_fingerprints.add(fingerprint)
    for item in instructions:
        local = profile_review(data, item, request, 'initiate')
        iid, amount, currency = item.get('instruction_id'), number(item.get('amount'), True), item.get('currency')
        fingerprint = tuple(item.get(key) for key in BINDING if key != 'instruction_id')
        if any(not item.get(key) for key in BINDING) or not sources(item) or amount is None or not isinstance(currency, str) or len(currency) != 3 or not currency.isupper():
            local.append(finding('instruction-incomplete', f'{iid}: exact sourced instruction fields and positive decimal-string money are required.', item))
        if amount is not None and isinstance(currency, str):
            totals.setdefault(currency, []).append(amount)
        if iid in duplicate_ids or fingerprint in duplicate_fingerprints or iid in (prior or []) or fingerprint in {tuple(x.get(k) for k in BINDING if k != 'instruction_id') for x in data.get('prior_instruction_bindings', [])}:
            local.append(finding('duplicate-instruction', f'{iid}: duplicate identifier, same proposed payment details, or previously submitted identifier requires investigation.', item))
        if not day(item.get('execution_date')) or day(item.get('execution_date')) < day(request['as_of']):
            local.append(finding('execution-date-unresolved', f'{iid}: execution date must be a valid current or future date.', item))
        profile = item.get('rail_profile_id')
        if not scoped_policy(policy, request, profile) or not active(policy, item.get('execution_date')):
            local.append(finding('policy-scope-unresolved', f'{iid}: participant/jurisdiction/rail policy and provenance covering review and execution dates are required.', policy))
        intents = [x for x in data.get('intents', []) if x.get('intent_id') == item.get('intent_id') and x.get('instruction_id') == iid]
        if len(intents) != 1 or not (intents[0].get('authorized') is True and sources(intents[0]) and active(intents[0], request['as_of']) and matches(intents[0].get('binding'), item) and active(intents[0], item.get('execution_date')) and intents[0].get('principal_ref') == item.get('principal_ref') and item.get('principal_ref')):
            local.append(finding('payment-intent-unresolved', f'{iid}: one active unrevoked authorization for the exact instruction is required; authentication alone supplies no payment intent.', item))
        intent = intents[0] if len(intents) == 1 else {}
        if item.get('mandate_id'):
            mandates = [x for x in data.get('mandates', []) if x.get('mandate_id') == item['mandate_id']]
            mandate = mandates[0] if len(mandates) == 1 else {}
            maximum = number(mandate.get('max_amount'), True)
            exact = all(mandate.get(k) == item.get(k) and item.get(k) is not None for k in ('payer_account_ref', 'payee_ref', 'payee_account_ref', 'currency', 'rail_profile_id'))
            recurring = mandate.get('frequency') == 'recurring'
            once = mandate.get('frequency') == 'one-off' and mandate.get('permitted_instruction_id') == iid and mandate.get('prior_use_count') == 0
            if not (sources(mandate) and active(mandate, request['as_of']) and exact and maximum is not None and amount is not None and amount <= maximum and (recurring or once) and mandate.get('revocation_check_current') is True and active(mandate, item.get('execution_date'))):
                local.append(finding('mandate-scope-unresolved', f'{iid}: mandate scope, limit, recurrence, current revocation and expiry evidence are insufficient.', mandate))
        elif item.get('direction') == 'debit':
            local.append(finding('mandate-missing', f'{iid}: a debit collection requires a linked mandate review.', item))
        if not item.get('submitter_ref') or item.get('submitter_ref') not in policy.get('authorized_submitter_refs', []):
            local.append(finding('submitter-authority-unresolved', f'{iid}: submitting actor is not listed in the scoped policy.', item))
        if item.get('submitter_ref') != item.get('principal_ref'):
            delegations = [x for x in data.get('delegations', []) if x.get('delegate_ref') == item.get('submitter_ref') and x.get('principal_ref') == item.get('principal_ref')]
            acceptable = [x for x in delegations if sources(x) and active(x, request['as_of']) and active(x, item.get('execution_date')) and x.get('binding') == binding(item)]
            if len(acceptable) != 1 or intent.get('principal_ref') != item.get('principal_ref'):
                local.append(finding('delegation-unresolved', f'{iid}: delegated authority must bind the principal, delegate and exact instruction at review and execution dates.', item))
        screenings = [x for x in data.get('screenings', []) if x.get('instruction_id') == iid]
        if len(screenings) != 1 or not (screenings[0].get('status') == 'clear' and matches(screenings[0].get('binding'), item) and sources(screenings[0]) and active(screenings[0], request['as_of']) and active(screenings[0], item.get('execution_date'))):
            local.append(finding('screening-unresolved', f'{iid}: clear screening bound to the exact payment and explicitly valid through its execution date is missing or unresolved; no sanctions determination is made here.', item))
        checks = [x for x in data.get('account_verifications', []) if x.get('instruction_id') == iid]
        if len(checks) != 1 or not (checks[0].get('status') == 'matched' and sources(checks[0]) and active(checks[0], request['as_of']) and active(checks[0], item.get('execution_date')) and all(checks[0].get(key) == item.get(key) and item.get(key) is not None for key in ('payer_account_ref', 'payee_ref', 'payee_account_ref'))):
            local.append(finding('account-verification-unresolved', f'{iid}: account ownership/access and payee-account binding require evidence explicitly applicable at review and execution dates.', item))
        limits = [x for x in policy.get('currency_limits', []) if x.get('currency') == currency]
        limit = number(limits[0].get('max_instruction_amount'), True) if len(limits) == 1 else None
        if limit is None or amount is None or amount > limit:
            local.append(finding('instruction-limit-unresolved', f'{iid}: amount does not satisfy one explicit currency-specific policy limit.', policy))
        findings.extend(local)
        results.append({'instruction_id': iid, 'binding': binding(item), 'review': 'gaps' if local else 'ready-for-human-review', 'finding_codes': [x['code'] for x in local], 'source_ids': sources(item)})
    computed = {currency: str(total(amounts)) for currency, amounts in sorted(totals.items())}
    controls = data.get('batch_controls', {})
    supplied = controls.get('totals_by_currency', {})
    valid_totals = isinstance(supplied, dict) and set(supplied) == set(computed) and all(number(supplied[c]) == number(computed[c]) for c in computed)
    if controls.get('count') != len(instructions) or not valid_totals or not sources(controls):
        findings.append(finding('batch-control-mismatch', 'Declared batch count and independently sourced totals must match each currency partition exactly.', controls))
    for currency, value in computed.items():
        limits = [x for x in policy.get('currency_limits', []) if x.get('currency') == currency]
        cap = number(limits[0].get('max_batch_amount'), True) if len(limits) == 1 else None
        if cap is None or number(value) > cap:
            findings.append(finding('batch-limit-unresolved', f'{currency}: batch total exceeds or lacks a currency-specific policy cap.', policy))
    if not policy.get('approval_roles'):
        findings.append(finding('approval-roles-missing', 'Named human approval roles must be supplied by the applicable policy.', policy))
    return {'result': {'review': 'gaps' if findings else 'ready-for-human-review', 'instructions': results, 'batch_count': len(instructions), 'totals_by_currency': computed, 'approval_roles': policy.get('approval_roles', []), 'submission_authorized': False, 'authentication_proves_payment_intent': False}, 'findings': findings, 'handoffs': [{'target_skill': 'payment-platform-architecture-reviewer', 'reason': 'Implement binding, deduplication and approval gates in the operating system; this review cannot enforce them.', 'required_inputs': ['exact instruction bindings', 'applicable policy and approval roles', 'source evidence and control findings', 'complete prior-submission history']}]}
