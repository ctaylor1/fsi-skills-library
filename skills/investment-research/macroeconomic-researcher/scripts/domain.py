"""Point-in-time supplied macro series and explicit transformation research (MIT)."""
from __future__ import annotations
import calendar
import copy
from analysis_contract import validate_base, require, number, rows, unique, references, finish
from research_runtime import text, strings, calendar_date, temporal, eligible_time, only

SKILL = 'macroeconomic-researcher'
BASIS = 'series_id label geography frequency measure_kind unit price_basis price_base seasonal_adjustment annualization'
SELECTED = BASIS + ' observation_id period_end release_at vintage_id value evidence_refs'
FREQUENCIES = {'monthly': 1, 'quarterly': 3, 'annual': 12}


def period(value, frequency):
    d = calendar_date(value)
    require(d.day == calendar.monthrange(d.year, d.month)[1], 'period_end must be a calendar period end')
    require(frequency != 'quarterly' or d.month in (3, 6, 9, 12), 'quarterly period_end requires calendar quarter end')
    require(frequency != 'annual' or d.month == 12, 'annual period_end requires calendar year end')
    return d


def validate_basis(row):
    for key in BASIS.split():
        require(text(row.get(key)), 'series requires explicit ' + key)
        require(row[key].strip().lower() != 'unknown', 'unknown ' + key + ' cannot establish series comparability')
    require(row['frequency'] in FREQUENCIES, 'frequency must be monthly, quarterly or annual')
    require(row['measure_kind'] in {'level', 'index', 'rate'}, 'unsupported measure_kind')
    require(row['price_basis'] in {'real', 'nominal', 'not-applicable'}, 'unsupported price_basis')
    require(row['seasonal_adjustment'] in {'seasonally-adjusted', 'not-seasonally-adjusted', 'not-applicable'}, 'unsupported seasonal_adjustment')
    require(row['annualization'] in {'annual-rate', 'period-level', 'not-applicable'}, 'unsupported annualization')
    require(row['price_basis'] != 'real' or row['price_base'] != 'not-applicable', 'real series requires explicit price_base')
    require(row['measure_kind'] != 'index' or row['price_base'] != 'not-applicable', 'index requires explicit price_base')


def cite(doc, row, time_key):
    refs = row.get('evidence_refs')
    require(isinstance(refs, list) and bool(refs), 'analytical rows require precise evidence_refs')
    references(doc, refs)
    temporal(row.get(time_key))
    sources = {s['source_id']: s for s in doc['sources']}
    for ref in refs:
        require(eligible_time(sources[ref['source_id']]['known_at'], row[time_key]) is True,
                'source knowledge must precede the cited row release/knowledge time with matching precision')


def day(value):
    kind, date = temporal(value)
    return date if kind == 'date' else date.date()


def validate_document(doc):
    validate_base(doc, subject_types=('economy', 'sector'))
    only(doc, 'request_id purpose audience subject as_of use_on knowledge_cutoff information_barrier sources evidence_refs unresolved_issues pre_event event_time series_inventory_complete requested_series_ids series calculations outlooks research_questions', 'macro request')
    require(isinstance(doc.get('series_inventory_complete'), bool), 'series_inventory_complete must be explicit boolean')
    strings(doc.get('requested_series_ids'), 'requested_series_ids', True)
    series = unique(rows(doc.get('series'), 'series', True), 'series_id', 'series')
    observation_ids = set()
    for s in series:
        only(s, BASIS + ' observations', 'series')
        validate_basis(s)
        observations = unique(rows(s.get('observations'), 'observations', True), 'observation_id', 'observations')
        duplicates = set()
        for r in observations:
            only(r, 'observation_id period_end release_at vintage_id value evidence_refs', 'observation')
            require(r['observation_id'] not in observation_ids, 'observation_id must be globally unique')
            observation_ids.add(r['observation_id'])
            require(text(r.get('vintage_id')), 'vintage_id required')
            require('value' in r, 'value required; use explicit null for unavailable observation')
            number(r['value'], 'observation value', nullable=True)
            p = period(r.get('period_end'), s['frequency'])
            cite(doc, r, 'release_at')
            require(p <= day(r['release_at']), 'reported observation period cannot postdate release')
            # Same instant with conflicting releases has no deterministic priority.
            stamp = temporal(r['release_at'])
            key = (r['period_end'], stamp)
            require(key not in duplicates, 'duplicate or ambiguous release for same period')
            duplicates.add(key)
    known = {s['series_id']: s for s in series}
    calculations = unique(rows(doc.get('calculations'), 'calculations'), 'calculation_id', 'calculations')
    for c in calculations:
        only(c, 'calculation_id series_id from_period to_period operation', 'calculation')
        require(c.get('series_id') in known, 'calculation references unknown series')
        s = known[c['series_id']]
        start, end = period(c.get('from_period'), s['frequency']), period(c.get('to_period'), s['frequency'])
        require(start < end, 'calculation periods must increase')
        require(c.get('operation') in {'difference', 'percent-change', 'annualized-percent-change'}, 'unsupported operation')
        if c['operation'] != 'difference':
            require(s['measure_kind'] != 'rate', 'rate series requires difference; percent changes in a rate are not supported')
        if c['operation'] == 'annualized-percent-change':
            require(s['seasonal_adjustment'] != 'not-seasonally-adjusted', 'annualization of unadjusted seasonal changes is not supported')
    outlooks = unique(rows(doc.get('outlooks'), 'outlooks'), 'outlook_id', 'outlooks')
    for o in outlooks:
        only(o, 'outlook_id kind series_id period_end value known_at assumptions consensus_provider evidence_refs', 'outlook')
        require(o.get('kind') in {'scenario', 'analyst-forecast', 'consensus'}, 'outlook kind must distinguish assumptions, forecast or supplied consensus')
        require(o.get('series_id') in known, 'outlook references unknown series')
        require(period(o.get('period_end'), known[o['series_id']]['frequency']) > calendar_date(doc['as_of']), 'outlook must concern a future period')
        require('value' in o, 'outlook value required; use null for unavailable')
        number(o['value'], 'outlook value', nullable=True)
        strings(o.get('assumptions'), 'outlook assumptions', True)
        cite(doc, o, 'known_at')
        require(eligible_time(o['known_at'], doc['knowledge_cutoff']) is True and day(o['known_at']) <= calendar_date(doc['as_of']), 'outlook assumptions must be known by cutoff and as_of')
        if o['kind'] == 'consensus':
            require(text(o.get('consensus_provider')), 'consensus requires supplied provider identity')
        else:
            require('consensus_provider' not in o, 'only consensus accepts consensus_provider')
    questions = unique(rows(doc.get('research_questions'), 'research_questions', True), 'question_id', 'research_questions')
    calculation_ids = {c['calculation_id'] for c in calculations}
    for q in questions:
        only(q, 'question_id question required_calculation_ids interpretation counter_evidence', 'research question')
        require(text(q.get('question')), 'research question text required')
        strings(q.get('required_calculation_ids'), 'required_calculation_ids')
        require(set(q['required_calculation_ids']) <= calculation_ids, 'research question references unknown calculation')
        for key in ('interpretation', 'counter_evidence'):
            require(key in q, key + ' required; use explicit null when unavailable')
            require(q.get(key) is None or text(q[key]), key + ' must be text or explicit null')
    return doc


def compute(doc):
    validate_document(doc)
    selected, excluded, revisions, calculated, issues, lineage = [], [], [], [], [], []
    by_series = {s['series_id']: s for s in doc['series']}
    index = {}
    for s in doc['series']:
        eligible = {}
        for r in s['observations']:
            reason = None
            time_ok = eligible_time(r['release_at'], doc['knowledge_cutoff'])
            if time_ok is None:
                reason = 'release/cutoff time precision differs; intraday availability is unestablished'
            elif not time_ok or day(r['release_at']) > calendar_date(doc['as_of']):
                reason = 'release postdates research cutoff or economic as_of'
            elif calendar_date(r['period_end']) > calendar_date(doc['as_of']):
                reason = 'reported observation period postdates economic as_of'
            if reason:
                excluded.append({'observation_id': r['observation_id'], 'series_id': s['series_id'], 'period_end': r['period_end'], 'release_at': r['release_at'], 'reason': reason})
                continue
            eligible.setdefault(r['period_end'], []).append(r)
        for p, records in sorted(eligible.items()):
            records.sort(key=lambda r: temporal(r['release_at'])[1])
            chosen = records[-1]
            row = {k: copy.deepcopy(s[k]) for k in BASIS.split()}
            row.update(copy.deepcopy(chosen))
            selected.append(row)
            index[(s['series_id'], p)] = row
            if chosen['value'] is None:
                issues.append(s['series_id'] + ' ' + p + ': latest eligible observation is explicitly unavailable; earlier release is not substituted')
            for previous in records[:-1]:
                excluded.append({'observation_id': previous['observation_id'], 'series_id': s['series_id'], 'period_end': p, 'release_at': previous['release_at'], 'reason': 'superseded by latest eligible supplied release'})
            if len(records) > 1:
                first = records[0]
                delta = None if first['value'] is None or chosen['value'] is None else chosen['value'] - first['value']
                revisions.append({'series_id': s['series_id'], 'period_end': p, 'first_observation_id': first['observation_id'], 'latest_observation_id': chosen['observation_id'], 'value_change': delta, 'unit': 'percentage-point' if s['measure_kind'] == 'rate' and s['unit'] == 'percent' else s['unit'], 'scope': 'first-to-latest eligible supplied releases; not necessarily initial publication'})
    coverage = []
    for sid in doc['requested_series_ids']:
        present = sid in by_series and any(r['series_id'] == sid for r in selected)
        coverage.append({'series_id': sid, 'eligible_observation_supplied': present})
        if not present:
            issues.append('Requested series has no eligible supplied observation: ' + sid)
    if not doc['series_inventory_complete']:
        issues.append('Supplied series inventory is not asserted complete for requested research scope')
    for c in doc['calculations']:
        s = by_series[c['series_id']]
        left = index.get((c['series_id'], c['from_period']))
        right = index.get((c['series_id'], c['to_period']))
        unit = s['unit'] if c['operation'] == 'difference' else 'percent'
        if c['operation'] == 'difference' and s['measure_kind'] == 'rate' and s['unit'] == 'percent':
            unit = 'percentage-point'
        value, reason = None, None
        if left is None or right is None or left['value'] is None or right['value'] is None:
            reason = 'missing or unavailable eligible endpoints; no interpolation or substitution'
        elif c['operation'] == 'difference':
            value = right['value'] - left['value']
        elif left['value'] <= 0 or right['value'] < 0:
            reason = 'percent-change comparison requires positive start and nonnegative end levels'
        elif c['operation'] == 'percent-change':
            value = 100 * (right['value'] / left['value'] - 1)
        elif right['value'] == 0:
            reason = 'annualized growth requires positive endpoints'
        else:
            start, end = calendar_date(c['from_period']), calendar_date(c['to_period'])
            months = (end.year - start.year) * 12 + end.month - start.month
            value = 100 * ((right['value'] / left['value']) ** (12 / months) - 1)
        if reason:
            issues.append(c['calculation_id'] + ': ' + reason)
        result = dict(c, value=value, unit=unit, unavailable_reason=reason,
                      from_observation_id=left['observation_id'] if left else None,
                      to_observation_id=right['observation_id'] if right else None)
        calculated.append(result)
        lineage.append({'calculation_id': c['calculation_id'], 'formula': {'difference':'end - start', 'percent-change':'100 * (end / start - 1)', 'annualized-percent-change':'100 * ((end / start) ** (12 / elapsed_calendar_months) - 1)'}[c['operation']], 'basis': {k:s[k] for k in BASIS.split()}})
    question_rows = []
    by_calc = {c['calculation_id']: c for c in calculated}
    for q in doc['research_questions']:
        gaps = [cid for cid in q['required_calculation_ids'] if by_calc[cid]['value'] is None]
        if q['interpretation'] is None or q['counter_evidence'] is None:
            gaps.append('supplied interpretation or counter-evidence missing')
        if gaps:
            issues.append(q['question_id'] + ': incomplete research response: ' + ', '.join(gaps))
        question_rows.append(dict(copy.deepcopy(q), review_status='needs-review' if gaps else 'supplied-interpretation-for-review', gaps=gaps))
    for o in doc['outlooks']:
        if o['value'] is None:
            issues.append(o['outlook_id'] + ': outlook value is unavailable')
    return finish(doc, SKILL, {'selected_observations': selected, 'excluded_observations': excluded,
        'revisions': revisions, 'calculations': calculated, 'requested_coverage': coverage,
        'outlooks': copy.deepcopy(doc['outlooks']), 'research_questions': question_rows,
        'selection_scope': 'latest eligible supplied release per series and period; external release inventory not authenticated',
        'limitations': ['No cross-series arithmetic, rebasing, currency conversion, interpolation or automatic seasonal adjustment.',
            'Annualized growth is a compounding comparison convention; it is not a forecast.',
            'Supplied interpretations, consensus and scenarios remain unverified judgments; no probabilities inferred.']}, issues=issues, lineage=lineage)
