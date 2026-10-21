import copy,json,unittest
from pathlib import Path
from domain import compute,validate
from foundation_contract import validate_result

class Native(unittest.TestCase):
    def setUp(self):self.doc=json.loads((Path(__file__).parents[1]/'evals/files/transition.json').read_text())
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

    def test_independent_arithmetic(self):
        r=self.result()['results'];self.assertEqual(r['estimated_explicit_cost'],'15');self.assertEqual(r['estimated_reference_slippage'],'150');self.assertEqual(r['estimated_combined_cost'],'165');self.assertEqual(r['projected_final_cash'],'9835');self.assertTrue(r['schedule_candidate']);self.assertEqual(r['settlement_cash_path'][0]['conservative_minimum_cash'],'9995');self.assertEqual(r['settlement_cash_path'][1]['conservative_minimum_cash'],'9835')
    def test_slices_aggregate_participation(self):
        extra=copy.deepcopy(self.doc['proposed_slices'][0]);extra['slice_id']='SELL-2';extra['quantity']='1';self.doc['proposed_slices'].append(extra);r=self.issue();self.assertFalse(next(x for x in r['participation'] if x['security_id']=='OLD')['within_cap'])
    def test_decimal_cap_uses_unrounded_product(self):
        self.doc['volume_assumptions'][0]['maximum_participation']='.099999999999999999';self.assertFalse(next(x for x in self.issue()['participation'] if x['security_id']=='OLD')['within_cap'])
    def test_same_day_sale_does_not_fund_buy(self):
        self.doc['initial_settled_cash']='100';self.doc['proposed_slices'][1]['settlement_date']='2026-10-06';r=self.issue();self.assertEqual(r['settlement_cash_path'][0]['conservative_minimum_cash'],'-4965')
    def test_cashflow_outflow_first(self):
        self.doc['external_cashflows']=[{'cashflow_id':'INFLOW','settlement_date':'2026-10-07','amount':'10000','currency':'USD','source_ref':'cash'},{'cashflow_id':'OUTFLOW','settlement_date':'2026-10-07','amount':'-12000','currency':'USD','source_ref':'cash'}];r=self.issue();self.assertEqual(r['settlement_cash_path'][1]['closing_cash'],'7835');self.assertEqual(r['settlement_cash_path'][1]['conservative_minimum_cash'],'-2165')
    def test_target_difference(self):
        self.doc['positions'][1]['target_quantity']='51';self.assertEqual(self.issue()['target_reconciliation'][1]['difference'],'-1')
    def test_cost_budget(self):
        self.doc['policy']['explicit_cost_budget']='14.99';self.issue()
    def test_permitted_side(self):
        self.doc['positions'][0]['sell_permitted']=False;self.issue()
    def test_same_day_shares_not_assumed_deliverable(self):
        self.doc['positions'][0]['current_settled_quantity']='0';extra=copy.deepcopy(self.doc['proposed_slices'][0]);extra.update(slice_id='PREBUY',side='buy',trade_date='2026-10-05',settlement_date='2026-10-06');self.doc['proposed_slices'].insert(0,extra);r=self.issue();self.assertFalse(r['delivery_checks'][0]['deliverable_before_receipts'])
    def test_settlement_before_trade(self):
        self.doc['proposed_slices'][0]['settlement_date']='2026-10-04';self.reject()
    def test_outside_horizon(self):
        self.doc['proposed_slices'][0]['settlement_date']='2026-10-10';self.reject()
    def test_stale_cash(self):
        self.doc['cash_as_of']='2026-10-03';self.reject()
    def test_stale_position(self):
        self.doc['positions'][0]['observed_on']='2026-10-03';self.reject()
    def test_currency(self):
        self.doc['proposed_slices'][0]['currency']='EUR';self.reject()
    def test_units(self):
        self.doc['positions'][0]['unit']='contracts';self.reject()
    def test_derivative_unsupported(self):
        self.doc['positions'][0]['instrument_type']='option';self.reject()
    def test_duplicate_slice(self):
        self.doc['proposed_slices'].append(copy.deepcopy(self.doc['proposed_slices'][0]));self.reject()
    def test_missing_market_volume(self):
        self.doc['volume_assumptions'].pop();self.reject()
    def test_boolean_quantity(self):
        self.doc['proposed_slices'][0]['quantity']=True;self.reject()
    def test_negative_explicit_fee(self):
        self.doc['proposed_slices'][0]['explicit_cost']='-1';self.reject()
    def test_initial_short(self):
        self.doc['positions'][0]['current_settled_quantity']='-1';self.reject()
    def test_nonfinite_price(self):
        self.doc['proposed_slices'][0]['estimated_execution_price']='NaN';self.reject()
    def test_missing_quantity(self):
        self.doc['proposed_slices'][0]['quantity']=None;self.reject()
    def test_excessive_precision(self):
        self.doc['proposed_slices'][0]['quantity']='0.'+'1'*39;self.reject()
    def test_negative_slippage_is_retained(self):
        self.doc['proposed_slices'][0]['estimated_execution_price']='51';self.assertEqual(self.result()['results']['estimated_reference_slippage'],'-50')

if __name__=="__main__":unittest.main()
