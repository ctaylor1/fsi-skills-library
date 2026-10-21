"""Native behavior and evidence regressions; no professional acceptance claim."""
import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from domain import evaluate, validate
from workflow_contract import build_artifact
from workflow_foundation import run, check_output
NAME = 'workflow-automation-assessor'
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

    def test_pair_and_projection_math(self):
        x=self.result()['results'];self.assertEqual(Decimal(x['human_minutes_saved_per_case']),13);s=x['scenarios'][0];self.assertEqual(Decimal(s['annual_cash_net']),26500);self.assertEqual(Decimal(s['eligible_annual_volume']),5000);self.assertTrue(x['pilot_candidate'])
    def test_missing_pair_blocks_means(self):
        self.doc['data']['cases'][0]['candidate_human_minutes']=None;self.assertIsNone(self.gap()['human_minutes_saved_per_case'])
    def test_fractional_volume_is_scenario_not_observed_count(self):
        self.doc['data']['scenarios'][0]['eligible_fraction']='.125';self.assertEqual(Decimal(self.result()['results']['scenarios'][0]['eligible_annual_volume']),1250)
    def test_controls_override_positive_economics(self):
        self.doc['data']['controls'][0]['status']='failed';x=self.result()['results'];self.assertFalse(x['pilot_candidate']);self.assertGreater(Decimal(x['scenarios'][0]['annual_cash_net']),0)
    def test_autonomous_regulated_decision_not_recommended(self):
        self.doc['data']['requested_mode']='autonomous-regulated-decision';self.assertFalse(self.result()['results']['pilot_candidate'])
    def test_error_guardrail(self):
        self.doc['data']['cases'][0]['candidate_error']=True;x=self.result()['results'];self.assertFalse(x['pilot_candidate']);self.assertEqual(Decimal(x['observed_error_rates']['candidate']),Decimal('.5'))
    def test_cash_not_capacity(self):
        self.doc['data']['scenarios'][0]['cash_realization_fraction']=0;x=self.result()['results']['scenarios'][0];self.assertGreater(Decimal(x['capacity_hours']),0);self.assertEqual(Decimal(x['annual_cash_net']),-6000);self.assertIsNone(x['simple_payback_months'])
    def test_boolean_cost_rejected(self):
        self.doc['data']['cases'][0]['candidate_nonlabor_cost']=False
        with self.assertRaises(ValueError):self.result()

if __name__=='__main__': unittest.main()
