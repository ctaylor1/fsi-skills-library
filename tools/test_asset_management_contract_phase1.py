#!/usr/bin/env python3
"""Independent negative cases for the bounded investment evidence adapter.

No hashes authenticate sources, reviewers or approvals. Tests operate in memory.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('shared/asset-management', 'shared/investment-data', 'shared/workflow-review')]
import investment_contract as c
from workflow_contract import stable_hash

METHOD = {'id': 'synthetic-fixture', 'version': '1', 'implementation_version': '1', 'origin': 'local-analysis'}
PRODUCER = 'fund-fact-sheet-builder'


def request():
    return {
        'native_skill': PRODUCER, 'request_id': 'review-1', 'as_of': '2026-06-30', 'knowledge_cutoff': '2026-06-30',
        'context': {'capacity': 'asset-manager', 'represented_party': 'CLIENT-A', 'object_id': 'FUND-A',
                    'subject_type': 'fund', 'line_of_business': 'asset-management', 'currency': 'USD',
                    'units': 'percentage-points', 'book_basis': 'not-applicable', 'audience': 'internal-review',
                    'jurisdictions': ['US']},
        'sources': [{'source_ref': 'S-1', 'version': '1', 'as_of': '2026-06-30', 'known_at': '2026-06-30',
                     'permitted_use': 'internal-review', 'permitted_audiences': ['internal-review'],
                     'permitted_parties': ['CLIENT-A']}],
        'native_input': {'fund': {'fund_id': 'FUND-A', 'currency': 'USD'}, 'as_of_date': '2026-06-30'},
        'native_identity_pointer': '/fund/fund_id', 'native_as_of_pointer': '/as_of_date',
    }


def packet(req=None, result=None, validator=None):
    return c.build_packet(req or request(), result if result is not None else {'computed': 5}, producer=PRODUCER,
                          method=METHOD, native_validator=validator or (lambda output, source: []))


def rehash(p):
    p['artifact']['output_hash'] = stable_hash({k: v for k, v in p.items() if k != 'artifact'})
    p['artifact']['artifact_hash'] = stable_hash({k: v for k, v in p['artifact'].items() if k != 'artifact_hash'})
    return p


def mapping(p, req):
    return {'reviewed_by': 'synthetic-reviewer', 'basis': 'supplied additional receiver input; not authenticated',
            'source_artifact_hash': p['artifact']['artifact_hash'], 'target_request_hash': c.canonical_hash(req),
            'fields': [{'target_path': '', 'source_ref': 'S-1', 'value_hash': c.canonical_hash(req['native_input'])}]}


def native_module(name, filename):
    path = ROOT / 'skills/asset-management' / name / 'scripts' / filename
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location('contract_test_' + filename.replace('.', '_'), path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


class InvestmentContractPhase1(unittest.TestCase):
    def test_validation_level_requires_explicit_choice(self):
        r = request(); p = packet(r)
        self.assertTrue(c.validate_packet(p))
        self.assertTrue(c.validate_packet(p, r))
        self.assertTrue(c.validate_packet(p, native_validator=lambda out, source: []))
        self.assertEqual([], c.validate_packet(p, integrity_only=True))
        self.assertEqual([], c.validate_packet(p, r, native_validator=lambda out, source: []))
        self.assertTrue(c.validate_packet(p, r, integrity_only=True))
        self.assertTrue(c.validate_packet(p, integrity_only='yes'))

    def test_handoff_requires_detached_source_request_and_native_validator(self):
        r = request(); p = packet(r)
        for source_request, source_validator in [(None, None), (r, None), (None, lambda out, source: [])]:
            with self.subTest(source_request=source_request, source_validator=source_validator), self.assertRaises(ValueError):
                c.make_handoff(p, r, target_skill=PRODUCER, requested_output='review', mapping=mapping(p, r),
                               receiver_validator=lambda native: [], source_request=source_request, source_validator=source_validator)
        different = copy.deepcopy(r); different['native_input']['fund']['fund_id'] = 'OTHER'
        different['context']['object_id'] = 'OTHER'
        self.assertTrue(c.validate_packet(p, different, native_validator=lambda out, source: []))

    def test_rehashed_native_fabrication_fails_actual_source_reconstruction(self):
        native = json.loads((ROOT / 'skills/asset-management/fund-fact-sheet-builder/evals/files/factsheet_intake_example.json').read_text())
        producer_validator = native_module(PRODUCER, 'validate_output.py').validate
        receiver_validator = native_module(PRODUCER, 'validate_input.py').validate
        out = native_module(PRODUCER, 'calculate_or_transform.py').assemble(native)
        r = request(); r['native_input'] = native; r['context']['object_id'] = 'FND-100'
        original = c.build_packet(r, out, producer=PRODUCER, method=METHOD, native_validator=producer_validator)
        self.assertEqual([], c.validate_packet(original, r, native_validator=producer_validator))
        valid_handoff = c.make_handoff(original, r, target_skill=PRODUCER, requested_output='review', mapping=mapping(original, r),
                                      receiver_validator=receiver_validator, source_request=r, source_validator=producer_validator)
        self.assertNotIn('source_request', valid_handoff)
        self.assertEqual([], c.validate_handoff(valid_handoff, target_skill=PRODUCER, receiver_validator=receiver_validator,
                                                source_request=r, source_validator=producer_validator))
        forged = copy.deepcopy(original)
        forged['result']['fabricated_narrative'] = 'The fund guarantees a 50 percent annual return.'
        rehash(forged)
        # Explicit envelope-only validation remains possible and is insufficient.
        self.assertEqual([], c.validate_packet(forged, integrity_only=True))
        self.assertTrue(c.validate_packet(forged))
        self.assertTrue(c.validate_packet(forged, r))
        errors = c.validate_packet(forged, r, native_validator=producer_validator)
        self.assertTrue(any('original-input reconstruction' in error for error in errors))
        with self.assertRaisesRegex(ValueError, 'original-input reconstruction'):
            c.make_handoff(forged, r, target_skill=PRODUCER, requested_output='review', mapping=mapping(forged, r),
                           receiver_validator=receiver_validator, source_request=r, source_validator=producer_validator)
        # Rebuild every transport hash/mapping too: fresh receiving validation must
        # still rerun the producer's native validator against detached evidence.
        transport = c.workflow_handoff(forged['artifact'], target_skill=PRODUCER, target_input=r, requested_output='review')
        transport.update(source_packet=forged, mapping=mapping(forged, r), mapped_target_request=copy.deepcopy(r))
        errors = c.validate_handoff(transport, target_skill=PRODUCER, receiver_validator=receiver_validator,
                                    source_request=r, source_validator=producer_validator)
        self.assertTrue(any('original-input reconstruction' in error for error in errors))

    def test_recomputed_validator_warnings_must_match_packet(self):
        p = packet(); r = request()
        self.assertTrue(c.validate_packet(p, r, native_validator=lambda out, source: ([], ['new material warning'])))

    def test_local_native_work_cannot_claim_external_origin_or_verified_method(self):
        for origin in ('external-analysis', 'supplied-system-of-record'):
            method = dict(METHOD, origin=origin)
            with self.subTest(origin=origin), self.assertRaisesRegex(ValueError, 'separate declared engine adapter'):
                c.build_packet(request(), {'computed': 5}, producer=PRODUCER, method=method, native_validator=lambda out, source: [])
            forged = packet(); forged['method']['origin'] = origin; rehash(forged)
            self.assertTrue(c.validate_packet(forged, integrity_only=True))
        p = packet(); self.assertEqual('caller-declared-unverified', p['method_metadata_assurance'])
        p['method_metadata_assurance'] = 'registry-verified'; rehash(p)
        self.assertTrue(c.validate_packet(p, integrity_only=True))

    def test_valid_packet_and_review_only_handoff(self):
        r = request(); p = packet(r)
        self.assertEqual([], c.validate_request(r)); self.assertEqual([], c.validate_packet(p, r, native_validator=lambda out, source: []))
        h = c.make_handoff(p, r, target_skill=PRODUCER, source_request=r, source_validator=lambda out, source: [], requested_output='review', mapping=mapping(p, r), receiver_validator=lambda native: [])
        self.assertEqual([], c.validate_handoff(h, target_skill=PRODUCER, source_request=r, source_validator=lambda out, source: [], receiver_validator=lambda native: []))
        self.assertFalse(h['authority_granted']); self.assertEqual('review-only', h['action_mode'])
        self.assertEqual('supplied_not_authenticated', p['artifact']['evidence_assurance'])
        self.assertNotIn('native_input', p); self.assertNotIn('source_input', p)

    def test_unknown_producer_and_six_incompatible_native_schemas_blocked(self):
        blocked = {'investment-thesis-monitor', 'investment-committee-memo-builder', 'investment-mandate-reviewer',
                   'counterparty-exposure-monitor', 'research-source-indexer', 'investment-record-normalizer'}
        manifest = c.adapter_manifest()
        self.assertEqual(67, len(manifest)); self.assertEqual(blocked, {k for k, v in manifest.items() if 'blocked_reason' in v})
        for name in blocked | {'invented-producer'}:
            r = request(); r['native_skill'] = name
            self.assertTrue(c.validate_request(r))
            with self.assertRaises(ValueError):
                c.build_packet(r, {}, producer=name, method=METHOD, native_validator=lambda out, source: [])
        manifest[PRODUCER]['identity_pointer'] = '/fake'
        self.assertEqual('/fund/fund_id', c.adapter_manifest()[PRODUCER]['identity_pointer'])

    def test_fake_identity_and_date_pointers_rejected(self):
        for pointer_field, extra, value in [('native_identity_pointer', 'invented_identity', 'OTHER-FUND'),
                                             ('native_as_of_pointer', 'invented_date', '2020-01-01')]:
            r = request(); r['native_input'][extra] = value; r[pointer_field] = '/' + extra
            if pointer_field == 'native_identity_pointer': r['context']['object_id'] = value
            else: r['as_of'] = value
            self.assertTrue(c.validate_request(r))
            with self.assertRaises(ValueError): packet(r)

    def test_native_currency_subject_and_actual_producer_bound(self):
        for field, value in [('currency', 'EUR'), ('subject_type', 'security'), ('object_id', 'FUND-B')]:
            r = request(); r['context'][field] = value
            self.assertTrue(c.validate_request(r))
        r = request(); r['native_skill'] = 'investment-commentary-builder'
        self.assertTrue(c.validate_request(r, producer=PRODUCER))

    def test_real_factsheet_open_items_force_partial(self):
        d = json.loads((ROOT / 'skills/asset-management/fund-fact-sheet-builder/evals/files/factsheet_intake_example.json').read_text())
        out = native_module(PRODUCER, 'calculate_or_transform.py').assemble(d)
        self.assertGreater(len(out['sections']['open_items']), 0)
        r = request(); r['native_input'] = d; r['context']['object_id'] = 'FND-100'
        p = c.build_packet(r, out, producer=PRODUCER, method=METHOD,
                           native_validator=native_module(PRODUCER, 'validate_output.py').validate)
        self.assertEqual([], c.validate_packet(p, r, native_validator=native_module(PRODUCER, 'validate_output.py').validate))
        self.assertEqual('partial', p['artifact']['completeness']); self.assertEqual('partial', p['artifact']['evaluability'])
        self.assertTrue(any('/open_items' in issue for issue in p['artifact']['unresolved_issues']))
        d['forged_subject'] = 'OTHER-FUND'; r['native_identity_pointer'] = '/forged_subject'; r['context']['object_id'] = 'OTHER-FUND'
        with self.assertRaises(ValueError):
            c.build_packet(r, native_module(PRODUCER, 'calculate_or_transform.py').assemble(d), producer=PRODUCER,
                           method=METHOD, native_validator=native_module(PRODUCER, 'validate_output.py').validate)

    def test_compound_status_and_domain_gaps_retained(self):
        cases = [{'sections': {'open_items': [{'detail': 'missing figure'}]}},
                 {'responses': [{'status': 'unapproved-source'}]}, {'responses': [{'status': 'data-gap'}]},
                 {'status': 'stale'}, {'evaluation_gaps': ['zero EPS baseline']},
                 {'data_quality_gaps': ['future engagement']}, {'source_reference_resolved': False},
                 {'unsupported_claims': ['unsupported narrative']}, {'reconciled': False}]
        for native in cases:
            with self.subTest(native=native):
                p = packet(result=native)
                self.assertEqual('partial', p['artifact']['completeness'])
                self.assertTrue(p['artifact']['unresolved_issues']); self.assertEqual([], c.validate_packet(p, integrity_only=True))

    def test_promoted_completeness_fails_even_with_recomputed_hashes(self):
        p = packet(result={'status': 'incomplete'})
        for field, promoted in [('completeness', 'complete'), ('evaluability', 'evaluable')]:
            bad = copy.deepcopy(p); bad['artifact'][field] = promoted; rehash(bad)
            self.assertTrue(c.validate_packet(bad, integrity_only=True)); self.assertTrue(c.validate_packet(bad, request(), native_validator=lambda out, source: []))

    def test_native_validator_warnings_retained_and_type_checked(self):
        p = packet(validator=lambda out, source: ([], ['material source coverage warning']))
        self.assertEqual(['material source coverage warning'], p['native_validation_warnings'])
        self.assertEqual('partial', p['artifact']['completeness']); self.assertEqual([], c.validate_packet(p, integrity_only=True))
        for response in [(), ([],), ([], [], []), ([], {}), None, {'errors': []}, [False]]:
            with self.subTest(response=response), self.assertRaises(ValueError):
                packet(validator=lambda out, source: response)

    def test_native_validator_rejection_and_failure_do_not_build(self):
        with self.assertRaises(ValueError): packet(validator=lambda out, source: ['native mismatch'])
        def broken(out, source): raise RuntimeError('not evaluable')
        with self.assertRaises(ValueError): packet(validator=broken)

    def test_future_known_at_rejected_but_known_forecast_economic_date_allowed(self):
        r = request(); r['sources'][0]['known_at'] = '2026-07-01'
        self.assertTrue(c.validate_request(r))
        p = packet(); p['artifact']['sources'][0]['known_at'] = '2026-07-01'; rehash(p)
        self.assertTrue(c.validate_packet(p, integrity_only=True))
        r = request(); r['sources'][0]['as_of'] = '2027-01-01'
        self.assertEqual([], c.validate_request(r))  # Forecast economic date is not knowledge date.

    def test_supplied_audience_and_party_restrictions_enforced(self):
        for field, value in [('permitted_audiences', ['external']), ('permitted_parties', ['CLIENT-B'])]:
            r = request(); r['sources'][0][field] = value
            self.assertTrue(c.validate_request(r))
            p = packet(); p['artifact']['sources'][0][field] = value; rehash(p)
            self.assertTrue(c.validate_packet(p, integrity_only=True))
        r = request(); r['context']['audience'] = 'client'
        self.assertTrue(c.validate_request(r))

    def test_source_restriction_cannot_be_overridden_by_context_mapping(self):
        p = packet(); target = request(); target['context']['represented_party'] = 'CLIENT-B'
        target['sources'][0]['permitted_parties'] = ['CLIENT-B']
        m = mapping(p, target); m['context_mapping'] = {'source': p['artifact']['context'], 'target': target['context'], 'basis': 'reviewer says okay'}
        self.assertTrue(c.validate_mapping(p, target, m))

    def test_direct_upstream_injection_does_not_bypass_cutoff_or_rights(self):
        p = packet(); r = request()
        r['context']['represented_party'] = 'CLIENT-B'; r['sources'][0]['permitted_parties'] = ['CLIENT-B']
        r['upstream_artifacts'] = [p['artifact']]
        self.assertTrue(c.validate_request(r))
        r = request(); r['knowledge_cutoff'] = '2026-06-29'; r['sources'][0]['known_at'] = '2026-06-29'
        r['upstream_artifacts'] = [p['artifact']]
        self.assertTrue(c.validate_request(r))

    def test_backward_cutoff_or_asof_handoff_rejected(self):
        p = packet()
        for field in ('knowledge_cutoff', 'as_of'):
            r = request(); r[field] = '2026-06-29'
            if field == 'as_of': r['native_input']['as_of_date'] = r[field]
            r['sources'][0]['known_at'] = '2026-06-29'
            self.assertTrue(c.validate_mapping(p, r, mapping(p, r)))

    def test_handoff_inherits_issues_and_invokes_native_receiver(self):
        p = packet(result={'evaluation_gaps': ['not measurable']}); r = request(); calls = []
        def receiver(native): calls.append(copy.deepcopy(native)); return []
        h = c.make_handoff(p, r, target_skill=PRODUCER, source_request=r, source_validator=lambda out, source: [], requested_output='review', mapping=mapping(p, r), receiver_validator=receiver)
        self.assertEqual([r['native_input']], calls)
        self.assertEqual(p['artifact']['unresolved_issues'], h['target_input']['unresolved_issues'])
        self.assertTrue(c.validate_handoff(h, target_skill=PRODUCER, source_request=r, source_validator=lambda out, source: [], receiver_validator=lambda native: ['missing receiver field']))
        h['target_input']['unresolved_issues'] = []; h['target_input_hash'] = c.canonical_hash(h['target_input'])
        self.assertTrue(c.validate_handoff(h, target_skill=PRODUCER, source_request=r, source_validator=lambda out, source: [], receiver_validator=receiver))

    def test_changed_receiver_native_input_cannot_be_rehashed_away(self):
        p = packet(); r = request()
        h = c.make_handoff(p, r, target_skill=PRODUCER, source_request=r, source_validator=lambda out, source: [], requested_output='review', mapping=mapping(p, r), receiver_validator=lambda native: [])
        h['target_input']['native_input']['fund']['fund_id'] = 'OTHER'
        h['target_input_hash'] = c.canonical_hash(h['target_input'])
        self.assertTrue(c.validate_handoff(h, target_skill=PRODUCER, source_request=r, source_validator=lambda out, source: [], receiver_validator=lambda native: []))

    def test_mapping_must_cover_fields_and_copy_exact_values(self):
        p = packet(result={'id': 'FUND-B'}); r = request(); m = mapping(p, r)
        m['fields'] = [{'target_path': '/fund/fund_id', 'source_path': '/result/id'}]
        errors = c.validate_mapping(p, r, m)
        self.assertTrue(any('mapped field differs' in e for e in errors)); self.assertTrue(any('unmapped receiver' in e for e in errors))

    def test_json_pointer_negative_or_noncanonical_indices_rejected(self):
        for path in ('/-1', '/01', '/+0', '/0~2'):
            with self.assertRaises((ValueError, KeyError)): c.pointer(['A'], path)
        self.assertEqual('A', c.pointer(['A'], '/0'))
        self.assertEqual(7, c.pointer({'a/b': {'~key': 7}}, '/a~1b/~0key'))

    def test_merged_modes_have_distinct_authoritative_bindings(self):
        r = request(); r['native_skill'] = 'proxy-voting-reviewer'
        r['native_input'] = {'mode': 'policy', 'input': {'mandate_id': 'MANDATE-A', 'as_of': '2026-06-30'}}
        r['native_identity_pointer'] = '/input/mandate_id'; r['native_as_of_pointer'] = '/input/as_of'
        r['context'].update(object_id='MANDATE-A', subject_type='mandate')
        self.assertEqual([], c.validate_request(r))
        r['native_input']['mode'] = 'evidence'
        self.assertTrue(c.validate_request(r))

    def test_malformed_public_validator_inputs_return_errors(self):
        r = request(); p = packet(); m = mapping(p, r)
        bad_values = [None, [], '', 4, True, {}, {'bad': 'shape'}]
        for bad in bad_values:
            with self.subTest(value=bad):
                self.assertTrue(c.validate_request(bad)); self.assertTrue(c.validate_packet(bad, integrity_only=True))
                self.assertTrue(c.validate_mapping(p, r, bad))
                self.assertTrue(c.validate_handoff(bad, target_skill=PRODUCER, source_request=r, source_validator=lambda out, source: [], receiver_validator=lambda native: []))
        for field in ('context', 'sources', 'native_input', 'upstream_artifacts', 'unresolved_issues', 'native_skill'):
            for bad in bad_values:
                doc = request(); doc[field] = bad
                self.assertIsInstance(c.validate_request(doc), list)
        for field in ('subject_type', 'audience', 'jurisdictions'):
            doc = request(); doc['context'][field] = []
            self.assertTrue(c.validate_request(doc))
        for field in ('context', 'unresolved_issues', 'sources', 'producer'):
            doc = packet(); doc['artifact'][field] = [{}]
            self.assertTrue(c.validate_packet(doc, integrity_only=True))
        for field in ('fields', 'context_mapping'):
            bad = copy.deepcopy(m); bad[field] = None
            target = copy.deepcopy(r)
            if field == 'context_mapping': target['context']['units'] = 'different'
            self.assertTrue(c.validate_mapping(p, target, bad))

    def test_nonfinite_values_and_authority_claims_rejected(self):
        r = request(); r['native_input']['extra'] = float('nan'); self.assertTrue(c.validate_request(r))
        p = packet(); p['result']['x'] = float('inf'); self.assertTrue(c.validate_packet(p, integrity_only=True))
        for key, value in [('action_taken', True), ('human_review_required', False), ('delivery_status', 'sent')]:
            p = packet(); p[key] = value; rehash(p); self.assertTrue(c.validate_packet(p, integrity_only=True))


if __name__ == '__main__':
    unittest.main(verbosity=2)
