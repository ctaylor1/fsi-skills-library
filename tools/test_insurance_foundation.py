"""Shared implementation invariants, not domain professional acceptance."""
import copy
from decimal import Decimal
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'shared/insurance'))
from insurance_contract import build_artifact, stable_hash
from insurance_foundation import check_output, number, profile_issues, run, sources_for, validate_base


def request():
    return {'case_id': 'CASE', 'as_of': '2026-09-18',
            'context': {'capacity': 'carrier', 'represented_party': 'INSURER', 'object_id': 'POLICY',
                        'jurisdiction': 'US-NY', 'line_of_business': 'pc'},
            'sources': [{'source_ref': 'S1', 'version': 'v1', 'as_of': '2026-09-18'}],
            'unresolved_issues': [], 'data': {'amount': '5.15'}}


def evaluate(doc):
    return {'status': 'ready-for-review', 'findings': [], 'results': {'amount': number(doc['data']['amount'])},
            'completeness': 'complete', 'evaluability': 'evaluable'}


class FoundationTests(unittest.TestCase):
    def test_decimal_unknown_and_invalid_values(self):
        self.assertEqual(number('0'), Decimal('0'))
        self.assertIsNone(number(None))
        for value in (True, False, 'NaN', float('inf'), '', [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                number(value)

    def test_recompute_rejects_resealed_amount_and_identity(self):
        doc = request()
        out = run(doc, 'test', evaluate)
        self.assertEqual(check_output(out, 'test', evaluate), [])
        for field, value in [('case_id', 'OTHER'), ('action_taken', True), ('results', {'amount': '7.00'})]:
            changed = copy.deepcopy(out)
            changed[field] = value
            changed['artifact'] = build_artifact(doc, changed, producer='test', artifact_type='insurance-workflow-review')
            self.assertTrue(check_output(changed, 'test', evaluate))

    def test_upstream_unknown_stays_partial(self):
        doc = request()
        upstream_input = copy.deepcopy(doc)
        upstream_input['unresolved_issues'] = ['beneficiary conflict not resolved']
        upstream = run(upstream_input, 'upstream', evaluate)['artifact']
        doc['upstream_artifacts'] = [upstream]
        out = run(doc, 'test', evaluate)
        self.assertEqual(out['status'], 'needs-data')
        self.assertIn('beneficiary conflict not resolved', out['unresolved_issues'])
        self.assertEqual(out['artifact']['completeness'], 'partial')

    def test_unknown_context_and_future_sources_not_ready(self):
        for key in ('context', 'source'):
            doc = request()
            if key == 'context':
                doc['context']['jurisdiction'] = 'unknown'
            else:
                doc['sources'][0]['as_of'] = '2026-09-19'
            out = run(doc, 'test', evaluate)
            self.assertEqual(out['status'], 'needs-data')

    def test_unrelated_upstream_requires_source_bound_reviewed_mapping(self):
        doc = request()
        upstream_doc = copy.deepcopy(doc)
        upstream_doc['context']['object_id'] = 'ANOTHER-POLICY'
        upstream = run(upstream_doc, 'upstream', evaluate)['artifact']
        doc['upstream_artifacts'] = [upstream]
        self.assertEqual(run(doc, 'test', evaluate)['status'], 'needs-data')
        mapping = {'source_artifact_hash': stable_hash(upstream),
                   'source_context': upstream['context'], 'target_context': doc['context'],
                   'reviewed_by': 'Synthetic reviewer', 'basis': 'Documented policy identity migration',
                   'source_refs': ['S1']}
        doc['context_mappings'] = [mapping]
        self.assertEqual(run(doc, 'test', evaluate)['status'], 'ready-for-review')
        mapping['source_artifact_hash'] = 'unrelated'
        self.assertEqual(run(doc, 'test', evaluate)['status'], 'needs-data')

    def test_future_upstream_cannot_support_current_review(self):
        doc = request()
        upstream_doc = copy.deepcopy(doc)
        upstream_doc['as_of'] = '2026-09-19'
        doc['upstream_artifacts'] = [run(upstream_doc, 'upstream', evaluate)['artifact']]
        self.assertEqual(run(doc, 'test', evaluate)['status'], 'needs-data')

    def test_duplicate_sources_and_invalid_calendar_reject(self):
        doc = request()
        doc['sources'] *= 2
        self.assertTrue(validate_base(doc))
        doc = request()
        doc['as_of'] = '2026-02-30'
        self.assertTrue(validate_base(doc))

    def test_evaluator_cannot_mutate_retained_source(self):
        def mutator(doc):
            doc['data']['amount'] = '10'
            return evaluate(doc)
        doc = request()
        out = run(doc, 'test', mutator)
        self.assertEqual(doc['data']['amount'], '5.15')
        self.assertEqual(out['source_document'], doc)

    def test_scope_and_evidence_profile(self):
        doc = request()
        p = {'profile_id': 'P', 'version': 'v1', 'source_refs': ['S1'],
             'effective_from': '2026-01-01', 'effective_to': '2026-12-31',
             'jurisdictions': ['US-NY'], 'lines_of_business': ['pc']}
        self.assertEqual(profile_issues(doc, p), [])
        for field, value in [('effective_to', '2026-09-17'), ('jurisdictions', ['US-CA']),
                             ('source_refs', ['missing']), ('lines_of_business', ['life'])]:
            changed = dict(p, **{field: value})
            self.assertTrue(profile_issues(doc, changed))
        self.assertTrue(sources_for(doc, []))

    def test_domain_validator_is_called(self):
        with self.assertRaisesRegex(ValueError, 'bad domain'):
            run(request(), 'test', evaluate, lambda doc: ['bad domain'])


if __name__ == '__main__':
    unittest.main()
