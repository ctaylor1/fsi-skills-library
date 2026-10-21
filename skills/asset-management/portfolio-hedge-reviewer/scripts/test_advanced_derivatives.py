import copy,json,unittest
from pathlib import Path
from advanced_derivatives import compute,validate
from native_integrity import canonical_hash
from foundation_contract import validate_result

class Native(unittest.TestCase):
    def setUp(self):self.doc=json.loads((Path(__file__).parents[1]/'evals/files/advanced_derivatives.json').read_text())
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

    def refresh_hash(self):
        digest=canonical_hash(self.doc['engine_request']);self.doc['engine_result']['request_hash']=digest;self.doc['independent_benchmark']['request_hash']=digest
    def test_independent_nonlinear_difference(self):
        r=self.result()['results'];stress=r['comparison'][0]['scenarios'][1];self.assertEqual(stress['baseline_pnl'],'-40');self.assertEqual(stress['hedged_book_pnl_before_cost'],'-15');self.assertEqual(stress['incremental_pnl_before_cost'],'25');self.assertEqual(stress['hedged_book_pnl_after_supplied_cost'],'-17');self.assertIsNone(r['hedge_selection']);self.assertFalse(r['engine_review']['engine_invoked'])
    def test_unavailable_engine_no_fallback(self):
        self.doc['engine_result']=None;self.assertEqual(self.issue()['comparison'],[])
    def test_missing_benchmark_no_fallback(self):
        self.doc['independent_benchmark']=None;self.assertEqual(self.issue()['comparison'],[])
    def test_failed_engine_no_fallback(self):
        self.doc['engine_result']['status']='failed';self.assertEqual(self.issue()['comparison'],[])
    def test_partial_engine_no_fallback(self):
        self.doc['engine_result']['status']='partial';self.assertEqual(self.issue()['comparison'],[])
    def test_engine_unresolved_blocks(self):
        self.doc['engine_result']['unresolved_issues']=['Calibration failed'];self.assertEqual(self.issue()['comparison'],[])
    def test_benchmark_break_withholds(self):
        self.doc['independent_benchmark']['values'][0]['value']='101';self.assertEqual(self.issue()['comparison'],[])
    def test_precision_boundary_comparison(self):
        self.doc['independent_benchmark']['values'][0]['value']='100.01000000000000000001';self.assertEqual(self.issue()['comparison'],[])
    def test_engine_coverage(self):
        self.doc['engine_result']['values'].pop();self.reject()
    def test_expected_inventory_complete(self):
        self.doc['engine_request']['expected_metrics'].pop();self.refresh_hash();self.reject()
    def test_engine_version(self):
        self.doc['engine_result']['engine_version']='5';self.reject()
    def test_input_digest(self):
        self.doc['engine_request']['input']['instruments'][0]['terms']['barrier']='70';self.reject()
    def test_engine_units(self):
        self.doc['engine_result']['values'][0]['unit']='EUR';self.reject()
    def test_independent_source_required(self):
        self.doc['independent_benchmark']['source_ref']='engine-result';self.reject()
    def test_binary_float_engine_value(self):
        self.doc['engine_result']['values'][0]['value']=100.0;self.reject()
    def test_nonfinite_engine(self):
        self.doc['engine_result']['values'][0]['value']='NaN';self.reject()
    def test_future_observation(self):
        self.doc['engine_result']['observed_on']='2026-10-05';self.reject()
    def test_scope_mismatch(self):
        self.doc['engine_result']['object_id']='OTHER';self.reject()
    def test_cost_horizon_required(self):
        self.doc['engine_request']['input']['candidate_costs'][0]['horizon']='';self.refresh_hash();self.reject()
    def test_cost_not_double_counted(self):
        self.doc['engine_request']['input']['cost_basis']='includes-cost';self.refresh_hash();self.reject()
    def test_base_shock_invalid(self):
        self.doc['engine_request']['input']['scenarios'][0]['shocks']={'equity':{'unit':'fraction','value':'.1'}};self.refresh_hash();self.reject()
    def test_linear_method_not_substituted(self):
        self.doc['engine_request']['input']['valuation_method']='delta-only';self.refresh_hash();self.reject()
    def test_empty_terms(self):
        self.doc['engine_request']['input']['instruments'][0]['terms']={};self.refresh_hash();self.reject()
    def test_sensitivity_units_required(self):
        self.doc['engine_request']['input']['measures'][1]['unit']='';self.refresh_hash();self.reject()
    def test_legacy_path_still_independent(self):
        import subprocess,sys
        result=subprocess.run([sys.executable,str(Path(__file__).with_name('calculate_or_transform.py')),'--selftest'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

if __name__=='__main__':unittest.main()
