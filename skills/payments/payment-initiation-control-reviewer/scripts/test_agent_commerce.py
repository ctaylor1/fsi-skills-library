"""Independent invariants for normalized agent commerce; synthetic fixtures only."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
import agent_domain as domain
from payment_contract import stable_hash
from payment_foundation import build, validate_request, validate_output
BASE=json.loads((Path(__file__).parents[1]/"evals/files/agent-request.json").read_text())
class AgentCommerceTests(unittest.TestCase):
    def setUp(self):
        self.doc=deepcopy(BASE);self.data=self.doc['data'];self.intent=self.data['intent'];self.proposal=self.data['proposal']
    def out(self):return build(self.doc,domain)
    def gaps(self):return set(self.out()['result']['gaps'])
    def bind(self):
        self.proposal['cart_hash']=stable_hash(self.data['cart']);self.data['review']['intent_hash']=stable_hash(self.intent);self.data['review']['proposal_hash']=stable_hash(self.proposal)
    def test_complete_is_not_authority(self):
        out=self.out();self.assertEqual(out['status'],'draft');self.assertFalse(out['authority_granted']);self.assertFalse(out['result']['payment_authorized']);self.assertFalse(out['result']['reservation_created']);self.assertFalse(out['result']['protocol_conformance_verified']);self.assertEqual(validate_output(out,domain,self.doc),[])
    def test_cart_math(self):self.assertEqual(self.out()['result']['cart_calculated_amount'],'100.00')
    def test_pending_spend_consumes_budget(self):self.assertEqual(self.out()['result']['remaining_budget_before_proposal'],'275.00')
    def test_incomplete_history_is_unknown(self):
        self.data['ledger_complete']=False;self.assertIsNone(self.out()['result']['remaining_budget_before_proposal'])
    def test_unknown_outcome_is_unknown(self):
        self.data['history'][0]['state']='unknown';self.assertIsNone(self.out()['result']['remaining_budget_before_proposal'])
    def test_missing_prior_amount_is_unknown(self):
        self.data['history'][0]['amount']=None;self.assertIsNone(self.out()['result']['known_committed_amount'])
    def test_failed_without_terminal_evidence_unknown(self):
        self.data['history'][0]['state']='failed';self.assertIsNone(self.out()['result']['remaining_budget_before_proposal'])
    def test_documented_nonexecution_excludes_spend(self):
        self.data['history'][0].update(state='failed',terminal_nonexecution_ref='reviewed:nonexecution');self.assertEqual(self.out()['result']['remaining_budget_before_proposal'],'400.00')
    def test_unrelated_intent_history_not_netted(self):
        self.data['history'][0]['intent_id']='other';self.assertIsNone(self.out()['result']['remaining_budget_before_proposal'])
    def test_cross_currency_not_netted(self):
        self.data['history'][0]['currency']='EUR';self.assertIsNone(self.out()['result']['remaining_budget_before_proposal'])
    def test_future_history_unresolved(self):
        self.data['history'][0]['observed_at']='2026-09-19T12:00:00Z';self.assertIn('spend-history-scope-conflict',self.gaps())
    def test_duplicate_history_identity_rejects(self):
        self.data['history']*=2;self.assertTrue(validate_request(self.doc,domain))
    def test_replay_checkout_new_ids(self):
        self.data['history'][0]['checkout_id']=self.proposal['checkout_id'];self.assertIn('replay-or-retry-requires-investigation',self.gaps())
    def test_retry_same_key(self):
        self.data['history'][0]['idempotency_key']=self.proposal['idempotency_key'];self.assertIn('replay-or-retry-requires-investigation',self.gaps())
    def test_aggregate_budget(self):
        self.intent['total_limit']='200.00';self.bind();self.assertIn('aggregate-limit-exceeded',self.gaps())
    def test_count_limit(self):
        self.intent['max_payments']=1;self.bind();self.assertIn('payment-count-limit-exceeded',self.gaps())
    def test_per_payment_limit(self):
        self.intent['max_per_payment']='99.99';self.bind();self.assertIn('per-payment-limit-exceeded',self.gaps())
    def test_revoked_intent(self):
        self.intent['revoked']=True;self.bind();self.assertIn('intent-revocation-unresolved',self.gaps())
    def test_subdelegation(self):
        self.intent['delegation_depth']=1;self.bind();self.assertIn('subdelegation-outside-intent',self.gaps())
    def test_execution_after_intent_expiry(self):
        self.intent['valid_until']='2026-09-18T13:00:00Z';self.bind();self.assertIn('intent-outside-validity',self.gaps())
    def test_review_expires_before_execution(self):
        self.data['review']['valid_until']='2026-09-18T13:00:00Z';self.assertIn('review-outside-validity',self.gaps())
    def test_exact_merchant_scope(self):
        self.intent['merchant_refs']=['other'];self.bind();self.assertIn('merchant-outside-intent',self.gaps())
    def test_identity_binding(self):
        self.proposal['agent_ref']='different-agent';self.bind();self.assertIn('principal-or-agent-mismatch',self.gaps())
    def test_cart_changed_without_new_binding(self):
        self.data['cart']['items'][0]['quantity']=3;self.assertIn('cart-hash-mismatch',self.gaps());self.assertIn('cart-total-mismatch',self.gaps())
    def test_cart_item_outside_intent(self):
        self.data['cart']['items'][0]['item_ref']='unapproved';self.bind();self.assertIn('cart-items-outside-intent',self.gaps())
    def test_cart_mismatch_despite_rehashed_review(self):
        self.proposal['amount']='1.00';self.bind();self.assertIn('cart-total-mismatch',self.gaps())
    def test_review_scope_cannot_transfer(self):
        self.proposal['payee_account_ref']='changed';self.assertIn('review-binding-mismatch',self.gaps())
    def test_atomic_reservation_declaration_required(self):
        del self.data['review']['atomic_reservation_review_ref'];self.assertIn('trust-or-oversight-review-missing',self.gaps())
    def test_protocol_name_does_not_prove_deployment(self):
        self.data['protocol']={'family':'ap2','version':'0.2','source_ids':['review']};self.assertIn('protocol-deployment-review-unresolved',self.gaps())
    def test_naive_timestamp_rejected(self):
        self.proposal['execution_at']='2026-09-18T14:00:00';self.assertTrue(validate_request(self.doc,domain))
    def test_unknown_source_rejected(self):
        self.data['cart']['source_ids']=['invented'];self.assertTrue(validate_request(self.doc,domain))
    def test_unknowns_upstream_propagate(self):
        self.doc['upstream_issues']=[{'code':'ownership','message':'ownership unresolved'}];out=self.out();self.assertEqual(out['status'],'needs-evidence');self.assertIn('upstream:ownership',{x['code'] for x in out['handoffs'][0]['unresolved_issues']})
    def test_source_bound_output_rejects_replacement(self):
        out=self.out();self.doc['request_id']='other';self.assertTrue(validate_output(out,domain,self.doc))
    def test_review_does_not_transfer_jurisdiction(self):
        self.doc['jurisdiction']='UK';self.assertIn('review-participant-or-jurisdiction-mismatch',self.gaps())
    def test_accountable_owner_is_required(self):
        del self.data['review']['accountable_owner_ref'];self.assertIn('trust-or-oversight-review-missing',self.gaps())
    def test_public_protocol_subdelegation_unimplemented(self):
        self.intent.update(delegation_depth=1,max_delegation_depth=1,allows_subdelegation=True);self.bind()
        for family in ('ap2','acp'):
            self.data['protocol'].update(family=family,version='0.2');self.assertIn('protocol-subdelegation-not-implemented',self.gaps())
    def test_execution_request_rejected(self):
        self.doc['requested_action']='execute';self.assertTrue(validate_request(self.doc,domain))
    def test_bad_money_rejected(self):
        self.proposal['amount']='NaN';self.assertTrue(validate_request(self.doc,domain))

if __name__=='__main__':unittest.main()
