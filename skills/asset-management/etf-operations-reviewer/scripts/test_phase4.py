#!/usr/bin/env python3
"""Independent arithmetic expectations and adversarial Phase 4 regressions."""
import copy,json,unittest
from decimal import Decimal as D
from pathlib import Path
from calculate_or_transform import compute
from foundation_contract import validate_result
ROOT=Path(__file__).resolve().parents[1]
def fixture(name): return json.loads((ROOT/'evals/files'/('phase4-'+name+'-input.json')).read_text())
class Tests(unittest.TestCase):
    def test_independent_engine_component_value(self):
        r=compute(fixture('engine-forward'))['results'];self.assertEqual(D(r['securities_value_per_unit']),D('2594'));self.assertEqual(D(r['value_difference']),0);self.assertFalse(r['engine_review']['engine_invoked'])
    def test_rehashed_engine_other_instrument_rejected(self):
        from native_integrity import canonical_hash
        d=fixture('engine-forward');d['engine_request']['input']['components'][0]['instrument_id']='OTHER';digest=canonical_hash(d['engine_request']);d['engine_record']['request_hash']=digest;d['benchmark']['request_hash']=digest;self.rejects(d)
    def test_engine_benchmark_break_withholds_total(self):
        d=fixture('engine-forward');d['benchmark']['values'][0]['value']='2';r=compute(d)['results'];self.assertIsNone(r['securities_value_per_unit']);self.assertIsNone(r['value_difference'])
    def test_missing_engine_never_prices_locally(self):
        d=fixture('engine-forward');d['engine_record']=None;self.assertIsNone(compute(d)['results']['securities_value_per_unit'])
    def test_engine_per_contract_unit_required(self):
        d=fixture('engine-forward');d['engine_record']['values'][0]['unit']='USD';self.rejects(d)
    def rejects(self,doc):
        with self.assertRaises((ValueError,TypeError,KeyError,ArithmeticError)): compute(doc)
    def test_dirty_fx_and_custom_basket(self):
        r=compute(fixture('specialized-basket'))['results'];self.assertEqual(D(r['components'][0]['local_value_per_unit']),D('990'));self.assertEqual(D(r['securities_value_per_unit']),D('2089'));self.assertEqual(D(r['value_difference']),0);self.assertEqual(D(r['indicative_ap_cash']),27)
    def test_redemption_cash(self):
        d=fixture('specialized-basket');d['direction']='redemption';self.assertEqual(D(compute(d)['results']['indicative_ap_cash']),17)
    def test_unreviewed_substitution(self):
        d=fixture('specialized-basket');d['custom_reviews']=[];self.rejects(d)
    def test_standard_substitution(self):
        d=fixture('specialized-basket');d['basket_type']='standard';self.rejects(d)
    def test_missing_reference(self):
        d=fixture('specialized-basket');d['components'].pop();self.rejects(d)
    def test_stale_fx(self):
        d=fixture('specialized-basket');d['components'][0]['fx_date']='2026-10-01';self.rejects(d)
    def test_fx_convention(self):
        d=fixture('specialized-basket');d['components'][0]['fx_convention']='local-per-base';self.rejects(d)
    def test_unit_convention(self):
        d=fixture('specialized-basket');d['components'][0]['quantity_unit']='shares';self.rejects(d)
    def test_closed_market(self):
        d=fixture('specialized-basket');d['market_calendars'][0]['open']=False;self.assertTrue(compute(d)['unresolved_issues'])
    def test_late_settlement(self):
        d=fixture('specialized-basket');d['components'][0]['settlement_date']='2026-10-07';self.assertTrue(compute(d)['unresolved_issues'])
    def test_fractional_unit(self):
        d=fixture('specialized-basket');d['creation_units']='1.1';self.rejects(d)
    def test_detached_input(self):
        d=fixture('specialized-basket');r=compute(d);self.assertEqual(validate_result(r,d,compute),[]);r['results']['indicative_ap_cash']='28';self.assertTrue(validate_result(r,d,compute))

if __name__=='__main__': unittest.main()
