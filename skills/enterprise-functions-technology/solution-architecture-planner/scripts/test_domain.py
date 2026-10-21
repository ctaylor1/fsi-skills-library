"""Native behavior and evidence regressions; no professional acceptance claim."""
import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from domain import evaluate, validate
from workflow_contract import build_artifact
from workflow_foundation import run, check_output
NAME = 'solution-architecture-planner'
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

    def test_capacity_and_period_cost(self):
        x=self.result()['results'];self.assertEqual(Decimal(x['supplied_period_cost']),300);self.assertTrue(x['requirement_fit'][0]['meets'])
    def test_wrong_workload_measurement_not_fit(self):
        self.doc['data']['measurements'][0]['workload_profile']='different';self.assertIsNone(self.gap()['requirement_fit'][0]['meets'])
    def test_missing_measurement_not_pass(self):
        self.doc['data']['measurements']=[];self.gap()
    def test_capacity_failure_keeps_observed_result(self):
        self.doc['data']['measurements'][0]['value']=80;x=self.result();self.assertEqual(x['status'],'needs-review');self.assertFalse(x['results']['requirement_fit'][0]['meets'])
    def test_write_receipt_required(self):
        del self.doc['data']['interfaces'][0]['receipt_check'];self.gap()
    def test_retry_boolean_rejected(self):
        self.doc['data']['interfaces'][0]['max_attempts']=True
        with self.assertRaises(ValueError):self.result()
    def test_mixed_cost_currency(self):
        self.doc['data']['components'][0]['currency']='EUR';self.assertIsNone(self.gap()['supplied_period_cost'])
    def test_missing_endpoint(self):
        self.doc['data']['interfaces'][0]['to_component']='absent';self.gap()

if __name__=='__main__': unittest.main()
