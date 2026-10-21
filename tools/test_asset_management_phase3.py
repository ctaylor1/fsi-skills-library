"""Actual AM modernization producers, detached shared owners and native handoffs."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_asset_management_foundations_phase2 import wrap, compute, packet, native_validate, c, BASE
from native_integrity import canonical_hash

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['investment-data-architecture-planner', 'investment-platform-modernization-planner',
         'investment-operating-model-planner', 'investment-ai-workflow-designer']


def fixture(name):
    filename = 'request.json' if name == 'investment-data-architecture-planner' else 'input.json'
    return json.loads((BASE / name / 'evals/files' / filename).read_text())


class ModernizationIntegration(unittest.TestCase):
    def test_four_actual_producers_and_native_validators(self):
        for name in NAMES:
            with self.subTest(skill=name):
                request = wrap(name, fixture(name))
                result = packet(name, request)
                self.assertEqual([], c.validate_packet(result, request, native_validator=lambda o,i: native_validate(BASE/name, o,i)))
                self.assertFalse(result['action_taken'])
                self.assertEqual(result['result']['source_truth'], 'unverified')

    def test_shared_output_tampering_rejected_by_each_actual_producer(self):
        for name in NAMES:
            with self.subTest(skill=name):
                doc = fixture(name)
                pair = next(iter(doc['shared_reviews'].values()))
                pair['output']['results']['invented_approval'] = True
                with self.assertRaises(ValueError): compute(name, doc)

    def test_shared_source_versions_and_native_scope_cannot_be_relabelled(self):
        for name in NAMES:
            for kind in ['version', 'object', 'currency']:
                with self.subTest(skill=name, kind=kind):
                    doc = fixture(name)
                    pair = next(iter(doc['shared_reviews'].values()))
                    if kind == 'version':
                        ref = pair['input']['sources'][0]['source_ref']
                        next(s for s in doc['sources'] if s['source_ref'] == ref)['version'] = 'invented'
                    elif kind == 'object': doc['object_id'] = 'OTHER-MANAGER'
                    else: doc['currency'] = 'EUR'
                    with self.assertRaises(ValueError): compute(name, doc)

    def test_actual_platform_to_operating_receiver_mapping(self):
        source_name, target_name = NAMES[1], NAMES[2]
        source_doc = fixture(source_name)
        target_doc = fixture(target_name)
        # A new source-bound target review carries an explicit object mapping;
        # this does not amend either retained original's business facts.
        source = wrap(source_name, source_doc)
        target = wrap(target_name, target_doc)
        source['context']['subject_type'] = target['context']['subject_type'] = 'platform'
        result = packet(source_name, source)
        fields = [{'target_path': path, 'source_ref': target['sources'][0]['source_ref'],
                   'value_hash': canonical_hash(c.pointer(target_doc, path))} for path in sorted(c._leaves(target_doc))]
        mapping = dict(reviewed_by='synthetic transition owner', basis='Independently supplied target service inventory; explicit related platform-to-operating review mapping.',
                       source_artifact_hash=result['artifact']['artifact_hash'], target_request_hash=canonical_hash(target), fields=fields,
                       context_mapping=dict(source=source['context'], target=target['context'], basis='Synthetic relationship of platform migration review to retained operating service evidence; no implicit data conversion.'))
        args = dict(target_skill=target_name, requested_output='Internal source-linked operating-model draft', mapping=mapping,
                    receiver_validator=lambda d: native_validate(BASE/target_name,d), source_request=source,
                    source_validator=lambda o,i: native_validate(BASE/source_name,o,i))
        handoff = c.make_handoff(result, target, **args)
        self.assertEqual([], c.validate_handoff(handoff, target_skill=target_name, receiver_validator=args['receiver_validator'],
                                               source_request=source, source_validator=args['source_validator']))
        output = compute(target_name, handoff['target_input']['native_input'])
        self.assertFalse(output['results']['operating_change_authorized'])
        self.assertIn('Independent source confirmation remains outstanding.', handoff['target_input']['unresolved_issues'])
        corrupted = copy.deepcopy(target)
        corrupted['native_input']['controls'][0]['service_id'] = 'unknown-service'
        bad_mapping = copy.deepcopy(mapping)
        bad_mapping['target_request_hash'] = canonical_hash(corrupted)
        for row in bad_mapping['fields']:
            row['value_hash'] = canonical_hash(c.pointer(corrupted['native_input'], row['target_path']))
        with self.assertRaises(ValueError): c.make_handoff(result, corrupted, **{**args, 'mapping': bad_mapping})


if __name__ == '__main__': unittest.main()
