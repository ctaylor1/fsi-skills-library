"""Evaluate evidence for a merchant's supplied acceptance design options."""
from copy import deepcopy

SKILL = 'merchant-acceptance-strategy-designer'
RESPONSIBILITIES = ('checkout', 'authentication', 'screening', 'settlement', 'reconciliation', 'refunds', 'disputes')
STATUSES = {'supported', 'unsupported', 'unknown'}
KINDS = {'inspected', 'proposal', 'assumption', 'unknown'}


def validate(data):
    errors = []
    if not isinstance(data, dict):
        return ['data must be an object']
    for key in ('segments', 'options'):
        if not isinstance(data.get(key), list) or not data[key]:
            errors.append(key + ' must be a nonempty list')
    if errors:
        return errors
    segment_ids = set()
    for row in data['segments']:
        if not isinstance(row, dict):
            errors.append('segment must be an object')
            continue
        for key in ('segment_id', 'market', 'channel', 'customer_type', 'use_case', 'currency'):
            if not isinstance(row.get(key), str) or not row[key]:
                errors.append('segment requires ' + key)
        sid = row.get('segment_id')
        if sid in segment_ids:
            errors.append('duplicate segment_id')
        segment_ids.add(sid)
        if not isinstance(row.get('required_methods'), list) or not row['required_methods'] or not all(isinstance(x, str) and x for x in row['required_methods']):
            errors.append('required_methods must contain explicit method names')
        elif len(set(row['required_methods'])) != len(row['required_methods']):
            errors.append('duplicate required method')
    option_ids = set()
    for option in data['options']:
        if not isinstance(option, dict):
            errors.append('option must be an object')
            continue
        if not isinstance(option.get('option_id'), str) or not option['option_id'] or option['option_id'] in option_ids:
            errors.append('option_id must be unique and nonempty')
        option_ids.add(option.get('option_id'))
        if not isinstance(option.get('coverage', []), list) or not isinstance(option.get('constraints', []), list) or not isinstance(option.get('responsibilities', {}), dict):
            errors.append('coverage/constraints must be lists and responsibilities an object')
            continue
        keys = set()
        for row in option.get('coverage', []):
            if not isinstance(row, dict):
                errors.append('coverage row must be an object')
                continue
            key = (row.get('segment_id'), row.get('method'))
            if key in keys:
                errors.append('duplicate coverage segment/method')
            keys.add(key)
            if row.get('segment_id') not in segment_ids or not isinstance(row.get('method'), str):
                errors.append('coverage must reference a segment and method')
            if row.get('status') not in STATUSES or row.get('evidence_kind', 'unknown') not in KINDS:
                errors.append('invalid coverage status/evidence_kind')
            for field in ('presentment_currencies', 'settlement_currencies'):
                if field in row and (not isinstance(row[field], list) or not all(isinstance(x, str) for x in row[field])):
                    errors.append(field + ' must be a list of currency codes')
            for field in ('entity_eligible', 'recurring_supported'):
                if field in row and row[field] is not None and not isinstance(row[field], bool):
                    errors.append(field + ' must be boolean or null')
        for row in option.get('constraints', []):
            if not isinstance(row, dict) or not isinstance(row.get('mandatory'), bool) or row.get('status') not in STATUSES or row.get('evidence_kind', 'unknown') not in KINDS:
                errors.append('constraint requires mandatory boolean and valid status/evidence_kind')
    if 'orchestration' in data and not isinstance(data['orchestration'], dict):
        errors.append('orchestration must be an object')
    return errors


def analyze(request):
    data = request['data']
    current_sources = {s['source_id'] for s in request['sources'] if not s.get('review_due') or s['review_due'] >= request['as_of']}
    findings = []
    def gap(code, message, refs=None):
        findings.append({'code': code, 'message': message, 'source_ids': refs or [], 'severity': 'gap'})
    options = []
    for option in data['options']:
        gates = []
        matrix = []
        oid = option['option_id']
        for role in ('merchant_entity', 'gateway', 'acquirer', 'psp'):
            if not option.get(role):
                gates.append('Identify ' + role + ' or explain a documented non-applicability.')
        if not option.get('operating_model'):
            gates.append('Specify the contracting and funds-flow operating model.')
        for job in RESPONSIBILITIES:
            if not option.get('responsibilities', {}).get(job):
                gates.append('Assign an accountable party for ' + job + '.')
        coverage = {(x['segment_id'], x['method']): x for x in option.get('coverage', [])}
        for segment in data['segments']:
            for method in segment['required_methods']:
                row = coverage.get((segment['segment_id'], method), {})
                reasons = []
                state = row.get('status', 'unknown')
                if state != 'supported':
                    reasons.append('Method support is ' + state + '.')
                if row.get('evidence_kind') != 'inspected' or not row.get('source_ids') or not set(row.get('source_ids', [])).issubset(current_sources):
                    reasons.append('Obtain inspected scope-specific evidence; proposal or assumption is insufficient.')
                if segment['currency'] not in row.get('presentment_currencies', []):
                    reasons.append('Presentment currency support is not evidenced.')
                if not row.get('settlement_currencies'):
                    reasons.append('Settlement currency and any conversion responsibility are unresolved.')
                if row.get('entity_eligible') is not True:
                    reasons.append('Merchant entity eligibility is unresolved or unsupported.')
                if segment['use_case'] in ('recurring', 'subscription') and row.get('recurring_supported') is not True:
                    reasons.append('Recurring mandate/credential and consent support is unresolved or unsupported.')
                if segment['market'] not in ('US', 'EA', 'UK'):
                    reasons.append('Market outside the initial regional scope needs a country-specific review.')
                matrix.append({'segment': deepcopy(segment), 'method': method, 'status': state,
                               'evidence_kind': row.get('evidence_kind', 'unknown'),
                               'source_ids': row.get('source_ids', []), 'evidence_gates': reasons,
                               'ready_for_option_review': not reasons})
                gates.extend(segment['segment_id'] + '/' + method + ': ' + reason for reason in reasons)
        for constraint in option.get('constraints', []):
            if constraint['mandatory'] and (constraint['status'] != 'supported' or constraint.get('evidence_kind') != 'inspected' or not constraint.get('source_ids') or not set(constraint.get('source_ids', [])).issubset(current_sources)):
                gates.append('Resolve mandatory constraint: ' + constraint.get('description', constraint.get('constraint_id', 'unnamed')))
        if not option.get('constraints'):
            gates.append('Document legal, contractual, data, currency, settlement and operating constraints; absence is not clearance.')
        for gate in gates:
            gap('acceptance-option-gate', oid + ': ' + gate)
        options.append({'option_id': oid, 'operating_model': option.get('operating_model'),
                        'parties': {role: option.get(role) for role in ('merchant_entity', 'gateway', 'acquirer', 'psp')},
                        'responsibilities': deepcopy(option.get('responsibilities', {})), 'coverage_matrix': matrix,
                        'constraints': deepcopy(option.get('constraints', [])), 'gating_questions': gates,
                        'review_state': 'evidence-gated' if gates else 'ready-for-human-option-review',
                        'estimated_reach': None, 'conversion_uplift': None})
    orchestration = deepcopy(data.get('orchestration', {}))
    if orchestration:
        for field in ('objective', 'success_metric', 'guardrails', 'fallback_policy', 'experiment'):
            if not orchestration.get(field):
                gap('orchestration-design-gap', 'Supply orchestration ' + field + '; routing changes need measured outcomes and explicit duplicate-payment prevention.')
    return {'result': {'segments': deepcopy(data['segments']), 'options': options, 'orchestration': orchestration,
                       'selected_option': None,
                       'implementation_sequence': [
                           {'stage': 1, 'work': 'Resolve market/entity/method and mandatory constraint evidence for candidate options.', 'exit': 'All chosen option gates resolved by accountable owners.'},
                           {'stage': 2, 'work': 'Diligence provider scope, contracting responsibilities, funds flows, pricing and service levels.', 'exit': 'Documented provider and regulatory review; model comparable economics.'},
                           {'stage': 3, 'work': 'Design integration, reconciliation, refunds, servicing and operational fallback with explicit owners.', 'exit': 'Inspectable acceptance criteria and test evidence.'},
                           {'stage': 4, 'work': 'Run a bounded pilot with agreed success denominator and loss/cost/customer guardrails.', 'exit': 'Human launch decision based on pilot outcomes; no assumed conversion uplift.'}]},
            'findings': findings,
            'handoffs': [{'target_skill': 'payment-provider-evaluator', 'reason': 'Diligence candidate operating requirements and evidence.', 'required_inputs': ['options', 'coverage_matrix', 'gating_questions']},
                         {'target_skill': 'payment-economics-modeler', 'reason': 'Model participant-specific acceptance scenarios with adoption and displacement.', 'required_inputs': ['segments', 'options']},
                         {'target_skill': 'payment-integration-readiness-reviewer', 'reason': 'Review inspected/tested launch evidence after design.', 'required_inputs': ['responsibilities', 'implementation_sequence']}]}
