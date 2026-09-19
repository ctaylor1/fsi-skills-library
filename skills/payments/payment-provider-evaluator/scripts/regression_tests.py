import json
from pathlib import Path
import unittest
from copy import deepcopy
import domain
from payment_foundation import build, validate_request, validate_output

class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((Path(__file__).resolve().parents[1] / 'evals/files/request.json').read_text())
    def run_model(self):
        return build(self.request, domain)
    def test_mandatory_unknown_not_offset_by_score(self):
        r = self.run_model()['result']
        a, b = r['provider_comparisons']
        self.assertTrue(a['shortlist_eligible'])
        self.assertFalse(b['shortlist_eligible'])
        self.assertIsNone(b['weighted_score'])
        self.assertEqual(b['score_bounds'], {'minimum':'30.0','maximum':'100'})
        self.assertIsNone(r['ranking'])
        self.assertIsNone(r['selected_provider'])
    def test_unsupported_mandatory_excludes_even_high_score(self):
        d = self.request['data']
        d['requirements'][0]['weight'] = '1'
        d['requirements'][1]['weight'] = '99'
        d['providers'][0]['evidence'][0]['status'] = 'unsupported'
        row = self.run_model()['result']['provider_comparisons'][0]
        self.assertEqual(row['weighted_score'], '99.00')
        self.assertFalse(row['shortlist_eligible'])
    def test_missing_optional_keeps_score_unknown(self):
        self.request['data']['providers'][0]['evidence'].pop()
        r = self.run_model()['result']['provider_comparisons'][0]
        self.assertIsNone(r['weighted_score'])
        self.assertEqual(r['unknown_weight'], '30')
    def test_price_units_and_currency_separate(self):
        r = self.run_model()['result']['comparable_rate_groups']
        self.assertEqual(len(r), 2)
        self.assertIsNone(r[0]['rates'][0]['amount'])
    def test_missing_prices_gap(self):
        self.request['data']['providers'][0]['prices'] = []
        self.assertTrue(any(x['code'] == 'provider-price-gap' for x in self.run_model()['findings']))
    def test_duplicate_evidence_rejected(self):
        p = self.request['data']['providers'][0]
        p['evidence'].append(deepcopy(p['evidence'][0]))
        self.assertTrue(validate_request(self.request, domain))
    def test_nonfinite_weight_rejected(self):
        self.request['data']['requirements'][0]['weight'] = 'NaN'
        self.assertTrue(validate_request(self.request, domain))
    def test_boolean_rate_rejected(self):
        self.request['data']['providers'][0]['prices'][0]['amount'] = True
        self.assertTrue(validate_request(self.request, domain))
    def test_all_zero_weights_rejected(self):
        for r in self.request['data']['requirements']:
            r['weight'] = '0'
        self.assertTrue(validate_request(self.request, domain))
    def test_unregistered_source_rejected(self):
        self.request['data']['providers'][0]['evidence'][0]['source_ids'] = ['imaginary']
        self.assertTrue(validate_request(self.request, domain))
    def test_tampered_shortlist_rejected(self):
        r = self.run_model()
        r['result']['shortlist_for_human_diligence'].append('proposal-provider')
        self.assertTrue(validate_output(r, domain))
    def test_stale_mandatory_evidence_excludes_shortlist(self):
        self.request['sources'][1]['review_due'] = '2026-01-01'
        self.assertFalse(self.run_model()['result']['provider_comparisons'][0]['shortlist_eligible'])
    def test_external_input_and_authority(self):
        r = self.run_model()
        other = deepcopy(self.request)
        other['request_id'] = 'different'
        self.assertTrue(validate_output(r, domain, other))
        self.assertFalse(r['action_taken'])
        self.request['requested_action'] = 'execute'
        self.assertTrue(validate_request(self.request, domain))

if __name__ == '__main__':
    unittest.main()
