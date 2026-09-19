from decimal import Decimal
from analytics_helpers import Review, rows, ratio, total, validate_with

FIELDS = ('earned_premium', 'written_premium', 'incurred_loss_lae', 'underwriting_expense', 'claim_count', 'earned_exposure')


def evaluate(doc):
    r = Review(doc)
    d, scope = r.data, r.data.get('scope', {})
    r.evidence(scope, 'portfolio scope')
    basis_ok = scope.get('period_basis') == 'calendar' and scope.get('loss_basis') == 'incurred_including_lae' and scope.get('risk_basis') in {'gross_direct', 'net_retained'}
    if not basis_ok:
        r.add('basis-gap', 'This method requires calendar-period incurred loss including LAE and a consistent gross_direct or net_retained basis', scope)
    expense_basis = scope.get('expense_denominator')
    if expense_basis not in {'earned_premium', 'written_premium'}:
        r.add('basis-gap', 'Explicit earned_premium or written_premium expense denominator required', scope)
        basis_ok = False
    periods = rows(d.get('periods', []), 'period_id')
    if len(periods) != 2:
        raise ValueError('Supply exactly two ordered comparison periods')
    period_meta = {}
    for p in periods:
        r.evidence(p, p['period_id'])
        start, end = r.date(p, 'start'), r.date(p, 'end')
        if start is None or end is None or start > end or end > r.date(doc, 'as_of'):
            r.add('period-gap', 'Portfolio periods must be ordered and observed at as_of', p)
            basis_ok = False
        period_meta[p['period_id']] = (start, end)
    if all(all(x is not None for x in v) for v in period_meta.values()):
        prior, current = [period_meta[p['period_id']] for p in periods]
        if current[0] <= prior[1] or (prior[1]-prior[0]).days != (current[1]-current[0]).days:
            r.add('period-comparability', 'Nonoverlapping equal-length periods are required for this comparison; supply a reviewed normalized study separately')
            basis_ok = False
    records = rows(d.get('segments', []), 'row_id')
    seen, groups, evaluated = set(), {p['period_id']: [] for p in periods}, []
    if not records:
        r.add('portfolio-gap', 'Segment observations required')
    complete = d.get('segment_inventory_complete') is True
    if not complete:
        r.add('inventory-gap', 'Segment inventory completeness not established; totals are withheld')
    for row in records:
        identity = (row.get('period_id'), row.get('segment_id'))
        if identity in seen or not isinstance(identity[1], str) or not identity[1] or identity[0] not in groups:
            raise ValueError('Unique period/segment identities must reference the two supplied periods')
        seen.add(identity)
        valid = r.evidence(row, row['row_id']) and r.scope(row, scope, ('currency', 'risk_basis', 'loss_basis', 'period_basis', 'exposure_unit')) and basis_ok
        values = {k: r.num(row, k, signed=k == 'incurred_loss_lae') for k in FIELDS}
        if values['claim_count'] is not None and values['claim_count'] != values['claim_count'].to_integral_value():
            raise ValueError('claim_count must be an integer')
        if not valid:
            values = {k: None for k in FIELDS}
        result = {**row, **values, 'loss_ratio': ratio(values['incurred_loss_lae'], values['earned_premium']),
                  'frequency': ratio(values['claim_count'], values['earned_exposure']),
                  'severity': ratio(values['incurred_loss_lae'], values['claim_count'])}
        evaluated.append(result)
        groups[row['period_id']].append(result)
    aggregates = []
    for p in periods:
        items = groups[p['period_id']]
        sums = {k: total([row[k] for row in items]) if complete and items else None for k in FIELDS}
        lr = ratio(sums['incurred_loss_lae'], sums['earned_premium'])
        er = ratio(sums['underwriting_expense'], sums.get(expense_basis))
        if complete and (lr is None or er is None):
            r.add('ratio-unavailable', p['period_id'] + ': missing/zero premium denominator prevents ratio evaluation')
        aggregates.append({'period_id': p['period_id'], **sums, 'loss_ratio': lr, 'expense_ratio': er,
                           'combined_ratio': None if lr is None or er is None else lr+er,
                           'frequency': ratio(sums['claim_count'], sums['earned_exposure']),
                           'severity': ratio(sums['incurred_loss_lae'], sums['claim_count'])})
    old, new = [{x['segment_id']: x for x in groups[p['period_id']]} for p in periods]
    bridge = None
    if old.keys() == new.keys() and old and all(x['loss_ratio'] is not None for x in evaluated) and all(a['loss_ratio'] is not None and a['earned_premium'] > 0 for a in aggregates):
        contributions = []
        for key in sorted(old):
            a, b = old[key], new[key]
            w0, w1 = a['earned_premium']/aggregates[0]['earned_premium'], b['earned_premium']/aggregates[1]['earned_premium']
            contributions.append({'segment_id': key, 'mix_effect': (w1-w0)*a['loss_ratio'], 'within_segment_effect': w1*(b['loss_ratio']-a['loss_ratio'])})
        mix = sum((x['mix_effect'] for x in contributions), Decimal(0))
        within = sum((x['within_segment_effect'] for x in contributions), Decimal(0))
        delta = aggregates[1]['loss_ratio'] - aggregates[0]['loss_ratio']
        bridge = {'loss_ratio_change': delta, 'mix_effect': mix, 'within_segment_effect': within,
                  'rounding_residual': delta-mix-within, 'segment_contributions': contributions,
                  'interpretation': 'Arithmetic decomposition using prior segment rates then current weights; not causal attribution'}
    else:
        r.add('bridge-unavailable', 'Comparable complete segment sets and nonzero premiums required; no imputed new/closed-segment ratios')
    return r.finish({'scope': scope, 'segments': evaluated, 'period_totals': aggregates, 'loss_ratio_bridge': bridge,
                     'expense_denominator': expense_basis, 'management_action_selected': False})


def validate(doc):
    return validate_with(evaluate, doc)
