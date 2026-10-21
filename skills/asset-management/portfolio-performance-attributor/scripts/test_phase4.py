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
    def test_same_currency_fx_return_must_be_zero(self):
        d=fixture('currency');d['segments'][0]['local_currency']=d['currency'];d['segments'][0]['fx_return']='.1';self.rejects(d)
    def test_local_currency_requires_uppercase_code(self):
        d=fixture('currency');d['segments'][0]['local_currency']='usd';self.rejects(d)
    def test_currency_method_requires_base_currency(self):
        d=fixture('currency');d['currency']='not-applicable';self.rejects(d)
    def test_hedge_contribution_known_before_period_end_rejected(self):
        d=fixture('currency');d['hedge_source_ref']='early-hedge-record';d['sources'].append({'source_ref':'early-hedge-record','version':'1','as_of':d['period_start'],'known_at':d['period_start']});self.rejects(d)
    def rejects(self,doc):
        with self.assertRaises((ValueError,TypeError,KeyError,ArithmeticError)): compute(doc)
    def test_currency_independent(self):
        r=compute(fixture('currency'))['results']
        for key,value in {'portfolio_return':'.09384','benchmark_return':'.0619','active_return':'.03194','residual':'0'}.items(): self.assertEqual(D(r[key]),D(value))
        self.assertEqual({k:D(v) for k,v in r['effects'].items()},{'local':D('.023'),'currency':D('.007'),'local_currency_interaction':D('.00094'),'supplied_hedge':D('.001')})
    def test_duration_residual_retained(self):
        r=compute(fixture('fixed-income'));self.assertEqual(D(r['results']['explained_active_return']),D('-.0095'));self.assertEqual(D(r['results']['residual']),D('.0045'));self.assertTrue(r['unresolved_issues'])
    def test_factor_residual(self):
        r=compute(fixture('factor'));self.assertEqual(D(r['results']['residual']),D('.001'));self.assertTrue(r['unresolved_issues'])
    def test_recursive_linking(self):
        r=compute(fixture('linking'))['results'];self.assertEqual(D(r['active_return']),D('.0312'));self.assertEqual(D(r['effects']['selection']),D('.0257'));self.assertEqual(D(r['effects']['allocation']),D('.0055'))
    def test_missing_weight(self):
        d=fixture('currency');d['segments'].pop();self.rejects(d)
    def test_unknown_source(self):
        d=fixture('factor');d['factors'][0]['source_ref']='absent';self.rejects(d)
    def test_missing_period(self):
        d=fixture('linking');d['periods'][1]['period_start']='2026-09-02';self.rejects(d)
    def test_future_source(self):
        d=fixture('currency');d['sources'][0]['known_at']='2026-10-03';self.rejects(d)
    def test_no_implicit_percent(self):
        d=fixture('currency');d['return_unit']='percent';self.rejects(d)
    def test_unknown_extension(self):
        d=fixture('factor');d['extension']='other';self.rejects(d)
    def test_detached_input_and_tampering(self):
        d=fixture('currency');r=compute(d);self.assertEqual(validate_result(r,d,compute),[]);r['results']['active_return']='1';self.assertTrue(validate_result(r,d,compute))

if __name__=='__main__': unittest.main()
