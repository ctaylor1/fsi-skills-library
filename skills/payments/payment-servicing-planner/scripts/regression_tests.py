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
    def test_completed_and_pending_amounts_reserved(self):
        result=build(fixture(),domain)['result']
        self.assertEqual('ready-for-human-review',result['review'])
        self.assertEqual('70.00',result['remaining_serviceable_amount'])
        self.assertFalse(result['execution_authorized'])
        self.assertFalse(result['expected_effect']['original_ledger_rolled_back'])

    def test_pending_prevents_duplicate_full_refund(self):
        request=fixture();request['data']['service_request']['amount']='80.00'
        self.assertIn('service-amount-exceeds-remaining',codes(build(request,domain)))

    def test_unknown_history_not_zero(self):
        request=fixture();request['data'].pop('prior_service_ledger_complete')
        result=build(request,domain)
        self.assertIn('service-history-unknown',codes(result))
        self.assertIsNone(result['result']['remaining_serviceable_amount'])

    def test_settled_void_cannot_rollback(self):
        request=fixture();request['data']['service_request']['action']='void';request['data']['service_request']['requested_effect']='rollback'
        result=build(request,domain)
        self.assertIn('void-after-submission',codes(result));self.assertIn('rollback-not-supported',codes(result))

    def test_authorization_is_not_settlement(self):
        request=fixture();request['data']['original_payment']['state']='authorized'
        self.assertIn('funds-movement-not-evidenced',codes(build(request,domain)))

    def test_repair_approval_does_not_authorize_service(self):
        request=fixture();request['data']['repair_approval']={'approved':True}
        self.assertIn('repair-authority-inapplicable',codes(build(request,domain)))

    def test_service_request_duplicate(self):
        request=fixture();request['data']['service_request']['service_id']='service-1'
        self.assertIn('duplicate-service',codes(build(request,domain)))

    def test_duplicate_ledger_means_unknown_capacity(self):
        request=fixture();request['data']['prior_services'].append(deepcopy(request['data']['prior_services'][0]))
        result=build(request,domain)
        self.assertIn('service-ledger-invalid',codes(result));self.assertIsNone(result['result']['remaining_serviceable_amount'])

    def test_wrong_currency_never_net(self):
        request=fixture();request['data']['prior_services'][0]['currency']='EUR'
        result=build(request,domain)
        self.assertIsNone(result['result']['remaining_serviceable_amount'])

    def test_destination_change_needs_new_authority(self):
        request=fixture();request['data']['service_request']['destination_account_ref']='new-beneficiary'
        self.assertIn('beneficiary-redirection',codes(build(request,domain)))

    def test_exact_original_binding_detects_state_change(self):
        request=fixture();request['data']['original_payment']['state']='posted'
        self.assertIn('original-binding-mismatch',codes(build(request,domain)))

    def test_deadline_missing_not_universal_default(self):
        request=fixture();request['data']['policy']['permissions'][0].pop('deadline_date')
        self.assertIn('service-window-unresolved',codes(build(request,domain)))

    def test_expired_scope_not_permission(self):
        request=fixture();request['data']['policy']['effective_until']='2026-09-17'
        self.assertIn('service-policy-unresolved',codes(build(request,domain)))

    def test_cancellation_has_no_guaranteed_funds(self):
        request=fixture();request['data']['service_request']['action']='cancel-recovery'
        effect=build(request,domain)['result']['expected_effect']
        self.assertFalse(effect['guaranteed_recovery'])
        self.assertEqual('unknown-until-counterparty-and-system-response',effect['actual_financial_effect'])

    def test_unknown_card_profile_not_generic_scheme_permission(self):
        request=fixture();request['data']['original_payment']['rail_family']='card';request['data']['original_payment']['rail_profile_id']='provider-card'
        self.assertIn('card-profile-unresolved',codes(build(request,domain)))

    def test_positive_supplied_card_scope_is_exact(self):
        request=fixture();d=request['data'];o=d['original_payment'];o.update({'rail_family':'card','rail_profile_id':'provider-card','network':'synthetic-network','product':'consumer-credit'})
        d['service_request']['original_binding'].update({k:o[k] for k in ('rail_profile_id','rail_family','network','product')});d['policy'].update({'network':'synthetic-network','product':'consumer-credit','profile_ids':['provider-card']})
        d['card_profile']={'profile_id':'provider-card','network':'synthetic-network','product':'consumer-credit','jurisdiction':'US','participants':['bank'],'actions':['return'],'source_version':'synthetic-v1','effective_from':'2026-09-01','effective_until':'2026-10-31','revoked':False,'reviewed_on':'2026-09-18','review_due':'2026-10-01','source_ids':['s1']}
        self.assertNotIn('card-profile-unresolved',codes(build(request,domain)))
        d['card_profile']['product']='business-debit'
        self.assertIn('card-profile-unresolved',codes(build(request,domain)))

    def test_no_false_capacity_for_absent_incomplete_or_ambiguous_history(self):
        for variant in ('absent','incomplete','undeclared-completeness','currency-conflict','duplicate'):
            request=fixture();data=request['data']
            if variant == 'absent':data.pop('prior_services')
            elif variant == 'incomplete':data['prior_service_ledger_complete']=False
            elif variant == 'undeclared-completeness':data.pop('prior_service_ledger_complete')
            elif variant == 'currency-conflict':data['prior_services'][0]['currency']='EUR'
            else:data['prior_services'].append(deepcopy(data['prior_services'][0]))
            result=build(request,domain)['result']
            with self.subTest(variant=variant):
                for key in ('completed_service_amount','pending_service_amount','remaining_serviceable_amount'):
                    self.assertIsNone(result[key])

    def test_explicit_empty_complete_history_can_report_zero_prior_services(self):
        request=fixture();request['data']['prior_services']=[]
        result=build(request,domain)['result']
        self.assertEqual('0',result['completed_service_amount'])
        self.assertEqual('0',result['pending_service_amount'])
        self.assertEqual('100.00',result['remaining_serviceable_amount'])

    def test_handoffs_declare_receiving_contract(self):
        for handoff in build(fixture(),domain)['handoffs']:
            self.assertTrue(handoff['target_skill'])
            self.assertTrue(handoff['reason'])
            self.assertTrue(handoff['required_inputs'])


if __name__ == '__main__':
    unittest.main()
