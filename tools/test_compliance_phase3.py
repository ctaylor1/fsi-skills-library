"""Actual Phase3 native packets and the two explicit same-subject review projections."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import tempfile
import unittest
import yaml
from pathlib import Path

from test_compliance_phase1 import (ROOT, ROUTER, package, calculate, load,
    native_validate, build_packet, validate_packet, build_handoff, canonical_hash)
from test_compliance_phase2 import fixture, validator, sourced_packet, separate_registry
from review_projection import (build_review_projection, validate_review_projection,
                               expected_basis, PAIRS)

SCOPE = load(ROOT / 'catalog/compliance-financial-crime-phase3-capabilities.json')


def projection_case(producer, receiver):
    source = fixture(producer)
    # Replayed synthetic fixture only; original archived intakes stay untouched.
    source['as_of'] = '2026-10-04'; source['knowledge_cutoff'] = '2026-10-03'
    if producer == 'financial-crime-case-investigator': source['knowledge_cutoff'] = '2026-10-04'
    source['workflow']['as_of'] = source['as_of']
    out, packet = sourced_packet(producer, source)
    target = separate_registry(fixture(receiver))
    context = target['workflow']['context']
    for key, value in source['workflow']['context'].items():
        if key not in {'capacity', 'purpose', 'object_type'}:
            context[key] = copy.deepcopy(value)
    target['object_id'] = source['object_id']
    def amend_claims(item):
        if isinstance(item, dict):
            for key, claim in item.items():
                value = None
                if key == 'review_id': value = source['object_id']
                elif key in {'institution_id', 'legal_entity_id', 'jurisdiction'}:
                    value = context[key]
                if value is not None and isinstance(claim, dict) and 'fact_ids' in claim:
                    claim['value'] = value
                    for record in target['sources']:
                        for fact in record['facts']:
                            if fact['fact_id'] in claim['fact_ids']:
                                fact['value'] = value
                                fact['excerpt'] = 'Synthetic amended receiver context fact: ' + json.dumps(value)
                else: amend_claims(claim)
        elif isinstance(item, list):
            for child in item: amend_claims(child)
    amend_claims(target['data'])
    if producer == 'transaction-monitoring-scenario-designer':
        for key in ('scenario_id', 'engine_id', 'engine_version', 'population_id', 'population_unit',
                    'mapping_dataset_id', 'identifier_namespace', 'entity_mapping_ref',
                    'entity_mapping_version', 'graph_reference', 'graph_version'):
            claim = target['data']['scope'][key]
            value = source['data']['scenario'][key]['value']; claim['value'] = value
            for record in target['sources']:
                for fact in record['facts']:
                    if fact['fact_id'] in claim['fact_ids']:
                        fact['value'] = value; fact['excerpt'] = 'Synthetic source-linked receiver scope amendment: ' + str(value)
    if producer == 'financial-crime-case-investigator':
        first = target['data']['cases'][0]['native_case_id']
        target['data']['cases'] = target['data']['cases'][:1]
        for section in ('exhibits', 'events', 'reasoning', 'observations', 'tool_outputs'):
            target['data'][section] = [r for r in target['data'][section] if r['case_id']['value'] == first]
        def replace(item):
            if isinstance(item, dict):
                for key, value in item.items():
                    if value == first: item[key] = source['object_id']
                    elif isinstance(value, list) and first in value: item[key] = [source['object_id']]
                    else: replace(value)
            elif isinstance(item, list):
                for value in item: replace(value)
        replace(target)
        claim = target['data']['cases'][0]['upstream_native_id']
        version = target['data']['cases'][0]['upstream_native_version']
        for amended, value in ((claim, source['object_id']), (version, canonical_hash(source))):
            amended['value'] = value
            for record in target['sources']:
                for fact in record['facts']:
                    if fact['fact_id'] in amended['fact_ids']:
                        fact['value'] = value
                        fact['excerpt'] = 'Synthetic single-case projection linkage amendment: ' + value
    target['as_of'] = source['as_of']; target['knowledge_cutoff'] = source['knowledge_cutoff']
    target['workflow']['as_of'] = source['as_of']
    for key in ('classification', 'audience', 'allowed_audiences'):
        target['workflow'][key] = copy.deepcopy(source['workflow'][key])
    for record in target['sources']:
        record['classification'] = target['workflow']['classification']
        record['permitted_audiences'] = copy.deepcopy(target['workflow']['allowed_audiences'])
    target['sources'] += copy.deepcopy(source['sources'])
    target['workflow']['unresolved_issues'] = copy.deepcopy(packet['unresolved_issues'])
    basis = {'value': expected_basis(packet, source, target, producer, receiver),
             'source_refs': ['SYNTHETIC-PROJECTION-REVIEW'], 'fact_ids': ['SYNTHETIC-PROJECTION-BASIS']}
    target['sources'].append({'source_ref': basis['source_refs'][0], 'version': 'synthetic/v1',
        'publication_date': source['knowledge_cutoff'], 'received_at': source['knowledge_cutoff'],
        'classification': target['workflow']['classification'],
        'permitted_audiences': copy.deepcopy(target['workflow']['allowed_audiences']),
        'facts': [{'fact_id': basis['fact_ids'][0], 'value': copy.deepcopy(basis['value']),
                   'excerpt': 'Synthetic explicitly supplied review-scope assertion; reviewer authority and semantic sufficiency remain unverified.'}]})
    target['workflow']['sources'] = [{'source_ref': s['source_ref'], 'version': s['version']} for s in target['sources']]
    mappings = [{'target_field': key, 'source': 'supplemental', 'source_pointer': '/receiver/' + key,
        'basis': 'Synthetic retained receiver evidence; human semantic review still required',
        'reviewed_by': 'SYNTHETIC-REVIEWER', 'source_refs': [s['source_ref'] for s in target['sources']]}
        for key in target]
    next(m for m in mappings if m['target_field'] == 'object_id').update(source='source_input', source_pointer='/object_id')
    args = dict(producer=producer, target_skill=receiver, producer_validator=validator(producer),
                receiver_validator=lambda doc: native_validate(package(receiver), doc),
                supplemental_inputs={'receiver': copy.deepcopy(target)})
    return source, out, packet, target, mappings, basis, args


class Phase3IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = [projection_case(*pair) for pair in sorted(PAIRS)]

    def projection(self, case):
        source, out, packet, target, mappings, basis, args = case
        return build_review_projection(packet, source, target, mappings=mappings, projection_basis=basis, **args)

    def test_four_actual_native_packets_and_detached_reconstruction(self):
        for name in SCOPE['new_packages']:
            with self.subTest(name=name):
                doc = fixture(name); out, packet = sourced_packet(name, doc)
                self.assertEqual(validate_packet(packet, doc, producer=name, native_validator=validator(name)), [])
                self.assertFalse(out['action_taken']); self.assertEqual(out['source_truth'], 'unverified')
                self.assertTrue(out['human_review_required'])
                forged = copy.deepcopy(out); forged['authority_granted'] = True
                self.assertTrue(native_validate(package(name), forged, doc))

    def test_catalog_preserves_declared_metadata_without_default_jurisdiction(self):
        from spec_card import card
        rows = {r['name']: r for r in load(ROOT / 'catalog/skills-catalog.json')['skills']}
        for name in SCOPE['new_packages']:
            with self.subTest(name=name):
                actual = yaml.safe_load((package(name) / 'SKILL.md').read_text().split('---', 2)[1])['metadata']
                generated = yaml.safe_load(card(rows[name])[0])['metadata']
                self.assertEqual(generated, {key: actual[key] for key in generated})
                self.assertNotIn('US (default)', generated['aws-fsi-jurisdictions'])

    def test_two_actual_review_pairs_reconstruct_and_keep_unknowns(self):
        for case in self.cases:
            with self.subTest(pair=case[-1]['producer']):
                projection = self.projection(case)
                self.assertEqual(validate_review_projection(projection, case[0], **case[-1]), [])
                result = calculate(case[-1]['target_skill'], projection['target_input'])
                self.assertEqual(native_validate(package(case[-1]['target_skill']), result, projection['target_input']), [])
                self.assertFalse(projection['authority_granted']); self.assertFalse(result['action_taken'])
                self.assertEqual(projection['semantic_evidence_sufficiency'], 'human-review-required')

    def test_original_general_handoff_still_rejects_object_scope_change(self):
        for case in self.cases:
            with self.assertRaises(ValueError):
                build_handoff(case[2], case[0], case[3], mappings=case[4], **case[-1])

    def test_projection_unsupported_pair_rejected(self):
        case = copy.deepcopy(self.cases[0]); case[-1]['target_skill'] = 'sanctions-screening-control-evaluator'
        with self.assertRaisesRegex(ValueError, 'unregistered'):
            self.projection(case)

    def test_review_id_cannot_hide_unrelated_underlying_subject(self):
        for base in self.cases:
            case = copy.deepcopy(base)
            if case[-1]['producer'] == 'transaction-monitoring-scenario-designer':
                claim = case[3]['data']['scope']['scenario_id']
            else:
                claim = case[3]['data']['cases'][0]['upstream_native_id']
            claim['value'] = 'UNRELATED'
            for source in case[3]['sources']:
                for fact in source['facts']:
                    if fact['fact_id'] in claim['fact_ids']: fact['value'] = 'UNRELATED'
            case[-1]['supplemental_inputs']['receiver'] = copy.deepcopy(case[3])
            with self.assertRaisesRegex(ValueError, 'linkage'):
                self.projection(case)

    def test_protected_context_cannot_change_even_with_revised_basis(self):
        for key in ('institution_id', 'legal_entity_id', 'represented_party', 'object_id', 'jurisdiction', 'line_of_business'):
            case = copy.deepcopy(self.cases[0]); case[3]['workflow']['context'][key] = 'OTHER'
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.projection(case)

    def test_temporal_access_and_fact_retention_guards(self):
        for mutation in ('as_of', 'knowledge_cutoff', 'audience', 'classification', 'facts', 'issues', 'versions'):
            case = copy.deepcopy(self.cases[0]); target = case[3]
            if mutation in {'as_of', 'knowledge_cutoff'}: target[mutation] = '2026-10-02'
            elif mutation in {'audience', 'classification'}: target['workflow'][mutation] = 'OTHER'
            elif mutation == 'facts': target['sources'][-2]['facts'][0]['value'] = 'ALTERED'
            elif mutation == 'issues': target['workflow']['unresolved_issues'] = []
            else: target['workflow']['sources'] = target['workflow']['sources'][:1]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.projection(case)

    def test_basis_must_be_exact_sourced_scope_and_versions(self):
        for mutation in ('missing', 'fact', 'role', 'source_hash', 'extra'):
            case = copy.deepcopy(self.cases[0]); basis = case[5]
            if mutation == 'missing': basis['source_refs'] = []
            elif mutation == 'fact': basis['fact_ids'] = ['INVENTED']
            elif mutation == 'role': case[3]['workflow']['role'] = 'internal_audit'
            elif mutation == 'source_hash': basis['value']['source_input_hash'] = 'fabricated'
            else: basis['authority_granted'] = True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.projection(case)

    def test_direct_subject_mapping_and_all_receiver_fields_required(self):
        for mutation in ('indirect', 'missing', 'invented-source', 'wrong-value'):
            case = copy.deepcopy(self.cases[0]); mapping = next(m for m in case[4] if m['target_field'] == 'object_id')
            if mutation == 'indirect': mapping.update(source='supplemental', source_pointer='/receiver/object_id')
            elif mutation == 'missing': case[4].pop()
            elif mutation == 'invented-source': mapping['source_refs'] = ['INVENTED']
            else: case[3]['request_id'] = 'ALTERED'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.projection(case)

    def test_native_forgery_and_projection_tamper_rejected(self):
        for case in self.cases:
            projection = self.projection(case)
            for key, value in [('authority_granted', True), ('execution', 'performed'), ('extra', 'invented')]:
                forged = copy.deepcopy(projection); forged[key] = value
                self.assertTrue(validate_review_projection(forged, case[0], **case[-1]))
            forged = copy.deepcopy(projection); forged['source_packet']['native_output']['action_taken'] = True
            self.assertTrue(validate_review_projection(forged, case[0], **case[-1]))

    def test_actual_projection_cli_build_verify_and_strict_json(self):
        case = self.cases[0]
        with tempfile.TemporaryDirectory(prefix='phase3-cli-') as tmp:
            tmp = Path(tmp)
            values = {'source-input': case[0], 'source-packet': case[2], 'target-input': case[3],
                      'mappings': case[4], 'projection-basis': case[5], 'supplemental': case[-1]['supplemental_inputs']}
            command = [sys.executable, '-B', str(ROUTER / 'scripts/project_review.py'),
                '--source-package', str(package(case[-1]['producer'])),
                '--receiver-package', str(package(case[-1]['target_skill']))]
            for key, value in values.items():
                path = tmp / (key + '.json'); path.write_text(json.dumps(value)); command += ['--' + key, str(path)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            packet_path = tmp / 'projection.json'; packet_path.write_text(result.stdout)
            result = subprocess.run(command + ['--verify', str(packet_path)], capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            path = tmp / 'mappings.json'; path.write_text('{"duplicate":1,"duplicate":2}')
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertNotEqual(result.returncode, 0); self.assertIn('duplicate JSON', result.stdout)


if __name__ == '__main__':
    unittest.main()
