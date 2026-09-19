#!/usr/bin/env python3
"""Behavioral invariants for the portable domain adapter; all evidence is synthetic."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
import domain
from payment_foundation import build, validate_output, validate_request

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / 'evals/files/normal.json').read_text())


def codes(result):
    return {f['code'] for f in result['findings']}


class SharedContractTests(unittest.TestCase):
    def test_normal_source_replay(self):
        request = fixture()
        output = build(request, domain)
        self.assertEqual([], validate_output(output, domain, request))
        self.assertFalse(output['authority_granted'])
        self.assertFalse(output['action_taken'])

    def test_unknown_region_is_not_generic_profile(self):
        request = fixture(); request['jurisdiction'] = 'CA'
        self.assertEqual('unsupported', build(request, domain)['status'])

    def test_upstream_gap_survives_handoff(self):
        request = fixture(); request['upstream_issues'] = [{'code':'reach-unresolved','message':'Endpoint reach is unknown','source_ids':['s1']}]
        result = build(request, domain)
        self.assertIn('upstream:reach-unresolved', codes(result))
        self.assertEqual('needs-evidence', result['status'])

    def test_stale_source_blocks_reliance(self):
        request = fixture(); request['sources'][0]['review_due'] = '2026-09-17'
        self.assertIn('stale-source', codes(build(request, domain)))

    def test_injected_execution_is_rejected(self):
        request = fixture(); request['requested_action'] = 'execute'
        self.assertTrue(validate_request(request, domain))

    def test_tamper_and_rebound_source_are_rejected(self):
        request = fixture(); result = build(request, domain)
        result['authority_granted'] = True
        self.assertTrue(validate_output(result, domain, request))
        result = build(request, domain)
        changed = deepcopy(request); changed['request_id'] = 'replacement'
        self.assertTrue(validate_output(result, domain, changed))

class DomainTests(unittest.TestCase):
    def test_supported_scenario_has_actual_decision_dimensions(self):
        result = build(fixture(), domain)
        row = result['result']['rail_comparison'][0]
        self.assertEqual('evidence-needed', row['review'])
        self.assertEqual('declared-only', next(x['assessment'] for x in row['decision_criteria'] if x['criterion'] == 'funding'))
        self.assertGreaterEqual(len(row['decision_criteria']), 9)
        self.assertIsNone(result['result']['preferred_profile_id'])
        self.assertTrue(row['source_refs'])

    def test_native_rail_mechanisms_differ(self):
        request = fixture(); request['data']['candidate_profile_ids'] = ['US-ACH','US-FEDWIRE','US-FEDNOW','US-RTP']
        result = build(request, domain)['result']['rail_comparison']
        self.assertEqual('requirements-conflict', result[0]['review'])
        self.assertEqual('requirements-conflict', result[1]['review'])
        self.assertNotEqual(result[2]['profile_facts']['funding'], result[3]['profile_facts']['funding'])

    def test_all_regional_profiles_resolve(self):
        groups = [('EA','EUR',['EA-SCT','EA-SCT-INST','EA-SDD-CORE']),('UK','GBP',['UK-FPS','UK-BACS','UK-CHAPS'])]
        for jurisdiction,currency,ids in groups:
            request=fixture();request['jurisdiction']=jurisdiction;request['data']['requirements']['currency']=currency;request['data']['candidate_profile_ids']=ids
            result=build(request,domain)
            self.assertNotIn('unsupported-rail-profile',codes(result))
            self.assertEqual(len(ids),len(result['result']['rail_comparison']))

    def test_unknown_fees_not_zero(self):
        request = fixture(); request['data'].pop('costs')
        result=build(request,domain)
        self.assertIsNone(result['result']['rail_comparison'][0]['contracted_cost'])
        self.assertIn('commercial-cost-unknown',codes(result))

    def test_contract_is_not_endpoint_reach(self):
        request=fixture();request['data']['access_evidence'][0]['reachable']=False
        self.assertIn('access-and-reach-unknown',codes(build(request,domain)))

    def test_credit_rail_does_not_support_debit_mandate_by_name(self):
        request=fixture();request['data']['requirements']['direction']='debit'
        result=build(request,domain)
        self.assertIn('direction-incompatible',codes(result))
        self.assertIn('collection-authority-unknown',codes(result))

    def test_guaranteed_recovery_rejected(self):
        request=fixture();request['data']['requirements']['return_need']='guaranteed-rollback'
        self.assertIn('servicing-incompatible',codes(build(request,domain)))

    def test_unknown_profile_does_not_crash(self):
        request=fixture();request['data']['candidate_profile_ids']=['generic-instant']
        self.assertIn('unsupported-rail-profile',codes(build(request,domain)))

    def test_future_native_profile_not_reliable(self):
        request=fixture();request['as_of']='2026-09-17';request['sources'][0]['as_of']='2026-09-17'
        self.assertIn('profile-review-overdue',codes(build(request,domain)))

    def test_low_balance_remains_gap(self):
        request=fixture();request['data']['funding_evidence'][0]['available_amount']='99.99'
        self.assertIn('funding-unknown',codes(build(request,domain)))

    def test_wrong_currency_funding_not_combined(self):
        request=fixture();request['data']['funding_evidence'][0]['currency']='EUR'
        self.assertIn('funding-unknown',codes(build(request,domain)))

    def test_duplicate_evidence_does_not_select_arbitrary_record(self):
        request=fixture();request['data']['access_evidence']*=2
        self.assertIn('access-and-reach-unknown',codes(build(request,domain)))

    def test_handoffs_declare_receiving_contract(self):
        for handoff in build(fixture(),domain)['handoffs']:
            self.assertTrue(handoff['target_skill'])
            self.assertTrue(handoff['reason'])
            self.assertTrue(handoff['required_inputs'])

    def test_free_text_funding_cannot_prove_native_mechanism_compatibility(self):
        request=fixture()
        request['data']['funding_evidence'][0]['arrangement']='RTP-style prefunding account (no Federal Reserve master-account arrangement)'
        result=build(request,domain)
        row=result['result']['rail_comparison'][0]
        funding=next(x for x in row['decision_criteria'] if x['criterion']=='funding')
        self.assertEqual('declared-only',funding['assessment'])
        self.assertEqual('evidence-needed',row['review'])
        self.assertIn('funding-declared-only',codes(result))
        self.assertIn('Master/correspondent',row['profile_facts']['funding'])


if __name__ == '__main__':
    unittest.main()
