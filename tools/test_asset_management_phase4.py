"""Phase4 native reconstruction, specialist adapters and reviewed draft handoffs.

These tests exercise real package entry points. They establish bounded software
behavior, not source truth, professional acceptance or deployment readiness.
"""
import copy
import json
from pathlib import Path
import unittest

from test_asset_management_foundations_phase2 import (
    BASE, c, compute, native_validate, packet, wrap,
)
from native_integrity import canonical_hash
from specialist_contract import review_engine

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'portfolio-transition-planner': ['transition.json'],
    'securities-financing-reviewer': ['financing.json'],
    'private-fund-financing-reviewer': ['phase4-subscription.json', 'phase4-nav.json'],
    'private-fund-restructuring-reviewer': ['phase4-secondary.json', 'phase4-continuation.json'],
    'tokenized-fund-operations-reviewer': ['request.json'],
    'sustainability-mandate-reviewer': ['request.json'],
    'portfolio-hedge-reviewer': ['advanced_derivatives.json'],
    'portfolio-performance-attributor': [
        'phase4-fixed-income-input.json', 'phase4-factor-input.json',
        'phase4-currency-input.json', 'phase4-linking-input.json',
    ],
    'systematic-investment-research-reviewer': ['phase4-walk-forward-input.json'],
    'etf-operations-reviewer': ['phase4-specialized-basket-input.json', 'phase4-engine-forward-input.json'],
    'institutional-investment-solutions-planner': ['phase4-liabilities.json'],
    'investment-regulatory-obligation-reviewer': ['jurisdiction_request.json'],
}
EXTENSIONS = {
    'portfolio-hedge-reviewer': 'advanced-derivatives',
    'portfolio-performance-attributor': 'specialist-attribution',
    'systematic-investment-research-reviewer': 'walk-forward',
    'etf-operations-reviewer': 'specialized-basket',
    'institutional-investment-solutions-planner': 'liability-real-assets',
    'investment-regulatory-obligation-reviewer': 'jurisdiction-profile-comparison',
}
LEGACY = {
    'portfolio-hedge-reviewer': [('hedge_input_example.json', 'hedge_packet_example.json')],
    'portfolio-performance-attributor': [('attribution_intake_example.json', 'attribution_example.json')],
    'systematic-investment-research-reviewer': [('request.json', 'result.json')],
    'etf-operations-reviewer': [('basket_control_input.json', 'basket_control_expected.json'),
                                ('secondary_market_input.json', 'secondary_market_expected.json')],
    'institutional-investment-solutions-planner': [('request.json', 'result.json')],
    'investment-regulatory-obligation-reviewer': [('input.json', None)],
}


def fixture(name, filename=None):
    return json.loads((BASE / name / 'evals/files' / (filename or FILES[name][0])).read_text())


def checker(name):
    return lambda output, original: native_validate(BASE / name, output, original)


def replace_pointer(doc, path, value):
    parts = [p.replace('~1', '/').replace('~0', '~') for p in path.split('/')[1:]]
    node = doc
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    node[int(parts[-1]) if isinstance(node, list) else parts[-1]] = value


def rehash(result):
    """Recompute integrity metadata without asserting that invented facts are true."""
    result['artifact']['output_hash'] = canonical_hash({k: v for k, v in result.items() if k != 'artifact'})
    result['artifact']['artifact_hash'] = canonical_hash({k: v for k, v in result['artifact'].items() if k != 'artifact_hash'})


def governance_handoff():
    """A held fund mandate review informs a separately supplied manager review.

    Only date/currency context is copied. Jurisdiction applicability is determined
    from the receiver's independently supplied profiles, never the ESG result.
    """
    source_name = 'sustainability-mandate-reviewer'
    target_name = 'investment-regulatory-obligation-reviewer'
    source = wrap(source_name, fixture(source_name, 'request_breach.json'))
    target = wrap(target_name, fixture(target_name))
    result = packet(source_name, source)
    copies = {path: '/result' + path for path in ('/as_of', '/knowledge_cutoff', '/currency')}
    fields = []
    for path in sorted(c._leaves(target['native_input'])):
        row = {'target_path': path}
        if path in copies:
            row['source_path'] = copies[path]
        else:
            row.update(source_ref=target['sources'][0]['source_ref'],
                       value_hash=canonical_hash(c.pointer(target['native_input'], path)))
        fields.append(row)
    mapping = dict(
        reviewed_by='synthetic governance reviewer',
        basis='Carry the dated fund mandate exception to its manager review; independently supply every jurisdiction profile and entity fact. No compliance conclusion is inherited.',
        source_artifact_hash=result['artifact']['artifact_hash'],
        target_request_hash=canonical_hash(target), fields=fields,
        context_mapping=dict(source=source['context'], target=target['context'],
                             basis='Explicit synthetic fund mandate to manager relationship; distinct scopes remain visible.'),
    )
    args = dict(target_skill=target_name, requested_output='Draft source-linked jurisdiction comparison for human review',
                mapping=mapping, receiver_validator=lambda doc: native_validate(BASE / target_name, doc),
                source_request=source, source_validator=checker(source_name))
    handoff = c.make_handoff(result, target, **args)
    return source, result, target, mapping, handoff, args


class SpecialistIntegration(unittest.TestCase):
    def test_all_six_new_and_six_expanded_actual_native_producers(self):
        manifest = json.loads((ROOT / 'catalog/asset-management-phase4-capabilities.json').read_text())
        self.assertEqual(6, len(manifest['new_packages']))
        self.assertEqual(6, len(manifest['expanded_packages']))
        self.assertEqual(set(FILES), set(manifest['new_packages']) | set(manifest['expanded_packages']))
        self.assertEqual(18, sum(map(len, FILES.values())))
        for name, filenames in FILES.items():
            for filename in filenames:
                with self.subTest(skill=name, fixture=filename):
                    doc = fixture(name, filename)
                    self.assertEqual([], native_validate(BASE / name, doc))
                    request = wrap(name, doc)
                    result = packet(name, request)
                    self.assertEqual([], c.validate_packet(result, request, native_validator=checker(name)))
                    self.assertEqual(canonical_hash(doc), result['result']['input_hash'])
                    self.assertFalse(result['action_taken'])
                    self.assertFalse(result['result']['action_taken'])
                    self.assertTrue(result['result']['human_review_required'])
                    self.assertEqual('unverified', result['result']['source_truth'])
                    self.assertEqual('local-analysis', result['method']['origin'])

    def test_extension_registry_is_explicit_and_outputs_resolve_to_foundation(self):
        manifest = json.loads((ROOT / 'catalog/asset-management-phase4-capabilities.json').read_text())
        self.assertEqual(EXTENSIONS, {name: row['extension'] for name, row in manifest['expanded_packages'].items()})
        for name, extension in EXTENSIONS.items():
            with self.subTest(skill=name):
                doc = fixture(name)
                self.assertEqual(extension, doc['extension'])
                self.assertEqual([extension], c.NATIVE_ADAPTERS[name]['foundation_extensions'])
                adapter = c._resolve_adapter(name, doc)
                self.assertEqual('/object_id', adapter['identity_pointer'])
                self.assertEqual('/as_of', adapter['as_of_pointer'])
                self.assertEqual(adapter, c._resolve_adapter(name, compute(name, doc)))

    def test_unknown_extensions_do_not_fall_through_to_legacy(self):
        for name in EXTENSIONS:
            for filename in (FILES[name][0], LEGACY[name][0][0]):
                with self.subTest(skill=name, fixture=filename):
                    doc = fixture(name, filename)
                    doc['extension'] = 'unregistered-specialist-method'
                    with self.assertRaises(ValueError):
                        c._resolve_adapter(name, doc)
                    self.assertTrue(native_validate(BASE / name, doc))
                    with self.assertRaises(ValueError):
                        compute(name, doc)

    def test_legacy_inputs_outputs_and_old_identity_pointers_are_preserved(self):
        for name, pairs in LEGACY.items():
            for filename, golden in pairs:
                with self.subTest(skill=name, fixture=filename):
                    doc = fixture(name, filename)
                    self.assertNotIn('extension', doc)
                    self.assertEqual([], native_validate(BASE / name, doc))
                    output = compute(name, doc)
                    self.assertEqual([], native_validate(BASE / name, output, doc))
                    if golden:
                        self.assertEqual(fixture(name, golden), output)
                    else:
                        for path, expected in fixture(name, 'independent-expectations.json').items():
                            self.assertEqual(expected, c.pointer(output['results'], '/' + path.replace('.', '/')))
                    expected_pointer = {'portfolio-hedge-reviewer': '/portfolio/id',
                                        'portfolio-performance-attributor': '/portfolio_id'}.get(name, '/object_id')
                    self.assertEqual(expected_pointer, c._resolve_adapter(name, doc)['identity_pointer'])

    def test_every_wrapper_binds_scope_dates_units_and_source_metadata(self):
        changes = [
            ('/context/object_id', 'OTHER-FUND'), ('/context/subject_type', 'insurance-policy'),
            ('/context/currency', 'JPY'), ('/context/units', 'USD-millions'),
            ('/as_of', '2026-10-03'), ('/knowledge_cutoff', '2026-12-01'),
            ('/context/audience', 'public'), ('/native_identity_pointer', '/request_id'),
            ('/sources/0/version', 'fabricated-version'), ('/sources/0/as_of', '2026-01-01'),
            ('/sources/0/known_at', '2026-01-01'),
            ('/sources/0/permitted_audiences', ['internal-review', 'public']),
            ('/sources/0/permitted_parties', ['SYNTHETIC-FIRM', 'OTHER-FIRM']),
        ]
        for name in FILES:
            doc = fixture(name)
            doc['sources'][0]['permitted_audiences'] = ['internal-review']
            doc['sources'][0]['permitted_parties'] = ['SYNTHETIC-FIRM']
            request = wrap(name, doc)
            self.assertEqual([], c.validate_request(request))
            for path, value in changes:
                with self.subTest(skill=name, path=path):
                    bad = copy.deepcopy(request)
                    replace_pointer(bad, path, value)
                    self.assertTrue(c.validate_request(bad))

    def test_rehashed_invented_results_fail_detached_native_reconstruction(self):
        for name in FILES:
            with self.subTest(skill=name):
                request = wrap(name, fixture(name))
                result = packet(name, request)
                bad = copy.deepcopy(result)
                # Change an existing business-result leaf, not the safety envelope.
                path = next(p for p in sorted(c._leaves(bad['result']['results']))
                            if isinstance(c.pointer(bad['result']['results'], p), str))
                replace_pointer(bad['result']['results'], path, 'fabricated-result')
                rehash(bad)
                self.assertEqual([], c.validate_packet(bad, integrity_only=True))
                self.assertTrue(c.validate_packet(bad, request, native_validator=checker(name)))
                self.assertTrue(c.validate_packet(result))
                changed_original = copy.deepcopy(request)
                changed_original['native_input']['unresolved_issues'].append('New detached material exception')
                self.assertTrue(c.validate_packet(result, changed_original, native_validator=checker(name)))

    def test_fractional_json_numbers_rejected_in_every_phase4_schema(self):
        paths = {
            'portfolio-transition-planner': '/initial_settled_cash',
            'securities-financing-reviewer': '/available_funding_cash',
            'private-fund-financing-reviewer': '/facility/interest_rate',
            'private-fund-restructuring-reviewer': '/transaction/reference_nav',
            'tokenized-fund-operations-reviewer': '/fund/official_issued_units',
            'sustainability-mandate-reviewer': '/observations/0/value',
            'portfolio-hedge-reviewer': '/engine_result/values/0/value',
            'portfolio-performance-attributor': '/tolerance',
            'systematic-investment-research-reviewer': '/embargo_days',
            'etf-operations-reviewer': '/transaction_fee',
            'institutional-investment-solutions-planner': '/opening_cash',
            # This schema is categorical. Even extra supplied quantitative facts
            # must preserve their lexical precision rather than escape the guard.
            'investment-regulatory-obligation-reviewer': '/review_scopes/0/supplied_materiality',
        }
        for name, path in paths.items():
            for filename in FILES[name]:
                with self.subTest(skill=name, fixture=filename):
                    doc = fixture(name, filename)
                    replace_pointer(doc, path, 0.12345678901234567890123456789)
                    errors = native_validate(BASE / name, doc)
                    self.assertTrue(errors)
                    self.assertIn('decimal strings or integers', ' '.join(errors))
                    with self.assertRaises(ValueError):
                        compute(name, doc)

    def test_actual_new_to_extended_handoff_preserves_native_exception(self):
        source, result, target, mapping, handoff, args = governance_handoff()
        self.assertTrue(result['result']['unresolved_issues'])
        self.assertEqual([], c.validate_handoff(handoff, target_skill=args['target_skill'],
                         receiver_validator=args['receiver_validator'], source_request=source,
                         source_validator=args['source_validator']))
        for issue in result['unresolved_issues']:
            self.assertIn(issue, handoff['target_input']['unresolved_issues'])
        output = compute(args['target_skill'], handoff['target_input']['native_input'])
        self.assertEqual([], native_validate(BASE / args['target_skill'], output, target['native_input']))
        self.assertFalse(output['action_taken'])
        self.assertEqual('unverified', output['source_truth'])
        self.assertNotEqual(source['context']['object_id'], target['context']['object_id'])
        self.assertEqual(source['context'], mapping['context_mapping']['source'])

    def test_handoff_needs_context_review_complete_mapping_and_real_receiver(self):
        source, result, target, mapping, handoff, args = governance_handoff()
        for mutation in ('no-context-review', 'unmapped-field', 'invalid-native-profile', 'changed-currency'):
            with self.subTest(mutation=mutation):
                bad_target, bad_map = copy.deepcopy(target), copy.deepcopy(mapping)
                if mutation == 'no-context-review':
                    del bad_map['context_mapping']
                elif mutation == 'unmapped-field':
                    bad_map['fields'] = [row for row in bad_map['fields'] if row['target_path'] != '/currency']
                elif mutation == 'changed-currency':
                    bad_target['native_input']['currency'] = bad_target['context']['currency'] = 'EUR'
                    bad_map['context_mapping']['target'] = copy.deepcopy(bad_target['context'])
                else:
                    bad_target['native_input']['jurisdiction_profiles'][0]['primary_authority']['source_ref'] = 'UNREGISTERED'
                    for row in bad_map['fields']:
                        if 'value_hash' in row:
                            row['value_hash'] = canonical_hash(c.pointer(bad_target['native_input'], row['target_path']))
                bad_map['target_request_hash'] = canonical_hash(bad_target)
                with self.assertRaises(ValueError):
                    c.make_handoff(result, bad_target, **{**args, 'mapping': bad_map})

    def test_handoff_rejects_rehashed_fabricated_upstream_clearance(self):
        source, result, target, mapping, handoff, args = governance_handoff()
        forged = copy.deepcopy(result)
        forged['result']['results']['exclusions'][0]['status'] = 'no-breach-in-supplied-scope'
        rehash(forged)
        forged_map = copy.deepcopy(mapping)
        forged_map['source_artifact_hash'] = forged['artifact']['artifact_hash']
        self.assertEqual([], c.validate_packet(forged, integrity_only=True))
        with self.assertRaises(ValueError):
            c.make_handoff(forged, target, **{**args, 'mapping': forged_map})

    def test_engine_pins_scope_hash_coverage_units_and_chronology(self):
        name = 'portfolio-hedge-reviewer'
        changes = [
            ('/engine_request/model_version', 'latest'),
            ('/engine_request/input/volatility_snapshot', 'different-snapshot'),
            ('/engine_request/currency', 'EUR'), ('/engine_result/object_id', 'OTHER'),
            ('/engine_result/model_version', 'different-model'),
            ('/engine_result/request_hash', '0' * 64),
            ('/engine_result/observed_on', '2026-10-03'),
            ('/engine_result/observed_on', '2026-10-05'),
            ('/engine_result/values/0/unit', 'USD-thousands'),
            ('/engine_result/values/0/id', 'unrequested-metric'),
            ('/independent_benchmark/independent_from_engine', False),
            ('/independent_benchmark/source_ref', 'engine-result'),
            ('/independent_benchmark/values/0/tolerance', '-.01'),
        ]
        for path, value in changes:
            with self.subTest(path=path, value=value):
                doc = fixture(name)
                replace_pointer(doc, path, value)
                with self.assertRaises(ValueError):
                    review_engine(doc, doc['engine_request'], doc['engine_result'], doc['independent_benchmark'])
                self.assertTrue(native_validate(BASE / name, doc))

    def test_engine_missing_partial_or_failed_challenge_never_falls_back(self):
        name = 'portfolio-hedge-reviewer'
        for mutation in ('missing-result', 'missing-benchmark', 'partial-result', 'failed-benchmark', 'unresolved-model-limit'):
            with self.subTest(mutation=mutation):
                doc = fixture(name)
                if mutation == 'missing-result': doc['engine_result'] = None
                elif mutation == 'missing-benchmark': doc['independent_benchmark'] = None
                elif mutation == 'partial-result': doc['engine_result']['status'] = 'partial'
                elif mutation == 'failed-benchmark': doc['independent_benchmark']['values'][0]['value'] = '200'
                else: doc['engine_result']['unresolved_issues'] = ['Calibration exception remains open']
                result = review_engine(doc, doc['engine_request'], doc['engine_result'], doc['independent_benchmark'])
                self.assertIsNone(result['values'])
                self.assertFalse(result['eligible_for_review'])
                self.assertFalse(result['engine_invoked'])
                self.assertFalse(result['engine_approval_authenticated'])
                self.assertFalse(result['benchmark_independence_authenticated'])
                output = compute(name, doc)
                self.assertEqual([], native_validate(BASE / name, output, doc))
                self.assertTrue(output['unresolved_issues'])
                self.assertFalse(output['action_taken'])

    def test_matching_supplied_engine_does_not_authenticate_or_change_origin(self):
        name = 'portfolio-hedge-reviewer'
        doc = fixture(name)
        result = review_engine(doc, doc['engine_request'], doc['engine_result'], doc['independent_benchmark'])
        self.assertTrue(result['eligible_for_review'])
        self.assertFalse(result['engine_invoked'])
        self.assertFalse(result['engine_approval_authenticated'])
        self.assertFalse(result['benchmark_independence_authenticated'])
        request = wrap(name, doc)
        output = compute(name, doc)
        method = dict(output['method'], implementation_version='0.1.0', origin='approved-engine')
        with self.assertRaises(ValueError):
            c.build_packet(request, output, producer=name, method=method, native_validator=checker(name))


if __name__ == '__main__':
    unittest.main()
