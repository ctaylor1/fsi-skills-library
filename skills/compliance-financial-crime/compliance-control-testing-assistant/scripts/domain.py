"""Domain-owned, offline supplied-evidence method; no professional/action authority."""
from __future__ import annotations
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, number, day, records, strings, unique_ids)

SKILL = "compliance-control-testing-assistant"
OBJECT_TYPES = {'compliance_control_test'}
METHOD = "mandate-population-observation-testing/1.0"
T = text
B = lambda v: isinstance(v, bool)
N = number
I = lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0
D = lambda v: day(v) is not None
L = strings
OBJECT_SCHEMAS = {'test': {'mandate_type': lambda v: v in {'operational-qa','second-line-monitoring','independent-testing','model-validation','internal-audit'},
    'mandate_owner': T, 'independent_assessment': B, 'operational_involvement': B, 'conflict_review': B,
    'reporting_line_review': B, 'tester_competence_review': B, 'population_ids': L, 'sample_ids': L,
    'sampling_method': T, 'maximum_failures': I, 'procedure': T,
    'control_id': T, 'control_objective': T, 'window_from': D, 'window_to': D}}
RECORD_SCHEMAS = {'observations': ('observation_id', {'item_id': T, 'outcome': lambda v: v in {'pass','fail','unknown'},
    'performed_on': D, 'procedure': T, 'evidence_complete': B, 'control_id': T})}


def validate(doc):
    errors = validate_common(doc, OBJECT_TYPES)
    if not isinstance(doc, dict) or not isinstance(doc.get('data'), dict):
        return errors, []
    if set(doc) - {'request_id','object_id','object_type','as_of','knowledge_cutoff','workflow','sources','data'}:
        errors.append('undeclared native top-level fields')
    data = doc['data']
    if set(data) != set(OBJECT_SCHEMAS) | set(RECORD_SCHEMAS):
        errors.append('data must contain exactly the declared domain collections/objects')
    for collection, (id_key, schema) in RECORD_SCHEMAS.items():
        rows = data.get(collection)
        if not records(rows) or not unique_ids(rows, id_key):
            errors.append(collection + ': distinct nonempty record IDs required')
            continue
        for row in rows:
            if set(row) != {id_key} | set(schema):
                errors.append(collection + ': undeclared or missing record fields')
            for field, predicate in schema.items():
                claim = row.get(field)
                if not isinstance(claim, dict) or set(claim) != {'value','source_refs','fact_ids'}:
                    errors.append(collection + '.' + field + ': exact claim object required')
                    continue
                if not strings(claim['source_refs']) or not strings(claim['fact_ids']):
                    errors.append(collection + '.' + field + ': reference lists must contain strings')
                if claim['value'] is not None and not predicate(claim['value']):
                    errors.append(collection + '.' + field + ': unsupported value type or enum')
    for name, schema in OBJECT_SCHEMAS.items():
        row = data.get(name)
        if not isinstance(row, dict):
            errors.append(name + ': domain object required')
            continue
        if set(row) != set(schema):
            errors.append(name + ': undeclared or missing fields')
        for field, predicate in schema.items():
            claim = row.get(field)
            if not isinstance(claim, dict) or set(claim) != {'value','source_refs','fact_ids'}:
                errors.append(name + '.' + field + ': exact claim object required')
                continue
            if not strings(claim['source_refs']) or not strings(claim['fact_ids']):
                errors.append(name + '.' + field + ': reference lists must contain strings')
            if claim['value'] is not None and not predicate(claim['value']):
                errors.append(name + '.' + field + ': unsupported value type or enum')
    if errors:
        return errors, []
    row = data.get('test', {})
    if isinstance(row, dict):
        start, end = row.get('window_from'), row.get('window_to')
        a = start.get('value') if isinstance(start, dict) else None
        b = end.get('value') if isinstance(end, dict) else None
        if day(a) and day(b) and day(a) > day(b):
            errors.append('test period ends before start')
        for field in ['population_ids','sample_ids']:
            claim = row.get(field)
            value = claim.get('value') if isinstance(claim, dict) else None
            if strings(value) and len(value) != len(set(value)):
                errors.append(field + ' must contain distinct item identities')
    return errors, []

def values(doc, row, fields, label, issues):
    resolved = {}
    for field in fields:
        resolved[field], gaps = claim_value(doc, row[field], label + '.' + field)
        issues.extend(gaps)
    return resolved

def compute(doc):
    require_valid(doc, validate)
    issues = []
    t = values(doc, doc['data']['test'], OBJECT_SCHEMAS['test'], 'test', issues)
    supported_mandate = t['mandate_type'] in {'operational-qa','second-line-monitoring','independent-testing'}
    if not supported_mandate:
        issues.append('Mandate belongs to model validation or internal audit, or is unknown; separate owner method required')
    control_scope_ok = all(t[k] is not None for k in ['control_id','control_objective','window_from','window_to'])
    if t['window_to'] is not None and day(t['window_to']) > min(day(doc['as_of']),day(doc['knowledge_cutoff'])):
        control_scope_ok = False
    if not control_scope_ok:
        issues.append('Control objective or observable testing period missing/incomplete')
    independent = None
    independence_fields = ['independent_assessment','operational_involvement','conflict_review','reporting_line_review','tester_competence_review','mandate_owner']
    if all(t[k] is not None for k in independence_fields):
        independent = t['independent_assessment'] is True and t['operational_involvement'] is False and t['conflict_review'] is True and t['reporting_line_review'] is True and t['tester_competence_review'] is True
    if t['mandate_type'] == 'independent-testing' and independent is not True:
        issues.append('Independence evidence missing or inconsistent; role label cannot establish independence')
    pop, selected = t['population_ids'], t['sample_ids']
    population_scope_ok = pop is not None and selected is not None and bool(pop) and bool(selected) and set(selected).issubset(pop)
    if not population_scope_ok:
        issues.append('Exact population/sample missing, empty or sample includes items outside population')
    observations, seen, counts = [], set(), {'pass':0,'fail':0,'unknown':0}
    observed_item_ids = []
    for row in doc['data']['observations']:
        v = values(doc, row, RECORD_SCHEMAS['observations'][1], row['observation_id'], issues)
        reasons = []
        if v['item_id'] is not None and v['item_id'] in seen:
            reasons.append('duplicate tested item identity; no double-counting')
        if v['item_id'] is not None:
            seen.add(v['item_id'])
        if not population_scope_ok or v['item_id'] not in (selected or []):
            reasons.append('observation outside exact selected population/sample')
        if v['procedure'] is None or t['procedure'] is None or v['procedure'] != t['procedure']:
            reasons.append('observation procedure differs or is unknown')
        if not control_scope_ok or v['control_id'] is None or v['control_id'] != t['control_id']:
            reasons.append('observed control differs or objective/period is unknown')
        if v['evidence_complete'] is not True:
            reasons.append('observation workpaper evidence is incomplete or unknown')
        if v['performed_on'] is not None:
            receipts = [day(s['received_at']) for s in doc['sources'] if s['source_ref'] in row['performed_on']['source_refs']]
            if day(v['performed_on']) > min([day(doc['as_of']),day(doc['knowledge_cutoff'])] + receipts):
                reasons.append('observed test date is future relative to assessment/cutoff/receipt')
            if control_scope_ok and not (day(t['window_from']) <= day(v['performed_on']) <= day(t['window_to'])):
                reasons.append('observed test date falls outside the exact mandated test period')
        else:
            reasons.append('test performance date unknown')
        state = v['outcome'] if not reasons and v['outcome'] in {'pass','fail'} else 'unknown'
        counts[state] += 1
        if state != 'unknown':
            observed_item_ids.append(v['item_id'])
        issues.extend(row['observation_id'] + ': ' + reason for reason in reasons)
        if state == 'unknown':
            issues.append(row['observation_id'] + ': test result remains unassessed')
        observations.append({'observation_id':row['observation_id'], 'evidence':v, 'eligible_observed_result':state,
            'finding': 'Observed procedure failed; control owner investigates the exact exception and cause' if state == 'fail' else None,
            'issues':reasons})
    unobserved = None if selected is None else sorted(set(selected) - set(observed_item_ids))
    if unobserved:
        issues.append('Selected items lack supported completed observations: ' + ', '.join(unobserved))
    observed_n = counts['pass'] + counts['fail']
    rate = counts['fail'] / observed_n if observed_n else None
    acceptance = None
    if supported_mandate and control_scope_ok and population_scope_ok and t['maximum_failures'] is not None and t['sampling_method'] is not None and not unobserved and not counts['unknown'] and (t['mandate_type'] != 'independent-testing' or independent is True):
        acceptance = counts['fail'] <= t['maximum_failures']
    if acceptance is False:
        issues.append('Observed failures exceed the supplied acceptance criterion')
    if acceptance is None:
        issues.append('Acceptance comparison withheld pending mandate, criteria and complete sample evidence')
    return result(doc, SKILL, METHOD, {'mandate':t, 'mandate_method_supported':supported_mandate,
        'supplied_independence_evidence_consistent':independent, 'population_sample_scope_consistent':population_scope_ok,
        'control_objective_period_evidence_consistent':control_scope_ok,
        'observations':observations, 'observed_results':counts, 'unobserved_selected_items':unobserved,
        'observed_exception_rate':rate, 'within_supplied_acceptance_criterion':acceptance,
        'statistical_population_inference':'not-performed', 'assurance_opinion':'not-issued',
        'required_review':['Mandate owner accepts scope, sampling and criteria', 'Qualified reviewer assesses independence and all findings/workpapers']}, issues,
        ['Observed exception rate is not a population estimate or independent assurance opinion.',
         'Operational QA, second-line monitoring, independent testing, model validation and audit mandates are distinct.'],
        ['model-validation-assistant','audit-evidence-packager','compliance-remediation-evidence-reviewer'])
