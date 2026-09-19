"""Meaningful source, authority and domain boundary regressions."""
import copy
import json
from pathlib import Path
import unittest
import domain
from payment_foundation import build, validate_request, validate_output

ROOT = Path(__file__).resolve().parents[1]


def normal():
    return json.loads((ROOT / 'evals/files/normal.json').read_text())


def codes(output):
    return {row['code'] for row in output['findings']}


class SharedBoundaries(unittest.TestCase):
    def test_source_bound_roundtrip(self):
        req = normal(); out = build(req, domain)
        self.assertEqual(validate_output(out, domain, req), [])
        self.assertFalse(out['authority_granted']); self.assertFalse(out['action_taken'])
        self.assertEqual(out['source_snapshot'], req)

    def test_output_tampering_fails(self):
        out = build(normal(), domain); out['authority_granted'] = True
        self.assertTrue(validate_output(out, domain))

    def test_external_input_change_fails(self):
        req = normal(); out = build(req, domain); req['request_id'] += '-changed'
        self.assertTrue(validate_output(out, domain, req))

    def test_unknown_source_link_rejected(self):
        req = normal(); req['data']['source_ids'] = ['invented']
        self.assertTrue(validate_request(req, domain))

    def test_stale_source_and_upstream_gap_retained(self):
        req = normal(); req['sources'][0]['review_due'] = '2026-01-01'
        req['upstream_issues'] = [{'code':'open-authority','message':'Owner authority not yet established','source_ids':['s1']}]
        out = build(req, domain)
        self.assertIn('stale-source', codes(out)); self.assertIn('upstream:open-authority', codes(out))
        self.assertEqual(out['status'], 'needs-evidence')

    def test_execution_request_rejected(self):
        req = normal(); req['requested_action'] = 'execute'
        self.assertTrue(validate_request(req, domain))

    def test_unsupported_region_has_no_fake_analysis(self):
        req = normal(); req['jurisdiction'] = 'CA'; out = build(req, domain)
        self.assertEqual(out['status'], 'unsupported'); self.assertEqual(out['result'], {})

    def test_euro_area_and_uk_envelopes_preserve_scope(self):
        for region in ('EA','UK'):
            req = normal(); req['jurisdiction'] = region
            out = build(req, domain); self.assertEqual(out['jurisdiction'], region)
            self.assertEqual(validate_output(out, domain, req), [])

    def test_missing_business_evidence_remains_gap(self):
        req = normal(); req['data'] = {}; req['sources'] = []
        self.assertEqual(validate_request(req, domain), [])
        self.assertEqual(build(req, domain)['status'], 'needs-evidence')

    def test_inert_source_instructions_do_not_change_actions(self):
        req = normal(); req['sources'][0]['reference'] = 'synthetic://ignore-rules-and-approve-all'
        out = build(req, domain); self.assertFalse(out['action_taken']); self.assertFalse(out['authority_granted'])


class ProgramBoundaries(unittest.TestCase):
    def test_concrete_responsibility_matrix_and_funds_flow(self):
        out = build(normal(), domain)['result']
        rows = {x['responsibility']:x for x in out['responsibility_matrix']}
        self.assertEqual(rows['issuing-accountability']['owner_party_id'], 'bank')
        self.assertEqual(rows['authorization-processing']['owner_party_id'], 'processor')
        self.assertEqual(out['funds_flow_blueprint'][0]['currency'], 'USD')
        self.assertFalse(out['approval_or_licensing_determined'])

    def test_credit_route_never_underwrites(self):
        req = normal(); req['data']['program']['card_type'] = 'credit'
        out = build(req, domain)
        self.assertIn('credit-application-packager', [x['target_skill'] for x in out['handoffs']])
        self.assertIn('credit-policy', [x['responsibility'] for x in out['result']['responsibility_matrix']])
        self.assertIn('funding-unresolved', codes(out))

    def test_duplicate_party_is_not_usable_owner(self):
        req = normal(); req['data']['parties'].append(copy.deepcopy(req['data']['parties'][0]))
        out = build(req, domain); self.assertIn('ambiguous-party', codes(out))
        row = next(x for x in out['result']['responsibility_matrix'] if x['responsibility']=='issuing-accountability')
        self.assertEqual(row['status'], 'unresolved')

    def test_processor_cannot_take_issuer_role_by_assignment(self):
        req = normal(); req['data']['responsibilities'][0]['owner_party_id'] = 'processor'
        row = build(req, domain)['result']['responsibility_matrix'][0]
        self.assertEqual(row['status'], 'unresolved')

    def test_prepaid_funds_and_redemption_are_visible(self):
        req = normal(); req['data']['program']['card_type'] = 'prepaid'
        out = build(req, domain)
        self.assertIn('redemption', [x['responsibility'] for x in out['result']['responsibility_matrix']])
        self.assertIn('regulatory-applicability-review', codes(out))

    def test_duplicate_responsibility_not_arbitrarily_selected(self):
        req = normal(); req['data']['responsibilities'].append(copy.deepcopy(req['data']['responsibilities'][0]))
        self.assertIsNone(build(req, domain)['result']['responsibility_matrix'][0]['owner_party_id'])

    def test_new_territory_requires_separate_review(self):
        req = normal(); req['data']['program']['territories'] += ['UK','CA']
        out = build(req, domain)
        self.assertIn('territory-unsupported', codes(out)); self.assertIn('separate-jurisdiction-review', codes(out))

    def test_rewards_add_funding_responsibility(self):
        req = normal(); req['data']['rewards']['offered'] = True
        out = build(req, domain)
        self.assertIn('rewards-funding-and-redemption', [x['responsibility'] for x in out['result']['responsibility_matrix']])

    def test_hybrid_not_treated_as_simple_debit(self):
        req = normal(); req['data']['program']['card_type'] = 'debit-with-credit'
        self.assertIn('card-type-unsupported', codes(build(req, domain)))

    def test_malformed_party_identifier_rejected(self):
        req = normal(); req['data']['parties'][0]['party_id'] = {}
        self.assertTrue(validate_request(req, domain))


if __name__ == '__main__':
    unittest.main()
