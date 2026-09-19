"""Linear, scenario-based payment economics with explicit adoption/displacement."""
from decimal import Decimal, InvalidOperation, localcontext
from copy import deepcopy

SKILL = 'payment-economics-modeler'
BASES = {'per_attempt', 'per_success', 'success_value', 'period_fixed'}
REQUIRED = {
    'merchant': {'processing', 'fraud_loss', 'funding', 'fx', 'operations', 'incentive', 'merchandise_margin'},
    'issuer': {'interchange', 'processing', 'scheme', 'fraud_loss', 'credit_loss', 'funding', 'fx', 'operations', 'rewards'},
    'acquirer': {'merchant_fee', 'interchange', 'scheme', 'processing', 'fraud_loss', 'funding', 'fx', 'operations'},
    'psp': {'processing_revenue', 'processing', 'fraud_loss', 'funding', 'fx', 'operations'},
    'bank': {'service_revenue', 'processing', 'fraud_loss', 'funding', 'fx', 'operations'},
}
REVENUES = {'merchant': {'merchandise_margin'}, 'issuer': {'interchange'}, 'acquirer': {'merchant_fee'}, 'psp': {'processing_revenue'}, 'bank': {'service_revenue'}}


def number(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError('use decimal strings or integer values')
    try:
        n = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('invalid decimal') from exc
    if not n.is_finite() or n < 0:
        raise ValueError('decimal must be finite and nonnegative')
    return n


def validate(data):
    errors = []
    if not isinstance(data, dict):
        return ['data must be an object']
    if data.get('perspective') not in REQUIRED:
        errors.append('perspective must be merchant, issuer, acquirer, psp or bank')
    if not isinstance(data.get('currency'), str) or len(data['currency']) != 3 or not data['currency'].isupper():
        errors.append('currency must be a three-letter uppercase code')
    if data.get('period') not in ('monthly', 'annual'):
        errors.append('period must be monthly or annual; all prices must use that period')
    try:
        if number(data.get('attempts')) <= 0:
            errors.append('attempts must be positive')
    except ValueError:
        errors.append('invalid attempts')
    for key in ('methods', 'baseline_mix', 'assumptions'):
        if not isinstance(data.get(key), list) or not data[key]:
            errors.append(key + ' must be a nonempty list')
    if not isinstance(data.get('scenario'), dict):
        errors.append('scenario must be an object')
    if errors:
        return errors
    assumption_ids = set()
    for row in data['assumptions']:
        if not isinstance(row, dict) or not isinstance(row.get('assumption_id'), str) or not row['assumption_id'] or not isinstance(row.get('statement'), str) or not row['statement']:
            errors.append('assumption needs id and statement')
        elif row['assumption_id'] in assumption_ids:
            errors.append('duplicate assumption_id')
        else:
            assumption_ids.add(row['assumption_id'])
    methods = set()
    for method in data['methods']:
        if not isinstance(method, dict):
            errors.append('method must be an object')
            continue
        mid = method.get('method_id')
        if not isinstance(mid, str) or not mid or mid in methods:
            errors.append('method_id must be unique and nonempty')
        else:
            methods.add(mid)
        for field in ('success_rate', 'average_value'):
            if method.get(field) is not None:
                try:
                    val = number(method[field])
                    if field == 'success_rate' and val > 1:
                        errors.append('success_rate cannot exceed 1')
                except ValueError:
                    errors.append('invalid ' + field)
        if method.get('assumption_id') not in assumption_ids:
            errors.append('method requires a registered assumption_id')
        if not isinstance(method.get('components', []), list):
            errors.append('components must be a list')
            continue
        ids, coverages = set(), set()
        for component in method.get('components', []):
            if not isinstance(component, dict):
                errors.append('component must be an object')
                continue
            cid = component.get('component_id')
            if not isinstance(cid, str) or not cid or cid in ids:
                errors.append('component_id must be unique and nonempty per method')
            else:
                ids.add(cid)
            coverage = component.get('coverage_keys')
            if not isinstance(coverage, list) or not coverage or not all(isinstance(x, str) and x for x in coverage):
                errors.append('component coverage_keys must identify disjoint economic items')
            elif len(set(coverage)) != len(coverage) or set(coverage) & coverages:
                errors.append('overlapping economic coverage would double count')
            else:
                coverages.update(coverage)
            if component.get('category') not in REQUIRED.get(data['perspective'], set()):
                errors.append('unsupported category for participant perspective')
            expected = 'revenue' if component.get('category') in REVENUES.get(data['perspective'], set()) else 'cost'
            if component.get('side') != expected:
                errors.append('component side inconsistent with participant/category')
            if component.get('basis') not in BASES:
                errors.append('unsupported component basis')
            if component.get('currency') != data['currency'] or component.get('period') != data['period']:
                errors.append('all components must use the explicit model currency and period; convert upstream with evidence')
            if component.get('assumption_id') not in assumption_ids:
                errors.append('component requires a registered assumption_id')
            if component.get('rate') is not None:
                try:
                    number(component['rate'])
                except ValueError:
                    errors.append('invalid component rate')
    baseline = {}
    for row in data['baseline_mix']:
        if not isinstance(row, dict) or not isinstance(row.get('method_id'), str) or row['method_id'] not in methods or row['method_id'] in baseline:
            errors.append('baseline method must be known and unique')
            continue
        try:
            baseline[row['method_id']] = number(row.get('share'))
            if baseline[row['method_id']] <= 0:
                errors.append('baseline shares must be positive; omit inactive methods')
        except ValueError:
            errors.append('invalid baseline share')
    if sum(baseline.values()) != 1:
        errors.append('baseline shares must sum exactly to 1')
    scenario = data['scenario']
    if not isinstance(scenario.get('new_method_id'), str) or scenario['new_method_id'] not in methods or scenario['new_method_id'] in baseline:
        errors.append('new_method_id must identify a method absent from baseline_mix')
    try:
        if number(scenario.get('adoption_rate')) > 1:
            errors.append('adoption_rate cannot exceed 1')
    except ValueError:
        errors.append('invalid adoption_rate')
    displacement = {}
    if not isinstance(scenario.get('displacement'), list) or not scenario['displacement']:
        errors.append('displacement must be a nonempty list')
    else:
        for row in scenario['displacement']:
            if not isinstance(row, dict) or not isinstance(row.get('method_id'), str) or row['method_id'] not in baseline or row['method_id'] in displacement:
                errors.append('displaced method must be unique and in baseline')
                continue
            try:
                displacement[row['method_id']] = number(row.get('share'))
            except ValueError:
                errors.append('invalid displacement share')
        if sum(displacement.values()) != 1:
            errors.append('displacement shares must sum exactly to 1')
    if not isinstance(data.get('sensitivity_adoption_rates', []), list):
        errors.append('sensitivity_adoption_rates must be a list')
    else:
        for rate in data.get('sensitivity_adoption_rates', []):
            try:
                if number(rate) > 1:
                    errors.append('sensitivity adoption rate cannot exceed 1')
            except ValueError:
                errors.append('invalid sensitivity adoption rate')
    if not errors:
        adoption = number(scenario['adoption_rate'])
        for mid, share in displacement.items():
            if adoption * share > baseline[mid]:
                errors.append('adoption displaces more attempts than available in baseline')
    return errors


def analyze(request):
    data = request['data']
    findings = []
    methods = {x['method_id']: x for x in data['methods']}
    baseline = {x['method_id']: number(x['share']) for x in data['baseline_mix']}
    scenario = data['scenario']
    displacement = {x['method_id']: number(x['share']) for x in scenario['displacement']}
    added = scenario['new_method_id']
    def gap(code, message, ids=None):
        findings.append({'code': code, 'message': message, 'source_ids': ids or [], 'severity': 'gap'})
    used = set(baseline) | {added}
    for mid in used:
        method = methods[mid]
        for field in ('success_rate', 'average_value'):
            if method.get(field) is None:
                gap('economics-missing-assumption', mid + ': ' + field + ' is unknown.', method.get('source_ids'))
        present = {x['category'] for x in method.get('components', [])}
        for category in sorted(REQUIRED[data['perspective']] - present):
            gap('economics-missing-component', mid + ': explicitly supply ' + category + ', including a justified zero when inapplicable.')
        for component in method.get('components', []):
            if component.get('rate') is None:
                gap('economics-missing-rate', mid + '/' + component['component_id'] + ': rate is unknown.', component.get('source_ids'))
            if not component.get('source_ids'):
                gap('economics-unbacked-assumption', mid + '/' + component['component_id'] + ': supplied assumption lacks a source record.')
        if not method.get('source_ids'):
            gap('economics-unbacked-assumption', mid + ': volume/outcome assumptions lack source records.')
    if request['participant'] != data['perspective']:
        gap('economics-participant-mismatch', 'Request participant and model perspective must match; do not reuse another participant margin model.')
    with localcontext() as ctx:
        ctx.prec = 40
        attempts = number(data['attempts'])
        capacity = min(baseline[mid] / share for mid, share in displacement.items() if share > 0)
        def model(adoption, is_baseline=False):
            mix = dict(baseline)
            if not is_baseline:
                for mid, share in displacement.items():
                    mix[mid] -= adoption * share
                mix[added] = adoption
            rows, total_cost, total_revenue, successful = [], Decimal(0), Decimal(0), Decimal(0)
            complete = True
            for mid, share in mix.items():
                method = methods[mid]
                n = attempts * share
                success = n * number(method['success_rate']) if method.get('success_rate') is not None else None
                value = success * number(method['average_value']) if success is not None and method.get('average_value') is not None else None
                terms, cost, revenue = [], Decimal(0), Decimal(0)
                known = success is not None and value is not None and REQUIRED[data['perspective']].issubset({x['category'] for x in method.get('components', [])})
                for component in method.get('components', []):
                    basis = {'per_attempt': n, 'per_success': success, 'success_value': value, 'period_fixed': Decimal(1)}[component['basis']]
                    amount = basis * number(component['rate']) if basis is not None and component.get('rate') is not None else None
                    terms.append({'component_id': component['component_id'], 'category': component['category'], 'side': component['side'],
                                  'basis': component['basis'], 'rate': component.get('rate'), 'amount': str(amount) if amount is not None else None,
                                  'source_ids': component.get('source_ids', []), 'assumption_id': component['assumption_id']})
                    if amount is None:
                        known = False
                    elif component['side'] == 'cost':
                        cost += amount
                    else:
                        revenue += amount
                complete = complete and known
                if success is not None:
                    successful += success
                total_cost += cost
                total_revenue += revenue
                rows.append({'method_id': mid, 'attempt_share': str(share), 'attempts': str(n), 'expected_successes': str(success) if success is not None else None,
                             'expected_success_value': str(value) if value is not None else None, 'components': terms,
                             'cost': str(cost) if known else None, 'revenue': str(revenue) if known else None,
                             'contribution': str(revenue - cost) if known else None})
            return {'method_economics': rows, 'attempts': str(attempts), 'expected_successes': str(successful) if complete else None,
                    'cost': str(total_cost) if complete else None, 'revenue': str(total_revenue) if complete else None,
                    'contribution': str(total_revenue - total_cost) if complete else None,
                    'cost_per_attempt': str(total_cost / attempts) if complete else None,
                    'cost_per_success': str(total_cost / successful) if complete and successful > 0 else None}
        base = model(Decimal(0), True)
        current = model(number(scenario['adoption_rate']))
        def delta(row):
            if row['contribution'] is None or base['contribution'] is None:
                return None
            return Decimal(row['contribution']) - Decimal(base['contribution'])
        change = delta(current)
        sensitivities = []
        for raw in data.get('sensitivity_adoption_rates', []):
            rate = number(raw)
            if rate > capacity:
                sensitivities.append({'adoption_rate': str(rate), 'state': 'infeasible-displacement', 'incremental_contribution': None})
            else:
                modeled = model(rate)
                change_at_rate = delta(modeled)
                sensitivities.append({'adoption_rate': str(rate), 'state': 'modeled-assumption', 'incremental_contribution': str(change_at_rate) if change_at_rate is not None else None,
                                      'expected_successes': modeled['expected_successes'], 'cost_per_success': modeled['cost_per_success']})
        at_zero, at_capacity = delta(model(Decimal(0))), delta(model(capacity))
        breakeven = {'adoption_rate': None, 'max_feasible_adoption': str(capacity), 'state': 'missing-assumptions'}
        if at_zero is not None and at_capacity is not None:
            slope = (at_capacity - at_zero) / capacity
            breakeven.update({'incremental_fixed_contribution': str(at_zero), 'contribution_per_unit_adoption': str(slope)})
            if slope == 0:
                breakeven['state'] = 'all-feasible-rates-break-even' if at_zero == 0 else 'no-finite-crossing'
            else:
                crossing = -at_zero / slope
                breakeven['state'] = 'within-feasible-range' if 0 <= crossing <= capacity else 'outside-feasible-range'
                breakeven['adoption_rate'] = str(crossing) if 0 <= crossing <= capacity else None
        return {'result': {'perspective': data['perspective'], 'currency': data['currency'], 'period': data['period'],
                           'assumptions': deepcopy(data['assumptions']), 'baseline': base, 'scenario': current,
                           'adoption_rate': str(number(scenario['adoption_rate'])), 'displacement': deepcopy(scenario['displacement']),
                           'incremental_contribution': str(change) if change is not None else None,
                           'sensitivity': sensitivities, 'break_even': breakeven,
                           'interpretation': 'Expected outcomes from supplied assumptions; no guaranteed savings. Baseline contracts remain active and fixed charges remain incurred; adding the new method incurs its fixed charges even at zero adoption. Fixed volume, no automatic retries or customer-growth effects, no discounting, tax or currency conversion.'},
                'findings': findings,
                'handoffs': [{'target_skill': 'merchant-payment-cost-analyzer', 'reason': 'Validate incurred merchant fees separately from modeled scenarios.', 'required_inputs': ['statement period', 'settled-sale transactions', 'fee and fixed-charge evidence']}]}
