"""Earned compensation activity, explicit splits and linked fractional chargebacks."""
from domain_support import Review, total, validate_shape
from insurance_foundation import number

SKILL = 'insurance-producer-compensation-reconciler'
METHOD = 'earned-base-rate-split-linked-chargeback'


def validate(doc):
    errors = validate_shape(doc, arrays=('agreements', 'events', 'reported'), objects=('period',),
                            numbers=('rate', 'share', 'base_amount', 'fraction', 'net_earned'),
                            dates=('start', 'end', 'date', 'effective_from', 'effective_to'),
                            lists=('source_refs', 'jurisdictions', 'lines_of_business'), booleans=('ledger_complete',))
    for row in doc.get('data', {}).get('agreements', []) if not errors else []:
        if not isinstance(row.get('splits', []), list) or any(not isinstance(x, dict) for x in row.get('splits', [])):
            errors.append('agreement splits must be an array of objects')
    return errors


def evaluate(doc):
    d, r = doc['data'], Review(doc, METHOD)
    start, end = r.date(d.get('period', {}).get('start'), 'Period start'), r.date(d.get('period', {}).get('end'), 'Period end')
    if start and end and start > end:
        r.add('period', 'Earnings period is reversed.')
    if d.get('agency_id') != doc['context']['object_id'] or not d.get('currency') or d.get('ledger_complete') is not True:
        r.add('scope', 'Require context-bound agency, one currency and complete earned activity ledger.')
    agreements, events, reported = d.get('agreements', []), d.get('events', []), d.get('reported', [])
    r.unique(agreements, 'agreement_id')
    r.unique(events, 'event_id')
    r.unique(reported, 'producer_id')
    agreement_map = {}
    for row in agreements:
        r.evidence(row, 'Compensation agreement')
        splits = row.get('splits', [])
        r.unique(splits, 'producer_id')
        rate = r.required(number(row.get('rate')), 'Commission rate', row)
        if rate is not None and rate > 1:
            r.add('rate', 'Rate must be a decimal fraction from zero to one.', row)
        a, b = r.date(row.get('effective_from'), 'Agreement start', row), r.date(row.get('effective_to'), 'Agreement end', row, future=True)
        if a and b and a > b:
            r.add('agreement-period', 'Agreement effective period is reversed.', row)
        shares = [r.required(number(x.get('share')), 'Producer split share', x) for x in splits]
        for split in splits:
            r.evidence(split, 'Contractual producer split')
        if not splits or None in shares or total(shares) != 1:
            r.add('split-total', 'Explicit producer shares must sum to exactly one; no residual recipient inferred.', row)
        if not row.get('basis') or not row.get('earning_trigger'):
            r.add('earning-trigger', 'Supply contractual premium basis and earning trigger.', row)
        agreement_map[row.get('agreement_id')] = (row, rate, a, b)
    computed, registry, reversed_fraction = {}, [], {}
    for event in sorted(events, key=lambda x: (x.get('date') or '', 0 if x.get('kind') == 'earned' else 1, x.get('event_id') or '')):
        good = r.evidence(event, 'Earned activity')
        aid, eid = event.get('agreement_id'), event.get('event_id')
        agreement, rate, a, b = agreement_map.get(aid, ({}, None, None, None))
        day = r.date(event.get('date'), 'Earning or chargeback date', event)
        if not day or not start or not end or not start <= day <= end or not a or not b or not a <= day <= b:
            good = False
            r.add('event-period', 'Activity must fall in this ledger and supplied agreement effective periods.', event)
        if event.get('currency') != d.get('currency') or event.get('basis') != agreement.get('basis') or not event.get('policy_id'):
            good = False
            r.add('event-basis', 'Currency, policy and contractual base must bind to the earning event.', event)
        gross = None
        if event.get('kind') == 'earned':
            base = r.required(number(event.get('base_amount')), 'Earned commissionable base', event)
            if event.get('trigger_evidence') != agreement.get('earning_trigger'):
                good = False
                r.add('trigger', 'Event must evidence the agreement earning trigger; written or collected premium alone is not automatically earned.', event)
            gross = base * rate if good and base is not None and rate is not None else None
        elif event.get('kind') == 'chargeback':
            if not event.get('chargeback_basis'):
                good = False
                r.add('chargeback-basis', 'Supply the contractual chargeback clause or approved entitlement basis; cancellation alone cannot create a chargeback.', event)
            prior = computed.get(event.get('reverses_id'))
            fraction = r.required(number(event.get('fraction')), 'Contractual chargeback fraction', event)
            if not prior or prior['kind'] != 'earned' or prior['agreement_id'] != aid or prior['policy_id'] != event.get('policy_id') or prior['gross'] is None or fraction is None:
                good = False
                r.add('chargeback-link', 'Chargeback must link a known earlier earned event for the same policy and agreement.', event)
            elif fraction > 1 or reversed_fraction.get(event['reverses_id'], 0) + fraction > 1:
                good = False
                r.add('over-chargeback', 'Cumulative chargebacks exceed original earned commission.', event)
            else:
                reversed_fraction[event['reverses_id']] = reversed_fraction.get(event['reverses_id'], 0) + fraction
                gross = -prior['gross'] * fraction if good else None
        else:
            r.add('event-kind', 'Only earned events and linked fractional chargebacks are supported.', event)
        allocations = {x['producer_id']: gross * number(x['share']) for x in agreement.get('splits', [])} if gross is not None and all(number(x.get('share')) is not None for x in agreement.get('splits', [])) else None
        result = {'event_id': eid, 'agreement_id': aid, 'policy_id': event.get('policy_id'), 'kind': event.get('kind'), 'gross': gross, 'producer_allocations': allocations, 'source_refs': event.get('source_refs', [])}
        computed[eid] = result
        registry.append(result)
    if not events or not reported:
        r.add('ledger', 'Supply nonempty earned activity and reported producer controls.')
    controls = {}
    for row in reported:
        r.evidence(row, 'Reported producer earnings')
        controls[row.get('producer_id')] = r.required(number(row.get('net_earned')), 'Reported net earned', row)
        if row.get('currency') != d.get('currency'):
            r.add('reported-currency', 'Reported producer earnings use another currency.', row)
    producers = {s['producer_id'] for a in agreements for s in a.get('splits', []) if s.get('producer_id')}
    if set(controls) != producers:
        r.add('producer-controls', 'Reported controls must cover exactly the contractual split recipients.')
    totals = {p: total(row['producer_allocations'].get(p, 0) for row in registry) for p in producers} if r.clear and all(x['producer_allocations'] is not None for x in registry) else None
    differences = {p: totals[p] - controls[p] for p in producers} if totals is not None else None
    if differences is not None and any(differences.values()):
        r.add('earnings-break', 'Computed earned activity differs from reported producer controls.', severity='review')
    return r.finish({'event_ledger': registry, 'currency': d.get('currency'), 'net_earned_by_producer': totals,
                         'reconciliation_differences': differences, 'payment_authorized': False, 'licensing_determination': 'not-performed'})
