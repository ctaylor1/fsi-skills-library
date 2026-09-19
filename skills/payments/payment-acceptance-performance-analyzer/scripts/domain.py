"""Order-denominated acceptance cohorts; observed associations, never causal uplift."""
from collections import defaultdict
from datetime import date
from decimal import Decimal
import re

from payment_foundation import dec, finding

SKILL = 'payment-acceptance-performance-analyzer'
DIMS = ('currency', 'channel', 'method', 'segment')


def nonempty(v):
    return isinstance(v, str) and bool(v.strip())


def number(v):
    n = dec(v)
    if n < 0:
        raise ValueError('amount must be nonnegative')
    return n


def ratio(n, d):
    return str(Decimal(n) / Decimal(d)) if d else None


def validate(d):
    e = []
    periods = d.get('periods', {})
    if set(periods) != {'baseline', 'current'}:
        e.append('periods require baseline and current')
    else:
        for row in periods.values():
            if date.fromisoformat(row['start']) > date.fromisoformat(row['end']):
                e.append('period start after end')
        if periods['baseline']['end'] >= periods['current']['start']:
            e.append('comparison periods overlap or are reversed')
    if d.get('cost_coverage') not in {'complete', 'partial', 'unknown'}:
        e.append('cost_coverage must be complete, partial or unknown')
    orders = d.get('orders')
    if not isinstance(orders, list) or not orders:
        return e + ['orders must be a nonempty list']
    ids = set()
    for o in orders:
        oid = o.get('order_id')
        if not nonempty(oid) or oid in ids:
            e.append('duplicate or missing order_id')
        ids.add(oid)
        for key in DIMS:
            if not nonempty(o.get(key)):
                e.append('order requires ' + key)
        if not re.fullmatch('[A-Z]{3}', o.get('currency', '')):
            e.append('currency must be ISO-style three uppercase letters')
        number(o['amount'])
        if o.get('period') not in periods:
            e.append('unknown order period')
        elif not periods[o['period']]['start'] <= o['ordered_on'] <= periods[o['period']]['end']:
            e.append('order date outside assigned period')
        date.fromisoformat(o['ordered_on'])
        if o.get('completion') not in {'completed', 'failed', 'pending', 'unknown'}:
            e.append('invalid completion state')
        if o.get('chargeback') not in {'none', 'chargeback', 'pending', 'unknown'}:
            e.append('invalid chargeback state')
        for key in ('outcome_observed_on', 'chargeback_observed_on', 'maturity_due'):
            date.fromisoformat(o[key])
        if o['outcome_observed_on'] < o['ordered_on'] or o['chargeback_observed_on'] < o['ordered_on'] or o['maturity_due'] < o['ordered_on']:
            e.append('outcome or maturity chronology precedes order')
        if o['chargeback'] == 'chargeback' and o['completion'] != 'completed':
            e.append('chargeback conflicts with uncompleted order')
    attempts = d.get('attempts')
    if not isinstance(attempts, list):
        return e + ['attempts must be a list']
    seen = set()
    by_id = {o['order_id']: o for o in orders}
    for a in attempts:
        if not nonempty(a.get('attempt_id')) or a['attempt_id'] in seen:
            e.append('duplicate or missing attempt_id')
        seen.add(a.get('attempt_id'))
        if a.get('order_id') not in ids:
            e.append('attempt references unknown order')
        elif a.get('method') != by_id[a['order_id']]['method']:
            e.append('attempt method differs from order cohort; mixed-method attribution unsupported')
        elif a['attempted_on'] < by_id[a['order_id']]['ordered_on']:
            e.append('attempt precedes order')
        date.fromisoformat(a['attempted_on'])
        if a.get('authorization') not in {'approved', 'declined', 'unknown'}:
            e.append('invalid authorization state')
        if not nonempty(a.get('provider')):
            e.append('attempt provider required')
    if not isinstance(d.get('costs'), list):
        return e + ['costs must be a list']
    seen_cost, coverage = set(), set()
    for c in d['costs']:
        if not nonempty(c.get('cost_id')) or c['cost_id'] in seen_cost:
            e.append('duplicate or missing cost_id')
        seen_cost.add(c.get('cost_id'))
        if c.get('order_id') not in ids:
            e.append('cost references unknown order')
        elif c.get('currency') != by_id[c['order_id']]['currency']:
            e.append('cost currency differs from order; no implicit FX')
        if c.get('category') not in {'processing', 'fraud_loss', 'chargeback_fee', 'operations'}:
            e.append('unsupported cost category')
        number(c['amount'])
        keys = c.get('coverage_keys')
        if not isinstance(keys, list) or not keys or any(not nonempty(x) for x in keys):
            e.append('nonempty cost coverage_keys required')
        else:
            if coverage.intersection(keys) or len(set(keys)) != len(keys):
                e.append('overlapping economic cost coverage')
            coverage.update(keys)
    experiment = d.get('experiment')
    if experiment is not None:
        if not nonempty(experiment.get('experiment_id')) or experiment.get('assignment_unit') != 'order':
            e.append('experiment requires id and order assignment unit')
        arms = experiment.get('arms', [])
        if len(arms) < 2 or len({a['arm_id'] for a in arms}) != len(arms):
            e.append('at least two unique experiment arms required')
        if sum((number(a['expected_share']) for a in arms), Decimal(0)) != 1:
            e.append('expected arm shares must sum to one')
        if any(not 0 < number(a['expected_share']) < 1 or not nonempty(a.get('provider')) for a in arms):
            e.append('arms require positive shares and provider')
        for g in experiment.get('guardrails', []):
            if g.get('metric') not in {'completion_rate', 'retry_order_rate', 'mature_chargeback_rate'} or g.get('direction') not in {'min', 'max'} or not 0 <= number(g['threshold']) <= 1:
                e.append('invalid experiment guardrail')
    return e


def analyze(req):
    d = req['data']
    findings = []
    orders = d['orders']
    attempts = defaultdict(list)
    costs = defaultdict(list)
    for a in d['attempts']:
        attempts[a['order_id']].append(a)
    for c in d['costs']:
        costs[c['order_id']].append(c)
    for kind, rows in [('order', orders), ('attempt', d['attempts']), ('cost', d['costs'])]:
        for r in rows:
            if not r.get('source_ids'):
                findings.append(finding('missing-row-evidence', kind + ' row lacks source_ids'))
    future = any(d['periods'][p]['end'] > req['as_of'] for p in d['periods'])
    for o in orders:
        if o['outcome_observed_on'] > req['as_of'] or o['chargeback_observed_on'] > req['as_of'] or o['ordered_on'] > req['as_of']:
            future = True
    if any(a['attempted_on'] > req['as_of'] for a in d['attempts']):
        future = True
    if future:
        return {'result': {'cohorts': [], 'comparisons': [], 'experiments': [], 'quarantined': True},
                'findings': [finding('future-evidence', 'Observation or completed reporting period extends after as_of; no metrics produced.')], 'handoffs': []}
    if d['cost_coverage'] != 'complete':
        findings.append(finding('partial-cost-coverage', 'Costs are observed partial amounts, not all-in profitability.'))
    if not d.get('cost_coverage_source_ids'):
        findings.append(finding('missing-cost-coverage-evidence', 'Supplier cost coverage attestation requires source evidence.'))
    if any(a['authorization'] == 'unknown' for a in d['attempts']):
        findings.append(finding('unknown-authorization', 'Authorization success is bounded by unknown attempt outcomes.'))
    if not d.get('population_source_ids'):
        findings.append(finding('missing-population-evidence', 'Confirm extraction completeness including orders with no attempts.'))
    if not d.get('maturity_policy_source_ids'):
        findings.append(finding('missing-maturity-policy', 'Maturity dates require an approved cohort-specific observation policy.'))
    for o in orders:
        if not attempts[o['order_id']]:
            findings.append(finding('unattempted-order', 'Order ' + o['order_id'] + ' has no attempt; retained in conversion denominator.', o.get('source_ids', []), 'warning'))
        if o['completion'] == 'completed' and o['method'] == 'card' and not any(a['authorization'] == 'approved' for a in attempts[o['order_id']]):
            findings.append(finding('completion-authorization-conflict', 'Completed card order lacks a linked observed approval: ' + o['order_id']))
    def metrics(rows):
        aa = [a for o in rows for a in attempts[o['order_id']]]
        completed = [o for o in rows if o['completion'] == 'completed']
        unresolved = [o for o in rows if o['completion'] in {'pending', 'unknown'}]
        mature = [o for o in completed if o['maturity_due'] <= req['as_of'] and o['chargeback'] in {'none', 'chargeback'} and (o['chargeback'] == 'chargeback' or o['chargeback_observed_on'] >= o['maturity_due'])]
        cb = [o for o in mature if o['chargeback'] == 'chargeback']
        categories = defaultdict(Decimal)
        for o in rows:
            for c in costs[o['order_id']]:
                categories[c['category']] += number(c['amount'])
        retry = sum(len(attempts[o['order_id']]) > 1 for o in rows)
        return {'orders': len(rows), 'attempts': len(aa), 'retry_orders': retry, 'retry_order_rate': ratio(retry, len(rows)),
                'authorized_attempts': sum(a['authorization'] == 'approved' for a in aa),
                'unknown_authorizations': sum(a['authorization'] == 'unknown' for a in aa),
                'authorization_rate_per_attempt': ratio(sum(a['authorization'] == 'approved' for a in aa), len(aa)),
                'authorization_rate_upper_bound': ratio(sum(a['authorization'] != 'declined' for a in aa), len(aa)),
                'orders_with_approval': sum(any(a['authorization'] == 'approved' for a in attempts[o['order_id']]) for o in rows),
                'completed_orders': len(completed), 'unresolved_orders': len(unresolved),
                'completion_rate': ratio(len(completed), len(rows)),
                'completion_upper_bound': ratio(len(completed) + len(unresolved), len(rows)),
                'completed_gross_value': str(sum((number(o['amount']) for o in completed), Decimal(0))),
                'mature_completed_orders': len(mature), 'immature_or_unknown_completed_orders': len(completed) - len(mature),
                'mature_chargebacks': len(cb), 'mature_chargeback_rate': ratio(len(cb), len(mature)),
                'mature_completed_value': str(sum((number(o['amount']) for o in mature), Decimal(0))),
                'chargeback_gross_value': str(sum((number(o['amount']) for o in cb), Decimal(0))),
                'observed_costs_by_category': {k: str(v) for k, v in sorted(categories.items())},
                'observed_total_cost': str(sum(categories.values(), Decimal(0))), 'all_in_cost_confirmed_by_supplier': d['cost_coverage'] == 'complete'}
    grouped = defaultdict(list)
    for o in orders:
        grouped[(o['period'],) + tuple(o[x] for x in DIMS)].append(o)
    cohorts = [{**dict(zip(('period',) + DIMS, key)), **metrics(rows), 'order_ids': sorted(o['order_id'] for o in rows)} for key, rows in sorted(grouped.items())]
    comparisons = []
    dimensions = sorted({tuple(o[x] for x in DIMS) for o in orders})
    for dim in dimensions:
        base, current = (grouped.get((p,) + dim, []) for p in ('baseline', 'current'))
        row = dict(zip(DIMS, dim))
        if not base or not current:
            row.update({'state': 'unmatched-cohort', 'metric_deltas': None})
            findings.append(finding('unmatched-cohort', 'No comparable period cohort for ' + '/'.join(dim), severity='warning'))
        else:
            b, c = metrics(base), metrics(current)
            row.update({'state': 'observed-cohort-comparison', 'metric_deltas': {key: str(Decimal(c[key]) - Decimal(b[key])) if b[key] is not None and c[key] is not None else None for key in ('completion_rate', 'authorization_rate_per_attempt', 'retry_order_rate', 'mature_chargeback_rate')}})
        comparisons.append(row)
    if any(o['completion'] in {'pending', 'unknown'} for o in orders):
        findings.append(finding('unresolved-completion', 'Observed completion is a lower bound; unresolved orders are neither completed nor failed.'))
    if any(o['completion'] == 'completed' and (o['maturity_due'] > req['as_of'] or o['chargeback'] in {'pending', 'unknown'} or (o['chargeback'] == 'none' and o['chargeback_observed_on'] < o['maturity_due'])) for o in orders):
        findings.append(finding('immature-chargebacks', 'Incomplete dispute observation is excluded from the mature denominator; zero disputes is not inferred.'))
    experiments = []
    ex = d.get('experiment')
    if ex:
        arm_ids = {a['arm_id'] for a in ex['arms']}
        enrolled = [o for o in orders if o['period'] == 'current']
        missing = [o['order_id'] for o in enrolled if o.get('experiment_arm') not in arm_ids]
        contamination = []
        arm_rows = []
        for arm in ex['arms']:
            selected = [o for o in enrolled if o.get('experiment_arm') == arm['arm_id']]
            for o in selected:
                if any(a['provider'] != arm['provider'] for a in attempts[o['order_id']]):
                    contamination.append(o['order_id'])
            rows_by_dim = defaultdict(list)
            for o in selected:
                rows_by_dim[tuple(o[x] for x in DIMS)].append(o)
            for dim, rows in sorted(rows_by_dim.items()):
                m = metrics(rows)
                guardrails = []
                for g in ex.get('guardrails', []):
                    value = m[g['metric']]
                    passed = None if value is None else (Decimal(value) >= number(g['threshold']) if g['direction'] == 'min' else Decimal(value) <= number(g['threshold']))
                    uncertain = g['metric'] == 'completion_rate' and m['unresolved_orders'] > 0 and (passed is None or (g['direction'] == 'max' and passed and Decimal(m['completion_upper_bound']) > number(g['threshold'])) or (g['direction'] == 'min' and not passed and Decimal(m['completion_upper_bound']) >= number(g['threshold'])))
                    state = 'unknown' if passed is None or uncertain else 'within-supplied-guardrail' if passed else 'outside-supplied-guardrail'
                    if state != 'within-supplied-guardrail':
                        findings.append(finding('experiment-guardrail-review', arm['arm_id'] + '/' + g['metric'] + ': ' + state))
                    guardrails.append({**g, 'observed': value, 'state': state})
                arm_rows.append({'arm_id': arm['arm_id'], **dict(zip(DIMS, dim)), **m, 'guardrails': guardrails})
        if missing or contamination or not ex.get('randomization_source_ids') or not ex.get('guardrails') or not ex.get('guardrail_source_ids'):
            findings.append(finding('experiment-design-gap', 'Review missing assignment, fallback contamination, randomization evidence and supplied guardrails before interpreting routing results.'))
        experiments.append({'experiment_id': ex['experiment_id'], 'analysis_basis': 'intention-to-treat by supplied order assignment',
                            'arm_counts': [{'arm_id': a['arm_id'], 'assigned_orders': sum(o.get('experiment_arm') == a['arm_id'] for o in enrolled), 'expected_share': a['expected_share']} for a in ex['arms']],
                            'missing_assignment_order_ids': missing, 'contaminated_order_ids': sorted(set(contamination)), 'cohorts': arm_rows,
                            'causal_uplift_established': False, 'sample_ratio_significance_tested': False})
    return {'result': {'cohorts': cohorts, 'comparisons': comparisons, 'experiments': experiments, 'quarantined': False,
                       'interpretation': 'Within supplied cohorts only. Rate deltas are fractions, not relative uplift. Gross completed/chargeback value is not profit or net loss. No pooled multi-currency value, customer-level causal inference, significance claim or invented retry benefit.'},
            'findings': findings,
            'handoffs': [{'target_skill': 'payment-fraud-control-evaluator', 'reason': 'Evaluate control interactions and mature fraud labels behind observed acceptance changes.', 'required_inputs': ['matched cohorts', 'rule versions', 'mature label and loss evidence']},
                         {'target_skill': 'merchant-payment-cost-analyzer', 'reason': 'Reconcile incurred fee evidence and confirm disjoint cost coverage.', 'required_inputs': ['fee statements', 'settled-sale population', 'economic coverage keys']}],
            'limitations': ['Routing experiment summaries do not test sample ratio mismatch significance, balance, power, interference or causal effects. Review provider mix, time trends, retry policy, seasonality and label maturity before attributing differences.']}
