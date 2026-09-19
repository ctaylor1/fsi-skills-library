"""Use-case assessment of supplied stablecoin and fiat quotes, not legal approval."""
from datetime import date
from decimal import Decimal, InvalidOperation
from payment_foundation import finding

SKILL = 'stablecoin-settlement-assessor'
COSTS = ('network', 'provider', 'fx', 'onramp', 'offramp', 'redemption', 'custody', 'liquidity', 'operations')
EVIDENCE = ('availability', 'provider_counterparty', 'legal_applicability', 'sanctions_aml', 'liquidity_access', 'failure_recovery', 'economic_finality')
STABLE_EVIDENCE = ('issuer_reserves', 'redemption_rights', 'custody_control', 'chain_finality', 'freeze_fork_bridge', 'holder_rights')
ROLES = {'issuer', 'holder', 'intermediary', 'custodian'}


def text(v):
    return isinstance(v, str) and bool(v.strip())


def money(v):
    if isinstance(v, bool) or not isinstance(v, (str, int)):
        raise ValueError('money requires decimal string or integer')
    try:
        n = Decimal(v)
    except InvalidOperation as exc:
        raise ValueError('invalid decimal money') from exc
    if not n.is_finite() or n < 0:
        raise ValueError('money must be finite and nonnegative')
    return n


def validate(d):
    errors = []
    for key in ('use_case', 'participant_ref', 'origin_jurisdiction', 'destination_jurisdiction', 'source_currency', 'destination_currency', 'comparison_currency', 'accountable_owner'):
        if not text(d.get(key)):
            errors.append(key + ' required')
    for key in ('source_currency', 'destination_currency', 'comparison_currency'):
        if not isinstance(d.get(key), str) or len(d[key]) != 3 or not d[key].isupper():
            errors.append(key + ' needs uppercase three-letter code')
    for key in ('principal',):
        try:
            if money(d.get(key)) <= 0:
                errors.append(key + ' must be positive')
        except ValueError as exc:
            errors.append(str(exc))
    for key in ('window_start', 'window_end'):
        try:
            date.fromisoformat(d[key])
        except (KeyError, ValueError, TypeError):
            errors.append(key + ' needs ISO date')
    if not errors and d['window_start'] > d['window_end']:
        errors.append('window order invalid')
    roles = d.get('role_assignments')
    if not isinstance(roles, list) or not roles:
        errors.append('role_assignments needs explicit participant responsibilities')
        roles = []
    seen = set()
    for r in roles:
        if not isinstance(r, dict):
            errors.append('role assignment must be object')
            continue
        key = (r.get('entity_ref'), r.get('role'))
        if key in seen:
            errors.append('duplicate role assignment')
        seen.add(key)
        if not text(r.get('entity_ref')) or r.get('role') not in ROLES or not text(r.get('responsibility')):
            errors.append('role assignment requires entity_ref, supported role and responsibility')
        if not r.get('source_ids'):
            errors.append('role assignment requires source_ids')
    options = d.get('options')
    if not isinstance(options, list) or len(options) != 2:
        return errors + ['options must contain exactly one stablecoin and one fiat alternative']
    if {r.get('type') for r in options if isinstance(r, dict)} != {'stablecoin', 'fiat'}:
        errors.append('options require one stablecoin and one fiat')
    ids = set()
    for r in options:
        if not isinstance(r, dict):
            errors.append('option must be object')
            continue
        for key in ('option_id', 'instrument_ref', 'provider_ref', 'quote_basis_ref'):
            if not text(r.get(key)):
                errors.append('option ' + key + ' required')
        if r.get('option_id') in ids:
            errors.append('duplicate option_id')
        ids.add(r.get('option_id'))
        if r.get('type') == 'stablecoin':
            for key in ('asset_ref', 'chain_id', 'issuer_ref', 'custodian_ref'):
                if not text(r.get(key)):
                    errors.append('stablecoin ' + key + ' required')
        if not r.get('source_ids'):
            errors.append('option source_ids required')
        if not isinstance(r.get('quote_binding'), dict):
            errors.append('quote_binding object required')
        if r.get('availability_status') not in {'production', 'pilot', 'research', 'unknown'}:
            errors.append('availability_status must distinguish production/pilot/research/unknown')
        if type(r.get('costs_complete')) is not bool:
            errors.append('costs_complete boolean required')
        costs = r.get('costs')
        if not isinstance(costs, dict) or set(costs) != set(COSTS):
            errors.append('costs must explicitly include exactly: ' + ', '.join(COSTS))
        else:
            for key, value in costs.items():
                if value is not None:
                    try:
                        money(value)
                    except ValueError as exc:
                        errors.append(key + ': ' + str(exc))
        if r.get('delivered_amount') is not None:
            try:
                money(r['delivered_amount'])
            except ValueError as exc:
                errors.append(str(exc))
        profile = r.get('applicability')
        if not isinstance(profile, dict):
            errors.append('applicability profile required')
            continue
        for key in ('profile_id', 'version', 'owner'):
            if not text(profile.get(key)):
                errors.append('applicability ' + key + ' required')
        for key in ('reviewed_on', 'review_due'):
            try:
                date.fromisoformat(profile[key])
            except (KeyError, ValueError, TypeError):
                errors.append('applicability ' + key + ' needs ISO date')
        for key in ('jurisdictions', 'participant_roles', 'instrument_refs') + (('asset_refs', 'chain_ids') if r.get('type') == 'stablecoin' else ()):
            if not isinstance(profile.get(key), list) or not profile[key] or any(not text(v) for v in profile[key]):
                errors.append('applicability ' + key + ' list required')
        if not profile.get('source_ids'):
            errors.append('applicability source_ids required')
        if not isinstance(r.get('evidence'), dict):
            errors.append('evidence object required')
    return errors


def analyze(request):
    d = request['data']
    findings = []
    results = []
    def gap(code, message, row=None):
        findings.append(finding(code, message, (row or {}).get('source_ids', [])))
    if request['participant'] != d['participant_ref']:
        gap('participant-mismatch', 'Envelope participant must identify the assessed entity.')
    if request['jurisdiction'] != d['origin_jurisdiction']:
        gap('origin-jurisdiction-mismatch', 'Envelope jurisdiction must match the origin of this bounded use case.')
    if d['window_start'] < request['as_of']:
        gap('historical-quote-window', 'Refresh quotes and access for a prospective settlement decision.')
    participant_roles = {r['role'] for r in d['role_assignments'] if r['entity_ref'] == d['participant_ref']}
    if not participant_roles:
        gap('participant-role-unknown', 'Identify this participant as holder, issuer, intermediary or custodian; duties do not transfer automatically.')
    for o in d['options']:
        local_gaps = []
        def issue(code, message):
            local_gaps.append(code)
            gap(code, o['option_id'] + ': ' + message, o)
        p = o['applicability']
        if not p['reviewed_on'] <= request['as_of'] <= p['review_due'] or d['window_end'] > p['review_due']:
            issue('stale-applicability', 'Profile does not cover the as-of date and full decision window.')
        if not {d['origin_jurisdiction'], d['destination_jurisdiction']}.issubset(set(p['jurisdictions'])) or not participant_roles or not participant_roles.issubset(set(p['participant_roles'])):
            issue('applicability-mismatch', 'Profile must cover both corridor jurisdictions and the actual participant roles.')
        if o['instrument_ref'] not in p['instrument_refs']:
            issue('instrument-profile-mismatch', 'Applicability review does not cover this instrument.')
        if o['type'] == 'stablecoin' and (o['chain_id'] not in p.get('chain_ids', []) or o['asset_ref'] not in p.get('asset_refs', [])):
            issue('asset-chain-profile-mismatch', 'Review must explicitly cover this asset and chain.')
        evidence = o['evidence']
        for key in EVIDENCE + (STABLE_EVIDENCE if o['type'] == 'stablecoin' else ()):
            if not text(evidence.get(key)):
                issue('missing-' + key, 'Require a reviewed evidence reference for ' + key + '; unknown is not approval.')
        if o['availability_status'] != 'production':
            issue('not-evidenced-production', 'Pilot, research and unknown availability cannot be treated as deployable access.')
        if o['type'] == 'stablecoin':
            for entity, role in [(o['issuer_ref'], 'issuer'), (o['custodian_ref'], 'custodian')]:
                if not any(r['entity_ref'] == entity and r['role'] == role for r in d['role_assignments']):
                    issue('role-owner-missing', role + ' needs a separately assigned entity responsibility.')
        binding = {k: d[k] for k in ('principal', 'source_currency', 'destination_currency', 'comparison_currency', 'window_start', 'window_end')}
        quote_matches = o['quote_binding'] == binding
        if not quote_matches:
            issue('quote-binding-mismatch', 'Quote must bind exactly to this principal, source/destination/cost currencies and window.')
        cost_known = quote_matches and o['costs_complete'] and all(o['costs'][k] is not None for k in COSTS)
        if not cost_known:
            issue('unknown-all-in-cost', 'Unknown or incomplete costs prevent a total and a price comparison.')
        total = sum((money(o['costs'][k]) for k in COSTS), Decimal(0)) if cost_known else None
        if o.get('delivered_amount') is None:
            issue('unknown-delivered-amount', 'Evidence the final fiat amount available to the beneficiary; token par is not a conversion quote.')
        results.append({'option_id': o['option_id'], 'type': o['type'], 'cost_currency': d['comparison_currency'], 'all_in_cost': str(total) if total is not None else None, 'destination_currency': d['destination_currency'], 'delivered_amount': o.get('delivered_amount'), 'availability_status': o['availability_status'], 'unresolved_conditions': local_gaps, 'adoption_authorized': False})
    stable = next(r for r in results if r['type'] == 'stablecoin')
    fiat = next(r for r in results if r['type'] == 'fiat')
    comparable = all(r['all_in_cost'] is not None and r['delivered_amount'] is not None for r in results)
    same_delivery = comparable and money(stable['delivered_amount']) == money(fiat['delivered_amount'])
    if comparable and not same_delivery:
        gap('unequal-beneficiary-value', 'Quotes deliver different fiat amounts; total cost delta is not a like-for-like saving.')
    delta = str(money(fiat['all_in_cost']) - money(stable['all_in_cost'])) if same_delivery else None
    return {'result': {'use_case': d['use_case'], 'corridor': [d['origin_jurisdiction'], d['destination_jurisdiction']], 'principal': d['principal'], 'source_currency': d['source_currency'], 'participant_roles': sorted(participant_roles), 'role_assignments': d['role_assignments'], 'options': results, 'fiat_minus_stablecoin_cost': delta, 'comparison_currency': d['comparison_currency'], 'comparison_is_adoption_recommendation': False, 'settlement_authorized': False, 'peg_guaranteed': False, 'redemption_guaranteed': False, 'legal_permission_determined': False, 'next_step': 'Review evidence-qualified alternatives with treasury, product risk and corridor legal owners.'}, 'findings': findings, 'handoffs': [{'target_skill': 'stablecoin-payment-controls-reviewer', 'reason': 'Evaluate applicable issuer, custody and holder controls under separately approved role-specific policy profiles.', 'required_inputs': ['role-specific active policy_profile', 'control evidence', 'unresolved assessment conditions']}, {'target_skill': 'payment-liquidity-and-funding-analyzer', 'reason': 'Model dated fiat funding and redemption availability by entity and currency.', 'required_inputs': ['funding window', 'entity accounts', 'firm inflows and obligations', 'source evidence']}], 'limitations': ['Cost inputs are disjoint all-in amounts for the same stated principal and window in the comparison currency; the helper does not perform FX conversion or verify quotes.', 'Evidence references and source IDs are not authentication, legal conclusions or actual access. No peg, redemption, technical or legal finality guarantee is inferred.']}
