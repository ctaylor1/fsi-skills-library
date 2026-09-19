"""Evidence-qualified payment economics; no company data collection or investing advice."""
from datetime import date
from decimal import Decimal, InvalidOperation
from payment_foundation import finding

SKILL = 'payment-business-model-analyzer'
ROLES = {'issuer', 'acquirer', 'processor', 'scheme', 'gateway', 'orchestrator', 'merchant', 'platform', 'wallet', 'bank', 'agent', 'infrastructure-provider'}
NUMBERS = ('payment_volume', 'gross_billings', 'pass_through', 'incentives', 'reported_net_revenue', 'variable_cost', 'allocated_fixed_cost')


def text(v):
    return isinstance(v, str) and bool(v.strip())


def number(v, signed=False):
    if isinstance(v, bool) or not isinstance(v, (str, int)):
        raise ValueError('amount requires decimal string or integer')
    try:
        n = Decimal(v)
    except InvalidOperation as exc:
        raise ValueError('invalid decimal') from exc
    if not n.is_finite() or (n < 0 and not signed):
        raise ValueError('amount must be finite and nonnegative')
    return n


def validate(d):
    errors = []
    for key in ('analysis_question', 'accountable_owner'):
        if not text(d.get(key)):
            errors.append(key + ' required')
    for key, identity in [('companies', 'company_id'), ('segments', 'segment_id'), ('comparisons', 'comparison_id'), ('strategic_options', 'option_id')]:
        rows = d.get(key)
        if not isinstance(rows, list):
            errors.append(key + ' explicit list required')
            continue
        seen = set()
        for r in rows:
            if not isinstance(r, dict):
                errors.append(key + ' row must be object')
                continue
            if not text(r.get(identity)) or r.get(identity) in seen:
                errors.append(key + ' missing or duplicate ' + identity)
            seen.add(r.get(identity))
            if not isinstance(r.get('source_ids'), list) or not r['source_ids']:
                errors.append(key + ' source_ids required')
    if not d.get('companies') or not d.get('segments'):
        errors.append('companies and segments cannot be empty')
    for r in d.get('companies', []):
        if not isinstance(r, dict):
            continue
        if not isinstance(r.get('roles'), list) or not r['roles'] or any(role not in ROLES for role in r['roles']):
            errors.append('company needs supported ecosystem roles')
        for key in ('customer', 'value_proposition', 'monetization', 'dependencies', 'jurisdiction'):
            if not text(r.get(key)):
                errors.append('company ' + key + ' required')
    for r in d.get('segments', []):
        if not isinstance(r, dict):
            continue
        for key in ('company_id', 'economic_partition_id', 'segment_name', 'currency', 'volume_definition', 'scope_definition', 'accounting_policy_ref', 'period_basis'):
            if not text(r.get(key)):
                errors.append('segment ' + key + ' required')
        if not isinstance(r.get('currency'), str) or len(r['currency']) != 3 or not r['currency'].isupper():
            errors.append('currency needs uppercase three-letter code')
        if r.get('revenue_basis') not in {'gross-billings', 'net-revenue'}:
            errors.append('revenue_basis must be gross-billings or net-revenue')
        if r.get('volume_unit') not in {'currency-amount', 'transaction-count', 'unknown'}:
            errors.append('volume_unit must be currency-amount, transaction-count or unknown')
        if type(r.get('costs_complete')) is not bool:
            errors.append('costs_complete boolean required')
        for key in ('period_start', 'period_end'):
            try:
                date.fromisoformat(r[key])
            except (KeyError, TypeError, ValueError):
                errors.append('segment ' + key + ' requires ISO date')
        if text(r.get('period_start')) and text(r.get('period_end')) and r['period_start'] > r['period_end']:
            errors.append('segment period reversed')
        for key in NUMBERS:
            if key not in r:
                errors.append(key + ' must be explicit amount or null')
            elif r[key] is not None:
                try:
                    number(r[key], signed=key == 'reported_net_revenue')
                except ValueError as exc:
                    errors.append(key + ': ' + str(exc))
    for r in d.get('comparisons', []):
        if not isinstance(r, dict):
            continue
        for key in ('left_segment', 'right_segment'):
            if not text(r.get(key)):
                errors.append('comparison ' + key + ' required')
    for r in d.get('strategic_options', []):
        if not isinstance(r, dict):
            continue
        for key in ('hypothesis', 'test', 'owner', 'dependency', 'risk'):
            if not text(r.get(key)):
                errors.append('strategic option ' + key + ' required')
        if not isinstance(r.get('segment_ids'), list) or not r['segment_ids'] or any(not text(v) for v in r['segment_ids']):
            errors.append('strategic option segment_ids required')
    return errors


def analyze(request):
    d = request['data']
    findings = []
    companies = {r['company_id']: r for r in d['companies']}
    segments = {r['segment_id']: r for r in d['segments']}
    invalid = set()
    def gap(code, message, row):
        findings.append(finding(code, message, row.get('source_ids', [])))
    for row in d['segments']:
        sid = row['segment_id']
        if row['company_id'] not in companies:
            invalid.add(sid)
            gap('unknown-company', sid, row)
        if row['period_end'] > request['as_of']:
            invalid.add(sid)
            gap('future-reported-period', sid + ': supplied actuals end after the as-of date.', row)
        for other in d['segments']:
            if other['segment_id'] == sid:
                continue
            same = all(row[k] == other[k] for k in ('company_id', 'economic_partition_id', 'currency'))
            overlap = max(row['period_start'], other['period_start']) <= min(row['period_end'], other['period_end'])
            if same and overlap:
                invalid.add(sid)
                gap('overlapping-economic-partition', sid + ': aggregate/detail or duplicate economic coverage is ambiguous.', row)
    results = []
    for row in d['segments']:
        sid = row['segment_id']
        net = None
        if sid not in invalid:
            if row['revenue_basis'] == 'gross-billings':
                keys = ('gross_billings', 'pass_through', 'incentives')
                if all(row[k] is not None for k in keys):
                    net = number(row['gross_billings']) - number(row['pass_through']) - number(row['incentives'])
                    if row['reported_net_revenue'] is not None and net != number(row['reported_net_revenue'], signed=True):
                        gap('net-revenue-reconciliation', sid + ': supplied gross bridge conflicts with reported net revenue.', row)
                        net = None
                else:
                    gap('unknown-revenue-bridge', sid + ': gross, pass-through and incentives must all be known.', row)
            else:
                if row['reported_net_revenue'] is not None:
                    net = number(row['reported_net_revenue'], signed=True)
                    # Net means already after pass-through and incentives: never subtract them again.
                    bridge = ('gross_billings', 'pass_through', 'incentives')
                    if all(row[k] is not None for k in bridge) and number(row['gross_billings']) - number(row['pass_through']) - number(row['incentives']) != net:
                        gap('net-revenue-reconciliation', sid + ': disclosed bridge conflicts with reported net.', row)
                        net = None
                else:
                    gap('unknown-net-revenue', sid, row)
        volume = number(row['payment_volume']) if row['payment_volume'] is not None and row['volume_unit'] == 'currency-amount' else None
        if volume is None or volume == 0:
            gap('take-rate-denominator', sid + ': positive, defined payment volume is needed; zero is not missing and does not produce an infinite rate.', row)
        contribution = net - number(row['variable_cost']) if net is not None and row['costs_complete'] and row['variable_cost'] is not None else None
        if contribution is None:
            gap('unknown-contribution', sid + ': net revenue and complete variable costs are required.', row)
        after_fixed = contribution - number(row['allocated_fixed_cost']) if contribution is not None and row['allocated_fixed_cost'] is not None else None
        if after_fixed is None:
            gap('unknown-fixed-cost-result', sid + ': no profit proxy is inferred from incomplete fixed costs.', row)
        results.append({'segment_id': sid, 'company_id': row['company_id'], 'currency': row['currency'], 'period_start': row['period_start'], 'period_end': row['period_end'], 'volume_definition': row['volume_definition'], 'scope_definition': row['scope_definition'], 'net_revenue': str(net) if net is not None else None, 'net_take_rate_bps': str(net / volume * 10000) if net is not None and volume else None, 'contribution_before_fixed': str(contribution) if contribution is not None else None, 'contribution_after_allocated_fixed': str(after_fixed) if after_fixed is not None else None, 'is_accounting_profit': False, 'source_ids': row['source_ids']})
    by_id = {r['segment_id']: r for r in results}
    comparisons = []
    for row in d['comparisons']:
        left, right = segments.get(row['left_segment']), segments.get(row['right_segment'])
        mismatches = []
        if not left or not right or row['left_segment'] == row['right_segment']:
            mismatches.append('unknown-or-identical-segment')
        else:
            for key in ('currency', 'period_start', 'period_end', 'period_basis', 'volume_definition', 'scope_definition'):
                if left[key] != right[key]:
                    mismatches.append(key)
            if not text(row.get('accounting_comparability_review_ref')):
                mismatches.append('accounting-comparability-review')
            if by_id[left['segment_id']]['net_take_rate_bps'] is None or by_id[right['segment_id']]['net_take_rate_bps'] is None:
                mismatches.append('unknown-take-rate')
        if mismatches:
            gap('noncomparable-segments', row['comparison_id'] + ': ' + ', '.join(mismatches), row)
        difference = None if mismatches else str(Decimal(by_id[left['segment_id']]['net_take_rate_bps']) - Decimal(by_id[right['segment_id']]['net_take_rate_bps']))
        comparisons.append({'comparison_id': row['comparison_id'], 'comparable_on_supplied_basis': not mismatches, 'mismatches': mismatches, 'left_minus_right_net_take_rate_bps': difference, 'competitive_superiority_inferred': False})
    options = []
    for row in d['strategic_options']:
        if any(sid not in segments for sid in row['segment_ids']):
            gap('option-unknown-segment', row['option_id'], row)
        options.append({**row, 'status': 'hypothesis-for-owner-review', 'approved': False})
    return {'result': {'analysis_question': d['analysis_question'], 'value_chain': d['companies'], 'segments': results, 'comparisons': comparisons, 'strategic_options': options, 'cross_currency_total': None, 'securities_recommendation': False, 'strategy_approved': False}, 'findings': findings, 'handoffs': [{'target_skill': 'payment-economics-modeler', 'reason': 'Deepen method-specific economics using reconciled segment inputs.', 'required_inputs': ['participant and payment method', 'currency and period', 'cost basis', 'unresolved accounting issues']}], 'limitations': ['All financial values are supplied evidence. No company filings are collected or authenticated by this helper.', 'Contribution and take rate are explicitly defined management measures, not accounting profit, valuation or investment recommendations.', 'Segment values remain separate by entity, currency and period; overlap checks use declared economic partitions and cannot discover undisclosed overlap.']}
