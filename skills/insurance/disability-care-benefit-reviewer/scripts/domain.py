"""Criterion evidence and bounded daily-indemnity arithmetic; no medical decision."""
from datetime import timedelta

from domain_support import Review, total, validate_shape
from insurance_foundation import number

SKILL = 'disability-care-benefit-reviewer'
METHOD = 'continuous-calendar-daily-indemnity-offset'


def validate(doc):
    return validate_shape(doc, arrays=('criteria', 'observations', 'periods', 'offsets'), objects=('benefit',),
                          numbers=('daily_amount', 'daily_limit', 'remaining_limit', 'waiting_days', 'amount'),
                          dates=('start', 'end', 'onset_date', 'effective_from', 'effective_to'),
                          lists=('source_refs', 'jurisdictions', 'lines_of_business'), booleans=('offset_inventory_complete',))


def evaluate(doc):
    d, r = doc['data'], Review(doc, METHOD)
    if d.get('claim_id') != doc['context']['object_id'] or d.get('benefit_type') not in {'disability', 'long-term-care'}:
        r.add('scope', 'Context claim and explicit disability or long-term-care benefit type required.')
    if doc['context']['capacity'] not in {'carrier-benefits-review', 'benefits-administrator-review'}:
        r.add('capacity', 'Carrier/administrator evidence review must remain separate from claimant advocacy.')
    if any(str(doc['context'].get(k, '')).strip().lower() in {'', 'unknown', 'na', 'n/a'}
           for k in ('capacity', 'represented_party', 'object_id', 'jurisdiction', 'line_of_business')):
        r.add('scope', 'Unresolved case context cannot establish this benefit calculation scope.')
    scope_valid = r.clear
    criteria, observations, periods, offsets = (d.get(k, []) for k in ('criteria', 'observations', 'periods', 'offsets'))
    criteria_unique = r.unique(criteria, 'criterion_id')
    periods_unique = r.unique(periods, 'period_id')
    observations_unique = r.unique(observations, 'observation_id')
    offsets_unique = r.unique(offsets, 'offset_id')
    if not criteria or not periods:
        r.add('criterion-period', 'Policy-derived required criteria and explicit benefit periods are needed.')
    offset_inventory_valid = d.get('offset_inventory_complete') is True and 'offsets' in d and offsets_unique
    if not offset_inventory_valid:
        r.add('offset-inventory', 'An explicit complete offset inventory with unique offset identities, including an empty list for no offsets, is required.')
    criterion_map, criterion_valid = {}, {}
    for row in criteria:
        valid = r.evidence(row, 'Policy criterion') and criteria_unique
        if not row.get('description') or row.get('assessor_role') not in {'medical', 'vocational', 'administrative'}:
            valid = False
            r.add('criterion-role', 'Each criterion needs policy wording and responsible qualified assessor role.', row)
        criterion_map[row.get('criterion_id')] = row
        criterion_valid[row.get('criterion_id')] = valid
    benefit = d.get('benefit', {})
    benefit_evidence_valid = r.evidence(benefit, 'Benefit basis, waiting period and cap')
    values = {key: r.required(number(benefit.get(key)), key, benefit) for key in ('daily_amount', 'daily_limit', 'remaining_limit', 'waiting_days')}
    onset = r.date(benefit.get('onset_date'), 'Evidence-established continuous period onset', benefit)
    wait = values['waiting_days']
    wait_valid = wait is not None and wait == wait.to_integral_value() and wait <= 365000
    if wait is not None and wait != wait.to_integral_value():
        r.add('waiting-days', 'Waiting days must be a nonnegative whole count.', benefit)
    if wait is not None and wait > 365000:
        r.add('waiting-days-limit', 'Waiting period exceeds the bounded supported calendar range.', benefit)
    currency_valid = bool(d.get('currency')) and benefit.get('currency') == d.get('currency')
    if not currency_valid:
        r.add('currency', 'One explicit benefit/offset currency is required.', benefit)
    method_basis_valid = scope_valid and benefit_evidence_valid and currency_valid
    eligible_start = None
    if method_basis_valid and onset and wait_valid:
        try:
            eligible_start = onset + timedelta(days=int(wait))
        except OverflowError:
            r.add('waiting-date-overflow', 'Waiting period exceeds the supported calendar date range.', benefit)
    periods_map, period_valid, report, used_dates = {}, {}, [], {}
    for row in periods:
        pid = row.get('period_id')
        valid = r.evidence(row, 'Requested benefit period') and periods_unique
        a, b = r.date(row.get('start'), 'Benefit start', row), r.date(row.get('end'), 'Benefit end', row)
        if not a or not b or a > b or (onset and a < onset):
            valid = False
            r.add('period', 'Benefit periods must be ordered and no earlier than the evidenced continuous onset.', row)
        elif (b - a).days > 3660:
            valid = False
            r.add('period-limit', 'A single daily-indemnity review is bounded to 3661 calendar days.', row)
        else:
            dates = {a + timedelta(days=i) for i in range((b - a).days + 1)}
            overlaps = {used_dates[day] for day in dates if day in used_dates}
            if overlaps:
                valid = False
                for other in overlaps:
                    period_valid[other] = False
                r.add('overlap', 'Benefit periods overlap and would double-count payable days.', row)
            used_dates.update(dict.fromkeys(dates, pid))
        periods_map[pid] = (row, a, b)
        period_valid[pid] = valid
    observation_map = {}
    for row in observations:
        valid = r.evidence(row, 'Qualified criterion observation') and observations_unique
        key = (row.get('period_id'), row.get('criterion_id'))
        criterion = criterion_map.get(row.get('criterion_id'))
        period = periods_map.get(row.get('period_id'))
        a, b = r.date(row.get('start'), 'Observation start', row), r.date(row.get('end'), 'Observation end', row)
        if not criterion or not period or row.get('assessor_role') != criterion.get('assessor_role') or not row.get('assessed_by'):
            valid = False
            r.add('assessor', 'Observation must bind period and criterion with the correct qualified role and named assessor.', row)
        if not period or not a or not b or not period[1] or not period[2] or a > period[1] or b < period[2]:
            valid = False
            r.add('observation-period', 'Observation must cover the entire requested period; split periods when evidence changes.', row)
        if row.get('disposition') not in {'met', 'unmet', 'unknown'}:
            valid = False
            r.add('observation-value', 'Use supplied met, unmet or unknown; the assistant cannot diagnose.', row)
        observation_map.setdefault(key, []).append((row, valid))
    offset_map, offset_valid = {}, {}
    for row in offsets:
        pid = row.get('period_id')
        valid = r.evidence(row, 'Policy-permitted offset')
        value = r.required(number(row.get('amount')), 'Offset amount', row)
        if pid not in periods_map or row.get('currency') != d.get('currency') or not row.get('basis'):
            valid = False
            r.add('offset-binding', 'Offset must identify a benefit period, same currency and policy basis.', row)
        if pid not in periods_map:
            # An unallocated offset could belong to any period; none has a complete allocation basis.
            offset_inventory_valid = False
        offset_valid[pid] = offset_valid.get(pid, True) and valid and value is not None
        offset_map.setdefault(pid, []).append(value)
    for pid, (row, a, b) in periods_map.items():
        matrix, supported = [], bool(criterion_map) and criteria_unique
        for cid in criterion_map:
            evidence = observation_map.get((pid, cid), [])
            states = {e.get('disposition') for e, _ in evidence}
            state = 'conflicting' if len(states) > 1 else next(iter(states), 'unknown')
            relationship_valid = criterion_valid[cid] and bool(evidence) and all(valid for _, valid in evidence)
            supported = supported and relationship_valid
            if state != 'met':
                supported = False
                r.add('criterion-unresolved', f'{pid}/{cid}: criterion evidence is {state}; qualified human review required.', row, 'gap' if state in {'unknown', 'conflicting'} else 'review')
            matrix.append({'criterion_id': cid, 'evidence_state': state, 'evidence_basis_valid': relationship_valid,
                           'observation_ids': [e.get('observation_id') for e, _ in evidence]})
        period_basis_valid = method_basis_valid and period_valid[pid]
        days = max(0, (b - max(a, eligible_start)).days + 1) if period_basis_valid and eligible_start else None
        amounts = offset_map.get(pid, [])
        offset = total(amounts) if period_basis_valid and offset_inventory_valid and offset_valid.get(pid, True) else None
        gross = days * min(values['daily_amount'], values['daily_limit']) if supported and days is not None and values['daily_amount'] is not None and values['daily_limit'] is not None else None
        if gross is not None and offset is not None and offset > gross:
            r.add('offset-exceeds-benefit', 'Supplied offset exceeds gross scenario; no recovery or negative payment is inferred.', row, 'review')
        report.append({'period_id': pid, 'criteria': matrix, 'calendar_days_after_waiting': days, 'gross_scenario': gross,
                       'offsets': offset, 'net_before_remaining_cap': max(0, gross - offset) if gross is not None and offset is not None else None,
                       'source_refs': row.get('source_refs', [])})
    net = total(x['net_before_remaining_cap'] for x in report) if r.clear and all(x['net_before_remaining_cap'] is not None for x in report) else None
    capped = min(net, values['remaining_limit']) if net is not None and values['remaining_limit'] is not None else None
    return r.finish({'period_reviews': report, 'eligibility_start': eligible_start.isoformat() if eligible_start else None,
                     'total_net_scenario': net, 'remaining_limit': values['remaining_limit'], 'capped_scenario': capped,
                     'currency': d.get('currency'), 'medical_adjudication': 'not-performed', 'benefit_authorized': False})
