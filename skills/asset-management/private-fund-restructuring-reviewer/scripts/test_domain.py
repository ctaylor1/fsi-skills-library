import copy,json,unittest
from pathlib import Path
from domain import compute,validate
from validate_output import validate as output_errors

class SecondaryTests(unittest.TestCase):
    def setUp(self): self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/phase4-continuation.json').read_text())
    def test_independent_cash_roll_bridge(self):
        out=compute(self.doc);r=out['results']['options'][0]
        for k,v in {'adjusted_whole_interest_price':'95.0','net_cash_at_settlement':'40.50','net_rolled_capital':'51.00','total_transaction_fees':'1.5','total_crystallized_carry':'2','new_uncalled_commitment':'10'}.items(): self.assertEqual(r[k],v)
        self.assertFalse(out['results']['election_authorized']);self.assertIsNone(out['results']['selected_option']);self.assertEqual(output_errors(out,self.doc),[])
    def test_independent_lp_partial_sale(self):
        doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/phase4-secondary.json').read_text());r=compute(doc)['results']['options'][0]
        self.assertEqual(r['net_cash_at_settlement'],'54.00');self.assertEqual(r['retained_reference_nav'],'42.0');self.assertEqual(r['net_rolled_capital'],'0')
    def test_missing_cashflows_withholds_amounts(self):
        self.doc['flow_inventory_complete']=False;self.assertIsNone(compute(self.doc)['results']['options'][0]['net_cash_at_settlement'])
    def test_duplicate_economic_event_rejected(self):
        self.doc['interim_flows'].append(copy.deepcopy(self.doc['interim_flows'][0]));self.assertTrue(validate(self.doc))
    def test_pre_nav_and_future_events_rejected(self):
        for date in ('2026-09-01','2026-10-05'):
            d=copy.deepcopy(self.doc);d['interim_flows'][0]['date']=date;self.assertTrue(validate(d))
    def test_open_conflict_preserved(self):
        self.doc['conflicts']=[dict(id='GP-1',description='GP participates on both sides',owner='independent committee',status='open',source_ref='reviewed-fixture')]
        self.assertIn('transaction conflict remains open: GP-1',compute(self.doc)['unresolved_issues'])
    def test_false_status_quo_is_flagged(self):
        self.doc['options'][0].update(status_quo_claimed=True,new_management_fee_rate='0.025')
        self.assertTrue(any('status quo' in s for s in compute(self.doc)['unresolved_issues']))
    def test_short_or_expired_election_period_flagged(self):
        self.doc['transaction'].update(decision_deadline='2026-10-03',minimum_review_days=10)
        issues=compute(self.doc)['unresolved_issues'];self.assertTrue(any('deadline has passed' in s for s in issues));self.assertTrue(any('shorter' in s for s in issues))
    def test_wrong_version_currency_and_mixed_modes_fail(self):
        for key,value in [('transaction_version','t2'),('currency','EUR'),('sale_fraction','0.5')]:
            d=copy.deepcopy(self.doc);d['options'][0][key]=value;self.assertTrue(validate(d))
    def test_cash_only_cannot_hide_roll_obligations(self):
        self.doc['options'][0]['roll_fraction']='0';self.assertTrue(validate(self.doc))
    def test_invalid_amounts_and_source_rights_fail(self):
        for value in (False,None,'NaN','-1'):
            d=copy.deepcopy(self.doc);d['options'][0]['cash_fees']=value;self.assertTrue(validate(d))
        self.doc['sources'][0]['permitted_audiences']=['external'];self.assertTrue(validate(self.doc))
    def test_detached_output_rejects_fabricated_election(self):
        out=compute(self.doc);out['results']['selected_option']='half-roll';self.assertTrue(output_errors(out,self.doc))
        self.assertTrue(output_errors(compute(self.doc),None))
    def test_lp_sale_cannot_silently_ignore_continuation_fields(self):
        original=json.loads((Path(__file__).resolve().parents[1]/'evals/files/phase4-secondary.json').read_text())
        for key in ('roll_fees','roll_crystallized_carry','upfront_new_capital','new_uncalled_commitment'):
            doc=copy.deepcopy(original);doc['options'][0][key]='1'
            self.assertTrue(validate(doc),key)
    def test_status_quo_requires_no_new_capital_commitment(self):
        option=self.doc['options'][0]
        option.update(status_quo_claimed=True,new_management_fee_rate=self.doc['transaction']['existing_management_fee_rate'],new_carried_interest_rate=self.doc['transaction']['existing_carried_interest_rate'],side_letter_treatment='preserved',cash_fees='0',roll_fees='0',cash_crystallized_carry='0',roll_crystallized_carry='0',upfront_new_capital='0',new_uncalled_commitment='1')
        self.assertTrue(any('status quo' in issue for issue in compute(self.doc)['unresolved_issues']))
    def test_status_quo_also_retains_transaction_fees_and_upfront_capital(self):
        base=copy.deepcopy(self.doc)
        base['options'][0].update(status_quo_claimed=True,new_management_fee_rate=self.doc['transaction']['existing_management_fee_rate'],new_carried_interest_rate=self.doc['transaction']['existing_carried_interest_rate'],side_letter_treatment='preserved',cash_fees='0',roll_fees='0',cash_crystallized_carry='0',roll_crystallized_carry='0',upfront_new_capital='0',new_uncalled_commitment='0')
        self.assertFalse(any('status quo' in issue for issue in compute(base)['unresolved_issues']))
        for key in ('cash_fees','roll_fees','upfront_new_capital'):
            doc=copy.deepcopy(base);doc['options'][0][key]='1'
            self.assertTrue(any('status quo' in issue for issue in compute(doc)['unresolved_issues']),key)

if __name__=='__main__':unittest.main()
