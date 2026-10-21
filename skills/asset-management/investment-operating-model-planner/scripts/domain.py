"""Source-linked AM service ownership and transition-control review (MIT)."""
from foundation_contract import D, exact, finish, require_sources, text, validate_actual_date, validate_common
from modernization_contract import shared_review
from shared_operations import evaluate as operations_evaluate, validate as operations_validate
from design_support import ordered

SKILL = 'investment-operating-model-planner'


def rows(doc, key, identity):
    values = doc.get(key)
    if not isinstance(values, list) or not values or len(values) > 10000 or any(not isinstance(r, dict) for r in values):
        raise ValueError(key + ' requires 1..10000 records')
    ids = [r.get(identity) for r in values]
    if any(not text(v) for v in ids) or len(set(ids)) != len(ids):
        raise ValueError(key + ' identities must be unique nonempty strings')
    for row in values:
        require_sources(doc, [row.get('source_ref')])
    return values


@exact
def compute(doc):
    errors = validate_common(doc)
    if errors:
        raise ValueError('; '.join(errors))
    baseline = shared_review(doc, 'operations', 'operations-performance-analyzer', operations_evaluate, operations_validate)
    issues = list(baseline['unresolved_issues'])
    services = rows(doc, 'services', 'service_id')
    controls = rows(doc, 'controls', 'control_id')
    transitions = rows(doc, 'transitions', 'transition_id')
    expected = doc.get('service_inventory')
    if not isinstance(expected, list) or any(not text(v) for v in expected) or len(set(expected)) != len(expected):
        raise ValueError('service_inventory requires unique explicit IDs')
    require_sources(doc, [doc.get('inventory_source_ref')])
    ids = {s['service_id'] for s in services}
    if set(expected) != ids:
        issues.append('Declared service inventory differs from supplied service records')
    if doc.get('inventory_complete') is not True:
        issues.append('Service inventory completeness is not established')
    by = {s['service_id']: s for s in services}
    edges, service_results, control_results = [], [], []
    covered = set()
    for service in services:
        sid = service['service_id']
        gaps = []
        for field in ('function', 'current_owner', 'target_owner', 'accountable_owner', 'backup_owner',
                      'system_of_record', 'population', 'definition_version', 'provider', 'retained_oversight_owner',
                      'escalation_route', 'business_calendar', 'time_zone'):
            if not text(service.get(field)):
                gaps.append(field + ' missing')
        if service.get('delivery_model') not in {'internal', 'outsourced', 'co-sourced'}:
            gaps.append('Unsupported delivery model')
        if service.get('criticality') not in {'critical', 'material', 'standard'}:
            gaps.append('Criticality assessment missing')
        dependencies = service.get('depends_on')
        if not isinstance(dependencies, list) or any(not text(d) for d in dependencies) or len(set(dependencies)) != len(dependencies):
            raise ValueError('depends_on must contain unique service IDs')
        edges.extend((d, sid) for d in dependencies)
        if service.get('delivery_model') in {'outsourced', 'co-sourced'}:
            for field in ('audit_rights_ref', 'exit_plan_ref', 'subcontractor_register_ref'):
                if text(service.get(field)):
                    require_sources(doc, [service[field]])
                else:
                    gaps.append(field + ' missing')
        # Baseline comparisons are meaningful only for the observed population.
        native = baseline['source_document']['data']
        matched = (service.get('population') == native.get('population') and service.get('definition_version') == native.get('definition_version'))
        if not matched:
            gaps.append('No comparable observed operating baseline for this service population/version')
        issues.extend(sid + ': ' + g for g in gaps)
        service_results.append({'service_id': sid, 'accountable_owner': service.get('accountable_owner'),
                                'target_owner': service.get('target_owner'), 'gaps': gaps,
                                'baseline_comparable': matched, 'source_ref': service['source_ref']})
    for control in controls:
        sid = control.get('service_id')
        if sid not in by:
            raise ValueError('control refers to unknown service')
        covered.add(sid)
        gaps = []
        for key in ('maker', 'checker', 'frequency', 'evidence_locator', 'failure_route', 'control_version'):
            if not text(control.get(key)):
                gaps.append(key + ' unresolved')
        if control.get('maker') == control.get('checker'):
            gaps.append('Maker/checker separation is not established')
        state = control.get('test_result')
        if state not in {'pass', 'fail', 'not-tested'}:
            raise ValueError('control test_result must be pass/fail/not-tested')
        if state in {'pass', 'fail'}:
            validate_actual_date(doc, control.get('tested_on'), control['source_ref'])
        if state != 'pass':
            gaps.append('Control effectiveness observation is not a pass')
        if control.get('tested_version') != control.get('control_version'):
            gaps.append('Control version differs from tested version')
        issues.extend(control['control_id'] + ': ' + g for g in gaps)
        control_results.append({'control_id': control['control_id'], 'service_id': sid, 'gaps': gaps,
                                'test_result': state, 'source_ref': control['source_ref']})
    for sid in sorted(ids - covered):
        issues.append(sid + ': no control coverage')
    sequence = ordered(ids, edges)
    if sequence is None:
        issues.append('Service dependencies are cyclic or refer to unknown services')
    transition_results = []
    seen = set()
    for transition in transitions:
        sid = transition.get('service_id')
        if sid not in by or sid in seen:
            raise ValueError('transition must bind each service at most once')
        seen.add(sid)
        gaps = []
        for field in ('owner', 'acceptance_owner', 'rollback_owner', 'rollback_runbook', 'training_record_ref', 'access_review_ref'):
            if not text(transition.get(field)):
                gaps.append(field + ' unresolved')
            elif field.endswith('_ref'):
                require_sources(doc, [transition[field]])
        if transition.get('acceptance_owner') != by[sid].get('accountable_owner'):
            gaps.append('Acceptance owner differs from retained accountable owner')
        if transition.get('rehearsal_result') not in {'pass', 'fail', 'not-tested'}:
            raise ValueError('rehearsal_result must be pass/fail/not-tested')
        if transition['rehearsal_result'] != 'not-tested':
            validate_actual_date(doc, transition.get('rehearsed_on'), transition['source_ref'])
        if transition['rehearsal_result'] != 'pass':
            gaps.append('Transition rehearsal is not passed')
        count = transition.get('open_exceptions')
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError('open_exceptions must be an observed nonnegative integer')
        if count:
            gaps.append('Open transition exceptions remain')
        issues.extend(transition['transition_id'] + ': ' + g for g in gaps)
        transition_results.append({'transition_id': transition['transition_id'], 'service_id': sid,
                                    'gaps': gaps, 'source_ref': transition['source_ref']})
    for sid in sorted(ids - seen):
        issues.append(sid + ': no transition evidence')
    inherited = list(doc.get('unresolved_issues', []))
    clear = not issues and not inherited
    result = {'services': service_results, 'controls': control_results, 'transitions': transition_results,
              'dependency_order': sequence, 'operating_baseline': baseline['results'],
              'shared_baseline_status': baseline['status'], 'ready_for_owner_review': clear,
              'operating_change_authorized': False, 'staffing_change_authorized': False,
              'source_authentication': False}
    return finish(doc, SKILL, 'am-service-ownership-transition-v1', result, issues,
                  ['Service completeness, rights and observed controls are supplied declarations.',
                   'Shared operating measures retain their original observed window/cohort; no causal benefit or staffing decision.',
                   'Institutional acceptance, labor requirements, outsourcing obligations and current access require independent review.'],
                  ['operations-performance-analyzer', 'investment-platform-modernization-planner', 'fund-service-provider-oversight-reviewer'])


def validate(doc):
    try:
        compute(doc)
        return []
    except (ValueError, TypeError, KeyError, ArithmeticError):
        return ['Unsupported, malformed or unbound operating-model evidence']
