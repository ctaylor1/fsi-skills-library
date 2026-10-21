import copy,json,unittest
from pathlib import Path
from domain import compute,validate
from foundation_contract import validate_result

class Native(unittest.TestCase):
    def setUp(self):self.doc=json.loads((Path(__file__).parents[1]/'evals/files/financing.json').read_text())
    def result(self):return compute(self.doc)
    def reject(self):self.assertTrue(validate(self.doc))
    def issue(self):
        out=self.result();self.assertEqual(out['status'],'needs-review');self.assertFalse(out['action_taken']);return out['results']
    def test_roundtrip(self):
        out=self.result();self.assertEqual(out['status'],'draft');self.assertEqual(validate_result(out,self.doc,compute),[])
    def test_detached_required(self):self.assertTrue(validate_result(self.result(),None,compute))
    def test_result_tampering(self):
        out=self.result();out['action_taken']=True;self.assertTrue(validate_result(out,self.doc,compute))
    def test_immutable_input(self):
        before=copy.deepcopy(self.doc);self.result();self.assertEqual(before,self.doc)
    def test_unregistered_source(self):
        self.doc['sources']=self.doc['sources'][:1];self.reject()
    def test_cutoff(self):
        self.doc['sources'][0]['known_at']='2026-10-05';self.reject()
    def test_restricted_audience(self):
        self.doc['audience']='client';self.reject()
    def test_unresolved_retained(self):
        self.doc['unresolved_issues']=['Unverified holdings completeness'];self.issue()
    def test_unknown_extension(self):
        self.doc['extension']='unrecognized';self.reject()

    def test_independent_financing_math(self):
        r=self.result()['results'];repo,loan=r['trades'];self.assertEqual(repo['required_collateral_market_value'],'1000.000000000000');self.assertEqual(repo['haircut_adjusted_credit'],'980.00');self.assertEqual(repo['accrued_amount'],'0.294000000000');self.assertEqual(repo['projected_repo_repayment'],'980.980000000000');self.assertEqual(loan['required_collateral_market_value'],'1020.00');self.assertEqual(loan['accrued_amount'],'0.300000000000');self.assertEqual(r['funding_path'][0]['closing_cash'],'119.020000000000');self.assertFalse(r['legal_netting_recognized'])
    def test_act365_not_360(self):
        self.doc['agreements'][0]['day_count']='ACT/365F';self.assertEqual(self.result()['results']['trades'][0]['accrued_amount'],'0.289972602740')
    def test_negative_rate_supported_signed(self):
        self.doc['trades'][0]['annual_rate']='-.036';self.assertEqual(self.result()['results']['trades'][0]['accrued_amount'],'-0.294000000000')
    def test_haircut_not_initial_margin(self):
        self.doc['agreements'][0].update(margin_convention='initial-margin',margin_value='1.02');self.assertEqual(self.result()['results']['trades'][0]['required_collateral_market_value'],'999.60')
    def test_exact_coverage_not_rounded_ratio(self):
        self.doc['collateral_allocations'][0]['allocated_market_value']='999.999999999999999';self.assertFalse(self.issue()['trades'][0]['coverage_sufficient'])
    def test_ineligible_excluded(self):
        self.doc['collateral_inventory'][0]['eligible_agreement_ids']=[];self.assertEqual(self.issue()['trades'][0]['eligible_collateral_market_value'],'0')
    def test_overallocation_does_not_credit_twice(self):
        self.doc['collateral_inventory'][0]['market_value']='999';r=self.issue();self.assertTrue(r['collateral_overallocated']);self.assertFalse(r['trades'][0]['coverage_sufficient'])
    def test_funding_outflows_before_receipts(self):
        self.doc['available_funding_cash']='0';self.doc['committed_funding']=[{'funding_id':'F1','available_date':'2026-10-11','amount':'1000','currency':'USD','status':'supplied-committed','source_ref':'cash'}];r=self.issue();self.assertEqual(r['funding_path'][0]['cash_before_receipts'],'-980.980000000000')
    def test_uncommitted_funding_excluded(self):
        self.doc['committed_funding']=[{'funding_id':'F1','available_date':'2026-10-05','amount':'1000','currency':'USD','status':'proposed','source_ref':'cash'}];r=self.issue();self.assertEqual(len(r['funding_path']),1)
    def test_overdue_recall(self):
        self.doc['recalls'][0]['due_date']='2026-10-03';self.assertTrue(self.issue()['recalls'][0]['overdue'])
    def test_partial_recall(self):
        self.doc['recalls'][0].update(returned_quantity='20',returned_on='2026-10-04');self.assertEqual(self.result()['results']['recalls'][0]['unreturned_quantity'],'30')
    def test_aggregate_recalls(self):
        extra=copy.deepcopy(self.doc['recalls'][0]);extra.update(recall_id='R2',requested_quantity='60');self.doc['recalls'].append(extra);self.reject()
    def test_returned_exceeds_requested(self):
        self.doc['recalls'][0].update(returned_quantity='60',returned_on='2026-10-04');self.reject()
    def test_future_return_not_actual(self):
        self.doc['recalls'][0].update(returned_quantity='20',returned_on='2026-10-05');self.reject()
    def test_unknown_agreement_acceptance(self):
        self.doc['agreements'][0]['acceptance_status']='unknown';self.issue()
    def test_haircut_one_invalid(self):
        self.doc['agreements'][0]['margin_value']='1';self.reject()
    def test_initial_margin_less_than_one(self):
        self.doc['agreements'][1]['margin_value']='.02';self.reject()
    def test_cash_collateral_unsupported(self):
        self.doc['collateral_inventory'][0]['collateral_type']='cash';self.reject()
    def test_wrong_fee_basis(self):
        self.doc['agreements'][1]['rate_basis']='cash-principal';self.reject()
    def test_compounding_unsupported(self):
        self.doc['agreements'][0]['accrual_method']='compound';self.reject()
    def test_rate_reset_unsupported(self):
        self.doc['trades'][0]['rate_effective_to']='2026-10-05';self.reject()
    def test_changing_lending_basis_not_inferred(self):
        self.doc['trades'][1]['basis_constant_over_interval']=False;self.reject()
    def test_missing_constant_basis(self):
        del self.doc['trades'][0]['basis_constant_over_interval'];self.reject()
    def test_renamed_economic_collateral_duplicate(self):
        extra=copy.deepcopy(self.doc['collateral_inventory'][0]);extra['collateral_id']='RENAMED';self.doc['collateral_inventory'].append(extra);self.reject()
    def test_collateral_source_identity_required(self):
        del self.doc['collateral_inventory'][0]['source_position_id'];self.reject()
    def test_stale_collateral(self):
        self.doc['collateral_inventory'][0]['observed_on']='2026-10-03';self.reject()
    def test_stale_trade(self):
        self.doc['trades'][0]['observed_on']='2026-10-03';self.reject()
    def test_nonfinite_rate(self):
        self.doc['trades'][0]['annual_rate']='Infinity';self.reject()
    def test_bool_principal(self):
        self.doc['trades'][0]['cash_principal']=True;self.reject()
    def test_duplicate_collateral_identity(self):
        self.doc['collateral_inventory'].append(copy.deepcopy(self.doc['collateral_inventory'][0]));self.reject()
    def test_mixed_currency(self):
        self.doc['collateral_inventory'][0]['currency']='EUR';self.reject()
    def test_no_netting_of_deficits(self):
        self.doc['collateral_allocations'][0]['allocated_market_value']='999';self.assertFalse(self.issue()['trades'][0]['coverage_sufficient'])

if __name__=="__main__":unittest.main()
