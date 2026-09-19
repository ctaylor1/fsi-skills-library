"""Payment-flow architecture decisions and migration assessment, without deployment."""
from collections import Counter
from decimal import Decimal
from payment_contract import money

SKILL = 'payment-platform-architecture-reviewer'
STAGES = {'initiation', 'authentication', 'authorization', 'routing', 'capture', 'clearing',
          'settlement', 'funding', 'posting', 'reconciliation', 'servicing'}


def validate(data):
    if not isinstance(data, dict): return ['data must be an object']
    errors = []
    for key in ('context',):
        if key in data and not isinstance(data[key], dict): errors.append(f'{key} must be an object')
    for key in ('components', 'flows', 'data_models', 'nfrs', 'options', 'migration'):
        if key in data and (not isinstance(data[key], list) or any(not isinstance(x, dict) for x in data[key])):
            errors.append(f'{key} must be a list of objects')
    for flow in data.get('flows', []) if isinstance(data.get('flows', []), list) else []:
        if not isinstance(flow, dict): continue
        for key in ('idempotency', 'uncertain_outcome', 'reconciliation'):
            if key in flow and not isinstance(flow[key], dict): errors.append(f'flow.{key} must be an object')
        if 'mutates_money' in flow and not isinstance(flow['mutates_money'], bool): errors.append('mutates_money must be boolean')
    for nfr in data.get('nfrs', []) if isinstance(data.get('nfrs', []), list) else []:
        if isinstance(nfr, dict) and 'target' in nfr and nfr['target'] is not None:
            try:
                if money(nfr['target']) < 0: errors.append('NFR target must be nonnegative')
            except ValueError as exc: errors.append(str(exc))
    for step in data.get('migration', []) if isinstance(data.get('migration', []), list) else []:
        if isinstance(step, dict) and 'dual_financial_execution' in step and not isinstance(step['dual_financial_execution'], bool):
            errors.append('dual_financial_execution must be boolean')
        if isinstance(step, dict) and 'sequence' in step and (not isinstance(step['sequence'], int) or isinstance(step['sequence'], bool)):
            errors.append('migration sequence must be an integer')
    string_fields = {'component_id', 'entity', 'flow_id', 'state_entity', 'from_component', 'to_component', 'stage',
                     'authoritative_component', 'status_authority', 'source_component', 'target_component', 'nfr_id', 'metric', 'unit', 'option_id', 'phase_id', 'module'}
    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in string_fields and child is not None and not isinstance(child, str): errors.append(key + ' must be a string')
                if key in {'identifier_fields', 'state_values', 'key_fields', 'partition_fields', 'match_keys', 'component_changes', 'benefits', 'tradeoffs', 'acceptance_evidence', 'entry_evidence', 'exit_evidence'} and (not isinstance(child, list) or any(not isinstance(x, str) for x in child)): errors.append(key + ' must be a list of strings')
                walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(data)
    return errors


def analyze(request):
    d = request['data']; findings = []
    def issue(code, message, row=None, severity='gap'):
        findings.append({'code': code, 'message': message, 'source_ids': (row or {}).get('source_ids', []), 'severity': severity})
    context = d.get('context', {})
    for key in ('business_flow', 'current_constraint', 'target_outcome', 'module'):
        if not context.get(key): issue('business-context-missing', f'Architecture {key} is unresolved.', context)
    if context.get('module') not in {'issuer', 'acquirer', 'hub', 'orchestration'}:
        issue('module-unsupported', 'Choose issuer, acquirer, hub or orchestration for this foundational assessment.', context)
    components = d.get('components', [])
    counts = Counter(x.get('component_id') for x in components)
    index = {x.get('component_id'): x for x in components if x.get('component_id') and counts[x['component_id']] == 1}
    for comp in components:
        if not comp.get('component_id') or counts[comp.get('component_id')] > 1:
            issue('component-identity-ambiguous', 'Component identifier is missing or repeated; ownership cannot be resolved.', comp)
        for key in ('role', 'owner', 'source_ids'):
            if not comp.get(key): issue('component-context-missing', f'{comp.get("component_id")}: {key} is unresolved.', comp)
    models = d.get('data_models', [])
    model_counts = Counter(x.get('entity') for x in models)
    model_index = {x.get('entity'): x for x in models if x.get('entity') and model_counts[x['entity']] == 1}
    authority_map = []
    for model in models:
        reasons = []
        if not model.get('entity') or model_counts[model.get('entity')] > 1: reasons.append('entity identity ambiguous')
        if model.get('authoritative_component') not in index: reasons.append('unique authoritative component missing')
        if not model.get('identifier_fields'): reasons.append('stable identity fields missing')
        if not model.get('state_values'): reasons.append('explicit lifecycle state model missing')
        if not model.get('source_ids'): reasons.append('model evidence missing')
        authority_map.append({**model, 'assessment': 'unresolved' if reasons else 'supplied-design', 'issues': reasons})
        for reason in reasons: issue('state-authority-gap', f'{model.get("entity")}: {reason}.', model)
    flows = []; edges = []
    flow_counts = Counter(x.get('flow_id') for x in d.get('flows', []))
    for flow in d.get('flows', []):
        fid = flow.get('flow_id'); reasons = []
        if not fid or flow_counts[fid] > 1: reasons.append('flow identity ambiguous')
        if flow.get('from_component') not in index or flow.get('to_component') not in index: reasons.append('endpoints missing or ambiguous')
        if flow.get('stage') not in STAGES: reasons.append('lifecycle stage missing or unsupported')
        model = model_index.get(flow.get('state_entity'), {})
        if not model or model.get('authoritative_component') not in index: reasons.append('state authority unresolved')
        if not flow.get('source_ids'): reasons.append('flow evidence missing')
        if 'mutates_money' not in flow: reasons.append('financial mutation classification missing')
        if flow.get('mutates_money') is True:
            idem = flow.get('idempotency', {})
            for field in ('key_fields', 'scope', 'retention', 'atomic_enforcement', 'payload_conflict_behavior', 'source_ids'):
                if not idem.get(field): reasons.append('idempotency ' + field + ' unresolved')
            if idem.get('payload_conflict_behavior') not in {'reject-conflict', 'manual-review'}:
                reasons.append('changed payload under a reused key must not silently overwrite or execute')
            outcome = flow.get('uncertain_outcome', {})
            if outcome.get('strategy') not in {'status-then-reconcile', 'manual-reconcile-no-retry'}:
                reasons.append('uncertain outcome cannot be resolved by blind retry or a new idempotency key')
            if outcome.get('status_authority') not in index or not outcome.get('source_ids'):
                reasons.append('uncertain-outcome authoritative status/evidence missing')
            recon = flow.get('reconciliation', {})
            for field in ('source_component', 'target_component'):
                if recon.get(field) not in index: reasons.append('reconciliation ' + field + ' unresolved')
            partitions = recon.get('partition_fields', [])
            if not isinstance(partitions, list) or not {'legal_entity_id', 'account_id', 'currency'}.issubset(partitions):
                reasons.append('reconciliation partitions omit entity, account or currency')
            for field in ('match_keys', 'owner', 'exception_queue', 'source_ids'):
                if not recon.get(field): reasons.append('reconciliation ' + field + ' unresolved')
            if flow.get('stage') == 'posting' and not flow.get('ledger_invariant'):
                reasons.append('ledger balancing invariant and reversal model unresolved')
        for reason in reasons: issue('flow-control-gap', f'{fid}: {reason}.', flow)
        flows.append({'flow_id': fid, 'stage': flow.get('stage'), 'state_entity': flow.get('state_entity'),
                      'authoritative_component': model.get('authoritative_component'), 'assessment': 'unresolved' if reasons else 'supplied-design',
                      'issues': reasons, 'proposed_flow': flow, 'source_ids': flow.get('source_ids', [])})
        edges.append({'from_component': flow.get('from_component'), 'to_component': flow.get('to_component'), 'flow_id': fid,
                      'stage': flow.get('stage'), 'source_ids': flow.get('source_ids', [])})
    if not flows: issue('flows-missing', 'Supply at least one concrete payment business flow and its system/state boundaries.')
    if not models: issue('state-model-missing', 'Supply payment, attempt, instruction and ledger identity/state models used by the flows; an API diagram is insufficient.')
    nfrs = []; nfr_counts = Counter(x.get('nfr_id') for x in d.get('nfrs', []))
    for nfr in d.get('nfrs', []):
        reasons = []
        if not nfr.get('nfr_id') or nfr_counts[nfr.get('nfr_id')] > 1: reasons.append('NFR identity missing or repeated')
        for key in ('metric', 'unit', 'measurement_plan', 'owner', 'source_ids'):
            if not nfr.get(key): reasons.append(key + ' unresolved')
        if nfr.get('target') is None: reasons.append('target unresolved')
        if nfr.get('metric') in {'availability', 'success-rate'} and nfr.get('target') is not None:
            target = money(nfr['target']); unit = nfr.get('unit')
            if unit not in {'percent', 'ratio'}: reasons.append('availability/rate needs explicit percent or ratio unit')
            if target > (Decimal('1') if unit == 'ratio' else Decimal('100')): reasons.append('target outside declared rate scale')
        for reason in reasons: issue('nfr-gap', f'{nfr.get("nfr_id")}: {reason}.', nfr)
        nfrs.append({**nfr, 'assessment': 'unresolved' if reasons else 'declared-target-not-demonstrated', 'issues': reasons})
    if not nfrs: issue('nfrs-missing', 'No scoped throughput, latency, availability, recovery or reconciliation targets are supplied.')
    decisions = []; option_counts = Counter(x.get('option_id') for x in d.get('options', []))
    for option in d.get('options', []):
        reasons = []
        if not option.get('option_id') or option_counts[option.get('option_id')] > 1: reasons.append('option identity missing or repeated')
        for field in ('description', 'component_changes', 'benefits', 'tradeoffs', 'acceptance_evidence', 'source_ids'):
            if not option.get(field): reasons.append(field + ' unresolved')
        for reason in reasons: issue('option-evidence-gap', f'{option.get("option_id")}: {reason}.', option)
        decisions.append({'option_id': option.get('option_id'), 'status': 'candidate-needs-evidence' if reasons else 'candidate-for-review',
                          'proposal': option, 'issues': reasons, 'selected': False,
                          'decision_context': context.get('target_outcome'), 'source_ids': option.get('source_ids', [])})
    if not decisions: issue('options-missing', 'No target alternative and retained/current-state alternative have been supplied; no selection is defensible.')
    steps = d.get('migration', []); seq_counts = Counter(x.get('sequence') for x in steps)
    phases = []
    for step in sorted(steps, key=lambda x: x.get('sequence', 0)):
        reasons = []
        for field in ('phase_id', 'scope', 'entry_evidence', 'exit_evidence', 'inflight_handling', 'financial_reconciliation', 'rollback_boundary', 'owner', 'source_ids'):
            if not step.get(field): reasons.append(field + ' unresolved')
        if step.get('sequence') is None or seq_counts[step.get('sequence')] > 1: reasons.append('sequence missing or repeated')
        if step.get('dual_financial_execution') is True: reasons.append('dual financial execution risks duplicate movement; shadow comparison must not post twice')
        if step.get('rollback_mode') == 'reverse-settled-payments': reasons.append('application rollback cannot reverse final settlement; separate servicing rights are required')
        for reason in reasons: issue('migration-gap', f'{step.get("phase_id")}: {reason}.', step)
        phases.append({**step, 'assessment': 'unresolved' if reasons else 'draft-gate', 'issues': reasons, 'go_live_authorized': False})
    if not phases: issue('migration-plan-missing', 'Define bounded migration phases with in-flight state, reconciliation and rollback boundaries.')
    return {'result': {'context': context, 'component_map': components, 'flow_edges': edges,
                       'flow_assessments': flows, 'state_authority_map': authority_map, 'nfr_assessments': nfrs,
                       'decision_records': decisions, 'migration_phases': phases,
                       'deployment_or_resilience_validated': False}, 'findings': findings,
            'handoffs': [{'target_skill': 'payment-integration-readiness-reviewer', 'reason': 'Evaluate inspected integration and migration evidence before any implementation acceptance.',
                          'required_inputs': ['selected design and obligations', 'test and reconciliation evidence', 'accountable reviewers'], 'source_ids': context.get('source_ids', [])}],
            'limitations': ['Foundational issuer/acquirer/hub/orchestration design review; no Phase 3 incident-response, active-active, chaos-testing or full resilience certification.']}
