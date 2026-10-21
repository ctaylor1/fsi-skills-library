"""Actual installed Phase2 producers/receivers and detached handoff regressions."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import unittest

from test_compliance_phase1 import (ROOT, package, calculate, load, native_validate,
    build_packet, validate_packet, build_handoff, validate_handoff)

SCOPE = load(ROOT / 'catalog/compliance-financial-crime-phase2-capabilities.json')
NAMES = list(SCOPE['new_packages']) + list(SCOPE['expanded_packages'])


def fixture(name):
    folder = package(name) / 'evals/files'
    for filename in ('phase2_input.json', 'input_complete.json', 'input.json'):
        if (folder / filename).exists():
            return load(folder / filename)
    raise ValueError('actual Phase2 fixture missing: ' + name)


def validator(name):
    return lambda out, doc: native_validate(package(name), out, doc)


def sourced_packet(name, doc):
    out = calculate(name, doc)
    packet = build_packet(doc, out, producer=name, native_validator=validator(name))
    return out, packet


def separate_registry(doc):
    """Give independent receiver fixture evidence distinct IDs before merging it."""
    def walk(item):
        if isinstance(item, dict):
            for key, value in item.items():
                if key in {'source_ref', 'fact_id'} and isinstance(value, str):
                    item[key] = 'receiver-' + value
                elif key in {'source_refs', 'fact_ids'} and isinstance(value, list):
                    item[key] = ['receiver-' + v for v in value]
                else:
                    walk(value)
        elif isinstance(item, list):
            for value in item:
                walk(value)
    walk(doc)
    return doc


def lifecycle_handoff():
    source = fixture('customer-due-diligence-reviewer')
    out, packet = sourced_packet('customer-due-diligence-reviewer', source)
    target = separate_registry(fixture('enhanced-due-diligence-assessor'))
    target['sources'] += copy.deepcopy(source['sources'])
    target['workflow'] = copy.deepcopy(source['workflow'])
    target['workflow']['sources'] = [{'source_ref': s['source_ref'], 'version': s['version']} for s in target['sources']]
    target['workflow']['unresolved_issues'] = copy.deepcopy(packet['unresolved_issues'])
    supplemental = {'receiver': copy.deepcopy(target)}
    mappings = [{'target_field': key, 'source': 'supplemental', 'source_pointer': '/receiver/' + key,
        'basis': 'Synthetic separately retained receiver evidence; no authenticated reviewer or authority implied',
        'reviewed_by': 'SYNTHETIC-MAPPING-REVIEWER', 'source_refs': [s['source_ref'] for s in target['sources']]}
        for key in target]
    args = dict(producer='customer-due-diligence-reviewer', target_skill='enhanced-due-diligence-assessor',
        producer_validator=validator('customer-due-diligence-reviewer'),
        receiver_validator=lambda doc: native_validate(package('enhanced-due-diligence-assessor'), doc),
        supplemental_inputs=supplemental)
    return source, out, packet, target, mappings, args


class Phase2HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = lifecycle_handoff()

    def setUp(self):
        self.source, self.out, self.packet, self.target, self.mappings, self.args = copy.deepcopy(self.base)

    def handoff(self):
        return build_handoff(self.packet, self.source, self.target, mappings=self.mappings, **self.args)

    def refresh_supplemental(self):
        self.args['supplemental_inputs']['receiver'] = copy.deepcopy(self.target)

    def test_all_21_actual_native_modes_accept_registered_packet(self):
        for name in NAMES:
            with self.subTest(name=name):
                doc = fixture(name); out, packet = sourced_packet(name, doc)
                self.assertEqual(validate_packet(packet, doc, producer=name, native_validator=validator(name)), [])
                self.assertFalse(out['action_taken']); self.assertTrue(out['human_review_required'])
                self.assertEqual(out['source_truth'], 'unverified')
                self.assertEqual(packet['artifact']['completeness'], 'partial')

    def test_actual_customer_lifecycle_to_substantive_edd_preserves_sources_and_issues(self):
        handoff = self.handoff()
        self.assertEqual(validate_handoff(handoff, self.source, **self.args), [])
        result = calculate('enhanced-due-diligence-assessor', handoff['target_input'])
        self.assertEqual(native_validate(package('enhanced-due-diligence-assessor'), result, handoff['target_input']), [])
        self.assertFalse(handoff['authority_granted']); self.assertFalse(result['action_taken'])
        self.assertEqual(result['source_truth'], 'unverified')

    def test_declared_source_version_cannot_hide_changed_fact(self):
        self.target['sources'][-1]['facts'][0]['value'] = 'fabricated-but-same-version'
        self.refresh_supplemental()
        with self.assertRaisesRegex(ValueError, 'detached source facts'):
            self.handoff()

    def test_receiver_cannot_drop_detached_source_facts(self):
        self.target['sources'][-1]['facts'] = []
        self.refresh_supplemental()
        with self.assertRaisesRegex(ValueError, 'detached source facts'):
            self.handoff()

    def test_receiver_cannot_change_knowledge_cutoff(self):
        self.target['knowledge_cutoff'] = '2026-10-02'
        self.refresh_supplemental()
        with self.assertRaisesRegex(ValueError, 'knowledge-cutoff'):
            self.handoff()

    def test_receiver_cannot_drop_open_issues(self):
        self.target['workflow']['unresolved_issues'] = []
        self.refresh_supplemental()
        with self.assertRaisesRegex(ValueError, 'dropped'):
            self.handoff()

    def test_mapping_sources_must_be_real_detached_registry_records(self):
        self.mappings[0]['source_refs'] = ['invented-source']
        with self.assertRaisesRegex(ValueError, 'outside receiver'):
            self.handoff()

    def test_mapping_changed_field_fails_even_with_valid_native_input(self):
        self.target['request_id'] = 'DIFFERENT-REQUEST'
        with self.assertRaisesRegex(ValueError, 'differs from mapped source'):
            self.handoff()

    def test_cross_customer_or_audience_requires_reviewed_projection(self):
        for key, value in [('object_id', 'OTHER-CUSTOMER'), ('audience', 'external-customer')]:
            with self.subTest(key=key):
                self.setUp()
                if key == 'object_id':
                    self.target[key] = value; self.target['workflow']['context'][key] = value
                else:
                    self.target['workflow']['audience'] = value
                    self.target['workflow']['allowed_audiences'].append(value)
                    for source in self.target['sources']:
                        source['permitted_audiences'].append(value)
                self.refresh_supplemental()
                with self.assertRaisesRegex(ValueError, 'cross-context|audience/classification'):
                    self.handoff()

    def test_rehashed_native_forgery_is_not_a_valid_packet(self):
        self.packet['native_output']['reportability'] = 'not-reportable'
        self.assertTrue(validate_packet(self.packet, self.source, producer='customer-due-diligence-reviewer', native_validator=validator('customer-due-diligence-reviewer')))

    def test_detached_original_and_native_context_remain_bound(self):
        altered = copy.deepcopy(self.source); altered['workflow']['context']['legal_entity_id'] = 'OTHER-ENTITY'
        self.assertTrue(validate_packet(self.packet, altered, producer='customer-due-diligence-reviewer', native_validator=validator('customer-due-diligence-reviewer')))


if __name__ == '__main__':
    unittest.main()
