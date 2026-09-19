"""Compare a concrete bank-payment use case against sourced native rail profiles."""
from payment_foundation import load_rail_profile
from domain_support import finding, number, object_list, row_fields, sources

SKILL = 'bank-payment-workflow-designer'


def validate(data):
    if not isinstance(data, dict):
        return ['data must be an object']
    errors = []
    if 'requirements' in data and not isinstance(data['requirements'], dict):
        errors.append('requirements must be an object')
    if not isinstance(data.get('candidate_profile_ids'), list) or not all(isinstance(x, str) for x in data.get('candidate_profile_ids', [])):
        errors.append('candidate_profile_ids must be a list of profile IDs')
    for key in ('access_evidence', 'timing_evidence', 'funding_evidence', 'costs'):
        errors += object_list(data, key)
    if errors:
        return errors
    errors += row_fields([data.get('requirements', {})], ('currency', 'direction', 'amount', 'urgency', 'availability', 'payer_location', 'payee_location', 'return_need'))
    for key in ('access_evidence', 'timing_evidence', 'funding_evidence', 'costs'):
        errors += row_fields(data.get(key, []), ('profile_id', 'participant', 'currency', 'available_amount', 'per_payment_fee', 'fixed_monthly_fee'))
    return errors


def analyze(request):
    data, findings = request['data'], []
    requirements = data.get('requirements', {})
    required = ('currency', 'direction', 'amount', 'urgency', 'availability', 'payer_location', 'payee_location', 'return_need')
    if any(not requirements.get(k) for k in required) or not sources(requirements) or number(requirements.get('amount'), True) is None:
        findings.append(finding('requirements-incomplete', 'Currency, direction, positive amount, timing, availability, party locations and return needs must be sourced.', requirements))
    if requirements.get('direction') not in {'credit', 'debit'} or requirements.get('urgency') not in {'instant', 'same-day', 'scheduled'} or requirements.get('availability') not in {'24x7', 'business-hours'}:
        findings.append(finding('unsupported-requirements', 'Use supported credit/debit, instant/same-day/scheduled, and 24x7/business-hours dimensions; other requirements need specialist extension.', requirements))
    if not data['candidate_profile_ids']:
        findings.append(finding('no-rail-candidates', 'Choose concrete native rail profiles before comparing workflow designs.'))
    candidates = []
    seen = set()
    for profile_id in data['candidate_profile_ids']:
        if profile_id in seen:
            findings.append(finding('duplicate-profile', f'{profile_id}: duplicate candidate profile.'))
            continue
        seen.add(profile_id)
        profile = load_rail_profile(profile_id)
        if not profile:
            candidates.append({'profile_id': profile_id, 'review': 'unsupported-profile', 'decision_criteria': [], 'source_refs': []})
            findings.append(finding('unsupported-rail-profile', f'{profile_id}: no bundled native profile; no generic rail substitution.'))
            continue
        local, matrix = [], []

        def criterion(name, status, rationale, evidence=None):
            matrix.append({'criterion': name, 'assessment': status, 'rationale': rationale, 'source_ids': sources(evidence or {})})
            if status != 'compatible':
                local.append(finding(f'{name}-{status}', f'{profile_id}: {rationale}', evidence))

        criterion('jurisdiction', 'compatible' if profile.get('jurisdiction') == request['jurisdiction'] else 'incompatible', f"Profile scope {profile.get('jurisdiction')} compared with requested {request['jurisdiction']}.")
        criterion('currency', 'compatible' if requirements.get('currency') in profile.get('currencies', []) else 'incompatible', f"Requested {requirements.get('currency')}; supported currencies {profile.get('currencies', [])}.", requirements)
        criterion('direction', 'compatible' if requirements.get('direction') in profile.get('directions', []) else 'incompatible', f"Requested {requirements.get('direction')}; supported directions {profile.get('directions', [])}.", requirements)
        criterion('availability', 'compatible' if requirements.get('availability') == profile.get('availability') or requirements.get('availability') == 'business-hours' and profile.get('availability') == '24x7' else 'incompatible', f"Profile operation {profile.get('availability')}; customer requirement {requirements.get('availability')}.", requirements)
        if not profile.get('review_due') or request['as_of'] > profile['review_due'] or not profile.get('reviewed_on') or request['as_of'] < profile['reviewed_on']:
            local.append(finding('profile-review-overdue', f'{profile_id}: refresh the native source profile before relying on the design.'))
        access_rows = [x for x in data.get('access_evidence', []) if x.get('profile_id') == profile_id]
        access = access_rows[0] if len(access_rows) == 1 else {}
        access_ok = sources(access) and access.get('participant') == request['participant'] and access.get('contracted') is True and access.get('reachable') is True and access.get('payer_location') == requirements.get('payer_location') and access.get('payee_location') == requirements.get('payee_location')
        criterion('access-and-reach', 'compatible' if access_ok else 'unknown', 'Institution access, contracted product and both actual endpoint locations/reach must be evidenced; public scheme access does not prove customer availability.', access)
        timing_rows = [x for x in data.get('timing_evidence', []) if x.get('profile_id') == profile_id]
        timing = timing_rows[0] if len(timing_rows) == 1 else {}
        native_class = profile.get('timing', {}).get('class')
        possible = requirements.get('urgency') != 'instant' or native_class == 'instant'
        timing_ok = sources(timing) and timing.get('participant') == request['participant'] and timing.get('required_urgency') == requirements.get('urgency') and timing.get('delivery_compatible') is True and timing.get('cutoff_and_calendar_checked') is True
        criterion('delivery-timing', 'incompatible' if not possible else 'compatible' if timing_ok else 'unknown', f"Native timing class {native_class}; actual instruction cutoff/calendar and customer-delivery commitment require provider evidence.", timing)
        funding_rows = [x for x in data.get('funding_evidence', []) if x.get('profile_id') == profile_id]
        funding = funding_rows[0] if len(funding_rows) == 1 else {}
        balance, amount = number(funding.get('available_amount')), number(requirements.get('amount'), True)
        funding_ok = sources(funding) and funding.get('participant') == request['participant'] and funding.get('currency') == requirements.get('currency') and funding.get('arrangement') and balance is not None and amount is not None and balance >= amount
        criterion('funding', 'declared-only' if funding_ok else 'unknown', 'The supplied currency-specific balance and free-text funding arrangement are declarations. Compatibility with the native settlement mechanism requires specialist review; neither text presence nor balance validates the funding model or grants access.', funding)
        if requirements.get('direction') == 'debit':
            criterion('collection-authority', 'compatible' if requirements.get('mandate_evidence_available') is True else 'unknown', 'Debit collection needs a valid mandate; its exact scope is separately reviewed at initiation.', requirements)
        else:
            criterion('payment-intent', 'compatible' if requirements.get('intent_evidence_available') is True else 'unknown', 'The future instruction requires explicit payer intent independently of authentication or request-for-payment receipt.', requirements)
        if requirements.get('return_need') not in {'none', 'best-effort-recovery', 'refund-rights-review'}:
            criterion('servicing', 'incompatible', 'Guaranteed rollback or recovery is not supported by this rail comparison.', requirements)
        else:
            criterion('servicing', 'compatible' if requirements.get('return_need') in {'none', 'best-effort-recovery'} else 'unknown', 'Native finality and return mechanisms remain distinct; consumer refund rights and operational return eligibility require separate review.', requirements)
        cost_rows = [x for x in data.get('costs', []) if x.get('profile_id') == profile_id]
        cost = cost_rows[0] if len(cost_rows) == 1 else {}
        costs_complete = sources(cost) and cost.get('currency') == requirements.get('currency') and number(cost.get('per_payment_fee')) is not None and number(cost.get('fixed_monthly_fee')) is not None
        criterion('commercial-cost', 'compatible' if costs_complete else 'unknown', 'Actual contracted per-payment and fixed costs must be supplied; public fees and zero assumptions are not customer economics.', cost)
        findings.extend(local)
        candidates.append({'profile_id': profile_id, 'review': 'requirements-conflict' if any(x['assessment'] == 'incompatible' for x in matrix) else 'evidence-needed' if local else 'candidate-for-human-review', 'decision_criteria': matrix, 'profile_facts': {key: profile.get(key) for key in ('availability', 'timing', 'finality', 'returns', 'funding', 'access', 'message_contract_id', 'limitations')}, 'source_refs': profile.get('source_refs', []), 'profile_reviewed_on': profile.get('reviewed_on'), 'contracted_cost': {'currency': cost.get('currency'), 'per_payment_fee': cost.get('per_payment_fee'), 'fixed_monthly_fee': cost.get('fixed_monthly_fee')} if costs_complete else None})
    return {'result': {'requirements': requirements, 'rail_comparison': candidates, 'preferred_profile_id': None, 'selection_rule': 'Human choice among candidates that meet required dimensions after evidence gaps are resolved; no inferred cheapest rail.', 'workflow': [{'stage': 'capture-intent', 'artifact': 'exact instruction and payer authorization or collection mandate'}, {'stage': 'review-initiation', 'artifact': 'account/payee binding, screening, limit and batch-control review'}, {'stage': 'fund-and-submit', 'artifact': 'operator-owned approval, funding and idempotent submission record'}, {'stage': 'observe-outcome', 'artifact': 'native acknowledgement, reject, settlement and posting evidence kept distinct'}, {'stage': 'reconcile-and-service', 'artifact': 'linked cash/ledger reconciliation plus separate servicing plan if required'}]}, 'findings': findings, 'handoffs': [{'target_skill': 'payment-initiation-control-reviewer', 'reason': 'Bind exact proposed instructions, authority, screening and batch controls before authorized submission.', 'required_inputs': ['selected native profile', 'exact instructions', 'intent/mandate evidence', 'comparison findings']}, {'target_skill': 'payment-regulatory-applicability-reviewer', 'reason': 'Determine entity/activity and national obligations beyond this bounded rail comparison.', 'required_inputs': ['entity', 'activity', 'jurisdictions', 'flow and customer model']}, {'target_skill': 'payment-economics-modeler', 'reason': 'Compare sourced commercial and funding assumptions by participant and scenario.', 'required_inputs': ['candidate rails', 'contracted cost evidence', 'volume and loss assumptions']}]}
