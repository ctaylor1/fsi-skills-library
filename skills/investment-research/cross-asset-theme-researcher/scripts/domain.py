"""Falsifiable supplied transmission hypotheses and bounded scenario responses (MIT)."""
from __future__ import annotations
import calendar
import copy
from analysis_contract import validate_base, require, number, rows, unique, references, finish
from research_runtime import text, strings, calendar_date, temporal, eligible_time, only

SKILL = 'cross-asset-theme-researcher'
ASSETS = {'rates', 'credit', 'equity', 'fx', 'commodities', 'real-assets'}
DRIVER_KEYS = 'observation_id series_id label geography frequency measure_kind unit price_basis price_base seasonal_adjustment annualization period_end release_at vintage_id value evidence_refs'


def day(value):
    kind, date = temporal(value)
    return date if kind == 'date' else date.date()


def cite(doc, row, time_key='known_at'):
    refs = row.get('evidence_refs')
    require(isinstance(refs, list) and bool(refs), 'analytical rows require precise evidence_refs')
    references(doc, refs)
    require(eligible_time(row.get(time_key), doc['knowledge_cutoff']) is True,
            'row knowledge/release must precede cutoff with matching time precision')
    require(day(row[time_key]) <= calendar_date(doc['as_of']), 'row knowledge/release postdates as_of')
    sources = {s['source_id']: s for s in doc['sources']}
    for ref in refs:
        require(eligible_time(sources[ref['source_id']]['known_at'], row[time_key]) is True,
                'source knowledge must precede cited row knowledge with matching precision')


def validate_document(doc):
    validate_base(doc, subject_types=('economy', 'sector', 'portfolio'))
    only(doc, 'request_id purpose audience subject as_of use_on knowledge_cutoff information_barrier sources evidence_refs unresolved_issues pre_event event_time theme_id hypothesis driver_observations evidence coverage falsifiers scenarios exposures', 'theme request')
    require(text(doc.get('theme_id')), 'theme_id required')
    hypothesis = doc.get('hypothesis')
    require(isinstance(hypothesis, dict), 'hypothesis must be an object')
    only(hypothesis, 'statement driver transmission horizon_date', 'hypothesis')
    for key in ('statement', 'driver', 'transmission'):
        require(text(hypothesis.get(key)), 'hypothesis requires ' + key)
    require(calendar_date(hypothesis.get('horizon_date')) > calendar_date(doc['as_of']), 'hypothesis horizon must be future')
    drivers = unique(rows(doc.get('driver_observations', []), 'driver_observations'), 'observation_id', 'driver_observations')
    for r in drivers:
        only(r, DRIVER_KEYS, 'driver observation')
        for key in DRIVER_KEYS.split():
            if key not in {'value', 'evidence_refs'}:
                require(text(r.get(key)) and r[key].strip().lower() != 'unknown', 'driver observation requires explicit ' + key)
        require(r['frequency'] in {'monthly', 'quarterly', 'annual'}, 'unsupported driver frequency')
        require(r['measure_kind'] in {'level', 'index', 'rate'}, 'unsupported driver measure_kind')
        require(r['price_basis'] in {'real', 'nominal', 'not-applicable'}, 'unsupported driver price_basis')
        require(r['seasonal_adjustment'] in {'seasonally-adjusted', 'not-seasonally-adjusted', 'not-applicable'}, 'unsupported driver seasonal_adjustment')
        require(r['annualization'] in {'annual-rate', 'period-level', 'not-applicable'}, 'unsupported driver annualization')
        require((r['price_basis'] != 'real' and r['measure_kind'] != 'index') or r['price_base'] != 'not-applicable', 'real/index driver requires price_base')
        p = calendar_date(r['period_end'])
        require(p.day == calendar.monthrange(p.year, p.month)[1], 'driver period_end must be calendar period end')
        require(r['frequency'] != 'quarterly' or p.month in (3, 6, 9, 12), 'driver quarter end invalid')
        require(r['frequency'] != 'annual' or p.month == 12, 'driver year end invalid')
        require(p <= day(r['release_at']), 'reported driver period postdates release')
        cite(doc, r, 'release_at')
        require('value' in r, 'driver requires value; use null for unavailable')
        number(r['value'], 'driver value', nullable=True)
    seen_periods = [(r['series_id'], r['period_end']) for r in drivers]
    require(len(set(seen_periods)) == len(seen_periods), 'driver observations cannot contain competing vintages for one series-period')
    driver_ids = {r['observation_id'] for r in drivers}
    evidence = unique(rows(doc.get('evidence'), 'evidence'), 'evidence_id', 'evidence')
    for e in evidence:
        only(e, 'evidence_id role statement known_at evidence_refs driver_observation_ids', 'theme evidence')
        require(e.get('role') in {'support', 'counter'}, 'evidence role must distinguish support/counter')
        require(text(e.get('statement')), 'evidence statement required')
        strings(e.get('driver_observation_ids', []), 'driver_observation_ids')
        require(set(e.get('driver_observation_ids', [])) <= driver_ids, 'evidence references unknown driver observation')
        cite(doc, e)
    coverage = doc.get('coverage')
    require(isinstance(coverage, dict), 'coverage object required')
    only(coverage, 'required_asset_classes inventory_complete', 'coverage')
    strings(coverage.get('required_asset_classes'), 'required_asset_classes', True)
    require(len(coverage['required_asset_classes']) >= 2 and set(coverage['required_asset_classes']) <= ASSETS,
            'cross-asset requested scope requires at least two supported asset classes')
    require(isinstance(coverage.get('inventory_complete'), bool), 'inventory_complete must be explicit boolean')
    falsifiers = unique(rows(doc.get('falsifiers'), 'falsifiers'), 'test_id', 'falsifiers')
    for f in falsifiers:
        only(f, 'test_id description monitor due_on status known_at evidence_refs', 'falsifier')
        for key in ('description', 'monitor'):
            require(text(f.get(key)), 'falsifier requires testable ' + key)
        calendar_date(f.get('due_on'))
        require(f.get('status') in {'not-tested', 'observed', 'not-observed'}, 'unsupported falsifier status')
        if f['status'] == 'not-tested':
            require(f.get('known_at') is None and f.get('evidence_refs') == [], 'untested falsifier cannot assert observed evidence')
        else:
            cite(doc, f)
    scenarios = unique(rows(doc.get('scenarios'), 'scenarios', True), 'scenario_id', 'scenarios')
    for s in scenarios:
        only(s, 'scenario_id label horizon_date known_at assumptions shocks evidence_refs', 'scenario')
        require(text(s.get('label')), 'scenario label required')
        require(calendar_date(s.get('horizon_date')) > calendar_date(doc['as_of']), 'scenario horizon must be future')
        require(s['horizon_date'] == hypothesis['horizon_date'], 'scenario/hypothesis horizons differ; split the research scope')
        strings(s.get('assumptions'), 'scenario assumptions', True)
        cite(doc, s)
        shocks = unique(rows(s.get('shocks'), 'shocks', True), 'driver_id', 'shocks')
        for shock in shocks:
            only(shock, 'driver_id value unit', 'shock')
            number(shock.get('value'), 'shock value')
            require(shock.get('unit') in {'basis-point', 'percentage-point', 'percent'}, 'unsupported shock unit')
    exposures = unique(rows(doc.get('exposures'), 'exposures'), 'exposure_id', 'exposures')
    for e in exposures:
        only(e, 'exposure_id asset_class instrument_id method driver_id sensitivity shock_unit response_unit known_at evidence_refs quote_convention limitations mechanism qualitative_response', 'exposure')
        require(e.get('asset_class') in ASSETS, 'unsupported asset_class')
        for key in ('instrument_id', 'driver_id', 'mechanism'):
            require(text(e.get(key)), 'exposure requires ' + key)
        require(e.get('method') in {'linear', 'modified-duration', 'qualitative'}, 'unsupported response method')
        require(e.get('shock_unit') in {'basis-point', 'percentage-point', 'percent'}, 'unsupported exposure shock_unit')
        strings(e.get('limitations'), 'exposure limitations', True)
        if e['method'] == 'qualitative':
            require(e.get('sensitivity') is None and e.get('response_unit') == 'qualitative', 'qualitative method cannot imply numeric sensitivity or unit')
            require(text(e.get('qualitative_response')), 'qualitative method requires supplied conditional response')
        else:
            number(e.get('sensitivity'), 'sensitivity')
            require(e.get('response_unit') in {'percent-price-change', 'percent-income-change', 'yield-basis-point'}, 'unsupported numeric response_unit')
            require('qualitative_response' not in e, 'numeric method does not accept qualitative_response')
        if e['method'] == 'modified-duration':
            require(e['asset_class'] in {'rates', 'credit'} and e['shock_unit'] == 'basis-point' and e['response_unit'] == 'percent-price-change', 'modified-duration requires rates/credit yield bp shock and percent-price-change response')
            require(e['sensitivity'] >= 0, 'modified duration must be nonnegative')
        if e['asset_class'] == 'fx':
            require(text(e.get('quote_convention')) and e['quote_convention'].strip().lower() != 'unknown', 'FX exposure requires explicit quote_convention; positive response means quoted price increases')
        else:
            require('quote_convention' not in e, 'quote_convention is reserved for FX exposure')
        cite(doc, e)
    return doc


def compute(doc):
    validate_document(doc)
    issues, responses, lineage = [], [], []
    evidence_roles = {e['role'] for e in doc['evidence']}
    if 'support' not in evidence_roles:
        issues.append('No supplied evidence supports the hypothesis')
    if 'counter' not in evidence_roles:
        issues.append('No supplied counter-evidence; confirmation bias review remains open')
    if not doc['falsifiers']:
        issues.append('No testable falsifier supplied')
    for f in doc['falsifiers']:
        if f['status'] == 'observed':
            issues.append('Supplied falsifier observed; hypothesis requires reassessment: ' + f['test_id'])
        elif f['status'] == 'not-tested' and calendar_date(f['due_on']) <= calendar_date(doc['as_of']):
            issues.append('Falsifier review is due and untested: ' + f['test_id'])
    actual_classes = {e['asset_class'] for e in doc['exposures']}
    gaps = sorted(set(doc['coverage']['required_asset_classes']) - actual_classes)
    issues.extend('Requested asset class has no supplied exposure analysis: ' + asset for asset in gaps)
    if not doc['coverage']['inventory_complete']:
        issues.append('Supplied exposure inventory is not asserted complete for requested scope')
    for d in doc.get('driver_observations', []):
        if d['value'] is None:
            issues.append('Supplied driver observation is unavailable: ' + d['observation_id'])
    for scenario in doc['scenarios']:
        shock_map = {s['driver_id']: s for s in scenario['shocks']}
        used = set()
        for e in doc['exposures']:
            shock = shock_map.get(e['driver_id'])
            unavailable, value = None, None
            if shock is None:
                unavailable = 'no supplied shock for exposure driver'
            else:
                require(shock['unit'] == e['shock_unit'], 'scenario shock unit differs from supplied sensitivity denominator; no automatic conversion')
                used.add(shock['driver_id'])
                if e['method'] == 'linear':
                    value = e['sensitivity'] * shock['value']
                elif e['method'] == 'modified-duration':
                    value = -e['sensitivity'] * shock['value'] / 100
            if unavailable:
                issues.append(scenario['scenario_id'] + '/' + e['exposure_id'] + ': ' + unavailable)
            if value is not None and e['response_unit'] == 'percent-price-change' and value <= -100:
                issues.append(scenario['scenario_id'] + '/' + e['exposure_id'] + ': local approximation implies a nonpositive price; response is outside usable range')
                unavailable, value = 'local approximation outside positive-price range', None
            responses.append({'scenario_id': scenario['scenario_id'], 'exposure_id': e['exposure_id'], 'asset_class': e['asset_class'],
                'instrument_id': e['instrument_id'], 'driver_id': e['driver_id'], 'shock': copy.deepcopy(shock), 'method': e['method'],
                'sensitivity': e['sensitivity'], 'value': value, 'response_unit': e['response_unit'], 'unavailable_reason': unavailable,
                'conditional_qualitative_response': e.get('qualitative_response') if not unavailable else None,
                'quote_convention': e.get('quote_convention'), 'limitations': copy.deepcopy(e['limitations'])})
            lineage.append({'scenario_id': scenario['scenario_id'], 'exposure_id': e['exposure_id'],
                'formula': {'linear':'supplied response units per shock unit * supplied shock units', 'modified-duration':'percent price change approximately -modified_duration * yield_shock_bp / 100', 'qualitative':'supplied conditional narrative; no numeric response'}[e['method']]})
        for driver_id in sorted(set(shock_map) - used):
            issues.append(scenario['scenario_id'] + ': shock has no supplied exposure sensitivity: ' + driver_id)
    results = {'theme_id': doc['theme_id'], 'hypothesis': copy.deepcopy(doc['hypothesis']),
        'driver_observations': copy.deepcopy(doc.get('driver_observations', [])), 'evidence': copy.deepcopy(doc['evidence']),
        'falsifiers': copy.deepcopy(doc['falsifiers']), 'scenarios': copy.deepcopy(doc['scenarios']), 'scenario_responses': responses,
        'coverage': {'required_asset_classes': copy.deepcopy(doc['coverage']['required_asset_classes']), 'supplied_asset_classes': sorted(actual_classes), 'missing_asset_classes': gaps},
        'hypothesis_status': 'challenged-by-supplied-falsifier' if any(f['status'] == 'observed' for f in doc['falsifiers']) else 'supplied-hypothesis-for-review',
        'causality_established': False, 'probabilities_estimated': False, 'portfolio_allocation_proposed': False,
        'limitations': ['Supplied sensitivities are assumptions, not estimated coefficients or authenticated market facts.',
            'Responses are conditional local approximations per instrument; no aggregation, portfolio weighting, covariance, convexity, carry or dynamic path modeled.',
            'Historical driver observations do not establish shocks, causal direction, forecasts or probability.',
            'A not-observed falsifier is evidence for the declared review scope only, not proof of the hypothesis.']}
    return finish(doc, SKILL, results, issues=issues, lineage=lineage)
