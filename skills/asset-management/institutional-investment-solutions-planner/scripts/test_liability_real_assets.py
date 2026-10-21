import copy,json,unittest
from pathlib import Path
from calculate_or_transform import compute
from validate_input import validate
from validate_output import validate as output_errors

class LiabilityTests(unittest.TestCase):
    def setUp(self): self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/phase4-liabilities.json').read_text())
    def test_independent_pv_sensitivity_and_cash_coverage(self):
        out=compute(self.doc);r=out['results'];self.assertEqual(r['liability_present_values'],dict(base='100.0',down='102.00',up='98.00'))
        self.assertEqual(r['effective_duration'],'2.000000000000');self.assertEqual(r['effective_convexity'],'0.000000000000')
        self.assertEqual([x['headroom'] for x in r['scenarios'][0]['cash_coverage']],['10','20'])
        self.assertEqual(r['scenarios'][1]['cash_coverage'][1]['headroom'],'-40');self.assertEqual(r['scenarios'][1]['funding_gap'],'6.00')
        self.assertFalse(r['actuarial_valuation']);self.assertFalse(r['portfolio_optimized']);self.assertEqual(output_errors(out,self.doc),[])
    def test_original_schema_golden_is_unchanged(self):
        p=Path(__file__).resolve().parents[1]/'evals/files';doc=json.loads((p/'request.json').read_text());expected=json.loads((p/'result.json').read_text());self.assertEqual(compute(doc),expected)
    def test_unknown_extension_cannot_fall_back(self):
        self.doc['extension']='other';self.assertTrue(validate(self.doc))
    def test_mixed_legacy_and_new_schema_fails(self):
        self.doc['candidates']=[];self.assertTrue(validate(self.doc))
    def test_wrong_factor_date_id_policy_and_order_fail(self):
        for key,value in [('due_date','2027-10-05'),('liability_id','OTHER'),('policy_version','p2'),('down_factor','0.7')]:
            d=copy.deepcopy(self.doc);d['discount_factors'][0][key]=value;self.assertTrue(validate(d))
    def test_missing_and_duplicate_factor_fail(self):
        self.doc['discount_factors'].pop();self.assertTrue(validate(self.doc))
    def test_principal_double_count_and_early_liquidation_fail(self):
        d=copy.deepcopy(self.doc);flow=copy.deepcopy(d['asset_cashflows'][0]);flow['id']='again';d['asset_cashflows'].append(flow);self.assertTrue(validate(d))
        self.doc['asset_cashflows'][1]['date']='2027-10-04';self.assertTrue(validate(self.doc))
    def test_distributions_are_distinct_from_principal(self):
        self.doc['asset_cashflows'].append(dict(id='income',asset_id='REAL',date='2027-10-04',kind='distribution',currency='USD',amount='5',source_ref='reviewed-fixture'))
        self.assertEqual(compute(self.doc)['results']['scenarios'][0]['cash_coverage'][0]['headroom'],'15')
    def test_stale_valuation_withholds_asset_metrics(self):
        self.doc['assets'][0]['valuation_date']='2026-01-01';out=compute(self.doc)
        self.assertIsNone(out['results']['scenarios'][0]['asset_value']);self.assertEqual(out['results']['scenarios'][0]['cash_coverage'],[])
    def test_incomplete_inventory_withholds_aggregate_pv(self):
        self.doc['inventory_complete']=False;r=compute(self.doc)['results'];self.assertIsNone(r['liability_present_values']['base']);self.assertIsNone(r['effective_duration']);self.assertIsNone(r['scenarios'][0]['liability_pv'])
    def test_stressed_principal_exceeds_asset_value_withholds_coverage(self):
        self.doc['scenarios'][1]['asset_shocks'][0]['cashflow_multiplier']='1';r=compute(self.doc)['results']['scenarios'][1];self.assertEqual(r['cash_coverage'],[]);self.assertTrue(r['issues'])
    def test_exact_illiquidity_limit(self):
        self.doc['policy']['maximum_illiquid_fraction']='0.49999999999999999999999';self.assertTrue(any('illiquid assets exceed' in x for x in compute(self.doc)['unresolved_issues']))
    def test_unknown_asset_and_negative_delay_fail(self):
        for key,value in [('asset_id','OTHER'),('delay_days',-1),('cashflow_multiplier',False)]:
            d=copy.deepcopy(self.doc);d['scenarios'][0]['asset_shocks'][0][key]=value;self.assertTrue(validate(d))
    def test_future_restricted_and_mixed_currency_fail(self):
        d=copy.deepcopy(self.doc);d['assets'][0]['valuation_date']='2026-10-05';self.assertTrue(validate(d))
        d=copy.deepcopy(self.doc);d['sources'][0]['permitted_audiences']=['external'];self.assertTrue(validate(d))
        self.doc['liability_cashflows'][0]['currency']='EUR';self.assertTrue(validate(self.doc))
    def test_zero_pv_keeps_undefined_sensitivity(self):
        for row in self.doc['liability_cashflows']:row['amount']='0'
        self.assertIsNone(compute(self.doc)['results']['effective_duration'])
    def test_detached_output_authority_and_source_mutation_fail(self):
        out=compute(self.doc);out['results']['portfolio_optimized']=True;self.assertTrue(output_errors(out,self.doc));self.assertTrue(output_errors(out,None))

if __name__=='__main__':unittest.main()
