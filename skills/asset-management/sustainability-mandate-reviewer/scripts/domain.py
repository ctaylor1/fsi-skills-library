"""Exact supplied sustainability mandate metrics; no scores or certification."""
from foundation_contract import D, date_value, exact, finish, ratio, require_sources, text, validate_actual_date, validate_common
from specialist_contract import validate_specialist_common as validate_common

SKILL = 'sustainability-mandate-reviewer'


def fields(row, *keys):
    if not isinstance(row, dict) or any(not text(row.get(k)) for k in keys):
        raise ValueError('nonempty text required: ' + ', '.join(keys))


def rows(doc, key, identity, *, empty=False):
    value = doc.get(key)
    if not isinstance(value, list) or len(value) > 10000 or not empty and not value:
        raise ValueError(key + ' requires a bounded explicit inventory')
    seen = set()
    for row in value:
        fields(row, identity, 'source_ref')
        if row[identity] in seen:
            raise ValueError('duplicate ' + identity)
        seen.add(row[identity]); require_sources(doc, [row['source_ref']])
    return value


def nonnegative(value):
    value = D(value)
    if value < 0:
        raise ValueError('this method requires nonnegative long-only amounts/metrics')
    return value


def compare(a, operator, b):
    if operator == '<=': return a <= b
    if operator == '>=': return a >= b
    if operator == '>': return a > b
    if operator == '<': return a < b
    raise ValueError('unsupported comparison operator')


@exact
def compute(doc):
    errors = validate_common(doc)
    if errors: raise ValueError('; '.join(errors))
    if doc.get('requested_action', 'review') not in {'review', 'draft'}:
        raise ValueError('business execution or certification unsupported')
    mandate = doc.get('mandate'); portfolio = doc.get('portfolio')
    fields(mandate, 'mandate_id', 'version', 'owner', 'reviewer', 'source_ref')
    fields(portfolio, 'snapshot_id', 'source_ref')
    require_sources(doc, [mandate['source_ref'], portfolio['source_ref']])
    issues = []
    if mandate.get('review_status') != 'reviewed': issues.append('mandate review evidence missing')
    start, end = date_value(mandate.get('effective_from')), date_value(mandate.get('effective_to'))
    if start > end: raise ValueError('mandate effective interval inverted')
    if not start <= date_value(doc['as_of']) <= end: issues.append('mandate not effective at review date')
    if portfolio.get('currency') != doc['currency']: raise ValueError('portfolio currency differs')
    validate_actual_date(doc, portfolio.get('valuation_date'), portfolio['source_ref'])
    if portfolio['valuation_date'] != doc['as_of']: raise ValueError('portfolio valuation date must equal review date')
    total = nonnegative(portfolio.get('total_market_value'))
    holdings = rows(doc, 'holdings', 'holding_id')
    metrics = rows(doc, 'metrics', 'metric_id')
    observations = rows(doc, 'observations', 'observation_id', empty=True)
    exclusions = rows(doc, 'exclusions', 'exclusion_id', empty=True)
    values = {}; eligible = set(); amounts = {}
    for row in holdings:
        fields(row, 'instrument_id', 'issuer_id', 'snapshot_id', 'currency')
        if row['snapshot_id'] != portfolio['snapshot_id'] or row['currency'] != doc['currency']:
            raise ValueError('holding snapshot/currency differs from portfolio')
        if not isinstance(row.get('metric_eligible'), bool): raise ValueError('metric_eligible must be boolean')
        if not row['metric_eligible']: fields(row, 'exclusion_basis')
        amount = nonnegative(row.get('market_value')); amounts[row['holding_id']] = amount
        if row['metric_eligible']: eligible.add(row['holding_id'])
    if sum(amounts.values(), D(0)) != total:
        raise ValueError('holding inventory does not reconcile to declared portfolio denominator')
    eligible_amount = sum((amounts[x] for x in eligible), D(0))
    if total == 0: issues.append('portfolio denominator is zero')
    if eligible_amount == 0: issues.append('eligible metric denominator is zero')
    metric_map = {x['metric_id']: x for x in metrics}
    for metric in metrics:
        fields(metric, 'definition', 'definition_version', 'unit', 'owner', 'denominator_basis')
        if metric['denominator_basis'] not in {'total-market-value', 'eligible-market-value'}:
            raise ValueError('metric denominator basis unsupported')
        year = metric.get('required_vintage')
        if isinstance(year, bool) or not isinstance(year, int) or not 1900 <= year <= date_value(doc['as_of']).year:
            raise ValueError('required_vintage must be an observed calendar year')
        if not isinstance(metric.get('estimates_allowed'), bool): raise ValueError('estimates_allowed must be boolean')
        coverage = nonnegative(metric.get('minimum_coverage'))
        if coverage > 1: raise ValueError('minimum_coverage is a fraction in [0,1]')
        if metric.get('operator') not in {'<=', '>='}: raise ValueError('metric limit operator must be <= or >=')
        nonnegative(metric.get('limit'))
    for observation in observations:
        fields(observation, 'holding_id', 'metric_id', 'unit', 'definition_version')
        key = (observation['holding_id'], observation['metric_id'])
        if key in values: raise ValueError('duplicate holding/metric observation; choose a reviewed version explicitly')
        if observation['holding_id'] not in amounts or observation['metric_id'] not in metric_map:
            raise ValueError('observation refers to unknown holding/metric')
        if not isinstance(observation.get('estimated'), bool): raise ValueError('estimated must be boolean')
        validate_actual_date(doc, observation.get('observed_on'), observation['source_ref'])
        if 'value' not in observation: raise ValueError('observation value required, including explicit null')
        metric = metric_map[observation['metric_id']]; gaps = []
        if observation['unit'] != metric['unit'] or observation['definition_version'] != metric['definition_version']:
            raise ValueError('metric unit/definition version mismatch; no conversion inferred')
        if observation.get('vintage') != metric['required_vintage']: gaps.append('metric vintage differs')
        if observation['estimated'] and not metric['estimates_allowed']: gaps.append('estimated metric is not permitted')
        if observation['value'] is None: gaps.append('metric value unknown')
        value = nonnegative(observation['value']) if observation['value'] is not None else None
        values[key] = (value if not gaps else None, observation, gaps)
    metric_results = []
    scope_valid = not issues and not doc.get('unresolved_issues')
    for metric in metrics:
        covered = numerator = estimated = D(0); missing = []; unavailable = []; source_refs = {metric['source_ref']}
        for holding_id in sorted(eligible):
            if amounts[holding_id] == 0: continue
            entry = values.get((holding_id, metric['metric_id']))
            if entry is None or entry[0] is None:
                missing.append(holding_id)
                unavailable.append({'holding_id': holding_id, 'reasons': entry[2] if entry else ['observation missing'],
                                    'source_ref': entry[1]['source_ref'] if entry else None})
                continue
            value, observation, _ = entry
            covered += amounts[holding_id]; numerator += amounts[holding_id] * value
            if observation['estimated']: estimated += amounts[holding_id]
            source_refs.add(observation['source_ref'])
        denominator = total if metric['denominator_basis'] == 'total-market-value' else eligible_amount
        coverage_met = covered >= D(metric['minimum_coverage']) * eligible_amount if eligible_amount > 0 else None
        complete = not missing and denominator > 0 and eligible_amount > 0 and scope_valid
        meets = compare(numerator, metric['operator'], D(metric['limit']) * denominator) if complete else None
        if missing: issues.append(metric['metric_id'] + ': metric coverage incomplete: ' + ', '.join(missing))
        if coverage_met is False: issues.append(metric['metric_id'] + ': minimum coverage not met')
        if meets is False: issues.append(metric['metric_id'] + ': supplied mandate limit breached')
        metric_results.append({'metric_id': metric['metric_id'], 'unit': metric['unit'], 'vintage': metric['required_vintage'],
            'denominator_basis': metric['denominator_basis'], 'denominator_market_value': str(denominator),
            'eligible_market_value': str(eligible_amount), 'covered_market_value': str(covered),
            'coverage_fraction': ratio(covered, eligible_amount), 'coverage_meets': coverage_met,
            'estimated_market_value': str(estimated), 'estimated_fraction_of_covered': ratio(estimated, covered),
            'weighted_metric': ratio(numerator, denominator) if complete else None,
            'covered_only_mean': ratio(numerator, covered), 'covered_only_mean_is_full_portfolio_metric': False,
            'limit': str(D(metric['limit'])), 'meets_supplied_limit': meets,
            'missing_holding_ids': missing, 'unavailable_observations': unavailable, 'source_refs': sorted(source_refs)})
    exclusion_results = []
    for exclusion in exclusions:
        fields(exclusion, 'metric_id', 'operator', 'owner')
        if exclusion['metric_id'] not in metric_map: raise ValueError('exclusion metric unknown')
        if exclusion['operator'] not in {'<', '>', '<=', '>='}: raise ValueError('unsupported exclusion comparison')
        threshold = nonnegative(exclusion.get('threshold')); breached = D(0); unknown = []; breached_ids = []
        for holding_id in sorted(eligible):
            if amounts[holding_id] == 0: continue
            entry = values.get((holding_id, exclusion['metric_id']))
            if entry is None or entry[0] is None: unknown.append(holding_id)
            elif compare(entry[0], exclusion['operator'], threshold):
                breached += amounts[holding_id]; breached_ids.append(holding_id)
        # Matching a supplied predicate is still useful diagnostic evidence, but
        # an inactive/unreviewed mandate cannot establish an active exclusion.
        status = 'undetermined' if not scope_valid or eligible_amount == 0 else 'breach' if breached_ids else 'undetermined' if unknown else 'no-breach-in-supplied-scope'
        if status != 'no-breach-in-supplied-scope': issues.append(exclusion['exclusion_id'] + ': exclusion ' + status)
        exclusion_results.append({'exclusion_id': exclusion['exclusion_id'], 'metric_id': exclusion['metric_id'],
            'status': status, 'operator': exclusion['operator'], 'threshold': str(threshold), 'unit': metric_map[exclusion['metric_id']]['unit'],
            'known_breached_market_value': str(breached), 'known_breached_fraction_of_eligible': ratio(breached, eligible_amount),
            'breached_holding_ids': breached_ids, 'unknown_holding_ids': unknown, 'source_ref': exclusion['source_ref']})
    return finish(doc, SKILL, 'supplied-sustainability-mandate-metrics/1', {
        'mandate_id': mandate['mandate_id'], 'mandate_version': mandate['version'], 'portfolio_market_value': str(total),
        'metrics': metric_results, 'exclusions': exclusion_results,
        'compliance_certified': False, 'sustainability_label_awarded': False, 'generic_esg_score': None,
    }, issues, limitations=[
        'Long-only supplied market values and nonnegative scalar metrics; no FX, derivatives, short netting or look-through is inferred.',
        'Full weighted metrics and limits are withheld when any positive eligible position lacks permitted, matching-vintage evidence; covered-only means are diagnostics.',
        'Metric definitions, exclusion rules, thresholds and applicability are supplied mandate terms, not universal law or a sustainability certification.',
    ])
