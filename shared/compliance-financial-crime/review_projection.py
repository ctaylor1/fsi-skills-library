"""Two explicit same-subject review adapters; no disclosure/action authority (MIT)."""
from __future__ import annotations
import copy

from native_integrity import canonical_hash
from cfc_contract import (validate_packet, validate_field_mappings, claim_value,
                          _workflow, _errors, _is_foundation)

VERSION = 'compliance-review-projection/1.0'
PAIRS = {
    ('transaction-monitoring-scenario-designer', 'transaction-monitoring-effectiveness-reviewer'),
    ('financial-crime-case-investigator', 'financial-crime-case-quality-reviewer'),
}
REVIEW_CONTEXT_FIELDS = {'object_type', 'capacity', 'purpose'}


def _bound(doc, claim, label):
    value, gaps = claim_value(doc, claim, label)
    if gaps or value is None:
        raise ValueError('native subject linkage lacks sourced evidence: ' + label)
    return value


def _subject_link(source, target, producer):
    """Review IDs alone do not identify the underlying scenario or case."""
    if producer == 'transaction-monitoring-scenario-designer':
        scenario = source['data']['scenario']; scope = target['data']['scope']
        pairs = [('scenario_id', 'scenario_id'), ('design_version', 'scenario_version'),
                 ('engine_id', 'engine_id'), ('engine_version', 'engine_version'),
                 ('population_id', 'population_id'), ('population_unit', 'population_unit'),
                 ('mapping_dataset_id', 'mapping_dataset_id'),
                 ('identifier_namespace', 'identifier_namespace'),
                 ('entity_mapping_ref', 'entity_mapping_ref'),
                 ('entity_mapping_version', 'entity_mapping_version'),
                 ('graph_reference', 'graph_reference'), ('graph_version', 'graph_version')]
        linked = {}
        for skey, tkey in pairs:
            old = _bound(source, scenario[skey], 'producer scenario.' + skey)
            new = _bound(target, scope[tkey], 'receiver scope.' + tkey)
            if canonical_hash(old) != canonical_hash(new):
                raise ValueError('underlying scenario/version/population/identity linkage differs: ' + tkey)
            linked[tkey] = old
        for section in ('observations', 'benchmark_references'):
            for row in target['data'][section]:
                for key in ('scenario_id', 'scenario_version', 'engine_id', 'engine_version'):
                    if key in row and canonical_hash(_bound(target, row[key], section + '.' + key)) != canonical_hash(linked[key]):
                        raise ValueError('receiver observation/benchmark refers to another scenario or engine: ' + key)
        return linked
    subject = source['object_id']; data = target['data']; mandate = data['mandate']
    for key in ('population_case_ids', 'selected_case_ids'):
        if _bound(target, mandate[key], 'QA mandate.' + key) != [subject]:
            raise ValueError('single-case projection requires the underlying producer case only: ' + key)
    if len(data['cases']) != 1:
        raise ValueError('single-case projection requires exactly one native QA case')
    case = data['cases'][0]
    for key in ('case_id', 'upstream_native_id'):
        if _bound(target, case[key], 'QA case.' + key) != subject:
            raise ValueError('underlying QA case linkage differs: ' + key)
    if case['native_case_id'] != subject:
        raise ValueError('underlying native QA case ID differs')
    original_hash = canonical_hash(source)
    if _bound(target, case['upstream_native_version'], 'QA upstream native version') != original_hash:
        raise ValueError('QA upstream native version must identify the retained producer original hash')
    for section in ('exhibits', 'events', 'reasoning', 'observations', 'tool_outputs'):
        for row in data[section]:
            if _bound(target, row['case_id'], section + '.case_id') != subject:
                raise ValueError('receiver QA evidence refers to another underlying case')
    return {'case_id': subject, 'upstream_native_version': original_hash, 'scope': 'single-case-only'}


def expected_basis(source_packet, source_input, target_input, producer, target_skill):
    return {
        'transfer_kind': 'same-subject-evidence-review',
        'producer': producer, 'target_skill': target_skill,
        'source_input_hash': canonical_hash(source_input),
        'source_output_hash': canonical_hash(source_packet['native_output']),
        'source_context': copy.deepcopy(source_input['workflow']['context']),
        'target_context': copy.deepcopy(target_input['workflow']['context']),
        'source_role': source_input['workflow']['role'],
        'target_role': target_input['workflow']['role'],
        'as_of': source_input['as_of'],
        'knowledge_cutoff': source_input['knowledge_cutoff'],
        'native_subject_link': _subject_link(source_input, target_input, producer),
    }


def build_review_projection(source_packet, source_input, target_input, *, producer,
                            target_skill, producer_validator, receiver_validator,
                            mappings, projection_basis, supplemental_inputs=None):
    """Record a sourced mapping review for one of two distinct review objects.

    Subject, institution, legal entity, represented party, jurisdiction, line of
    business, date/cutoff and audience/classification remain fixed. Capacity,
    purpose, role and object type may change only with the exact scoped review
    assertion. Its source consistency is not authenticated authority or proof
    that receiver observations substantively follow from producer evidence.
    """
    if (producer, target_skill) not in PAIRS:
        raise ValueError('unregistered review projection; no general schema conversion')
    errors = validate_packet(source_packet, source_input, producer=producer,
                             native_validator=producer_validator)
    if errors:
        raise ValueError('source: ' + '; '.join(errors))
    target = copy.deepcopy(target_input)
    if not _is_foundation(source_input, producer) or not _is_foundation(target, target_skill):
        raise ValueError('both actual foundation native objects required')
    tw = _workflow(target, target_skill)
    sw = source_packet['workflow']
    for key in set(sw['context']) - REVIEW_CONTEXT_FIELDS:
        if tw['context'].get(key) != sw['context'][key]:
            raise ValueError('review projection cannot change subject/institution context: ' + key)
    if target['as_of'] != source_input['as_of'] or target['knowledge_cutoff'] != source_input['knowledge_cutoff']:
        raise ValueError('assessment/cutoff change requires a separate temporal review')
    for key in ('classification', 'audience', 'allowed_audiences'):
        if tw[key] != sw[key]:
            raise ValueError('review projection cannot change audience/classification')
    if not set(source_packet['unresolved_issues']).issubset(tw['unresolved_issues']):
        raise ValueError('receiver dropped source unresolved issues')
    if not {canonical_hash(s) for s in source_input['sources']}.issubset({canonical_hash(s) for s in target['sources']}):
        raise ValueError('receiver dropped or altered detached source facts')
    if not {canonical_hash(s) for s in sw['sources']}.issubset({canonical_hash(s) for s in tw['sources']}):
        raise ValueError('receiver dropped source version records')
    if not isinstance(projection_basis, dict) or set(projection_basis) != {'value', 'source_refs', 'fact_ids'}:
        raise ValueError('exact source-bound projection review assertion required')
    observed, gaps = claim_value(target, projection_basis, 'projection review basis')
    expected = expected_basis(source_packet, source_input, target, producer, target_skill)
    if gaps or canonical_hash(observed) != canonical_hash(expected):
        raise ValueError('projection review scope/version/source support unestablished')
    supplemental = validate_field_mappings(source_packet, source_input, target, mappings, supplemental_inputs)
    registry = {s['source_ref'] for s in target['sources']}
    if any(not set(m['source_refs']).issubset(registry) for m in mappings):
        raise ValueError('mapping cites sources outside receiver detached registry')
    if not any(m['target_field'] == 'object_id' and m['source'] == 'source_input'
               and m['source_pointer'] == '/object_id' for m in mappings):
        raise ValueError('native subject ID must map directly from the producer original')
    errors = _errors(receiver_validator, target)
    if errors:
        raise ValueError('receiver: ' + '; '.join(errors))
    return {
        'contract_version': VERSION, 'source_packet': copy.deepcopy(source_packet),
        'producer': producer, 'target_skill': target_skill, 'target_input': target,
        'target_input_hash': canonical_hash(target), 'mappings': copy.deepcopy(mappings),
        'projection_basis': copy.deepcopy(projection_basis),
        'supplemental_hashes': {k: canonical_hash(v) for k, v in supplemental.items()},
        'authority_granted': False, 'action_mode': 'review-only',
        'human_review_required': True, 'source_truth': 'unverified',
        'mapping_assurance': 'supplied-not-authenticated',
        'semantic_evidence_sufficiency': 'human-review-required',
        'execution': 'not_performed',
    }


def validate_review_projection(packet, source_input, *, producer, target_skill,
                               producer_validator, receiver_validator,
                               supplemental_inputs=None):
    try:
        expected = build_review_projection(
            packet['source_packet'], source_input, packet['target_input'],
            producer=producer, target_skill=target_skill,
            producer_validator=producer_validator, receiver_validator=receiver_validator,
            mappings=packet['mappings'], projection_basis=packet['projection_basis'],
            supplemental_inputs=supplemental_inputs)
        return [] if canonical_hash(packet) == canonical_hash(expected) else ['projection differs from detached reconstruction']
    except (KeyError, TypeError, ValueError, IndexError, AttributeError) as exc:
        return [str(exc)]
