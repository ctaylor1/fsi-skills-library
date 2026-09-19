import json
from pathlib import Path
import unittest
from copy import deepcopy
import domain
from payment_foundation import build, validate_request, validate_output

class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((Path(__file__).resolve().parents[1] / 'evals/files/request.json').read_text())
    def run_model(self):
        return build(self.request, domain)
    def test_coverage_is_specific_and_has_sequence(self):
        r = self.run_model()['result']
        self.assertEqual(r['options'][0]['review_state'], 'ready-for-human-option-review')
        self.assertEqual(len(r['options'][0]['coverage_matrix']), 2)
        self.assertEqual(len(r['implementation_sequence']), 4)
        self.assertIsNone(r['selected_option'])
        self.assertIsNone(r['options'][0]['conversion_uplift'])
    def test_proposal_does_not_establish_support(self):
        self.request['data']['options'][0]['coverage'][0]['evidence_kind'] = 'proposal'
        self.assertEqual(self.run_model()['result']['options'][0]['review_state'], 'evidence-gated')
    def test_currency_mismatch_is_gap(self):
        self.request['data']['segments'][0]['currency'] = 'EUR'
        self.assertEqual(self.run_model()['status'], 'needs-evidence')
    def test_recurring_requires_specific_support(self):
        self.request['data']['segments'][0]['use_case'] = 'recurring'
        self.assertEqual(self.run_model()['status'], 'needs-evidence')
    def test_entity_eligibility_is_not_inferred(self):
        del self.request['data']['options'][0]['coverage'][0]['entity_eligible']
        self.assertEqual(self.run_model()['status'], 'needs-evidence')
    def test_missing_method_coverage_not_zero(self):
        self.request['data']['options'][0]['coverage'].pop()
        row = self.run_model()['result']['options'][0]['coverage_matrix'][1]
        self.assertEqual(row['status'], 'unknown')
        self.assertFalse(row['ready_for_option_review'])
    def test_responsibilities_are_required(self):
        del self.request['data']['options'][0]['responsibilities']['refunds']
        self.assertEqual(self.run_model()['status'], 'needs-evidence')
    def test_mandatory_constraints_gate(self):
        self.request['data']['options'][0]['constraints'][0]['status'] = 'unsupported'
        self.assertEqual(self.run_model()['status'], 'needs-evidence')
    def test_duplicate_coverage_rejected(self):
        self.request['data']['options'][0]['coverage'].append(deepcopy(self.request['data']['options'][0]['coverage'][0]))
        self.assertTrue(validate_request(self.request, domain))
    def test_unsupported_market_has_gap(self):
        self.request['data']['segments'][0]['market'] = 'BR'
        self.assertEqual(self.run_model()['status'], 'needs-evidence')
    def test_unsupported_request_no_analysis(self):
        self.request['jurisdiction'] = 'BR'
        self.assertEqual(self.run_model()['status'], 'unsupported')
        self.assertEqual(self.run_model()['result'], {})
    def test_stale_coverage_cannot_clear_option_gates(self):
        self.request['sources'][1]['review_due'] = '2026-01-01'
        self.assertEqual(self.run_model()['result']['options'][0]['review_state'], 'evidence-gated')
    def test_sources_and_outputs_bound(self):
        self.request['sources'][0]['review_due'] = '2025-01-01'
        output = self.run_model()
        self.assertEqual(output['status'], 'needs-evidence')
        output['result']['selected_option'] = 'two-method-psp'
        self.assertTrue(validate_output(output, domain))
    def test_upstream_and_execution_boundaries(self):
        self.request['upstream_issues'] = [{'code':'legal-review','message':'Open country review','source_ids':['merchant-brief']}]
        output = self.run_model()
        self.assertEqual(output['status'], 'needs-evidence')
        self.assertFalse(output['authority_granted'])
        self.request['requested_action'] = 'execute'
        self.assertTrue(validate_request(self.request, domain))

if __name__ == '__main__':
    unittest.main()
