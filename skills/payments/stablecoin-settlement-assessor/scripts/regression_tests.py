"""Meaningful arithmetic, evidence, responsibility and authority invariants."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
import domain
from payment_foundation import build, validate_request, validate_output


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / 'evals/files/request.json').read_text())
        self.option = self.doc['data']['options'][0]

    def result(self):
        return build(self.doc, domain)

    def gap(self, code):
        self.assertIn(code, [f['code'] for f in self.result()['findings']])

    def test_quote_cost(self):
        r = self.result()['result']
        self.assertEqual(r['options'][0]['all_in_cost'], '170')
        self.assertEqual(r['fiat_minus_stablecoin_cost'], '50')

    def test_unknown_fee(self):
        self.option['costs']['fx'] = None
        r = self.result()['result']
        self.assertIsNone(r['options'][0]['all_in_cost'])
        self.assertIsNone(r['fiat_minus_stablecoin_cost'])

    def test_incomplete_cost(self):
        self.option['costs_complete'] = False
        self.gap('unknown-all-in-cost')

    def test_quote_wrong_currency(self):
        self.option['quote_binding']['comparison_currency'] = 'EUR'
        self.gap('quote-binding-mismatch')
        self.assertIsNone(self.result()['result']['options'][0]['all_in_cost'])

    def test_quote_wrong_principal(self):
        self.option['quote_binding']['principal'] = '10000'
        self.gap('quote-binding-mismatch')

    def test_different_delivery(self):
        self.option['delivered_amount'] = '89999'
        self.gap('unequal-beneficiary-value')
        self.assertIsNone(self.result()['result']['fiat_minus_stablecoin_cost'])

    def test_unknown_delivery(self):
        self.option['delivered_amount'] = None
        self.gap('unknown-delivered-amount')

    def test_pilot(self):
        self.option['availability_status'] = 'pilot'
        self.gap('not-evidenced-production')
        self.assertFalse(self.result()['result']['options'][0]['adoption_authorized'])

    def test_holder_is_not_issuer(self):
        self.assertEqual(self.result()['result']['participant_roles'], ['holder'])

    def test_wrong_participant(self):
        self.doc['participant'] = 'other-entity'
        self.gap('participant-mismatch')

    def test_unknown_participant_role(self):
        self.doc['data']['role_assignments'].pop(0)
        self.gap('participant-role-unknown')

    def test_unknown_issuer(self):
        self.option['issuer_ref'] = 'different-issuer'
        self.gap('role-owner-missing')

    def test_stale_profile(self):
        self.option['applicability']['review_due'] = '2026-09-17'
        self.gap('stale-applicability')

    def test_window_outside_review(self):
        self.option['applicability']['review_due'] = '2026-09-19'
        self.gap('stale-applicability')

    def test_uncovered_corridor(self):
        self.option['applicability']['jurisdictions'] = ['US']
        self.gap('applicability-mismatch')

    def test_uncovered_role(self):
        self.option['applicability']['participant_roles'] = ['issuer']
        self.gap('applicability-mismatch')

    def test_wrong_chain_profile(self):
        self.option['applicability']['chain_ids'] = ['other-chain']
        self.gap('asset-chain-profile-mismatch')

    def test_wrong_instrument_profile(self):
        self.option['applicability']['instrument_refs'] = ['other-instrument']
        self.gap('instrument-profile-mismatch')

    def test_missing_chain_finality(self):
        self.option['evidence'].pop('chain_finality')
        self.gap('missing-chain_finality')

    def test_missing_redemption(self):
        self.option['evidence']['redemption_rights'] = ''
        self.gap('missing-redemption_rights')

    def test_missing_fiat_finality(self):
        self.doc['data']['options'][1]['evidence'].pop('economic_finality')
        self.gap('missing-economic_finality')

    def test_missing_actual_chain(self):
        self.option.pop('chain_id')
        self.assertTrue(validate_request(self.doc, domain))

    def test_need_fiat(self):
        self.doc['data']['options'].pop()
        self.assertTrue(validate_request(self.doc, domain))

    def test_negative_fee(self):
        self.option['costs']['fx'] = '-2'
        self.assertTrue(validate_request(self.doc, domain))

    def test_duplicate_roles(self):
        self.doc['data']['role_assignments'].append(deepcopy(self.doc['data']['role_assignments'][0]))
        self.assertTrue(validate_request(self.doc, domain))

    def test_float_rejected(self):
        self.option['costs']['fx'] = 0.1
        self.assertTrue(validate_request(self.doc, domain))

    def test_upstream_gap(self):
        self.doc['upstream_issues'] = [{'code':'custody-unknown','message':'Custody evidence missing','source_ids':['case']}]
        self.gap('upstream:custody-unknown')
        self.assertEqual(self.result()['status'], 'needs-evidence')

    def test_unsupported(self):
        self.doc['jurisdiction'] = 'XX'
        self.assertEqual(self.result()['status'], 'unsupported')

    def test_execution_rejected(self):
        self.doc['requested_action'] = 'execute'
        self.assertTrue(validate_request(self.doc, domain))

    def test_tampered_cost(self):
        r = self.result()
        r['result']['options'][0]['all_in_cost'] = '0'
        self.assertTrue(validate_output(r, domain, self.doc))

    def test_changed_external_input(self):
        r = self.result()
        self.doc['data']['use_case'] = 'a different purpose'
        self.assertTrue(validate_output(r, domain, self.doc))

    def test_no_authority(self):
        r = self.result()
        self.assertFalse(r['authority_granted'])
        self.assertFalse(r['action_taken'])
        for key in ['settlement_authorized','peg_guaranteed','redemption_guaranteed','legal_permission_determined']:
            self.assertFalse(r['result'][key])
        self.assertTrue(all(not h['authority_granted'] and h['target_validation'] == 'required' for h in r['handoffs']))


if __name__ == '__main__':
    unittest.main()
