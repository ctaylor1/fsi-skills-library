"""Native behavior and evidence regressions; no professional acceptance claim."""
import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from domain import evaluate, validate
from workflow_contract import build_artifact
from workflow_foundation import run, check_output
NAME = 'insurance-core-modernization-planner'
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

    def test_control_and_cost_math(self):
        x=self.result()['results'];self.assertEqual(Decimal(x['option_comparison'][0]['undiscounted_supplied_cost']),120000);self.assertEqual(Decimal(x['reconciliation'][0]['difference']),0);self.assertEqual(x['dependency_order'],['B1'])
    def test_reconciliation_break_is_visible(self):
        self.doc['data']['reconciliations'][0]['target_value']=99;x=self.result();self.assertEqual(x['status'],'needs-review');self.assertEqual(Decimal(x['results']['reconciliation'][0]['difference']),-1)
    def test_cycle_not_scheduled(self):
        self.doc['data']['batches'][0]['depends_on']=['B1'];self.assertIsNone(self.gap()['dependency_order'])
    def test_delta_recovery_required(self):
        del self.doc['data']['batches'][0]['delta_recovery_evidence'];self.gap()
    def test_wrong_snapshot_withholds_delta(self):
        self.doc['data']['reconciliations'][0]['source_snapshot']='other';self.assertIsNone(self.gap()['reconciliation'][0]['difference'])
    def test_missing_option_fit(self):
        self.doc['data']['options'][0]['fits']=[];self.gap()
    def test_failed_mandatory_not_ranked(self):
        self.doc['data']['options'][0]['fits'][0]['disposition']='not-met';x=self.result();self.assertEqual(x['status'],'needs-review');self.assertIsNone(x['results']['selected_option'])
    def test_unknown_cost_not_zero(self):
        self.doc['data']['options'][0]['costs'][0]['amount']=None;self.assertIsNone(self.gap()['option_comparison'][0]['undiscounted_supplied_cost'])
    def test_boolean_control_rejected(self):
        self.doc['data']['reconciliations'][0]['source_value']=True
        with self.assertRaises(ValueError):self.result()

if __name__=='__main__': unittest.main()
