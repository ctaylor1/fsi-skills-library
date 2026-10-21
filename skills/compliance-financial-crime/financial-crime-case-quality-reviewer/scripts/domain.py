"""Offline case workpaper QA. Supplied human judgments remain unverified."""
from __future__ import annotations

from decimal import Decimal, localcontext
import re

from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, day, records, strings, unique_ids, source_index, evidence_issues)
from native_integrity import canonical_hash

SKILL = 'financial-crime-case-quality-reviewer'
OBJECT_TYPES = {'financial_crime_case_quality_review'}
METHOD = 'case-criterion-source-and-reasoning-review/1.0'
T = text
B = lambda v: isinstance(v, bool)
D = lambda v: day(v) is not None
L = strings
E = lambda *allowed: lambda v: isinstance(v, str) and v in allowed
DEC = lambda v: isinstance(v, str) and re.fullmatch(r'(?:0(?:\.\d+)?|1(?:\.0+)?)', v) is not None


def proposed_facts(value):
    return records(value) and all(set(v) == {'source_ref', 'fact_id', 'value'} and
        T(v['source_ref']) and T(v['fact_id']) for v in value)


MANDATE = {'mandate_id': T, 'mandate_type': E('operational-qa', 'second-line-monitoring',
    'statutory-independent-testing', 'internal-audit', 'model-validation'),
    'mandate_owner': T, 'reviewer_id': T, 'legal_profile_id': T, 'legal_profile_version': T,
    'legal_profile_reviewed': B, 'authority_reviewed': B, 'authority_scope': T,
    'independence_owner_assessment': B, 'operational_involvement': B,
    'reporting_line_review': B, 'conflict_review': B, 'competence_review': B,
    'period_from': D, 'period_to': D, 'population_case_ids': L, 'selected_case_ids': L,
    'sampling_method': T, 'sampling_rationale': T, 'criteria_ids': L,
    'maximum_exception_proportion': DEC}
COLLECTIONS = {
    'cases': ('native_case_id', {'case_id': T, 'institution_id': T, 'legal_entity_id': T,
        'jurisdiction': T, 'upstream_native_id': T, 'upstream_native_version': T,
        'period_from': D, 'period_to': D, 'required_exhibit_ids': L, 'concern_ids': L,
        'contradiction_ids': L, 'counterevidence_ids': L,
        'disposition_reasoning_id': T, 'proposed_disposition': T, 'disposition_on': D}),
    'exhibits': ('exhibit_id', {'case_id': T, 'version': T, 'evidence_source_ref': T,
        'evidence_fact_ids': L, 'available': B, 'captured_on': D}),
    'events': ('event_id', {'case_id': T, 'occurred_on': D,
        'predecessor_event_ids': L, 'exhibit_ids': L,
        'event_kind': E('activity', 'case-opened', 'analysis', 'proposed-disposition'), 'statement': T}),
    'reasoning': ('reasoning_id', {'case_id': T, 'concern_ids': L,
        'considered_counterevidence_ids': L, 'addressed_contradiction_ids': L,
        'exhibit_ids': L, 'rationale': T, 'proposed_disposition': T,
        'human_review_complete': B, 'reviewer_id': T,
        'human_judgement': E('pass', 'fail', 'unknown')}),
    'criteria': ('criterion_id', {'kind': E('evidence-completeness', 'chronology-consistency',
        'reasoning-traceability', 'disposition-traceability', 'tool-source-faithfulness'),
        'version': T, 'procedure': T, 'requirement': T, 'legal_profile_id': T,
        'legal_profile_version': T, 'applicable_case_ids': L}),
    'observations': ('observation_id', {'case_id': T, 'criterion_id': T,
        'criterion_version': T, 'tested_on': D, 'observed_outcome': E('pass', 'fail', 'unknown'),
        'rationale': T, 'exhibit_ids': L, 'reasoning_ids': L,
        'human_reviewer_id': T, 'human_review_complete': B}),
    'tool_outputs': ('output_id', {'case_id': T, 'tool_name': T, 'tool_version': T,
        'model_id': T, 'model_version': T, 'prompt_version': T, 'output_version': T,
        'generated_on': D, 'purpose': E('case-narrative-draft', 'case-evidence-summary'),
        'proposed_facts': proposed_facts, 'exhibit_ids': L,
        'human_review_complete': B, 'human_reviewer_id': T})}


def _claims(row, schema, label, errors):
    for field, predicate in schema.items():
        claim = row.get(field)
        if not isinstance(claim, dict) or set(claim) != {'value', 'source_refs', 'fact_ids'}:
            errors.append(label + '.' + field + ': exact claim object required')
            continue
        if not strings(claim['source_refs']) or not strings(claim['fact_ids']):
            errors.append(label + '.' + field + ': source/fact reference lists required')
        value = claim['value']
        if value is not None and not predicate(value):
            errors.append(label + '.' + field + ': invalid type/enum or exact decimal string required')
        if strings(value) and len(value) != len(set(value)):
            errors.append(label + '.' + field + ': duplicate identities are ambiguous')
        if field == 'proposed_facts' and proposed_facts(value):
            keys = [(v['source_ref'], v['fact_id']) for v in value]
            if len(set(keys)) != len(keys):
                errors.append(label + '.proposed_facts: duplicate fact identities')


def validate(doc):
    errors = validate_common(doc, OBJECT_TYPES)
    if not isinstance(doc, dict) or not isinstance(doc.get('data'), dict):
        return errors, []
    if set(doc) != {'request_id', 'object_id', 'object_type', 'as_of', 'knowledge_cutoff',
            'workflow', 'sources', 'data'}:
        errors.append('undeclared or missing native top-level fields')
    data = doc['data']
    if set(data) != {'mandate'} | set(COLLECTIONS):
        errors.append('data must contain exactly mandate and all declared domain collections')
    mandate = data.get('mandate')
    if not isinstance(mandate, dict) or set(mandate) != set(MANDATE):
        errors.append('mandate must contain exactly declared fields')
    else:
        _claims(mandate, MANDATE, 'mandate', errors)
    for name, (id_key, schema) in COLLECTIONS.items():
        rows = data.get(name)
        if not records(rows) or not unique_ids(rows, id_key):
            errors.append(name + ': unique nonempty native identities required')
            continue
        for row in rows:
            if set(row) != {id_key} | set(schema):
                errors.append(name + ': undeclared or missing record fields')
            _claims(row, schema, name + '/' + row[id_key], errors)
    if errors:
        return errors, []
    for row in data['cases']:
        if row['case_id']['value'] != row['native_case_id']:
            errors.append('case_id must exactly retain the nonempty native_case_id')
        for field in ('institution_id', 'legal_entity_id', 'jurisdiction'):
            value = row[field]['value']
            if value is not None and value != doc['workflow']['context'][field]:
                errors.append(row['native_case_id'] + ': native ' + field + ' changes workflow context')
    for row in [mandate] + data['cases']:
        a, b = row['period_from']['value'], row['period_to']['value']
        if day(a) and day(b) and day(a) > day(b):
            errors.append('native period ends before it starts')
    pairs = [(r['case_id']['value'], r['criterion_id']['value']) for r in data['observations']]
    known_pairs = [p for p in pairs if all(T(v) for v in p)]
    if len(set(known_pairs)) != len(known_pairs):
        errors.append('duplicate case/criterion observation identity')
    return errors, []


def values(doc, row, schema, label, issues):
    resolved = {}
    for field in schema:
        resolved[field], gaps = claim_value(doc, row[field], label + '.' + field)
        issues.extend(gaps)
    return resolved


def _date_supported(doc, row, field, value):
    if day(value) is None:
        return False
    dates = [day(doc['as_of']), day(doc['knowledge_cutoff'])]
    dates += [day(s['received_at']) for s in doc['sources'] if s['source_ref'] in row[field]['source_refs']]
    return bool(dates) and day(value) <= min(dates)


def _exhibits(doc, case_id, refs, exhibits):
    if refs is None:
        return None, ['exhibit linkage is unknown']
    gaps = []
    for ref in refs:
        exhibit = exhibits.get(ref)
        if exhibit is None or exhibit['case_id'] != case_id:
            gaps.append('exhibit missing or belongs to another case: ' + ref)
        elif exhibit['available'] is not True or exhibit['version'] is None:
            gaps.append('exhibit availability/version is not established: ' + ref)
        elif exhibit['evidence_source_ref'] is None or not exhibit['evidence_fact_ids']:
            gaps.append('exhibit source/fact locator is missing: ' + ref)
        else:
            source = source_index(doc).get(exhibit['evidence_source_ref'])
            fact_ids = {f['fact_id'] for f in source['facts']} if source else set()
            if set(exhibit['evidence_fact_ids']) - fact_ids:
                gaps.append('exhibit cites absent source facts: ' + ref)
            gaps += evidence_issues(doc, [exhibit['evidence_source_ref']], 'exhibit ' + ref)
            if exhibit['captured_on'] is None or day(exhibit['captured_on']) > min(day(doc['as_of']), day(doc['knowledge_cutoff']), day(source['received_at']) if source else day(doc['as_of'])):
                gaps.append('exhibit capture is undated or after source receipt/cutoff: ' + ref)
    return not gaps, gaps


def compute(doc):
    require_valid(doc, validate)
    issues = []
    mandate = values(doc, doc['data']['mandate'], MANDATE, 'mandate', issues)
    resolved, raw = {}, {}
    for name, (key, schema) in COLLECTIONS.items():
        resolved[name], raw[name] = {}, {}
        for row in doc['data'][name]:
            raw[name][row[key]] = row
            resolved[name][row[key]] = values(doc, row, schema, name + '/' + row[key], issues)
    cases, exhibits, events, reasoning, criteria, observations, tools = [resolved[n] for n in COLLECTIONS]
    supported = mandate['mandate_type'] in {'operational-qa', 'second-line-monitoring'}
    if not supported:
        issues.append('Case QA method does not perform statutory independent testing, internal audit or model validation; transfer the mandate to its professional owner')
    independence_fields = ('independence_owner_assessment', 'operational_involvement',
        'reporting_line_review', 'conflict_review', 'competence_review', 'reviewer_id', 'mandate_owner')
    independence = None
    if all(mandate[k] is not None for k in independence_fields):
        independence = (mandate['independence_owner_assessment'] is True and
            mandate['operational_involvement'] is False and all(mandate[k] is True
                for k in ('reporting_line_review', 'conflict_review', 'competence_review')))
    profile_ok = all(mandate[k] is not None for k in ('mandate_id', 'legal_profile_id', 'legal_profile_version',
        'authority_scope', 'reviewer_id', 'mandate_owner')) and mandate['legal_profile_reviewed'] is True and mandate['authority_reviewed'] is True
    if not profile_ok:
        issues.append('Reviewed legal profile, institutional authority, owner or reviewer evidence is incomplete; no applicability or authority inferred')
    period_ok = mandate['period_from'] is not None and mandate['period_to'] is not None and day(mandate['period_to']) <= min(day(doc['as_of']), day(doc['knowledge_cutoff']))
    if not period_ok:
        issues.append('Mandated case review period is unknown or exceeds the observable cutoff')
    population, selected, criterion_ids = [mandate[k] for k in ('population_case_ids', 'selected_case_ids', 'criteria_ids')]
    scope_ok = bool(population) and bool(selected) and bool(criterion_ids) and set(selected).issubset(population) and all(k in criteria for k in criterion_ids)
    if not scope_ok:
        issues.append('Exact population, selected cases or criteria are missing/inconsistent; batch coverage and denominator withheld')
    if selected is not None and set(cases) - set(selected):
        scope_ok = False
        issues.append('Supplied case workpapers include cases outside the exact selected sample')
    # Every record belongs to one known native case; unsupported mappings are retained as gaps.
    for name in ('exhibits', 'events', 'reasoning', 'observations', 'tool_outputs'):
        for rid, row in resolved[name].items():
            if row['case_id'] not in cases:
                scope_ok = False
                issues.append(name + '/' + rid + ': unknown or unmatched native case ID')
    if criterion_ids is not None and set(criteria) != set(criterion_ids):
        scope_ok = False
        issues.append('Supplied criterion registry differs from the exact mandate criterion IDs')
    observation_pairs = {(o['case_id'], o['criterion_id']): (rid, o) for rid, o in observations.items() if o['case_id'] is not None and o['criterion_id'] is not None}
    for rid, o in observations.items():
        if o['criterion_id'] not in criteria or (selected is not None and o['case_id'] not in selected):
            scope_ok = False
            issues.append('observations/' + rid + ': case or criterion outside exact mandate')
    checks = []
    for case_id in selected or []:
        case = cases.get(case_id)
        for criterion_id in criterion_ids or []:
            criterion = criteria.get(criterion_id)
            if criterion and criterion['applicable_case_ids'] is not None and case_id not in criterion['applicable_case_ids']:
                continue
            failures, unknowns = [], []
            kind = criterion['kind'] if criterion else None
            supplied = observation_pairs.get((case_id, criterion_id))
            if not case or not criterion:
                unknowns.append('case workpaper or criterion unavailable')
            if criterion and (criterion['applicable_case_ids'] is None or criterion['version'] is None or criterion['procedure'] is None or criterion['requirement'] is None):
                unknowns.append('criterion procedure, requirement, version or applicability unknown')
            if criterion and (criterion['legal_profile_id'] != mandate['legal_profile_id'] or criterion['legal_profile_version'] != mandate['legal_profile_version']):
                unknowns.append('criterion legal profile differs or is unknown')
            if not profile_ok or not period_ok:
                unknowns.append('reviewed mandate profile/authority/period not established')
            if case:
                if any(case[k] is None for k in ('case_id', 'institution_id', 'legal_entity_id', 'jurisdiction', 'upstream_native_id', 'upstream_native_version', 'period_from', 'period_to')):
                    unknowns.append('case-native lineage, context or period unknown')
                elif not period_ok or not (day(mandate['period_from']) <= day(case['period_from']) <= day(case['period_to']) <= day(mandate['period_to'])):
                    unknowns.append('case-native period differs from the mandate')
            if not supplied:
                unknowns.append('criterion has no performed observation; untested is not pass')
                obs = None
            else:
                oid, obs = supplied
                if obs['criterion_version'] is None or not criterion or obs['criterion_version'] != criterion['version']:
                    unknowns.append('observation uses unknown or different criterion version')
                if not _date_supported(doc, raw['observations'][oid], 'tested_on', obs['tested_on']) or not period_ok or (obs['tested_on'] and not day(mandate['period_from']) <= day(obs['tested_on']) <= day(mandate['period_to'])):
                    unknowns.append('observation test date outside period/receipt/cutoff or unknown')
                if obs['human_review_complete'] is not True or obs['human_reviewer_id'] != mandate['reviewer_id'] or obs['rationale'] is None:
                    unknowns.append('case-specific human reviewer assessment/rationale incomplete')
                link_ok, link_gaps = _exhibits(doc, case_id, obs['exhibit_ids'], exhibits)
                if not link_ok or not obs['exhibit_ids']:
                    for gap in link_gaps or ['observation needs specific evidence exhibits']:
                        ref = gap.rsplit(': ', 1)[-1]
                        known_required_absence = (kind == 'evidence-completeness' and case and
                            case['required_exhibit_ids'] is not None and ref in case['required_exhibit_ids'] and
                            gap.startswith('exhibit availability') and
                            exhibits.get(ref, {}).get('case_id') == case_id and
                            exhibits.get(ref, {}).get('available') is False)
                        if known_required_absence:
                            failures.append('source-bound required exhibit is unavailable: ' + ref)
                        else:
                            unknowns.append(gap)
                if obs['reasoning_ids'] is None or any(r not in reasoning or reasoning[r]['case_id'] != case_id for r in obs['reasoning_ids'] or []):
                    unknowns.append('observation reasoning linkage unknown or belongs to another case')
            if case and criterion:
                case_reasoning = {k: v for k, v in reasoning.items() if v['case_id'] == case_id}
                if kind == 'evidence-completeness':
                    refs = case['required_exhibit_ids']
                    if refs is None or not refs:
                        unknowns.append('required case exhibit inventory not established')
                    else:
                        _, gaps = _exhibits(doc, case_id, refs, exhibits)
                        for gap in gaps:
                            # Absence from a complete inventory is an exception; unknown
                            # availability/provenance is an untested dependency, not failure.
                            if gap.startswith('exhibit missing or belongs'):
                                failures.append(gap)
                            elif gap.startswith('exhibit availability') and exhibits.get(
                                    gap.rsplit(': ', 1)[-1], {}).get('available') is False:
                                failures.append(gap)
                            else:
                                unknowns.append(gap)
                        available_refs = {ref for ref in refs if ref in exhibits and exhibits[ref]['available'] is True}
                        if obs and obs['exhibit_ids'] is not None and available_refs - set(obs['exhibit_ids']):
                            unknowns.append('required exhibits were not all linked to the performed observation')
                elif kind == 'chronology-consistency':
                    case_events = {k: v for k, v in events.items() if v['case_id'] == case_id}
                    if not case_events:
                        unknowns.append('no case chronology supplied')
                    for eid, ev in case_events.items():
                        if not _date_supported(doc, raw['events'][eid], 'occurred_on', ev['occurred_on']) or not ev['exhibit_ids'] or ev['statement'] is None or ev['predecessor_event_ids'] is None:
                            unknowns.append(eid + ': event date, statement, exhibits or predecessors unknown/unobservable')
                        else:
                            _, gaps = _exhibits(doc, case_id, ev['exhibit_ids'], exhibits)
                            unknowns += gaps
                            if obs and obs['exhibit_ids'] is not None and set(ev['exhibit_ids']) - set(obs['exhibit_ids']):
                                unknowns.append(eid + ': event exhibits omitted from chronology observation')
                            if case['period_from'] is None or case['period_to'] is None:
                                unknowns.append(eid + ': case period unknown')
                            elif not day(case['period_from']) <= day(ev['occurred_on']) <= day(case['period_to']):
                                failures.append(eid + ': event outside exact case period')
                            for pred in ev['predecessor_event_ids']:
                                prior = case_events.get(pred)
                                if prior is None or prior['occurred_on'] is None:
                                    unknowns.append(eid + ': predecessor missing or undated: ' + pred)
                                elif pred == eid or day(prior['occurred_on']) > day(ev['occurred_on']):
                                    failures.append(eid + ': predecessor contradicts event chronology: ' + pred)
                    remaining = set(case_events)
                    while remaining:
                        ready = {eid for eid in remaining if not (set(case_events[eid]['predecessor_event_ids'] or []) & remaining)}
                        if not ready:
                            break
                        remaining -= ready
                    if remaining:
                        failures.append('case event predecessor graph contains a cycle')
                elif kind in {'reasoning-traceability', 'disposition-traceability'}:
                    rid = case['disposition_reasoning_id']
                    r = case_reasoning.get(rid)
                    if not r or not obs or obs['reasoning_ids'] is None or rid not in obs['reasoning_ids']:
                        unknowns.append('specific disposition reasoning is absent from the observation')
                    else:
                        if r['human_review_complete'] is not True or r['reviewer_id'] != mandate['reviewer_id'] or r['rationale'] is None:
                            unknowns.append('specific reasoning has no complete human assessment')
                        for expected, reviewed in (('concern_ids', 'concern_ids'), ('counterevidence_ids', 'considered_counterevidence_ids'), ('contradiction_ids', 'addressed_contradiction_ids')):
                            if case[expected] is None or r[reviewed] is None:
                                unknowns.append(expected + ': material inventory or assessment unknown')
                            elif set(case[expected]) != set(r[reviewed]):
                                failures.append(expected + ': reasoning omits or invents scoped material IDs')
                        _, gaps = _exhibits(doc, case_id, r['exhibit_ids'], exhibits)
                        unknowns += gaps
                        if r['exhibit_ids'] is not None and obs['exhibit_ids'] is not None and set(r['exhibit_ids']) - set(obs['exhibit_ids']):
                            unknowns.append('reasoning exhibits omitted from the specific human observation')
                        if not r['exhibit_ids']:
                            unknowns.append('reasoning has no specific evidence exhibits')
                        _, gaps = _exhibits(doc, case_id, case['counterevidence_ids'], exhibits)
                        unknowns += gaps
                        if r['human_judgement'] == 'fail':
                            failures.append('supplied qualified reviewer identified a reasoning quality exception')
                        elif r['human_judgement'] != 'pass':
                            unknowns.append('substantive human reasoning judgment is unknown')
                        if kind == 'disposition-traceability':
                            if case['proposed_disposition'] is None or r['proposed_disposition'] is None:
                                unknowns.append('proposed disposition or supporting rationale is unknown')
                            elif case['proposed_disposition'] != r['proposed_disposition']:
                                failures.append('proposed disposition differs from the linked reasoning')
                            if not _date_supported(doc, raw['cases'][case_id], 'disposition_on', case['disposition_on']):
                                unknowns.append('proposed disposition date is unknown/unobservable')
                            elif case['period_from'] is None or case['period_to'] is None:
                                unknowns.append('proposed disposition case period unknown')
                            elif not day(case['period_from']) <= day(case['disposition_on']) <= day(case['period_to']):
                                failures.append('proposed disposition date is outside the exact case period')
                            elif any(ev['occurred_on'] is not None and day(ev['occurred_on']) > day(case['disposition_on']) for ev in events.values() if ev['case_id'] == case_id):
                                failures.append('proposed disposition precedes supplied case evidence chronology')
                elif kind == 'tool-source-faithfulness':
                    outputs = {k: v for k, v in tools.items() if v['case_id'] == case_id}
                    if not outputs:
                        unknowns.append('tool output criterion selected without a versioned output')
                    for tid, output in outputs.items():
                        if any(output[k] is None for k in ('tool_name', 'tool_version', 'model_id', 'model_version', 'prompt_version', 'output_version', 'purpose')) or not _date_supported(doc, raw['tool_outputs'][tid], 'generated_on', output['generated_on']):
                            unknowns.append(tid + ': tool/model/output identity, purpose or date unknown')
                        if output['human_review_complete'] is not True or output['human_reviewer_id'] != mandate['reviewer_id']:
                            unknowns.append(tid + ': human source-faithfulness review incomplete')
                        if not output['proposed_facts']:
                            unknowns.append(tid + ': proposed factual content mapping absent')
                        for proposed in output['proposed_facts'] or []:
                            source = source_index(doc).get(proposed['source_ref'])
                            fact = next((f for f in source['facts'] if f['fact_id'] == proposed['fact_id']), None) if source else None
                            unknowns += evidence_issues(doc, [proposed['source_ref']], tid)
                            if fact is None:
                                unknowns.append(tid + ': proposed fact locator absent')
                            elif canonical_hash(proposed['value']) != canonical_hash(fact['value']):
                                failures.append(tid + ': proposed tool factual value conflicts with the exact supplied source fact')
                        _, gaps = _exhibits(doc, case_id, output['exhibit_ids'], exhibits)
                        unknowns += gaps
                        if obs and output['exhibit_ids'] is not None and obs['exhibit_ids'] is not None and set(output['exhibit_ids']) - set(obs['exhibit_ids']):
                            unknowns.append(tid + ': tool exhibits omitted from source-faithfulness observation')
                        if not output['exhibit_ids']:
                            unknowns.append(tid + ': output lacks case exhibit linkage')
                else:
                    unknowns.append('criterion kind unknown; no substitute generic keyword score')
            if obs and obs['observed_outcome'] == 'unknown':
                unknowns.append('supplied observation remains unknown')
            if obs and obs['observed_outcome'] is None:
                unknowns.append('observation outcome has no exact supported source fact')
            # Mechanical conflicts cannot be overridden by a supplied favorable outcome.
            state = 'unknown' if unknowns else ('fail' if failures or (obs and obs['observed_outcome'] == 'fail') else 'pass')
            if state == 'fail' and not failures:
                failures.append('source-bound human observation records a case-specific exception')
            checks.append({'case_id': case_id, 'criterion_id': criterion_id, 'criterion_kind': kind,
                'observation_id': supplied[0] if supplied else None,
                'source_bound_observation': obs, 'eligible_observed_result': state,
                'mechanical_exceptions': list(dict.fromkeys(failures)),
                'unknowns': list(dict.fromkeys(unknowns)),
                'substantive_reasoning_assurance': 'human-judgment-supplied-unverified'})
            issues.extend(case_id + '/' + criterion_id + ': ' + g for g in failures + unknowns)
    criterion_counts = {s: sum(c['eligible_observed_result'] == s for c in checks) for s in ('pass', 'fail', 'unknown')}
    complete_cases, exception_cases, case_states = [], [], []
    for case_id in selected or []:
        group = [c for c in checks if c['case_id'] == case_id]
        complete = bool(group) and all(c['eligible_observed_result'] != 'unknown' for c in group)
        if not group:
            issues.append(case_id + ': no applicable criterion observation; case remains untested')
        failed = any(c['eligible_observed_result'] == 'fail' or c['mechanical_exceptions'] for c in group)
        if complete:
            complete_cases.append(case_id)
            if failed:
                exception_cases.append(case_id)
        case_states.append({'case_id': case_id, 'all_applicable_criteria_observed': complete,
            'known_quality_exception': failed, 'outcome': ('fail' if failed else 'pass') if complete else 'unknown'})
    denominator_ok = scope_ok and period_ok and profile_ok and mandate['sampling_method'] is not None and mandate['sampling_rationale'] is not None
    numerator = len(exception_cases) if denominator_ok and complete_cases else None
    denominator = len(complete_cases) if numerator is not None else None
    proportion = None
    if denominator:
        with localcontext() as ctx:
            ctx.prec = 28
            proportion = format(Decimal(numerator) / Decimal(denominator), 'f')
    comparison = None
    if supported and denominator_ok and selected and len(complete_cases) == len(selected) and mandate['maximum_exception_proportion'] is not None:
        # Integer cross-multiplication avoids comparing a rounded recurring decimal.
        threshold_n, threshold_d = Decimal(mandate['maximum_exception_proportion']).as_integer_ratio()
        comparison = numerator * threshold_d <= threshold_n * denominator
        if comparison is False:
            issues.append('Observed complete-case exception proportion exceeds the supplied exact threshold')
    if comparison is None:
        issues.append('Supplied threshold comparison withheld pending complete scoped sample, mandate, human review and exact decimal evidence')
    if not denominator_ok:
        issues.append('Observed-case denominator and proportions withheld because scope or sampling rationale is inconsistent/unknown')
    coverage = {'population_case_count': len(population) if scope_ok else None,
        'selected_case_count': len(selected) if scope_ok else None,
        'complete_observed_case_count': len(complete_cases) if denominator_ok else None,
        'unobserved_or_partial_selected_case_ids': [c for c in selected or [] if c not in complete_cases],
        'unit': 'unique native cases with all applicable criteria observed'}
    return result(doc, SKILL, METHOD, {'mandate': mandate,
        'mandate_method_supported': supported, 'supplied_independence_evidence_consistent': independence,
        'legal_profile_authority_evidence_consistent': profile_ok,
        'population_sample_criteria_scope_consistent': bool(scope_ok), 'case_criterion_checks': checks,
        'observed_criterion_counts': criterion_counts, 'case_outcomes': case_states, 'coverage': coverage,
        'observed_case_exception_proportion': {'numerator': numerator, 'denominator': denominator,
            'decimal_display': proportion, 'exact_ratio': f'{numerator}/{denominator}' if denominator else None,
            'population_inference': 'not-performed'},
        'within_supplied_exception_threshold': comparison,
        'case_closure': 'not-performed', 'reportability': 'not-assessed', 'guilt': 'not-assessed',
        'sar_filing': 'not-performed', 'assurance_opinion': 'not-issued',
        'legal_privilege': 'not-determined', 'automated_decision': 'not-performed',
        'reputation_assessment': 'not-performed', 'narrative_status': 'proposed-supplied-unverified'}, issues,
        ['Counts and exact ratios describe only supplied complete observed sample cases; no prevalence estimate or confidence interval.',
         'Criterion checks test explicit evidence linkage and source consistency, not semantic truth, legal sufficiency or human reasoning quality.',
         'No statutory independent testing, audit opinion, model validation, closure, reportability, guilt or filing authority is implemented.',
         'All proposed dispositions, tool identities, source facts and human judgments remain supplied and unverified.'],
        ['financial-crime-case-investigator', 'compliance-control-testing-assistant',
         'compliance-remediation-evidence-reviewer', 'model-validation-assistant', 'audit-evidence-packager'])
