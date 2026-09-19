"""Card operational reconstruction from normalized, source-declared events."""
from collections import Counter
from decimal import Decimal, localcontext
from payment_contract import money, require_currency, timestamp, validate_rule_profile

SKILL = 'card-lifecycle-operations-assistant'
KINDS = {'authorization', 'hold', 'hold-release', 'authorization-reversal',
         'authorization-expiry', 'presentment', 'presentment-reversal', 'clearing',
         'settlement', 'funding', 'posting', 'refund'}
MONEY_KINDS = KINDS - {'authorization-expiry'}


def validate(data):
    if not isinstance(data, dict): return ['data must be an object']
    errors = []
    for key in ('account', 'profile', 'operation'):
        if key in data and not isinstance(data[key], dict): errors.append(f'{key} must be an object')
    for key in ('cards', 'tokens', 'transactions'):
        if key in data and (not isinstance(data[key], list) or any(not isinstance(x, dict) for x in data[key])):
            errors.append(f'{key} must be a list of objects')
    for txn in data.get('transactions', []) if isinstance(data.get('transactions', []), list) else []:
        if not isinstance(txn, dict): continue
        if 'events' in txn and (not isinstance(txn['events'], list) or any(not isinstance(x, dict) for x in txn['events'])):
            errors.append('transaction.events must be a list of objects'); continue
        for ev in txn.get('events', []):
            if 'amount' in ev and ev['amount'] is not None:
                try:
                    if money(ev['amount']) < 0: errors.append('event amount must be nonnegative; use explicit reversal kinds')
                except ValueError as exc: errors.append(str(exc))
            if 'timestamp' in ev and ev['timestamp'] is not None:
                try: timestamp(ev['timestamp'])
                except ValueError as exc: errors.append(str(exc))
    profile = data.get('profile', {})
    if isinstance(profile, dict):
        for key in ('multiple_presentments', 'release_hold_on_presentment'):
            if key in profile and not isinstance(profile[key], bool): errors.append('profile.' + key + ' must be boolean')
        authorities = profile.get('source_authorities', {})
        if not isinstance(authorities, dict) or any(not isinstance(v, list) or any(not isinstance(x, str) for x in v) for v in authorities.values()):
            errors.append('source_authorities must map stages to lists of source-system names')
    string_fields = {'account_id', 'state', 'card_id', 'replaces_card_id', 'token_id', 'transaction_id', 'currency',
                     'event_id', 'kind', 'source_system', 'source_record_id', 'authorization_id', 'hold_id', 'presentment_id', 'type'}
    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in string_fields and child is not None and not isinstance(child, str): errors.append(key + ' must be a string')
                walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(data)
    return errors


def analyze(request):
    d = request['data']; profile = d.get('profile', {}); findings = []
    def flag(code, message, row=None, severity='gap'):
        findings.append({'code': code, 'message': message, 'source_ids': (row or {}).get('source_ids', []), 'severity': severity})
    profile_errors = validate_rule_profile(profile, request['as_of'], participant=request['participant'], jurisdiction=request['jurisdiction'])
    if not profile.get('source_ids'): profile_errors.append('profile requires registered source evidence')
    for error in profile_errors: flag('operating-profile-unresolved', error, profile)
    account = d.get('account', {})
    if not account.get('account_id') or not account.get('state') or not account.get('source_ids'):
        flag('account-state-unresolved', 'Account identity, state and source evidence must be explicit.', account)
    cards = d.get('cards', []); tokens = d.get('tokens', []); txns = d.get('transactions', [])
    card_counts = Counter(x.get('card_id') for x in cards)
    token_counts = Counter(x.get('token_id') for x in tokens)
    card_index = {x.get('card_id'): x for x in cards if x.get('card_id') and card_counts[x.get('card_id')] == 1}
    for card in cards:
        if not card.get('card_id') or card_counts[card.get('card_id')] > 1:
            flag('card-identity-ambiguous', 'Duplicate or missing card ID cannot establish state or replacement linkage.', card)
        if card.get('account_id') != account.get('account_id') or not card.get('account_id'):
            flag('card-account-mismatch', 'Card is not linked to the supplied account.', card)
        if not card.get('state') or not card.get('source_ids'):
            flag('card-state-unresolved', 'Card state requires supplied source evidence.', card)
        if card.get('replaces_card_id') and card['replaces_card_id'] not in card_index:
            flag('replacement-link-unresolved', 'Replacement card refers to an unknown or ambiguous old card.', card)
    for token in tokens:
        if not token.get('token_id') or token_counts[token.get('token_id')] > 1:
            flag('token-identity-ambiguous', 'Duplicate or missing token identity.', token)
        if token.get('card_id') not in card_index:
            flag('token-card-unresolved', 'Token has no unique linked card.', token)
        if not token.get('state') or not token.get('source_ids'):
            flag('token-state-unresolved', 'Token state requires its own evidence; card state does not prove token state.', token)
        card = card_index.get(token.get('card_id'), {})
        if card.get('state') in {'lost', 'stolen', 'blocked', 'closed'} and token.get('state') == 'active':
            flag('token-card-state-divergence', 'Active token remains linked to an unavailable card. Investigate issuer/token-service policy; do not infer automatic suspension or continued eligibility.', token)
    all_events = [ev for txn in txns for ev in txn.get('events', [])]
    event_counts = Counter(ev.get('event_id') for ev in all_events)
    record_counts = Counter((ev.get('source_system'), ev.get('source_record_id')) for ev in all_events if ev.get('source_record_id'))
    txn_counts = Counter(txn.get('transaction_id') for txn in txns)
    assessments = []
    for txn in txns:
        events = txn.get('events', []); quarantined = False; tid = txn.get('transaction_id')
        try: require_currency(txn.get('currency'))
        except ValueError:
            flag('transaction-currency-unresolved', f'{tid}: explicit currency required.', txn); quarantined = True
        if not tid or txn_counts[tid] > 1:
            flag('transaction-identity-ambiguous', 'Duplicate or missing transaction identity.', txn); quarantined = True
        if not txn.get('account_id') or txn.get('account_id') != account.get('account_id'):
            flag('transaction-account-mismatch', f'{tid}: transaction account does not match supplied account.', txn); quarantined = True
        if txn.get('card_id') not in card_index:
            flag('transaction-card-unresolved', f'{tid}: card identity is not uniquely known.', txn); quarantined = True
        for ev in events:
            eid = ev.get('event_id')
            if not eid or event_counts[eid] > 1 or (ev.get('source_record_id') and record_counts[(ev.get('source_system'), ev['source_record_id'])] > 1):
                flag('event-identity-ambiguous', f'{tid}: duplicated/missing event or source-record identity; amounts are quarantined.', ev); quarantined = True
            if ev.get('kind') not in KINDS:
                flag('event-kind-unsupported', f'{tid}: unsupported event kind {ev.get("kind")!r}.', ev); quarantined = True
            if ev.get('kind') in MONEY_KINDS and ev.get('currency') != txn.get('currency'):
                flag('event-currency-mismatch', f'{tid}: event currency differs; no implied FX conversion.', ev); quarantined = True
            if not ev.get('source_ids') or not ev.get('timestamp'):
                flag('event-evidence-missing', f'{tid}: each event requires evidence and offset timestamp.', ev)
            if ev.get('timestamp') and timestamp(ev['timestamp']).date().isoformat() > request['as_of']:
                flag('event-after-as-of', f'{tid}: event is after the requested analysis date.', ev); quarantined = True
        by_id = {ev.get('event_id'): ev for ev in events if ev.get('event_id') and event_counts[ev['event_id']] == 1}
        auths = {eid: ev for eid, ev in by_id.items() if ev.get('kind') == 'authorization'}
        holds = {eid: ev for eid, ev in by_id.items() if ev.get('kind') == 'hold'}
        presentments = {eid: ev for eid, ev in by_id.items() if ev.get('kind') == 'presentment'}
        link_issues = False
        for ev in events:
            kind = ev.get('kind')
            if kind in {'hold', 'presentment', 'authorization-reversal', 'authorization-expiry'}:
                if ev.get('authorization_id') not in auths:
                    link_issues = True
                    flag('authorization-link-unresolved', f'{tid}: {kind} does not identify an authorization in this transaction.', ev)
            if kind == 'hold-release' and ev.get('hold_id') not in holds:
                link_issues = True
                flag('hold-link-unresolved', f'{tid}: hold release has no unique linked hold.', ev)
            if kind == 'presentment-reversal' and ev.get('presentment_id') not in presentments:
                link_issues = True
                flag('presentment-link-unresolved', f'{tid}: reversal has no unique linked presentment.', ev)
            linked_auth = auths.get(ev.get('authorization_id'))
            if kind in {'hold', 'presentment'} and linked_auth and linked_auth.get('outcome') != 'approved':
                link_issues = True
                flag('nonapproved-authorization-link', f'{tid}: {kind} links to an authorization not reported approved; require exception evidence.', ev)
            if linked_auth and ev.get('timestamp') and linked_auth.get('timestamp') and timestamp(ev['timestamp']) < timestamp(linked_auth['timestamp']):
                link_issues = True
                flag('event-chronology-conflict', f'{tid}: linked event precedes its authorization.', ev)
            if kind == 'authorization-expiry':
                flag('expiry-is-not-settlement', f'{tid}: supplied expiry event does not establish clearing, settlement, refund or ledger posting.', ev, 'info')
        counts = Counter(ev.get('authorization_id') for ev in events if ev.get('kind') == 'presentment')
        multiple_policy_unresolved = any(count > 1 for count in counts.values()) and (bool(profile_errors) or profile.get('multiple_presentments') is not True)
        if multiple_policy_unresolved:
            flag('multiple-presentments-review', f'{tid}: multiple presentments require applicable scheme/issuer profile; do not deduplicate distinct presentments.')
        totals = {}
        with localcontext() as ctx:
            ctx.prec = 80
            for kind in sorted(KINDS):
                selected = [ev for ev in events if ev.get('kind') == kind]
                if not selected or kind not in MONEY_KINDS:
                    totals[kind] = None
                elif quarantined or any(ev.get('amount') is None for ev in selected):
                    totals[kind] = None
                    if not quarantined: flag('stage-amount-unresolved', f'{tid}: {kind} amount is missing; no zero is imputed.')
                else:
                    totals[kind] = str(sum((money(ev['amount']) for ev in selected), Decimal('0')))
            hold_reviews = []
            for hid, hold in holds.items():
                releases = [ev for ev in events if ev.get('kind') == 'hold-release' and ev.get('hold_id') == hid]
                linked = [ev for ev in events if ev.get('kind') == 'presentment' and ev.get('authorization_id') == hold.get('authorization_id')]
                unresolved = quarantined or bool(profile_errors) or link_issues or multiple_policy_unresolved or hold.get('amount') is None
                if hold.get('authorization_id') not in auths or auths.get(hold.get('authorization_id'), {}).get('outcome') != 'approved':
                    unresolved = True
                if sum(h.get('authorization_id') == hold.get('authorization_id') for h in holds.values()) > 1 and linked:
                    unresolved = True
                    flag('hold-allocation-unresolved', f'{tid}: several holds share this authorization; allocate presentments to holds before calculating remainders.', hold)
                if any(ev.get('authorization_id') == hold.get('authorization_id') and ev.get('kind') in {'authorization-reversal', 'authorization-expiry'} for ev in events) and not releases:
                    unresolved = True
                    flag('hold-release-evidence-required', f'{tid}: reversal/expiry needs explicit hold-release evidence or a separately implemented release rule.', hold)
                if any(ev.get('kind') == 'presentment-reversal' and ev.get('presentment_id') in {p.get('event_id') for p in linked} for ev in events):
                    unresolved = True
                    flag('hold-restoration-unresolved', f'{tid}: a reversed presentment does not establish whether or when a hold is restored.', hold)
                unresolved |= any(ev.get('amount') is None for ev in releases)
                if not isinstance(profile.get('release_hold_on_presentment'), bool): unresolved = True
                if profile.get('release_hold_on_presentment') is True and linked:
                    # Combining explicit releases with inferred presentment release can double count.
                    if releases: unresolved = True; flag('hold-release-overlap', f'{tid}: explicit releases coexist with presentment-based release; require allocation before calculating a remainder.', hold)
                    unresolved |= any(ev.get('amount') is None for ev in linked)
                remainder = None
                if not unresolved:
                    reduction = sum((money(ev['amount']) for ev in releases), Decimal('0'))
                    if profile.get('release_hold_on_presentment') is True:
                        reduction += sum((money(ev['amount']) for ev in linked), Decimal('0'))
                    remainder = money(hold['amount']) - reduction
                    if remainder < 0:
                        flag('hold-over-release', f'{tid}: reported/inferred release exceeds the recorded hold; do not clamp the discrepancy to zero.', hold)
                        remainder = None
                hold_reviews.append({'hold_id': hid, 'authorization_id': hold.get('authorization_id'),
                                     'recorded_hold': hold.get('amount'), 'remaining_hold_scenario': str(remainder) if remainder is not None else None,
                                     'basis': 'profile-dependent reconstruction; not verified available balance',
                                     'source_ids': sorted({s for ev in [hold] + releases + linked for s in ev.get('source_ids', [])})})
        observed_stages = sorted({ev.get('kind') for ev in events if ev.get('kind') in KINDS})
        for stage in ('clearing', 'settlement', 'funding', 'posting'):
            selected = [ev for ev in events if ev.get('kind') == stage]
            allowed = profile.get('source_authorities', {}).get(stage, []) if isinstance(profile.get('source_authorities', {}), dict) else []
            if selected and (profile_errors or not allowed or any(ev.get('source_system') not in allowed for ev in selected)):
                flag('stage-authority-unresolved', f'{tid}: {stage} events are supplied claims without an applicable source-authority mapping.')
        assessments.append({'transaction_id': tid, 'currency': txn.get('currency'), 'quarantined': quarantined,
                            'observed_stages': observed_stages, 'stage_amounts': totals, 'hold_assessments': hold_reviews,
                            'authorization_is_settlement': False, 'events': events,
                            'completion_or_funds_availability_verified': False})
    if not txns: flag('transaction-events-missing', 'No transaction events supplied; explain structural card/account/token state only.')
    operation = d.get('operation', {})
    requirements = []
    if operation:
        requirements = ['Identify the exact account/card/token scope and current authoritative state.',
                        'Obtain current issuer/scheme eligibility and identity/approval evidence.',
                        'Resolve outstanding holds, pending presentments, recurring credentials and token linkages.',
                        'Have the authorized runtime validate and execute any action; retain returned result evidence.']
        if operation.get('type') in {'replace-lost-card', 'reissue-card'}:
            requirements.append('Keep old and replacement card identities separate; token migration or suspension needs its own policy and returned evidence.')
        flag('operation-draft-only', 'Operation is a proposed work item; no card, account, token, hold or ledger state is changed.', operation)
    return {'result': {'account_state': account, 'card_states': cards, 'token_states': tokens,
                       'transaction_assessments': assessments, 'profile_issues': profile_errors,
                       'requested_operation': operation, 'controlled_action_requirements': requirements,
                       'card_token_or_account_state_changed': False},
            'findings': findings, 'handoffs': ([{'target_skill': 'payment-servicing-planner', 'reason': 'Prepare any ordinary refund/return as its own scoped plan; lifecycle review grants no repair authority.', 'required_inputs': ['original transaction', 'eligible operation', 'authority and policy evidence'], 'source_ids': operation.get('source_ids', [])}] if operation.get('type') in {'refund', 'return', 'cancel'} else [])}
