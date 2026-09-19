#!/usr/bin/env python3
"""Repair plan exact-diff, policy, screening, and offline-boundary regressions."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import build_plan,plan_hash
from validate_input import validate as validate_input,repair_binding
from validate_output import validate

class RepairTests(unittest.TestCase):
    def setUp(self):self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/case_example.json').read_text())
    def test_roundtrip_and_exact_change(self):
        plan=build_plan(self.doc);self.assertEqual(plan['status'],'planned');self.assertEqual(validate(plan),[])
        self.assertEqual(plan['exact_change'],{'field':'beneficiary_bic','before':'DEUTDEF','after':'DEUTDEFF'})
    def test_new_value_bound_to_screening_and_plan(self):
        plan=build_plan(self.doc);self.doc['proposed_repair']['new_value']='CHASUS33'
        self.assertEqual(build_plan(self.doc)['status'],'rejected')
        self.doc['screening']['repair_binding']=repair_binding(self.doc)
        revised=build_plan(self.doc);self.assertEqual(revised['status'],'planned');self.assertNotEqual(plan['plan_hash'],revised['plan_hash'])
    def test_old_value_must_match_snapshot(self):
        self.doc['proposed_repair']['old_value']='WRONG';self.assertTrue(validate_input(self.doc)[0])
    def test_missing_or_unchanged_replacement_rejected(self):
        for value in [None,'','DEUTDEF']:
            d=copy.deepcopy(self.doc);d['proposed_repair']['new_value']=value;self.assertEqual(build_plan(d)['status'],'rejected')
    def test_confirmation_is_required(self):
        self.doc['exception_confirmation']['status']='suspected';self.assertEqual(build_plan(self.doc)['status'],'rejected')
    def test_policy_scope_and_effective_time(self):
        for key,value in [('entity_id','OTHER'),('currency','EUR'),('rails',['Fedwire']),('allowed_fields',['purpose_code']),('max_amount','100'),('expires_at','2026-07-15T00:00:00Z')]:
            d=copy.deepcopy(self.doc);d['policy'][key]=value;self.assertEqual(build_plan(d)['status'],'rejected',key)
    def test_policy_role_version_limit_in_hash(self):
        baseline=build_plan(self.doc)['plan_hash']
        for key,value in [('version','2026.08'),('required_approver_role','payments-senior-supervisor'),('max_amount','200000')]:
            d=copy.deepcopy(self.doc);d['policy'][key]=value;self.assertNotEqual(build_plan(d)['plan_hash'],baseline,key)
    def test_numerics_are_finite_and_currency_explicit(self):
        for value in [True,'NaN','Infinity',None]:
            d=copy.deepcopy(self.doc);d['proposed_repair']['amount']=value;self.assertTrue(validate_input(d)[0])
        del self.doc['proposed_repair']['currency'];self.assertTrue(validate_input(self.doc)[0])
    def test_settled_payment_and_returns_not_repair(self):
        self.doc['payment_snapshot']['state']='settled';self.assertEqual(build_plan(self.doc)['status'],'rejected')
        self.doc['type']='unrecoverable_reject';self.assertEqual(build_plan(self.doc)['status'],'rejected')
    def test_executed_even_with_token_and_rehash_rejected(self):
        p=build_plan(self.doc);p['approval'].update(status='approved',token='fake-valid-token',approver='supervisor')
        p['execution']={'state':'executed','executed_steps':['S1','S2']};p['plan_hash']=plan_hash(p)
        self.assertTrue(validate(p))
    def test_tamper_rehash_does_not_override_source(self):
        for field,value in [('amount','1'),('end_to_end_id','other'),('policy',{})]:
            p=build_plan(self.doc);p[field]=value;p['plan_hash']=plan_hash(p);self.assertTrue(validate(p),field)
    def test_idempotency_scope_survives_replanning(self):
        first=build_plan(self.doc);self.doc['as_of']='2026-07-16T15:05:00Z';second=build_plan(self.doc)
        self.assertNotEqual(first['plan_id'],second['plan_id']);self.assertEqual(first['steps'][1]['idempotency_scope'],second['steps'][1]['idempotency_scope'])
    def test_valid_rejected_plan_validates(self):
        self.doc['screening']['status']='pending';out=build_plan(self.doc)
        self.assertEqual(out['status'],'rejected');self.assertEqual(out['steps'],[]);self.assertEqual(validate(out),[])

if __name__=='__main__':unittest.main()
