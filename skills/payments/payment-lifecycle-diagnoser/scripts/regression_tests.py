#!/usr/bin/env python3
"""Observable lifecycle and evidence regressions; no external services."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import compute
from validate_input import validate as input_errors
from validate_output import validate

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/trace_example.json').read_text())
    def one(self,status,code=None,stage='authorization',rail='card'):
        d=copy.deepcopy(self.doc); d['rail']=rail;d['legs']=[{'seq':1,'stage':stage,'status':status,'reason_code':code,'source_ref':'processor:attempt1'}];return d
    def test_card_approval_is_not_settlement(self):
        for d in [self.one('APPROVED'),self.one('OK','00'),self.one('APPROVED','00',stage='settlement')]:
            out=compute(d);self.assertEqual(out['root_cause']['category'],'authorized');self.assertFalse(out['trace_complete']);self.assertEqual(validate(out),[])
    def test_reported_settlement_requires_linked_evidence(self):
        d=self.one('SETTLED',stage='settlement');self.assertEqual(compute(d)['root_cause']['category'],'settlement_reported')
        d['legs'][0]['settlement_evidence']={'status':'confirmed','source_ref':'bank:credit','payment_id':'other'}
        self.assertNotEqual(compute(d)['root_cause']['category'],'settled')
        d['legs'][0]['settlement_evidence']['payment_id']=d['payment_id']
        self.assertEqual(compute(d)['root_cause']['category'],'settled')
    def test_pending_is_not_timeout_or_complete(self):
        d=self.one('PDNG',stage='routing',rail='iso20022');out=compute(d)
        self.assertEqual(out['root_cause']['category'],'in_progress');self.assertFalse(out['trace_complete']);self.assertFalse(out['retry_eligible'])
    def test_later_authorization_does_not_clear_failure(self):
        d=self.one('RJCT','05');d['legs'].append({'seq':2,'stage':'authorization','status':'APPROVED','source_ref':'processor:attempt2'})
        self.assertEqual(compute(d)['root_cause']['category'],'authorization_decline')
    def test_card_format_error_does_not_route_to_bank_repair(self):
        out=compute(self.one('RJCT','12'));self.assertEqual(out['suggested_route'],'payment-operations-review')
    def test_bank_error_requires_casework_before_repair(self):
        self.assertEqual(compute(self.doc)['suggested_route'],'bank-payment-exception-investigator')
    def test_wire_codes_require_declared_format(self):
        d=self.one('RJCT','AC04',rail='wire');self.assertEqual(compute(d)['root_cause']['category'],'unknown')
        d['code_system']='iso20022';self.assertEqual(compute(d)['root_cause']['category'],'account_invalid')
    def test_trace_hash_changes_with_evidence(self):
        before=compute(self.doc);self.doc['legs'][-1]['source_ref']+=':v2'
        self.assertNotEqual(before['diagnosis_id'],compute(self.doc)['diagnosis_id'])
    def test_actual_output_validator_rejects_false_settlement(self):
        out=compute(self.one('APPROVED'));out['root_cause']['category']='settled';out['trace_complete']=True
        self.assertTrue(validate(out))
    def test_no_retry_authority_from_decline(self):
        out=compute(self.one('RJCT','51'));self.assertFalse(out['retry_eligible'])
    def test_invalid_money_and_sequence_rejected(self):
        for amount in [True,'NaN','Infinity',None]:
            d=copy.deepcopy(self.doc);d['amount']=amount;self.assertTrue(input_errors(d)[0])
        d=copy.deepcopy(self.doc);d['legs'][0]['seq']=True;self.assertTrue(input_errors(d)[0])

if __name__=='__main__':unittest.main()
