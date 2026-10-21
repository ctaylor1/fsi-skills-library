#!/usr/bin/env python3
"""Exercise declared routing against the installed native input validators.

The matrix probes every common subject type through each public validator; it
does not infer native support from the route metadata it is checking. Synthetic
identity edits retain issuer context and update hashes on retained model inputs.
Routing remains a method suggestion, never evidence that execution took place.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBJECT_TYPES = (
    'issuer', 'security', 'universe', 'sector', 'economy', 'document',
    'model', 'research_project', 'portfolio', 'fund', 'client',
    'transaction', 'agent', 'workflow',
)
PROFILE_CASES = {
    'financial-statement-analyzer': ('issuer_profile', ('nonfinancial-corporate',), ('issuer_profile',)),
    'earnings-quality-analyzer': ('issuer_profile', ('nonfinancial-corporate',), ('issuer_profile',)),
    'three-statement-model-builder': ('issuer_type', ('nonfinancial-corporate',), ('issuer_type',)),
    'financial-model-update-preparer': ('issuer_type', ('nonfinancial-corporate',), ('original_model.issuer_type',)),
    'dcf-modeler': ('issuer_type', ('nonfinancial-corporate',), ('issuer_type',)),
    'comps-analysis-builder': ('issuer_type', ('nonfinancial-corporate', 'bank', 'insurer', 'reit'), ('issuer_type',)),
    'dividend-residual-income-modeler': ('issuer_type', ('bank', 'insurer', 'nonfinancial-corporate'), ('issuer_type',)),
    'scenario-sensitivity-generator': ('issuer_type', ('nonfinancial-corporate',), ('base_input.issuer_type',)),
    'issuer-credit-researcher': ('issuer_profile', ('nonfinancial-corporate',), ('issuer_profile',)),
    'issuer-credit-surveillance-reviewer': ('issuer_profile', ('nonfinancial-corporate',), ('issuer_profile',)),
    'structured-credit-researcher': ('structured_credit_profile', ('single-period-sequential-pay-v1',), ('reviewed_terms.profile',)),
}


def read(path):
    return json.loads(path.read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def fixture(package):
    files = package / 'evals/files'
    for name in ('phase2-input.json', 'phase2_input.json', 'input.json'):
        if (files / name).is_file():
            return read(files / name)
    raise ValueError('No current native fixture for ' + package.name)


@contextmanager
def native_validator(package):
    """Load the real public dispatcher without leaking another package's helpers."""
    scripts = package / 'scripts'
    shared_names = ('domain', 'phase2_domain', 'validate_input', 'analysis_contract',
                    'research_runtime', 'native_integrity')
    previous = {key: sys.modules.pop(key) for key in shared_names if key in sys.modules}
    path = list(sys.path)
    sys.path.insert(0, str(scripts))
    try:
        spec = importlib.util.spec_from_file_location('_route_contract_' + package.name.replace('-', '_'),
                                                     scripts / 'validate_input.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module.validate
    finally:
        sys.path[:] = path
        for key in shared_names:
            sys.modules.pop(key, None)
        sys.modules.update(previous)


def subject_case(original, kind):
    """Change only the requested subject basis, preserving the economic identity."""
    doc = copy.deepcopy(original)
    old = original['subject']
    issuer = old.get('issuer_id', old['id'])
    security = original.get('valuation_subject', {}).get('security_id', old['id'])
    if 'obligations' in original:
        security = next((row['security_id'] for row in original['obligations']
                         if row.get('scope') == 'direct'), security)
    subject = {'type': kind, 'id': security if kind == 'security' else old['id']}
    if kind == 'security':
        subject['issuer_id'] = issuer
    doc['subject'] = subject
    if 'original_model' in doc:
        doc['original_model']['subject'] = copy.deepcopy(subject)
        doc['original_model_hash'] = digest(doc['original_model'])
        doc['observed_current']['input_hash'] = doc['original_model_hash']
    if 'base_input' in doc:
        doc['base_input']['subject'] = copy.deepcopy(subject)
    return doc


def profile_case(original, path, value):
    doc = copy.deepcopy(original)
    target = doc
    parts = path.split('.')
    for part in parts[:-1]:
        target = target[part]
    if value is None:
        target.pop(parts[-1], None)
    else:
        target[parts[-1]] = value
    if path.startswith('original_model.'):
        if 'issuer_type' in doc:
            if value is None:
                doc.pop('issuer_type')
            else:
                doc['issuer_type'] = value
        doc['original_model_hash'] = digest(doc['original_model'])
        doc['observed_current']['input_hash'] = doc['original_model_hash']
    return doc


def routing_request(native, spec, profiles):
    return {
        'request_id': 'native-routing-contract-parity',
        'purpose': native['purpose'], 'audience': native['audience'],
        'subject': copy.deepcopy(native['subject']), 'as_of': native['as_of'],
        'knowledge_cutoff': native['knowledge_cutoff'], 'intents': [spec['intent']],
        'profiles': profiles, 'available_skills': [spec['target']], 'requested_action': 'route',
    }


def contract_parity_errors(root=ROOT, *, routes=None, caps=None):
    """Read-only guard used both by this regression suite and the library check."""
    routes = read(root / 'catalog/investment-research-routes.json') if routes is None else routes
    caps = read(root / 'catalog/investment-research-capabilities.json') if caps is None else caps
    route_by_target = {row['target']: row for row in routes['routes']}
    errors = []
    for cap in caps['capabilities']:
        if cap['support_status'] == 'planned':
            continue
        package = root / cap['path']
        native = fixture(package)
        spec = route_by_target.get(cap['name'])
        if spec is None:
            errors.append('Missing native route: ' + cap['name'])
            continue
        with native_validator(package) as validate:
            base_errors, _ = validate(copy.deepcopy(native))
            if base_errors:
                errors.append('Native routing fixture invalid: ' + cap['name'] + ': ' + '; '.join(base_errors))
                continue
            supported = set()
            for kind in SUBJECT_TYPES:
                findings, _ = validate(subject_case(native, kind))
                if not findings:
                    supported.add(kind)
            if set(spec['subject_types']) != supported:
                errors.append('Native/router subject drift: ' + cap['name'] +
                              ': native=' + ','.join(sorted(supported)) +
                              '; route=' + ','.join(sorted(spec['subject_types'])))
            expected_profile = PROFILE_CASES.get(cap['name'])
            selector = cap.get('required_profile')
            if expected_profile is None:
                if selector:
                    errors.append('Unreviewed profile restriction: ' + cap['name'])
            else:
                field, values, paths = expected_profile
                if (not selector or selector.get('field') != field or
                        set(selector.get('values', [])) != set(values) or
                        selector.get('native_paths') != list(paths)):
                    errors.append('Native/router profile drift: ' + cap['name'])
                for value in values:
                    if cap['name'] == 'comps-analysis-builder' and value == 'nonfinancial-corporate':
                        candidate = read(package / 'evals/files/comps_intake_example.json')
                    else:
                        candidate = profile_case(native, paths[0], value)
                        if cap['name'] == 'comps-analysis-builder':
                            candidate['multiple'] = 'P/FFO' if value == 'reit' else 'P/B'
                    findings, _ = validate(candidate)
                    if findings:
                        errors.append('Declared profile rejected natively: ' + cap['name'] + ':' + value)
                for value in (None, 'unimplemented-profile'):
                    findings, _ = validate(profile_case(native, paths[0], value))
                    if not findings:
                        errors.append('Native profile restriction drift: ' + cap['name'] + ':' + str(value))
    return errors


class RouteNativeContractParity(unittest.TestCase):
    def setUp(self):
        self.routes = read(ROOT / 'catalog/investment-research-routes.json')
        self.caps = read(ROOT / 'catalog/investment-research-capabilities.json')
        self.cap_by_name = {row['name']: row for row in self.caps['capabilities']}
        self.spec_by_name = {row['target']: row for row in self.routes['routes']}
        with native_validator(ROOT / 'skills/investment-research/investment-research-router'):
            self.route = sys.modules['research_runtime'].route

    def route_one(self, name, native, profiles):
        output = self.route(routing_request(native, self.spec_by_name[name], profiles), self.routes, self.caps)
        self.assertFalse(output['workflow_completed'])
        self.assertFalse(output['action_taken'])
        self.assertFalse(output['authority_granted'])
        return output['routes'][0]

    def test_all_42_native_subject_contracts_match_declared_routes(self):
        self.assertEqual(len(self.caps['capabilities']), 42)
        self.assertEqual(contract_parity_errors(), [])

    def test_router_bundles_match_canonical_contracts(self):
        refs = ROOT / 'skills/investment-research/investment-research-router/references'
        self.assertEqual(read(refs / 'routes.json'), self.routes)
        self.assertEqual(read(refs / 'capabilities.json'), self.caps)

    def test_guard_detects_subject_and_profile_metadata_regressions(self):
        routes = copy.deepcopy(self.routes)
        next(row for row in routes['routes'] if row['target'] == 'research-coverage-planner')['subject_types'].append('client')
        self.assertTrue(any('subject drift: research-coverage-planner' in error
                            for error in contract_parity_errors(routes=routes)))
        routes = copy.deepcopy(self.routes)
        next(row for row in routes['routes'] if row['target'] == 'research-quality-reviewer')['subject_types'].remove('economy')
        self.assertTrue(any('subject drift: research-quality-reviewer' in error
                            for error in contract_parity_errors(routes=routes)))
        for name, mutation in (('financial-statement-analyzer', 'missing'),
                               ('issuer-credit-surveillance-reviewer', 'wrong-field')):
            caps = copy.deepcopy(self.caps)
            cap = next(row for row in caps['capabilities'] if row['name'] == name)
            if mutation == 'missing':
                cap.pop('required_profile')
            else:
                cap['required_profile']['field'] = 'issuer_type'
            self.assertTrue(any('profile drift: ' + name in error
                                for error in contract_parity_errors(caps=caps)))

    def test_native_supported_broader_subjects_route_without_execution(self):
        cases = {
            'research-coverage-planner': ('universe', 'sector'),
            'research-universe-screener': ('sector',),
            'research-financial-model-reviewer': ('model',),
            'research-quality-reviewer': SUBJECT_TYPES,
            'investment-research-router': SUBJECT_TYPES,
        }
        for name, kinds in cases.items():
            package = ROOT / self.cap_by_name[name]['path']
            original = fixture(package)
            with native_validator(package) as validate:
                for kind in kinds:
                    with self.subTest(name=name, kind=kind):
                        native = subject_case(original, kind)
                        self.assertEqual(validate(native)[0], [])
                        self.assertEqual(self.route_one(name, native, {})['status'], 'routed-native-only')

    def test_corporate_and_dividend_profile_routes_match_native_validation(self):
        for name, (field, values, paths) in PROFILE_CASES.items():
            if name == 'comps-analysis-builder':
                continue  # Its two schema modes are exercised separately below.
            package = ROOT / self.cap_by_name[name]['path']
            original = fixture(package)
            with native_validator(package) as validate:
                for value in values:
                    with self.subTest(name=name, profile=value):
                        native = profile_case(original, paths[0], value)
                        self.assertEqual(validate(native)[0], [])
                        self.assertEqual(self.route_one(name, native, {field: value})['status'], 'routed-native-only')
                for value in ('bank' if values == ('nonfinancial-corporate',) else 'reit', 'unknown', None):
                    with self.subTest(name=name, unsupported=value):
                        native = profile_case(original, paths[0], value)
                        self.assertTrue(validate(native)[0])
                        profiles = {} if value is None else {field: value}
                        expected = 'needs-scope-clarification' if value is None else 'unsupported-method-profile'
                        self.assertEqual(self.route_one(name, original, profiles)['status'], expected)
                wrong = 'issuer_type' if field == 'issuer_profile' else 'issuer_profile'
                self.assertEqual(self.route_one(name, original, {wrong: values[0]})['status'], 'needs-scope-clarification')

    def test_comps_preserves_legacy_corporate_and_specialist_modes(self):
        name = 'comps-analysis-builder'
        package = ROOT / self.cap_by_name[name]['path']
        original = fixture(package)
        with native_validator(package) as validate:
            for value, multiple in (('bank', 'P/B'), ('insurer', 'P/B'), ('reit', 'P/FFO')):
                native = profile_case(original, 'issuer_type', value)
                native['multiple'] = multiple
                self.assertEqual(validate(native)[0], [], value)
                self.assertEqual(self.route_one(name, native, {'issuer_type': value})['status'], 'routed-native-only')
            legacy = read(package / 'evals/files/comps_intake_example.json')
            self.assertEqual(validate(legacy)[0], [])
            # Legacy native subjects use their own company intake. The router's
            # typed issuer request selects that mode; it does not convert it.
            self.assertEqual(self.route_one(name, original, {'issuer_type': 'nonfinancial-corporate'})['status'], 'routed-native-only')
            for value in ('sovereign', 'unknown'):
                self.assertEqual(self.route_one(name, original, {'issuer_type': value})['status'], 'unsupported-method-profile')

    def test_model_reviewer_preserves_legacy_parity_mode(self):
        name = 'research-financial-model-reviewer'
        package = ROOT / self.cap_by_name[name]['path']
        legacy = {'mode': 'legacy-roll-forward', 'input': read(package / 'evals/files/model_example.json')}
        with native_validator(package) as validate:
            self.assertEqual(validate(legacy)[0], [])
        self.assertEqual(self.route_one(name, subject_case(fixture(package), 'model'), {})['status'], 'routed-native-only')

    def test_router_declines_native_unsupported_subjects(self):
        for name, kind in (('financial-statement-analyzer', 'economy'),
                           ('structured-credit-researcher', 'issuer'),
                           ('research-universe-screener', 'issuer')):
            package = ROOT / self.cap_by_name[name]['path']
            native = subject_case(fixture(package), kind)
            with native_validator(package) as validate:
                self.assertTrue(validate(native)[0])
            self.assertEqual(self.route_one(name, native, {})['status'], 'needs-scope-clarification')


if __name__ == '__main__':
    unittest.main()
