import copy
import json
from pathlib import Path
import unittest
import incident_domain as domain
from payment_foundation import build, validate_output, validate_request


class IncidentTests(unittest.TestCase):
    def setUp(self): self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/incident.json').read_text())
    def run_doc(self): return build(self.doc,domain)
    def codes(self): return {r['code'] for r in self.run_doc()['findings']}
    def test_payment_attempt_denominators(self):
        i=self.run_doc()['result']['impact'];self.assertEqual((i['unique_payments'],i['attempts'],i['retry_attempts']),(3,4,1)); self.assertIsNone(i['eventual_success_rate'])
    def test_currencies_and_entities_separate(self):
        i=self.run_doc()['result']['impact'];self.assertEqual(len(i['monetary_partitions']),2);self.assertEqual(i['monetary_partitions'][1]['unknown_outcome_amount'],'75');self.assertIsNone(i['monetary_partitions'][0]['actual_loss'])
    def test_duplicate_attempt_no_extra_impact(self):
        self.doc['data']['attempts'].append(copy.deepcopy(self.doc['data']['attempts'][0]));self.assertEqual(self.run_doc()['result']['impact']['attempts'],4)
    def test_conflicting_attempt_quarantined(self):
        a=copy.deepcopy(self.doc['data']['attempts'][0]);a['status']='succeeded';self.doc['data']['attempts'].append(a);self.assertEqual(self.run_doc()['result']['impact']['attempts'],3)
    def test_conflicting_payment_invalidates_rate(self):
        p=copy.deepcopy(self.doc['data']['payments'][0]);p['amount']='200';self.doc['data']['payments'].append(p);self.assertIsNone(self.run_doc()['result']['impact']['confirmed_success_rate'])
    def test_authorization_not_success(self):
        self.doc['data']['payments'][0]['lifecycle_state']='authorized';self.assertEqual(self.run_doc()['result']['impact']['payment_outcomes']['unknown'],2)
    def test_attempt_success_cannot_settle_unknown(self):
        self.doc['data']['attempts'][2]['status']='succeeded';self.assertEqual(self.run_doc()['result']['impact']['payment_outcomes']['unknown'],1)
    def test_missing_coverage_not_zero(self):
        self.doc['data']['coverage']={};self.assertIsNone(self.run_doc()['result']['impact']['confirmed_success_rate'])
    def test_wrong_inventory_count_gap(self):
        self.doc['data']['coverage']['expected_unique_payments']=4;self.assertIn('population-incomplete',self.codes())
    def test_unknown_resend_blocked(self):
        self.doc['data']['containment']['replay']={'payment_id':'p2','authoritative_no_effect':True,'same_idempotency_key':True,'same_payload_hash':True,'source_ids':['s1']};self.assertIn('unsafe-replay',self.codes())
    def test_new_key_blocked(self):
        self.doc['data']['containment']['replay']={'payment_id':'p3','authoritative_no_effect':True,'same_idempotency_key':False,'same_payload_hash':True,'source_ids':['s1']};self.assertIn('unsafe-replay',self.codes())
    def test_exact_known_no_effect_not_execution(self):
        self.doc['data']['containment']['replay']={'payment_id':'p3','authoritative_no_effect':True,'same_idempotency_key':True,'same_payload_hash':True,'source_ids':['s1']};out=self.run_doc();self.assertIn('separately authorized review',out['result']['replay_assessment']);self.assertFalse(out['action_taken'])
    def test_unknown_remains_recovery_open(self):
        self.doc['data']['recovery']['matched_payment_ids'].append('p2');self.doc['data']['recovery']['unresolved_payment_ids']=[];self.assertIn('unknown-outcome-open',self.codes())
    def test_recovery_overlap_gap(self):
        self.doc['data']['recovery']['matched_payment_ids'].append('p2');self.assertIn('recovery-coverage-gap',self.codes())
    def test_correlation_not_cause(self):
        out=self.run_doc();self.assertFalse(out['result']['root_cause_confirmed']);self.assertFalse(out['result']['hypotheses'][0]['causal_conclusion'])
    def test_timeline_sorted(self):
        self.doc['data']['timeline'].reverse();out=self.run_doc();self.assertEqual(out['result']['timeline'][0]['event_id'],'r1')
    def test_missing_hypothesis_basis(self):
        self.doc['data']['hypotheses'][0]['supporting_event_ids']=['nonexistent'];self.assertIn('hypothesis-unsubstantiated',self.codes())
    def test_outside_attempt_excluded(self):
        self.doc['data']['attempts'][0]['at']='2026-08-01T00:00:00Z';self.assertIn('attempt-outside-window',self.codes())
    def test_timeline_orders_utc_instants(self):
        self.doc['data']['timeline'][0]['at']='2026-09-02T12:55:00+02:00'
        self.doc['data']['timeline'][1]['at']='2026-09-02T11:00:00Z'
        self.assertEqual(self.run_doc()['result']['timeline'][0]['event_id'],'r1')
    def test_retry_chains_preserve_individual_outcomes(self):
        chain=self.run_doc()['result']['retry_chains'][0]
        self.assertEqual(chain['payment_id'],'p1');self.assertEqual(len(chain['attempts']),2);self.assertEqual(chain['outcome'],'succeeded')
    def test_negative_amount_rejected(self):
        self.doc['data']['payments'][0]['amount']='-1';self.assertTrue(validate_request(self.doc,domain))
    def test_output_tamper(self):
        out=self.run_doc();out['result']['incident_closed']=True;self.assertTrue(validate_output(out,domain,self.doc))
    def test_execute_rejected(self):
        self.doc['requested_action']='execute';self.assertTrue(validate_request(self.doc,domain))

if __name__=='__main__': unittest.main()
