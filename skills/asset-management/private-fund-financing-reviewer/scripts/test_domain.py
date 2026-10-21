import copy,json,unittest
from pathlib import Path
from domain import compute,validate
from validate_output import validate as output_errors

class FacilityTests(unittest.TestCase):
    def setUp(self): self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/phase4-subscription.json').read_text())
    def test_independent_subscription_numbers(self):
        out=compute(self.doc);r=out['results']
        for k,v in {'borrowing_base':'75.0000','draw_headroom':'38.0000','leverage_headroom':'60.0','fund_debt_to_nav':'0.200000000000','interest_cost':'0.300000000000','undrawn_fee_cost':'0.065000000000','total_period_cost':'1.365000000000'}.items(): self.assertEqual(r[k],v)
        self.assertFalse(r['borrowing_authorized']);self.assertEqual(output_errors(out,self.doc),[])
    def test_independent_nav_method(self):
        doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/phase4-nav.json').read_text())
        self.assertEqual(compute(doc)['results']['borrowing_base'],'75.0000')
    def test_ineligible_collateral_gets_no_credit(self):
        self.doc['collateral'][0]['eligible']=False
        out=compute(self.doc);self.assertEqual(out['results']['borrowing_base'],'30.000');self.assertTrue(out['unresolved_issues'])
    def test_unrounded_covenant_boundary(self):
        self.doc['agreement']['maximum_fund_debt_to_nav']='0.2';self.doc['facility']['proposed_draw']='10.000000000000000000000001'
        out=compute(self.doc);self.assertIn('pro forma fund debt exceeds supplied leverage covenant',out['unresolved_issues'])
        self.assertEqual(out['results']['fund_debt_to_nav'],'0.200000000000')
    def test_negative_headroom_not_clipped(self):
        self.doc['facility']['proposed_draw']='50'
        self.assertEqual(compute(self.doc)['results']['draw_headroom'],'-2.0000')
    def test_incomplete_register_withholds_base(self):
        self.doc['inventory_complete']=False;self.assertIsNone(compute(self.doc)['results']['borrowing_base'])
    def test_raw_register_total_mismatch_withholds_base(self):
        self.doc['facility']['total_uncalled_commitments']='201';self.assertIsNone(compute(self.doc)['results']['draw_headroom'])
    def test_mixed_basis_duplicate_missing_caps_fail(self):
        for change in (lambda d:d['collateral'][0].update(nav='120'),lambda d:d['collateral'][1].update(id='LP-A'),lambda d:d['concentration_limits'].pop(),lambda d:d['agreement'].update(concentration_method='circular-base')):
            d=copy.deepcopy(self.doc);change(d);self.assertTrue(validate(d))
    def test_wrong_currency_and_agreement_fail(self):
        for key,value in [('currency','EUR'),('agreement_version','a2')]:
            d=copy.deepcopy(self.doc);d['collateral'][0][key]=value;self.assertTrue(validate(d))
    def test_unpermitted_proceeds_and_maturity_preserved(self):
        self.doc['facility'].update(proceeds_use='LP distribution',maturity_date='2026-10-01')
        self.assertEqual(len(compute(self.doc)['unresolved_issues']),2)
    def test_numerics_and_stale_restricted_future_sources_fail(self):
        for value in (True,None,'NaN','-0.1','1.0001'):
            d=copy.deepcopy(self.doc);d['collateral'][0]['haircut']=value;self.assertTrue(validate(d))
        for field,value in [('expires_at','2026-10-03'),('known_at','2026-10-05'),('permitted_audiences',['external'])]:
            d=copy.deepcopy(self.doc);d['sources'][0][field]=value;self.assertTrue(validate(d))
    def test_detached_output_authority_and_source_change_fail(self):
        out=compute(self.doc);out['results']['borrowing_authorized']=True;self.assertTrue(output_errors(out,self.doc))
        out=compute(self.doc);self.doc['facility']['outstanding']='21';self.assertTrue(output_errors(out,self.doc));self.assertTrue(output_errors(out,None))
    def test_draw_after_agreement_expiry_cannot_clear(self):
        self.doc['agreement']['expires']='2026-11-01'
        self.doc['facility'].update(proposed_draw_date='2026-12-01',maturity_date='2027-01-01')
        self.assertIn('proposed draw date is outside supplied reviewed agreement effective period',compute(self.doc)['unresolved_issues'])
    def test_draw_at_agreement_expiry_is_within_supplied_interval(self):
        self.doc['agreement']['expires']='2026-11-01'
        self.doc['facility'].update(proposed_draw_date='2026-11-01',maturity_date='2027-01-01')
        self.assertNotIn('proposed draw date is outside supplied reviewed agreement effective period',compute(self.doc)['unresolved_issues'])

if __name__=='__main__':unittest.main()
