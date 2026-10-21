"""Native behavior and evidence regressions; no professional acceptance claim."""
import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from domain import evaluate, validate
from workflow_contract import build_artifact
from workflow_foundation import run, check_output
NAME = 'data-product-value-evaluator'
class Native(unittest.TestCase):
    def setUp(self): self.doc=json.loads((Path(__file__).parents[1]/'evals/files/input.json').read_text())
    def result(self): return run(self.doc,NAME,evaluate,validate)
    def gap(self):
        out=self.result();self.assertEqual(out['status'],'needs-data',out['findings']);self.assertFalse(out['action_taken']);return out['results']
    def test_native_roundtrip(self):
        out=self.result();self.assertEqual(out['status'],'ready-for-review',out['findings']);self.assertEqual(check_output(out,NAME,evaluate,validate),[])
    def test_source_retention(self):
        before=copy.deepcopy(self.doc);out=self.result();self.assertEqual(self.doc,before);self.assertEqual(out['source_document'],before)
    def test_unsupported_method(self):
        self.doc['data']['profile']['method']='unsupported';self.gap()
    def test_expired_profile(self):
        self.doc['data']['profile']['effective_to']='2025-01-01';self.gap()
    def test_source_date_future(self):
        self.doc['sources'][0]['as_of']='2026-09-21';self.gap()
    def test_source_date_unknown(self):
        del self.doc['sources'][0]['as_of'];self.gap()
    def test_duplicate_source_identity(self):
        self.doc['sources'].append(copy.deepcopy(self.doc['sources'][0]))
        with self.assertRaises(ValueError):self.result()
    def test_inherited_uncertainty(self):
        self.doc['unresolved_issues']=['Production acceptance not established'];out=self.result();self.assertEqual(out['status'],'needs-data');self.assertIn('Production acceptance not established',out['unresolved_issues'])
    def test_resealed_result_tampering(self):
        out=self.result();out['results']['invented']=True;out['artifact']=build_artifact(out['source_document'],out,producer=NAME,artifact_type='workflow-review',completeness=out['completeness'],evaluability=out['evaluability'],issues=out['unresolved_issues']);self.assertTrue(check_output(out,NAME,evaluate,validate))
    def test_no_execution_authority(self):
        out=self.result();out['execution']='performed';self.assertTrue(check_output(out,NAME,evaluate,validate))

    def test_paired_outcomes_and_projection(self):
        x=self.result()['results'];self.assertEqual(Decimal(x['observed_outcome_cost_reduction']),110);self.assertEqual(Decimal(x['projected_annual_net']),40000);self.assertEqual(x['confusion_matrices']['augmented']['tp'],1);self.assertEqual(x['confusion_matrices']['augmented']['tn'],1)
    def test_temporal_leakage_withholds_uplift(self):
        self.doc['data']['cases'][0]['provider_available_on']='2026-08-02';self.assertIsNone(self.gap()['observed_outcome_cost_reduction'])
    def test_unknown_prediction_not_negative(self):
        self.doc['data']['cases'][0]['augmented_prediction']=None;self.assertIsNone(self.gap()['confusion_matrices'])
    def test_zero_positive_denominator_unknown(self):
        for x in self.doc['data']['cases']:x['augmented_prediction']=False
        self.assertIsNone(self.result()['results']['confusion_matrices']['augmented']['precision'])
    def test_license_purpose_mismatch(self):
        self.doc['data']['license']['purpose']='marketing';self.assertFalse(self.gap()['license_usable_for_stated_purpose'])
    def test_no_projection_without_representativeness(self):
        self.doc['data']['projection']['representativeness_reviewed']=False
        result=self.gap()
        self.assertIsNone(result['projected_annual_net'])
        self.assertTrue(result['license_usable_for_stated_purpose'])
        self.assertEqual(Decimal(result['observed_outcome_cost_reduction']),110)
    def test_observed_only_evaluation(self):
        self.doc['data']['projection']=None;x=self.result()['results'];self.assertEqual(Decimal(x['observed_outcome_cost_reduction']),110);self.assertIsNone(x['projected_annual_net'])
    def test_unknown_cost_not_zero(self):
        self.doc['data']['cases'][0]['augmented_outcome_cost']=None;self.assertIsNone(self.gap()['observed_outcome_cost_reduction'])

if __name__=='__main__': unittest.main()
