from decimal import Decimal
from analytics_helpers import Review, rows, ratio, total, text, validate_with


def evaluate(doc):
    r = Review(doc)
    d, profile = r.data, r.profile
    rules = rows(profile.get('rules', []), 'rule_id')
    if not rules:
        r.add('rule-gap', 'Applicable versioned market-conduct control definitions are required')
    cases = rows(d.get('cases', []), 'record_id')
    sampling = d.get('sampling', {})
    r.evidence(sampling, 'sampling design')
    population = r.num(sampling, 'population_count')
    method = sampling.get('method')
    if method not in {'census', 'random', 'purposive'}:
        raise ValueError('sampling.method must be census, random or purposive')
    if population is not None and (population != population.to_integral_value() or population < len(cases) or (method == 'census' and population != len(cases))):
        r.add('sample-frame-conflict', 'Population count and reviewed sample/census do not reconcile', sampling)
    if not cases:
        r.add('sample-gap', 'Review records are unavailable')
    tests = []
    now = r.date(doc, 'as_of')
    for rule in rules:
        r.evidence(rule, rule['rule_id'])
        if not text(rule.get('activity')) or rule.get('operator') not in {'max_calendar_days', 'maximum', 'minimum', 'equals'}:
            raise ValueError('Rule activity/operator unsupported')
        if rule['operator'] == 'max_calendar_days' and rule.get('day_basis') != 'elapsed_calendar_excluding_start':
            r.add('day-basis-gap', 'Only elapsed calendar days excluding the start date are calculated; business-day or notice-service rules require another reviewed method', rule)
    for case in cases:
        sourced = r.evidence(case, case['record_id'])
        applicable = [x for x in rules if x['activity'] == case.get('activity')]
        if not applicable:
            r.add('rule-coverage-gap', case['record_id']+': no applicable control definition', case)
        for rule in applicable:
            state, observed = 'not_evaluable', None
            if rule['operator'] == 'max_calendar_days':
                dates = case.get('dates', {})
                if not isinstance(dates, dict):
                    raise ValueError('case.dates must be an object')
                start = r.date(dates, rule.get('start_field'))
                end_value = dates.get(rule.get('end_field'))
                pending = case.get('pending_events', [])
                if not isinstance(pending, list) or any(not text(x) for x in pending):
                    raise ValueError('pending_events must be a list of explicit uncompleted event names')
                is_pending = rule.get('end_field') in pending
                if is_pending and end_value is not None:
                    r.add('event-conflict', case['record_id']+': event is both completed and pending', case)
                    end = None
                else:
                    end = now if is_pending else r.date(dates, rule.get('end_field'))
                limit = r.num(rule, 'value')
                if sourced and start is not None and end is not None and limit is not None and rule.get('day_basis') == 'elapsed_calendar_excluding_start':
                    if start <= end <= now:
                        observed = Decimal((end-start).days)
                        state = 'observed_exception' if observed > limit else 'pending_within_target' if is_pending else 'observed_within_target'
                    else:
                        r.add('chronology-gap', case['record_id']+': event dates reversed or after review', case)
            else:
                values = case.get('values', {})
                if not isinstance(values, dict):
                    raise ValueError('case.values must be an object')
                field = rule.get('field')
                if not text(field):
                    raise ValueError('Non-date rule field is required')
                observed = values.get(field)
                if observed is None or rule.get('value') is None:
                    r.add('observation-gap', case['record_id']+': observed/expected '+field+' unavailable', case)
                elif sourced:
                    if rule['operator'] == 'equals':
                        matches = type(observed) is type(rule['value']) and observed == rule['value']
                    else:
                        actual, threshold = r.num(values, field, signed=True), r.num(rule, 'value', signed=True)
                        matches = actual <= threshold if rule['operator'] == 'maximum' else actual >= threshold
                        observed = actual
                    state = 'observed_within_target' if matches else 'observed_exception'
            tests.append({'record_id': case['record_id'], 'rule_id': rule['rule_id'], 'observed': observed,
                          'expected': rule.get('value'), 'assessment': state, 'source_refs': case.get('source_refs', []),
                          'rule_source_refs': rule.get('source_refs', [])})
            if state == 'observed_exception':
                r.add('control-exception', case['record_id']+'/'+rule['rule_id']+': supplied control exception; obtain owner/root-cause/remediation review', case, 'review')
    metrics = rows(d.get('metrics', []), 'row_id')
    grouped, seen = {}, set()
    for row in metrics:
        sourced = r.evidence(row, row['row_id'])
        identity = (row.get('metric_id'), row.get('partition_id'))
        if not all(text(x) for x in identity) or identity in seen:
            raise ValueError('Metric partitions must be explicit and disjoint within each metric_id')
        seen.add(identity)
        valid = row.get('inventory_complete') is True and sourced
        if not valid:
            r.add('metric-inventory-gap', row['row_id']+': metric population completeness unresolved', row)
        n, den = r.num(row, 'numerator'), r.num(row, 'denominator')
        definition = (row.get('definition_id'), row.get('definition_version'), row.get('period'), row.get('unit'), row.get('scope_id'))
        if not all(text(x) for x in definition):
            r.add('metric-definition-gap', row['row_id']+': versioned definition, period, unit and scope required', row)
            valid = False
        group = grouped.setdefault(identity[0], {'definition': definition, 'rows': [], 'valid': True})
        if group['definition'] != definition:
            r.add('metric-scope-gap', row['row_id']+': metric definitions/bases differ; do not average ratios', row)
            valid = False
        group['valid'] &= valid
        group['rows'].append((n, den, row['row_id']))
    aggregates = []
    for key, group in grouped.items():
        n, den = (total([x[i] for x in group['rows']]) if group['valid'] else None for i in (0, 1))
        value = ratio(n, den)
        if value is None:
            r.add('metric-ratio-gap', key+': missing/mixed population or zero denominator; ratio withheld')
        aggregates.append({'metric_id': key, 'definition': group['definition'], 'numerator': n, 'denominator': den, 'ratio': value, 'source_rows': [x[2] for x in group['rows']]})
    return r.finish({'sample_design': sampling, 'control_observations': tests, 'population_metrics': aggregates,
                     'sample_extrapolation': 'not_performed', 'compliance_opinion': 'not_made', 'filing_submitted': False,
                     'review_scope': 'Supplied control tests and metric definitions, not a full examination or certified MCAS return'})


def validate(doc):
    return validate_with(evaluate, doc)
