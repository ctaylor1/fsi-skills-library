"""Source-bound current/target serial paths with explicit exception ownership."""
from decimal import Decimal
from design_support import Review, total, validate_with
METHOD = 'reviewed-insurance-paths-v1'


def evaluate(doc):
    r = Review(doc, METHOD); d = r.data
    steps = r.rows('steps', 'step_id'); paths = r.rows('paths', 'path_id')
    services = r.rows('source_contracts', 'contract_id')
    service_ids = {x['contract_id'] for x in services}; by = {x['step_id']: x for x in steps}
    for row in services:
        r.fields(row, ('system', 'version', 'owner', 'access_scope', 'purpose', 'schema_version', 'freshness_rule'))
        r.flag(row, 'access_reviewed'); r.flag(row, 'purpose_reviewed')
    times = {}
    for row in steps:
        r.fields(row, ('owner', 'input_contract', 'output_contract', 'completion_evidence'))
        r.need(row.get('mode') in {'human', 'read', 'draft', 'proposed-write'}, 'mode', 'Step mode must be human/read/draft/proposed-write', row)
        contracts = r.strings(row, 'contract_ids')
        r.need(set(contracts) <= service_ids, 'contract-link', 'Step references an unknown source contract', row)
        if row.get('mode') != 'human':
            r.need(bool(contracts), 'contract-link', 'Machine step needs an explicit source/tool contract', row)
            fallback = by.get(row.get('failure_step'))
            r.need(bool(fallback) and fallback.get('mode') == 'human', 'fallback', 'Machine step requires a named human failure route', row)
            r.fields(row, ('timeout_rule', 'audit_record'))
            attempts = r.num(row, 'max_attempts', integer=True)
            r.need(attempts is not None and 1 <= attempts <= 10, 'retry-bound', 'Attempt bound must be 1..10', row)
        if row.get('mode') == 'proposed-write':
            r.fields(row, ('approval_owner', 'idempotency_key', 'receipt_check', 'recovery_plan'))
        times[row['step_id']] = (r.num(row, 'human_minutes'), r.num(row, 'elapsed_minutes'))
    weighted = {}; rows = []
    for design in ('current', 'target'):
        relevant = [x for x in paths if x.get('design') == design]
        r.need(bool(relevant), 'design-paths', design+' needs explicit paths')
        weights = []
        for row in relevant:
            ids = r.strings(row, 'step_ids', nonempty=True)
            r.fields(row, ('outcome', 'population_basis'))
            r.need(row.get('kind') in {'normal', 'exception'}, 'path-kind', 'Path kind must be normal/exception', row)
            failures = r.strings(row, 'failure_of')
            r.need(all(i in by and by[i].get('mode') != 'human' for i in failures), 'failure-binding', 'Failure path must name actual machine steps', row)
            r.need(row.get('kind') != 'normal' or not failures, 'normal-path', 'Normal paths cannot represent declared failures', row)
            r.need(all(i in by for i in ids), 'path-link', 'Path references unknown steps', row)
            weight = r.num(row, 'share', proportion=True); weights.append(weight)
            values = [times[i] for i in ids if i in times]
            rows.append({'path_id': row['path_id'], 'design': design, 'kind': row.get('kind'), 'outcome': row.get('outcome'),
                         'step_ids': ids, 'share': weight, 'human_minutes': total(v[0] for v in values),
                         'elapsed_minutes': total(v[1] for v in values), 'source_refs': row['source_refs']})
        for step_id in {i for x in relevant for i in x['step_ids'] if i in by and by[i].get('mode') != 'human'}:
            r.need(any(x.get('kind') == 'exception' and step_id in x.get('failure_of', []) and by[step_id].get('failure_step') in x['step_ids'] for x in relevant), 'failure-coverage', design+' must cover failure of '+step_id)
        r.need(total(weights) == Decimal(1), 'path-mass', design+' exhaustive mutually exclusive shares must sum exactly to 1')
        r.need(any(x.get('kind') == 'exception' for x in relevant), 'failure-path', design+' needs an explicit exception path, including explicit zero share')
    r.need(all(x.get('design') in {'current','target'} for x in paths), 'design', 'Only current/target designs are supported')
    r.flag(d, 'path_inventory_complete'); r.fields(d, ('business_outcome', 'population_basis'))
    r.need(all(x.get('population_basis') == d.get('population_basis') for x in paths), 'population', 'All paths must describe the same reviewed population basis')
    valid = r.clear
    for design in ('current','target'):
        group = [x for x in rows if x['design'] == design]
        weighted[design] = {key: total(x['share'] * x[key] for x in group) if valid else None for key in ('human_minutes','elapsed_minutes')}
    if not valid:
        for row in rows:
            row.update(human_minutes=None, elapsed_minutes=None)
    return r.finish({'paths': rows, 'weighted_minutes': weighted, 'source_contracts': services,
                     'step_design': steps, 'business_outcome': d.get('business_outcome'),
                     'runtime_installed': False, 'workflow_approved': False})


def validate(doc): return validate_with(evaluate, doc)
