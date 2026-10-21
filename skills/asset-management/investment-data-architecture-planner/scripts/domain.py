"""AM grain, lineage, access evidence and bitemporal sample design review."""
from foundation_contract import (
    D, date_value, exact, finish, require_sources, text, validate_actual_date,
    validate_common,
)
from modernization_contract import shared_review
import shared_architecture

SKILL = 'investment-data-architecture-planner'
DIMENSIONS = {'security', 'portfolio', 'account', 'benchmark', 'time_series'}


def fields(row, names):
    for name in names:
        if not text(row.get(name)):
            raise ValueError(name + ' requires nonempty text')


def strings(value, label):
    if not isinstance(value, list) or not value or any(not text(x) for x in value) or len(set(value)) != len(value):
        raise ValueError(label + ' requires unique nonempty strings')
    return value


def rows(doc, key, id_key):
    values = doc.get(key)
    if not isinstance(values, list) or not values or len(values) > 10000:
        raise ValueError(key + ' requires 1..10000 rows')
    seen = set()
    for row in values:
        if not isinstance(row, dict):
            raise ValueError(key + ' rows must be objects')
        fields(row, (id_key, 'source_ref'))
        if row[id_key] in seen:
            raise ValueError('duplicate ' + id_key)
        seen.add(row[id_key])
        require_sources(doc, [row['source_ref']])
    return values


def interval(row, prefix):
    start = date_value(row.get(prefix + '_from'))
    end = date_value(row[prefix + '_to']) if row.get(prefix + '_to') is not None else None
    if end is not None and start >= end:
        raise ValueError(prefix + ' interval requires from < to; end is exclusive')
    return start, end


def active(span, day):
    start, end = span
    return start <= day and (end is None or day < end)


@exact
def compute(doc):
    errors = validate_common(doc)
    if errors:
        raise ValueError('; '.join(errors))
    fields(doc, ('purpose', 'principal', 'snapshot_id', 'owner'))
    for source in doc['sources']:
        fields(source, ('locator',))
    architecture = shared_review(doc, 'architecture', 'solution-architecture-planner',
                                 shared_architecture.evaluate, shared_architecture.validate)
    issues = ['Shared architecture: ' + x for x in architecture['unresolved_issues']]
    shared_summaries = [{'producer': architecture['producer'], 'status': architecture['status'],
                         'results': architecture['results'], 'source_ref': doc['shared_reviews']['architecture']['source_ref']}]
    if 'data_value' in doc['shared_reviews']:
        import shared_data_value
        value = shared_review(doc, 'data_value', 'data-product-value-evaluator',
                              shared_data_value.evaluate, shared_data_value.validate)
        if doc['shared_reviews']['data_value']['input']['data'].get('purpose') != doc['purpose']:
            raise ValueError('shared data value purpose differs from AM request')
        issues.extend('Shared data value: ' + x for x in value['unresolved_issues'])
        shared_summaries.append({'producer': value['producer'], 'status': value['status'],
                                 'results': value['results'], 'source_ref': doc['shared_reviews']['data_value']['source_ref']})
    components = {x['component_id'] for x in architecture['results']['components']}
    datasets = rows(doc, 'datasets', 'dataset_id')
    semantics = rows(doc, 'fields', 'field_id')
    identities = rows(doc, 'identities', 'identity_id')
    licenses = rows(doc, 'licenses', 'license_id')
    permissions = rows(doc, 'permission_observations', 'observation_id')
    history = rows(doc, 'history', 'record_id')
    queries = rows(doc, 'queries', 'query_id')
    monitors = rows(doc, 'monitors', 'monitor_id')
    dataset_map = {x['dataset_id']: x for x in datasets}
    field_map = {x['field_id']: x for x in semantics}
    identity_map = {x['identity_id']: x for x in identities}
    license_map = {x['license_id']: x for x in licenses}
    keys = set()
    for identity in identities:
        fields(identity, ('dimension', 'namespace', 'native_key'))
        if identity['dimension'] not in DIMENSIONS:
            raise ValueError('unsupported identity dimension')
        key = (identity['dimension'], identity['namespace'], identity['native_key'])
        if key in keys:
            raise ValueError('duplicate namespaced identity under another identity_id')
        keys.add(key)
    for license_row in licenses:
        fields(license_row, ('dataset_id', 'principal', 'license_version', 'contract_locator'))
        if license_row['dataset_id'] not in dataset_map:
            raise ValueError('license refers to unknown dataset')
        strings(license_row.get('purposes'), 'license purposes')
        strings(license_row.get('audiences'), 'license audiences')
        start, end = date_value(license_row.get('effective_from')), date_value(license_row.get('effective_to'))
        if start > end:
            raise ValueError('license effective range inverted')
    access = {}
    for dataset in datasets:
        fields(dataset, ('owner', 'classification', 'retention_rule', 'component_id', 'license_id'))
        dimensions = strings(dataset.get('grain_dimensions'), 'grain_dimensions')
        if not set(dimensions) <= DIMENSIONS or dataset['component_id'] not in components:
            raise ValueError('dataset requires supported grain and a shared architecture component')
        contract = license_map.get(dataset['license_id'])
        if not contract or contract['dataset_id'] != dataset['dataset_id']:
            raise ValueError('dataset license binding differs')
        gaps = []
        if (doc['purpose'] not in contract['purposes'] or doc['audience'] not in contract['audiences']
                or contract['principal'] != doc['principal']):
            gaps.append('license scope does not cover principal, purpose and audience')
        if not date_value(contract['effective_from']) <= date_value(doc['as_of']) <= date_value(contract['effective_to']):
            gaps.append('license not effective at review date')
        observations = [x for x in permissions if x.get('dataset_id') == dataset['dataset_id']]
        if len(observations) != 1:
            gaps.append('one unambiguous permission observation required')
        else:
            observation = observations[0]
            if (observation.get('principal') != doc['principal'] or observation.get('purpose') != doc['purpose']
                    or observation.get('audience') != doc['audience'] or observation.get('operation') != 'read'):
                gaps.append('permission observation scope differs')
            if observation.get('decision') not in {'allowed', 'denied', 'unknown'}:
                raise ValueError('permission decision must be allowed, denied or unknown')
            observed = validate_actual_date(doc, observation.get('observed_on'), observation['source_ref'])
            if observed != date_value(doc['as_of']) or observation['decision'] != 'allowed':
                gaps.append('permission evidence not current allowed read')
        access[dataset['dataset_id']] = {'dataset_id': dataset['dataset_id'],
            'evidence_status': 'withheld' if gaps else 'declared-allowed-unverified',
            'permission_verified': False, 'issues': gaps,
            'source_refs': [contract['source_ref']] + [x['source_ref'] for x in observations]}
        issues.extend(dataset['dataset_id'] + ': ' + gap for gap in gaps)
    for observation in permissions:
        if observation.get('dataset_id') not in dataset_map:
            raise ValueError('permission observation refers to unknown dataset')
    for field in semantics:
        fields(field, ('dataset_id', 'definition', 'unit', 'currency', 'source_system',
                       'source_field', 'transformation', 'transformation_version', 'owner'))
        if field['dataset_id'] not in dataset_map or field.get('value_type') not in {'decimal', 'text'}:
            raise ValueError('field requires known dataset and decimal/text type')
        if field['currency'] not in {doc['currency'], 'not-applicable'}:
            raise ValueError('field currency differs; FX transformation requires a separate reviewed contract')
        if not isinstance(field.get('nullable'), bool):
            raise ValueError('field nullable must be explicit boolean')

    def grain(row, field):
        dimension_values = row.get('dimensions')
        expected = dataset_map[field['dataset_id']]['grain_dimensions']
        if not isinstance(dimension_values, dict) or set(dimension_values) != set(expected):
            raise ValueError('record/query grain differs from dataset; aggregation is not inferred')
        for dimension, identifier in dimension_values.items():
            identity = identity_map.get(identifier) if isinstance(identifier, str) else None
            if not identity or identity['dimension'] != dimension:
                raise ValueError('unresolved or incompatible namespaced identity')
        return tuple(sorted(dimension_values.items()))

    indexed = {}
    for row in history:
        field = field_map.get(row.get('field_id'))
        if not field:
            raise ValueError('history field unresolved')
        key = (row['field_id'], grain(row, field))
        valid, known = interval(row, 'valid'), interval(row, 'known')
        validate_actual_date(doc, row['known_from'], row['source_ref'])
        if known[1] is not None:
            validate_actual_date(doc, row['known_to'], row['source_ref'])
        if valid[0] > date_value(doc['as_of']):
            raise ValueError('actual historical value starts after review date')
        if row.get('unit') != field['unit'] or row.get('currency') != field['currency']:
            raise ValueError('history unit/currency differs from semantic contract')
        if 'value' not in row:
            raise ValueError('history value must be explicit, including null')
        if row['value'] is not None:
            if field['value_type'] == 'decimal':
                D(row['value'])
            elif not text(row['value']):
                raise ValueError('text value must be nonempty text or null')
        indexed.setdefault(key, []).append((row, valid, known))
    resolved = []
    for query in queries:
        field = field_map.get(query.get('field_id'))
        if not field:
            raise ValueError('query field unresolved')
        key = (query['field_id'], grain(query, field))
        valid_on, known_on = date_value(query.get('valid_on')), date_value(query.get('known_on'))
        if valid_on > date_value(doc['as_of']) or known_on > date_value(doc['knowledge_cutoff']) or known_on > date_value(doc['as_of']):
            raise ValueError('query exceeds review/knowledge dates')
        candidates = [row for row, valid, known in indexed.get(key, []) if active(valid, valid_on) and active(known, known_on)]
        gaps = list(access[field['dataset_id']]['issues'])
        if len(candidates) != 1:
            gaps.append('ambiguous active history' if candidates else 'no known active history')
        elif candidates[0]['value'] is None and not field['nullable']:
            gaps.append('required semantic value unknown')
        if architecture['unresolved_issues'] or doc.get('unresolved_issues'):
            gaps.append('unresolved shared architecture or inherited scope issues')
        value = candidates[0]['value'] if not gaps else None
        if value is not None and field['value_type'] == 'decimal':
            value = str(D(value))
        resolved.append({'query_id': query['query_id'], 'field_id': field['field_id'],
            'dimensions': query['dimensions'], 'valid_on': query['valid_on'], 'known_on': query['known_on'],
            'status': 'withheld' if gaps else 'resolved-supplied-sample', 'value': value,
            'unit': field['unit'], 'currency': field['currency'],
            'record_ids': [x['record_id'] for x in candidates],
            'source_refs': sorted({query['source_ref'], field['source_ref']} | {x['source_ref'] for x in candidates}),
            'issues': gaps})
        issues.extend(query['query_id'] + ': ' + gap for gap in gaps)
    monitor_results = []
    monitored = set()
    for monitor in monitors:
        fields(monitor, ('dataset_id', 'owner', 'metric', 'unit', 'incident_route', 'runbook', 'snapshot_id'))
        if monitor['dataset_id'] not in dataset_map or monitor['snapshot_id'] != doc['snapshot_id']:
            raise ValueError('monitor dataset/snapshot differs')
        monitored.add(monitor['dataset_id'])
        if monitor.get('operator') not in {'<=', '>='} or monitor.get('basis') not in {'observed', 'projected'}:
            raise ValueError('monitor requires <=/>= operator and observed/projected basis')
        threshold = D(monitor.get('threshold'))
        measurement = D(monitor['value']) if monitor.get('value') is not None else None
        meets = None
        if monitor['basis'] == 'observed':
            validate_actual_date(doc, monitor.get('observed_on'), monitor['source_ref'])
            if measurement is not None:
                meets = measurement <= threshold if monitor['operator'] == '<=' else measurement >= threshold
        if meets is None:
            issues.append(monitor['monitor_id'] + ': measured operating evidence unavailable')
        elif not meets:
            issues.append(monitor['monitor_id'] + ': observed threshold breach')
        monitor_results.append({'monitor_id': monitor['monitor_id'], 'dataset_id': monitor['dataset_id'],
            'metric': monitor['metric'], 'unit': monitor['unit'], 'threshold': str(threshold),
            'observed_value': str(measurement) if measurement is not None and monitor['basis'] == 'observed' else None,
            'projected_value': str(measurement) if measurement is not None and monitor['basis'] == 'projected' else None,
            'meets': meets, 'incident_route': monitor['incident_route'], 'source_ref': monitor['source_ref']})
    for dataset_id in set(dataset_map) - monitored:
        issues.append(dataset_id + ': no observability coverage')
    return finish(doc, SKILL, 'investment-grain-bitemporal-access-design/1', {
        'datasets': datasets, 'semantic_contract': semantics, 'identity_contract': identities,
        'access_evidence': list(access.values()), 'resolved_sample': resolved, 'observability': monitor_results,
        'shared_reviews': shared_summaries, 'source_authentication': False, 'permission_verified': False,
        'deployment_authorized': False, 'production_identity_resolution': False,
    }, issues, limitations=[
        'Bitemporal sample selection uses explicit half-open intervals and exact identities; ambiguous assertions are withheld without latest-record selection.',
        'Historical source times, licenses, permission observations and monitor measurements are supplied declarations, not authenticated facts.',
        'The HTTPS connector runtime must obtain current policy-authorized access separately; this offline result never grants access.',
        'No missing security identifiers, FX conversion, aggregation, benchmark restatement or valuation policy is inferred.',
    ])
