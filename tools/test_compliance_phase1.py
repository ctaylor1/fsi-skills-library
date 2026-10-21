"""Integrated Phase1 native binding and common handoff regressions."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / 'skills/compliance-financial-crime/compliance-financial-crime-router'
sys.path.insert(0, str(ROUTER / 'scripts'))
from cfc_contract import build_packet, validate_packet, build_handoff, validate_handoff
from native_runner import native_validate
from workflow_contract import build_artifact
from native_integrity import canonical_hash


def load(path):
    return json.loads(path.read_text())


def package(name):
    paths = list((ROOT / 'skills').glob('*/' + name + '/SKILL.md'))
    if len(paths) != 1:
        raise ValueError('missing/ambiguous package ' + name)
    return paths[0].parent


def calculate(name, doc):
    with tempfile.TemporaryDirectory(prefix='cfc-test-') as temp:
        original = Path(temp) / 'input.json'; original.write_text(json.dumps(doc))
        result = subprocess.run([sys.executable, '-B', 'scripts/calculate_or_transform.py', str(original)],
                                cwd=package(name), capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError(result.stdout + result.stderr)
    return json.loads(result.stdout)


def original_fixture(name, filename):
    return load(package(name) / 'evals/files' / filename)


def make_sources():
    source = original_fixture('customer-due-diligence-reviewer', 'case_example.json')
    target = original_fixture('enhanced-due-diligence-assessor', 'edd_case_example.json')
    source['workflow'] = {'context': {'institution_id': 'SYNTHETIC-FI', 'legal_entity_id': 'SYNTHETIC-ENTITY',
        'capacity': 'customer_due_diligence', 'represented_party': 'SYNTHETIC-FI',
        'object_id': source['customer']['customer_id'], 'object_type': 'customer',
        'jurisdiction': 'US', 'line_of_business': 'synthetic-banking', 'purpose': 'CDD evidence review'},
        'as_of': source['as_of'], 'role': 'control_operator', 'classification': 'customer_pii',
        'audience': 'authorized_cdd', 'allowed_audiences': ['authorized_cdd'],
        'sources': [{'source_ref': 'SYNTHETIC-CDDCASERECORD', 'version': 'test-1'}],
        'unresolved_issues': ['SYNTHETIC: independent identity corroboration remains unresolved.']}
    target['customer']['customer_id'] = source['customer']['customer_id']
    target['as_of'] = source['as_of']
    output = calculate('customer-due-diligence-reviewer', source)
    validator = lambda out, doc: native_validate(package('customer-due-diligence-reviewer'), out, doc)
    packet = build_packet(source, output, producer='customer-due-diligence-reviewer', native_validator=validator)
    target['workflow'] = copy.deepcopy(source['workflow'])
    target['workflow']['unresolved_issues'] = list(packet['unresolved_issues'])
    supplemental = {'reviewed_receiver_evidence': copy.deepcopy(target)}
    mappings = [{'target_field': key, 'source': 'supplemental',
                 'source_pointer': '/reviewed_receiver_evidence/' + key,
                 'basis': 'Synthetic reviewed fixture field; no institutional approval claimed',
                 'reviewed_by': 'SYNTHETIC-MAPPING-REVIEWER', 'source_refs': ['SYNTHETIC-EDD-RECORD']}
                for key in target]
    return source, output, packet, target, supplemental, mappings


class ComplianceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = make_sources()

    def setUp(self):
        self.source, self.output, self.packet, self.target, self.supplemental, self.mappings = copy.deepcopy(self.base)
        self.kwargs = dict(producer='customer-due-diligence-reviewer', target_skill='enhanced-due-diligence-assessor',
            producer_validator=lambda out, doc: native_validate(package('customer-due-diligence-reviewer'), out, doc),
            receiver_validator=lambda doc: native_validate(package('enhanced-due-diligence-assessor'), doc),
            supplemental_inputs=self.supplemental)

    def handoff(self):
        return build_handoff(self.packet, self.source, self.target, mappings=self.mappings, **self.kwargs)

    def test_real_producer_and_receiver_accept_scoped_handoff(self):
        handoff = self.handoff()
        self.assertEqual(validate_handoff(handoff, self.source, **self.kwargs), [])
        self.assertFalse(handoff['authority_granted'])
        self.assertTrue(set(self.packet['unresolved_issues']).issubset(handoff['target_input']['workflow']['unresolved_issues']))
        self.assertNotIn('source_input', handoff)

    def test_native_limitations_survive_into_common_contract(self):
        self.assertTrue(any('Native evidence limitation' in issue for issue in self.packet['unresolved_issues']))
        self.target['workflow']['unresolved_issues'] = []
        with self.assertRaisesRegex(ValueError, 'dropped'):
            self.handoff()

    def test_rehashed_fabricated_native_payload_rejected(self):
        self.packet['native_output']['recommended_track'] = 'Standard-CDD'
        # Rebuild valid superficial envelope hashes around the forged result.
        w = self.packet['workflow']; meta = {k: w[k] for k in ('context', 'as_of', 'sources')}
        meta['unresolved_issues'] = self.packet['unresolved_issues']
        self.packet['artifact'] = build_artifact(meta, self.packet, producer='customer-due-diligence-reviewer',
            artifact_type='compliance-review', completeness='partial', evaluability='partial', issues=self.packet['unresolved_issues'])
        self.assertTrue(validate_packet(self.packet, self.source, producer='customer-due-diligence-reviewer',
                                       native_validator=self.kwargs['producer_validator']))

    def test_wrong_original_input_rejected(self):
        self.source['customer']['customer_id'] = 'SYNTHETIC-DIFFERENT'
        with self.assertRaises(ValueError):
            self.handoff()

    def test_cross_subject_context_cannot_be_asserted(self):
        self.target['customer']['customer_id'] = 'OTHER'
        self.target['workflow']['context']['object_id'] = 'OTHER'
        with self.assertRaisesRegex(ValueError, 'cross-context'):
            self.handoff()

    def test_context_must_match_native_identity(self):
        self.target['workflow']['context']['object_id'] = 'OTHER'
        with self.assertRaisesRegex(ValueError, 'native identity'):
            self.handoff()

    def test_audience_change_rejected(self):
        self.target['workflow']['audience'] = 'external_customer'
        self.target['workflow']['allowed_audiences'].append('external_customer')
        with self.assertRaisesRegex(ValueError, 'audience/classification'):
            self.handoff()

    def test_receiver_cannot_drop_producer_source_provenance(self):
        self.target['workflow']['sources'] = [{'source_ref': 'DIFFERENT', 'version': 'test-1'}]
        self.supplemental['reviewed_receiver_evidence'] = copy.deepcopy(self.target)
        with self.assertRaisesRegex(ValueError, 'dropped source provenance'):
            self.handoff()

    def test_receiver_data_cannot_be_invented_or_unmapped(self):
        self.target['customer']['customer_id'] = self.source['customer']['customer_id']
        self.target['case_id'] = 'INVENTED'
        with self.assertRaisesRegex(ValueError, 'differs from mapped source'):
            self.handoff()

    def test_every_receiver_field_needs_mapping(self):
        self.mappings.pop()
        with self.assertRaisesRegex(ValueError, 'every receiver-native field'):
            self.handoff()

    def test_real_receiver_rejects_bad_native_input(self):
        del self.target['customer']
        self.supplemental['reviewed_receiver_evidence'] = copy.deepcopy(self.target)
        self.mappings = [m for m in self.mappings if m['target_field'] != 'customer']
        with self.assertRaises((ValueError, KeyError)):
            self.handoff()

    def test_source_original_and_receiver_issues_are_not_approval(self):
        handoff = self.handoff(); handoff['authority_granted'] = True
        self.assertTrue(validate_handoff(handoff, self.source, **self.kwargs))
        self.assertEqual(self.packet['approval'], 'not_requested')
        self.assertEqual(self.packet['artifact']['evidence_assurance'], 'supplied_not_authenticated')

    def test_supplemental_sources_are_bound_detached(self):
        handoff = self.handoff()
        self.supplemental['reviewed_receiver_evidence']['case_id'] = 'OTHER'
        self.assertTrue(validate_handoff(handoff, self.source, **self.kwargs))

    def test_missing_adapter_fails_instead_of_guessing(self):
        with self.assertRaisesRegex(ValueError, 'batch identity'):
            build_packet(self.source, self.output, producer='aml-alert-triager', native_validator=lambda out, doc: [])

    def test_extra_packet_fields_fail(self):
        self.packet['external_message'] = 'Unexpected disclosure'
        self.assertTrue(validate_packet(self.packet, self.source, producer='customer-due-diligence-reviewer',
                                       native_validator=self.kwargs['producer_validator']))


if __name__ == '__main__':
    unittest.main()
