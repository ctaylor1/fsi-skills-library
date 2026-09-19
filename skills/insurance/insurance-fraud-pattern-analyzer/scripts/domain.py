from decimal import Decimal
from analytics_helpers import Review, rows, ratio, total, text, validate_with


def evaluate(doc):
    r = Review(doc)
    d, profile = r.data, r.profile
    threshold = profile.get('minimum_shared_claims')
    allowed = profile.get('entity_types')
    if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 2:
        raise ValueError('minimum_shared_claims must be an integer of at least two, supplied by reviewed profile')
    if not isinstance(allowed, list) or not allowed or any(not text(t) for t in allowed):
        raise ValueError('entity_types must explicitly list permitted exact-match identifier types')
    windows = rows(d.get('windows', []), 'window_id')
    if len(windows) != 2:
        raise ValueError('Two observation windows required')
    bounds, counts, valid_windows = {}, {}, True
    for w in windows:
        r.evidence(w, w['window_id'])
        start, end = r.date(w, 'start'), r.date(w, 'end')
        exposure = r.num(w, 'exposure', positive=True)
        valid = start is not None and end is not None and start <= end <= r.date(doc, 'as_of')
        if not valid or w.get('inventory_complete') is not True:
            r.add('window-gap', 'Observed dates and complete claim inventory required for window '+w['window_id'], w)
            valid_windows = False
        if w.get('exposure_unit') != windows[0].get('exposure_unit') or not text(w.get('exposure_unit')):
            r.add('exposure-basis-gap', 'Window exposure units differ or are unspecified', w)
            valid_windows = False
        bounds[w['window_id']] = (start, end)
        counts[w['window_id']] = {'window_id': w['window_id'], 'claims': 0, 'flagged_claims': 0, 'exposure': exposure, 'days': (end-start).days+1 if valid else None}
    a, b = list(bounds.values())
    if a[0] and a[1] and b[0] and b[1] and b[0] <= a[1]:
        raise ValueError('Windows must be ordered and nonoverlapping')
    claims = rows(d.get('claims', []), 'claim_id')
    if not claims:
        r.add('claim-gap', 'A claim inventory is required')
    links, admitted, amounts, labels = {}, {}, {}, {}
    excluded = d.get('common_entities')
    if not isinstance(excluded, list) or any(not isinstance(e, dict) or not text(e.get('entity_type')) or not text(e.get('entity_id')) for e in excluded):
        raise ValueError('common_entities requires explicit typed identifiers; empty list is allowed')
    exclusions = set()
    for e in excluded:
        supported = r.evidence(e, 'common entity exclusion')
        if not text(e.get('reason')):
            r.add('exclusion-gap', 'Common-entity suppression requires reviewed reason', e)
        elif supported:
            exclusions.add((e['entity_type'], e['entity_id']))
    for c in claims:
        evidence = r.evidence(c, c['claim_id'])
        reported = r.date(c, 'reported_date')
        window = c.get('window_id')
        if window not in bounds:
            raise ValueError('Claim window_id unknown')
        start, end = bounds[window]
        if not evidence or reported is None or start is None or end is None or not start <= reported <= end:
            r.add('claim-period-gap', c['claim_id']+': reporting date or evidence does not support its window', c)
            valid_windows = False
            continue
        counts[window]['claims'] += 1
        admitted[c['claim_id']] = c
        amounts[c['claim_id']] = r.num(c, 'claimed_amount')
        if c.get('currency') != d.get('currency') or not text(c.get('currency')):
            r.add('currency-gap', c['claim_id']+': amount currency differs', c)
            amounts[c['claim_id']] = None
        entities = c.get('entities')
        if not isinstance(entities, list) or any(not isinstance(e, dict) for e in entities):
            raise ValueError('claim.entities must be a list of typed identifier objects')
        for e in entities:
            if e.get('entity_type') not in allowed or not text(e.get('entity_id')):
                raise ValueError('Entity type or identifier unsupported')
            key = (e['entity_type'], e['entity_id'])
            if key not in exclusions:
                links.setdefault(key, set()).add(c['claim_id'])
        label = c.get('outcome')
        if label not in {'confirmed', 'cleared', 'pending', 'unknown'}:
            raise ValueError('outcome must be confirmed, cleared, pending or unknown')
        if label in {'confirmed', 'cleared'}:
            date = r.date(c, 'outcome_as_of')
            if date is None or date > r.date(doc, 'as_of') or date < reported:
                r.add('outcome-date-gap', c['claim_id']+': label unavailable at review date', c)
            elif r.evidence({'source_refs': c.get('outcome_source_refs')}, 'reviewed outcome'):
                labels[c['claim_id']] = label
    signals, flagged = [], set()
    for (kind, entity), ids in sorted(links.items()):
        if len(ids) >= threshold:
            flagged.update(ids)
            signals.append({'entity_type': kind, 'entity_id': entity, 'claim_ids': sorted(ids),
                            'claimed_amount': total([amounts[x] for x in ids]), 'currency': d.get('currency'),
                            'interpretation': 'Shared exact identifier; coincidence/common service provider remains a competing explanation'})
    for cid in flagged:
        counts[admitted[cid]['window_id']]['flagged_claims'] += 1
    for row in counts.values():
        row['claim_rate_per_exposure'] = ratio(Decimal(row['claims']), row['exposure']) if valid_windows else None
        row['flagged_claim_fraction'] = ratio(Decimal(row['flagged_claims']), Decimal(row['claims'])) if valid_windows else None
        row['claims_per_day'] = ratio(Decimal(row['claims']), Decimal(row['days'])) if valid_windows and row['days'] else None
    mature = [labels[cid] for cid in flagged if cid in labels]
    return r.finish({'signals': signals, 'window_rates': list(counts.values()), 'flagged_claim_ids': sorted(flagged),
                     'unique_flagged_claimed_amount': total([amounts[x] for x in flagged]),
                     'mature_flagged_outcomes': len(mature), 'pending_or_unknown_flagged': len(flagged)-len(mature),
                     'confirmed_share_among_mature_flagged': ratio(Decimal(mature.count('confirmed')), Decimal(len(mature))),
                     'fraud_determination': 'not_made', 'referral_sent': False,
                     'limits': 'Exact identifiers only; no fuzzy identity inference, prediction, causal attribution or estimated fraud loss'})


def validate(doc):
    return validate_with(evaluate, doc)
