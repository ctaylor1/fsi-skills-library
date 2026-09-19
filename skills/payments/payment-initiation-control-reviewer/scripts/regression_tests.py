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
    def test_exact_instruction_ready_for_review_only(self):
        result=build(fixture(),domain)
        self.assertEqual('ready-for-human-review',result['result']['review'])
        self.assertFalse(result['result']['submission_authorized'])

    def test_authentication_alone_not_intent(self):
        request=fixture();request['data']['intents']=[];request['data']['authentication']={'success':True}
        self.assertIn('payment-intent-unresolved',codes(build(request,domain)))

    def test_changed_payee_invalidates_intent_and_screening(self):
        request=fixture();request['data']['instructions'][0]['payee_account_ref']='changed'
        result=build(request,domain)
        self.assertIn('payment-intent-unresolved',codes(result))
        self.assertIn('screening-unresolved',codes(result))
        self.assertIn('account-verification-unresolved',codes(result))

    def test_revoked_or_expired_intent(self):
        for key,value in [('revoked',True),('effective_until','2026-09-17')]:
            request=fixture();request['data']['intents'][0][key]=value
            self.assertIn('payment-intent-unresolved',codes(build(request,domain)))

    def test_future_execution_outside_authority(self):
        request=fixture();request['data']['instructions'][0]['execution_date']='2026-12-01'
        request['data']['intents'][0]['binding']['execution_date']='2026-12-01'
        self.assertIn('payment-intent-unresolved',codes(build(request,domain)))

    def test_unknown_screening_not_approval(self):
        request=fixture();request['data']['screenings'][0]['status']='pending'
        self.assertIn('screening-unresolved',codes(build(request,domain)))

    def test_duplicate_new_identifier_same_payment(self):
        request=fixture();new=deepcopy(request['data']['instructions'][0]);new['instruction_id']='i2';request['data']['instructions'].append(new)
        result=build(request,domain)
        self.assertIn('duplicate-instruction',codes(result))
        self.assertTrue(all('duplicate-instruction' in i['finding_codes'] for i in result['result']['instructions']))

    def test_prior_history_detail_reuse(self):
        request=fixture();prior=deepcopy(request['data']['intents'][0]['binding']);prior['instruction_id']='old';request['data']['prior_instruction_bindings']=[prior]
        self.assertIn('duplicate-instruction',codes(build(request,domain)))

    def test_unknown_history_not_zero(self):
        request=fixture();request['data'].pop('prior_instruction_ledger_complete')
        self.assertIn('duplicate-history-unknown',codes(build(request,domain)))

    def test_batch_totals_exact_decimal(self):
        request=fixture();request['data']['batch_controls']['totals_by_currency']['USD']='100.01'
        self.assertIn('batch-control-mismatch',codes(build(request,domain)))
        request=fixture();request['data']['batch_controls']['totals_by_currency']['EUR']='100.00'
        self.assertIn('batch-control-mismatch',codes(build(request,domain)))

    def test_delegated_actor_not_blanket_permission(self):
        request=fixture();request['data']['instructions'][0]['submitter_ref']='delegate';request['data']['policy']['authorized_submitter_refs'].append('delegate')
        self.assertIn('delegation-unresolved',codes(build(request,domain)))

    def test_wrong_principal_not_authorized(self):
        request=fixture();request['data']['intents'][0]['principal_ref']='different-customer'
        self.assertIn('payment-intent-unresolved',codes(build(request,domain)))

    def test_debit_requires_mandate(self):
        request=fixture();request['data']['instructions'][0]['direction']='debit'
        self.assertIn('mandate-missing',codes(build(request,domain)))

    def test_reused_one_off_mandate_blocked(self):
        request=fixture();i=request['data']['instructions'][0];i['direction']='debit';i['mandate_id']='m1'
        mandate={k:i[k] for k in ('payer_account_ref','payee_ref','payee_account_ref','currency','rail_profile_id')}
        mandate.update({'mandate_id':'m1','max_amount':'1000.00','frequency':'one-off','permitted_instruction_id':'i1','prior_use_count':1,'effective_from':'2026-09-01','effective_until':'2026-10-31','revoked':False,'revocation_check_current':True,'source_ids':['s1']})
        request['data']['mandates']=[mandate]
        self.assertIn('mandate-scope-unresolved',codes(build(request,domain)))

    def test_no_generic_rail_fallback(self):
        request=fixture();request['data']['instructions'][0]['rail_profile_id']='generic-instant'
        self.assertIn('native-profile-unresolved',codes(build(request,domain)))

    def test_nonfinite_and_float_money_do_not_pass(self):
        for value in ['NaN','Infinity',100.00]:
            request=fixture();request['data']['instructions'][0]['amount']=value
            if isinstance(value,str):
                self.assertIn('instruction-incomplete',codes(build(request,domain)))
            else:
                self.assertTrue(validate_request(request,domain))

    def test_credit_only_rail_cannot_accept_debit_direction(self):
        request=fixture();request['data']['instructions'][0]['direction']='debit'
        self.assertIn('native-profile-direction',codes(build(request,domain)))

    def test_scoped_one_off_debit_mandate_can_be_reviewed(self):
        request=fixture();d=request['data'];i=d['instructions'][0]
        i.update({'direction':'debit','rail_profile_id':'US-ACH','mandate_id':'m1'})
        d['policy']['profile_ids']=['US-ACH']
        for row in d['intents']+d['screenings']:row['binding']=domain.binding(i)
        mandate={k:i[k] for k in ('payer_account_ref','payee_ref','payee_account_ref','currency','rail_profile_id')}
        mandate.update({'mandate_id':'m1','max_amount':'1000.00','frequency':'one-off','permitted_instruction_id':'i1','prior_use_count':0,'effective_from':'2026-09-01','effective_until':'2026-10-31','revoked':False,'revocation_check_current':True,'source_ids':['s1']})
        d['mandates']=[mandate]
        self.assertEqual('ready-for-human-review',build(request,domain)['result']['review'])
        d['mandates'][0]['revocation_check_current']=False
        self.assertIn('mandate-scope-unresolved',codes(build(request,domain)))

    def test_card_intent_requires_exact_provider_scope(self):
        request=fixture();d=request['data'];i=d['instructions'][0]
        i.update({'rail_family':'card','rail_profile_id':'provider-card','network':'synthetic-network','product':'consumer-credit'})
        d['policy'].update({'profile_ids':['provider-card'],'network':'synthetic-network','product':'consumer-credit'})
        for row in d['intents']+d['screenings']:row['binding']=domain.binding(i)
        d['card_profile']={'profile_id':'provider-card','network':'synthetic-network','product':'consumer-credit','jurisdiction':'US','participants':['bank'],'actions':['initiate'],'source_version':'synthetic-v1','effective_from':'2026-09-01','effective_until':'2026-10-31','revoked':False,'reviewed_on':'2026-09-18','review_due':'2026-10-01','source_ids':['s1']}
        self.assertEqual('ready-for-human-review',build(request,domain)['result']['review'])
        i['product']='business-debit'
        result=build(request,domain)
        self.assertIn('card-profile-unresolved',codes(result));self.assertIn('payment-intent-unresolved',codes(result))

    def test_handoffs_declare_receiving_contract(self):
        result=build(fixture(),domain)
        self.assertTrue(result['handoffs'])
        for handoff in result['handoffs']:
            self.assertTrue(handoff['target_skill'])
            self.assertTrue(handoff['reason'])
            self.assertTrue(handoff['required_inputs'])

    def test_expiring_delegation_does_not_authorize_future_execution(self):
        request=fixture();d=request['data'];i=d['instructions'][0]
        i.update({'execution_date':'2026-09-25','submitter_ref':'delegate-A'})
        d['policy']['authorized_submitter_refs'].append('delegate-A')
        for row in d['intents']+d['screenings']:row['binding']=domain.binding(i)
        d['delegations']=[{'principal_ref':i['principal_ref'],'delegate_ref':'delegate-A','binding':domain.binding(i),'effective_from':'2026-09-01','effective_until':'2026-09-20','revoked':False,'source_ids':['s1']}]
        self.assertIn('delegation-unresolved',codes(build(request,domain)))
        d['delegations'][0]['effective_until']='2026-09-30'
        self.assertEqual('ready-for-human-review',build(request,domain)['result']['review'])

    def test_explicit_policy_expiry_covers_scheduled_execution(self):
        request=fixture();d=request['data'];i=d['instructions'][0];i['execution_date']='2026-09-25'
        for row in d['intents']+d['screenings']:row['binding']=domain.binding(i)
        d['policy']['effective_until']='2026-09-20'
        self.assertIn('policy-scope-unresolved',codes(build(request,domain)))

    def test_explicit_screening_applicability_does_not_extend_to_future_execution(self):
        request=fixture();d=request['data'];i=d['instructions'][0];i['execution_date']='2026-09-25'
        for row in d['intents']+d['screenings']:row['binding']=domain.binding(i)
        d['screenings'][0]['effective_until']='2026-09-20'
        self.assertIn('screening-unresolved',codes(build(request,domain)))

    def test_explicit_account_verification_scope_covers_scheduled_execution(self):
        request=fixture();d=request['data'];i=d['instructions'][0];i['execution_date']='2026-09-25'
        for row in d['intents']+d['screenings']:row['binding']=domain.binding(i)
        d['account_verifications'][0]['effective_until']='2026-09-20'
        self.assertIn('account-verification-unresolved',codes(build(request,domain)))


if __name__ == '__main__':
    unittest.main()
