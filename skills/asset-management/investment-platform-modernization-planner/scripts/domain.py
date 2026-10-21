"""AM platform evidence adapter; supplied rehearsal evidence never authorizes cutover."""
import re
from foundation_contract import D, exact, finish, text, validate_common, require_sources, validate_actual_date, date_value
from modernization_contract import shared_review
import shared_architecture

SKILL = 'investment-platform-modernization-planner'
ROLES = {'PMS', 'OMS', 'EMS', 'IBOR', 'ABOR', 'custodian', 'market-data'}
GRAIN = ('fund_id', 'book_id', 'account_id', 'instrument_id', 'lot_id', 'valuation_date', 'measure', 'unit', 'currency')
GATES = {'reconciliation', 'parallel-run', 'rollback', 'security', 'business-acceptance'}


def fields(row, *keys):
    if not isinstance(row, dict) or any(not text(row.get(k)) for k in keys):
        raise ValueError('required nonempty fields: ' + ', '.join(keys))


def strings(row, key):
    value = row.get(key)
    if not isinstance(value, list) or any(not text(x) for x in value) or len(value) != len(set(value)):
        raise ValueError(key + ' requires an explicit unique string list')
    return value


def rows(doc, key, *, owner=None, nonempty=True):
    values = (doc if owner is None else owner).get(key)
    if not isinstance(values, list) or len(values) > 10000 or (nonempty and not values):
        raise ValueError(key + ' requires a bounded ' + ('nonempty ' if nonempty else '') + 'list')
    ids = set()
    for row in values:
        fields(row, 'id', 'source_ref')
        if row['id'] in ids:
            raise ValueError('duplicate ' + key + ' identity')
        ids.add(row['id'])
        require_sources(doc, [row['source_ref']])
    return values


def nonnegative(row, key):
    value = D(row.get(key))
    if value < 0:
        raise ValueError(key + ' must be nonnegative')
    return value


def grain(doc, row):
    fields(row, *GRAIN)
    if not re.fullmatch('[A-Z]{3}', row['currency']):
        raise ValueError('grain currency must be an explicit three-letter code')
    if date_value(row['valuation_date']) > date_value(doc['as_of']):
        raise ValueError('grain valuation_date postdates review')
    return tuple(row[k] for k in GRAIN)


@exact
def compute(doc):
    errors = validate_common(doc)
    if errors:
        raise ValueError('; '.join(errors))
    if 'mode' in doc:
        raise ValueError('this adapter has no selectable mode')
    arch = shared_review(doc, 'architecture', 'solution-architecture-planner', shared_architecture.evaluate, shared_architecture.validate)
    issues = list(arch['unresolved_issues'])
    if arch['completeness'] != 'complete' or arch['evaluability'] != 'evaluable':
        issues.append('shared architecture evidence is incomplete or not evaluable')
    components = {x['component_id'] for x in arch['results']['components']}
    arch_requirements = {x['requirement_id'] for x in arch['results']['requirement_fit']}
    platforms = rows(doc, 'platforms')
    excluded = rows(doc, 'excluded_roles', nonempty=False)
    by_platform = {p['id']: p for p in platforms}
    covered = set()
    for p in platforms:
        fields(p, 'component_id', 'role', 'owner', 'provider', 'provider_contract_version', 'provider_contract_source_ref',
               'licensed_purpose', 'record_identity', 'history_retention', 'failure_owner')
        require_sources(doc, [p['provider_contract_source_ref']])
        if p['role'] not in ROLES or p['component_id'] not in components:
            raise ValueError('platform role or shared architecture component is unsupported')
        covered.add(p['role'])
    for item in excluded:
        fields(item, 'role', 'rationale', 'reviewed_by')
        if item['role'] not in ROLES or item['role'] in covered:
            raise ValueError('excluded role is unknown, duplicated or still mapped')
        covered.add(item['role'])
    if covered != ROLES:
        raise ValueError('classify PMS/OMS/EMS/IBOR/ABOR/custodian/market-data roles explicitly')
    responsibilities = rows(doc, 'responsibilities')
    owned = set()
    for row in responsibilities:
        fields(row, 'platform_id', 'domain', 'book_scope', 'authoritative_state', 'version', 'reconciliation_owner')
        key = (row['domain'], row['book_scope'], row['authoritative_state'])
        if row['platform_id'] not in by_platform or key in owned:
            raise ValueError('responsibility requires one supplied system of record for each domain/book/state')
        owned.add(key)
    requirements = rows(doc, 'requirements')
    for row in requirements:
        fields(row, 'architecture_requirement_id', 'description', 'owner', 'disposition')
        if row['architecture_requirement_id'] not in arch_requirements or not isinstance(row.get('mandatory'), bool):
            raise ValueError('requirement needs a native architecture requirement and explicit mandatory flag')
        if row['disposition'] not in {'met', 'not-met', 'unknown'}:
            raise ValueError('requirement disposition unsupported')
        if row['disposition'] == 'unknown' or row['mandatory'] and row['disposition'] != 'met':
            issues.append('AM requirement unresolved or mandatory requirement unmet: ' + row['id'])
    snapshots = rows(doc, 'snapshots')
    by_snapshot = {s['id']: s for s in snapshots}
    for row in snapshots:
        fields(row, 'platform_id', 'version', 'sha256', 'observed_on')
        if row['platform_id'] not in by_platform or not re.fullmatch('[0-9a-f]{64}', row['sha256']):
            raise ValueError('snapshot requires known platform and supplied SHA256')
        validate_actual_date(doc, row['observed_on'], row['source_ref'])
    batches = rows(doc, 'batches')
    by_batch = {b['id']: b for b in batches}
    expected = {}
    for row in batches:
        fields(row, 'owner', 'mapping_version', 'source_snapshot', 'target_snapshot', 'rollback_owner', 'rollback_trigger', 'rollback_runbook')
        wave = nonnegative(row, 'wave')
        if wave != wave.to_integral_value():
            raise ValueError('wave must be an integer')
        if row['source_snapshot'] == row['target_snapshot'] or any(x not in by_snapshot for x in (row['source_snapshot'], row['target_snapshot'])):
            raise ValueError('batch requires two distinct known snapshot identities')
        if by_snapshot[row['source_snapshot']]['observed_on'] != by_snapshot[row['target_snapshot']]['observed_on']:
            raise ValueError('source/target snapshot observation dates must match')
        for dep in strings(row, 'depends_on'):
            if dep not in by_batch or nonnegative(by_batch[dep], 'wave') >= wave:
                raise ValueError('dependency must identify a strictly earlier migration wave')
        grains = row.get('expected_grains')
        if not isinstance(grains, list) or not grains or len(grains) > 10000:
            raise ValueError('each batch requires explicit complete expected_grains')
        keys = [grain(doc, g) for g in grains]
        if len(keys) != len(set(keys)):
            raise ValueError('duplicate expected financial grain')
        if row.get('grain_inventory_reviewed') is not True:
            issues.append('financial grain inventory lacks supplied review: ' + row['id'])
        expected[row['id']] = set(keys)
        if not isinstance(row.get('new_writes_after_cutover'), bool):
            raise ValueError('post-cutover write assumption must be boolean')
        if row['new_writes_after_cutover']:
            fields(row, 'delta_replay_evidence', 'delta_replay_source_ref', 'delta_replay_status', 'delta_replay_observed_on', 'delta_replay_run_id')
            require_sources(doc, [row['delta_replay_source_ref']])
            validate_actual_date(doc, row['delta_replay_observed_on'], row['delta_replay_source_ref'])
            if row['delta_replay_status'] not in {'passed', 'failed', 'not-run'}:
                raise ValueError('delta replay status must be passed/failed/not-run')
            if row['delta_replay_status'] != 'passed':
                issues.append('post-cutover delta replay evidence remains unresolved: ' + row['id'])
    reconciliations = rows(doc, 'reconciliations')
    seen = {bid: set() for bid in by_batch}
    differences = []
    for row in reconciliations:
        fields(row, 'batch_id', 'mapping_version', 'tolerance_reviewed_by', 'tolerance_source_ref')
        require_sources(doc, [row['tolerance_source_ref']])
        batch = by_batch.get(row['batch_id'])
        if batch is None or row['mapping_version'] != batch['mapping_version']:
            raise ValueError('reconciliation mapping differs from its batch')
        observations = []
        for side in ('source', 'target'):
            observation = row.get(side)
            fields(observation, 'snapshot_id', 'source_ref')
            require_sources(doc, [observation['source_ref']])
            if observation['snapshot_id'] != batch[side + '_snapshot']:
                raise ValueError('reconciliation snapshot differs from its batch')
            key = grain(doc, observation)
            validate_actual_date(doc, observation['valuation_date'], observation['source_ref'])
            if date_value(observation['valuation_date']) > date_value(by_snapshot[observation['snapshot_id']]['observed_on']):
                raise ValueError('financial observation postdates its snapshot')
            observations.append((key, D(observation.get('value'))))
        a, b = observations
        if a[0] != b[0] or a[0] not in expected[row['batch_id']] or a[0] in seen[row['batch_id']]:
            raise ValueError('reconciliation financial grain is mismatched, unexpected or duplicated')
        seen[row['batch_id']].add(a[0])
        delta = b[1] - a[1]
        within = abs(delta) <= nonnegative(row, 'tolerance')
        if not within:
            issues.append('financial grain reconciliation break: ' + row['id'])
        differences.append({'id': row['id'], 'batch_id': row['batch_id'], 'grain': dict(zip(GRAIN, a[0])),
                            'difference': format(delta, 'f'), 'within_tolerance': within})
    for bid, keys in expected.items():
        if seen[bid] != keys:
            issues.append('reconciliation evidence missing for expected financial grains: ' + bid)
    exceptions = rows(doc, 'exceptions', nonempty=False)
    by_exception = {r['id']: r for r in exceptions}
    for row in exceptions:
        fields(row, 'batch_id', 'owner', 'description', 'status')
        if row['batch_id'] not in by_batch or row['status'] not in {'open', 'closed', 'accepted'}:
            raise ValueError('invalid migration exception batch/status')
        if row['status'] != 'closed':
            issues.append('migration exception remains unresolved: ' + row['id'])
        else:
            fields(row, 'resolution', 'resolution_source_ref', 'resolved_on')
            require_sources(doc, [row['resolution_source_ref']])
            validate_actual_date(doc, row['resolved_on'], row['resolution_source_ref'])
    runs = rows(doc, 'parallel_runs')
    by_run = {r['id']: r for r in runs}
    for row in runs:
        fields(row, 'batch_id', 'mapping_version', 'source_snapshot', 'target_snapshot', 'window_start', 'window_end', 'owner')
        batch = by_batch.get(row['batch_id'])
        if batch is None or any(row[k] != batch[k] for k in ('mapping_version', 'source_snapshot', 'target_snapshot')):
            raise ValueError('parallel-run evidence does not bind batch mapping and snapshots')
        start = date_value(row['window_start'])
        end = validate_actual_date(doc, row['window_end'], row['source_ref'])
        if start > end or any(not start <= date_value(by_snapshot[row[k]]['observed_on']) <= end for k in ('source_snapshot', 'target_snapshot')):
            raise ValueError('snapshot observation must fall within the parallel-run window')
        if set(strings(row, 'exception_ids')) != {x['id'] for x in exceptions if x['batch_id'] == row['batch_id']}:
            raise ValueError('parallel run must retain all batch exceptions')
    for batch in batches:
        if not batch['new_writes_after_cutover']:
            continue
        replay_run = by_run.get(batch['delta_replay_run_id'])
        if replay_run is None or replay_run['batch_id'] != batch['id']:
            raise ValueError('delta replay must bind a parallel run for its own batch and snapshots')
        latest_end = max(date_value(run['window_end']) for run in runs if run['batch_id'] == batch['id'])
        if date_value(replay_run['window_end']) != latest_end:
            raise ValueError('delta replay must bind the latest supplied batch rehearsal')
        if date_value(batch['delta_replay_observed_on']) < latest_end:
            raise ValueError('delta replay observation predates its bound rehearsal completion')
    recoveries = rows(doc, 'recoveries')
    recovery_results = []
    for row in recoveries:
        fields(row, 'run_id', 'owner', 'observed_on', 'threshold_reviewed_by', 'threshold_source_ref', 'rollback_status')
        require_sources(doc, [row['threshold_source_ref']])
        run = by_run.get(row['run_id'])
        if run is None or row['rollback_status'] not in {'passed', 'failed', 'not-run'}:
            raise ValueError('recovery must bind a known run and explicit rollback status')
        observed = validate_actual_date(doc, row['observed_on'], row['source_ref'])
        if observed < date_value(run['window_end']):
            raise ValueError('recovery observation predates its rehearsal completion')
        rto = nonnegative(row, 'observed_rto_seconds')
        rpo = nonnegative(row, 'observed_rpo_seconds')
        rto_met = rto <= nonnegative(row, 'rto_limit_seconds')
        rpo_met = rpo <= nonnegative(row, 'rpo_limit_seconds')
        if not rto_met or not rpo_met or row['rollback_status'] != 'passed':
            issues.append('recovery or rollback requirement not met: ' + row['id'])
        recovery_results.append({'id': row['id'], 'run_id': row['run_id'], 'rto_met': rto_met, 'rpo_met': rpo_met, 'rollback_status': row['rollback_status']})
    gates = rows(doc, 'gates')
    gate_keys = set()
    for row in gates:
        fields(row, 'batch_id', 'kind', 'owner', 'status', 'reviewed_by', 'observed_on')
        key = (row['batch_id'], row['kind'])
        if row['batch_id'] not in by_batch or row['kind'] not in GATES or key in gate_keys or row['status'] not in {'passed', 'failed', 'not-run'}:
            raise ValueError('invalid or duplicate migration gate')
        gate_keys.add(key)
        gate_date = validate_actual_date(doc, row['observed_on'], row['source_ref'])
        evidence_ids = set(strings(row, 'evidence_ids'))
        if not evidence_ids:
            raise ValueError('human gate requires explicit evidence identities')
        native_ids = {'reconciliation': {r['id'] for r in reconciliations if r['batch_id'] == row['batch_id']},
                      'parallel-run': {r['id'] for r in runs if r['batch_id'] == row['batch_id']},
                      'rollback': {r['id'] for r in recoveries if by_run[r['run_id']]['batch_id'] == row['batch_id']}}
        if row['kind'] in native_ids and evidence_ids != native_ids[row['kind']]:
            raise ValueError('human gate must bind the complete batch evidence inventory')
        evidence_dates = {'reconciliation': [by_snapshot[by_batch[row['batch_id']][side + '_snapshot']]['observed_on'] for side in ('source', 'target')],
                          'parallel-run': [r['window_end'] for r in runs if r['batch_id'] == row['batch_id']],
                          'rollback': [r['observed_on'] for r in recoveries if by_run[r['run_id']]['batch_id'] == row['batch_id']]}
        # Exception closure and delta replay change the batch's reviewable
        # evidence. An earlier passed label cannot certify these later events.
        terminal_dates = [r['resolved_on'] for r in exceptions if r['batch_id'] == row['batch_id'] and r['status'] == 'closed']
        batch = by_batch[row['batch_id']]
        if batch['new_writes_after_cutover']:
            terminal_dates.append(batch['delta_replay_observed_on'])
        evidence_dates['business-acceptance'] = [day for dates in evidence_dates.values() for day in dates]
        for dates in evidence_dates.values():
            dates.extend(terminal_dates)
        if row['kind'] in evidence_dates and any(gate_date < date_value(day) for day in evidence_dates[row['kind']]):
            raise ValueError('human gate predates the evidence it claims to review')
        if row['status'] != 'passed':
            issues.append('human migration gate remains open: ' + row['id'])
    for bid in by_batch:
        if {k for b, k in gate_keys if b == bid} != GATES:
            issues.append('human migration gate coverage incomplete: ' + bid)
        batch_runs = {r['id'] for r in runs if r['batch_id'] == bid}
        if not batch_runs:
            issues.append('parallel-run evidence unavailable: ' + bid)
        if not batch_runs <= {r['run_id'] for r in recoveries}:
            issues.append('recovery rehearsal evidence unavailable: ' + bid)
    inherited = list(doc.get('unresolved_issues', [])) + issues
    results = {'shared_architecture': {'status': arch['status'], 'requirement_fit': arch['results']['requirement_fit'],
                                     'supplied_period_cost': arch['results']['supplied_period_cost']},
               'platforms': platforms, 'excluded_roles': excluded, 'system_of_record_responsibilities': responsibilities,
               'requirements': requirements, 'dependency_order': [r['id'] for r in sorted(batches, key=lambda r: (D(r['wave']), r['id']))],
               'migration_batches': batches,
               'reconciliation': differences, 'parallel_runs': runs, 'exceptions': exceptions, 'recovery': recovery_results, 'human_gates': gates,
               'readiness': 'blocked' if inherited else 'evidence-ready-for-human-review',
               'cutover_authorized': False, 'migration_executed': False, 'production_access_verified': False}
    return finish(doc, SKILL, 'am-platform-migration-evidence-adapter', results, issues,
                  ['Source snapshots, permissions, licensing, test results and review identities are supplied declarations, not authenticated facts.',
                   'Each declared financial grain is reconciled independently; no cross-currency conversion, lot matching, netting or accounting adjudication.',
                   'No production access, cutover, rollback, order routing, accounting posting or vendor selection is performed.'],
                  ['solution-architecture-planner', 'investment-data-architecture-planner', 'investment-operating-model-planner'])


def validate(doc):
    try:
        compute(doc)
        return []
    except (ValueError, TypeError, KeyError, IndexError, ArithmeticError, AttributeError) as exc:
        return [str(exc)]
