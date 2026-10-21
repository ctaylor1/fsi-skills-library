"""Native behavior and evidence regressions; no professional acceptance claim."""
import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from domain import evaluate, validate
from workflow_contract import build_artifact
from workflow_foundation import run, check_output
NAME = 'insurance-workflow-designer'
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

    def test_weighted_path_math(self):
        x=self.result()['results']['weighted_minutes'];self.assertEqual(Decimal(x['current']['human_minutes']),14);self.assertEqual(Decimal(x['target']['human_minutes']),13);self.assertEqual(Decimal(x['current']['elapsed_minutes']),32);self.assertEqual(Decimal(x['target']['elapsed_minutes']),27)
    def test_branch_mass_not_renormalized(self):
        self.doc['data']['paths'][0]['share']='.5';self.assertIsNone(self.gap()['weighted_minutes']['current']['human_minutes'])
    def test_unowned_machine_failure(self):
        self.doc['data']['steps'][1]['failure_step']='missing';self.assertIsNone(self.gap()['paths'][0]['human_minutes'])
    def test_exception_path_must_cover_machine_failure(self):
        self.doc['data']['paths'][3]['failure_of']=[];self.gap()
    def test_missing_source_contract_not_installed(self):
        self.doc['data']['source_contracts'][0]['source_refs']=['unregistered'];self.assertIsNone(self.gap()['weighted_minutes']['target']['human_minutes'])
    def test_boolean_time_rejected(self):
        self.doc['data']['steps'][0]['human_minutes']=True
        with self.assertRaises(ValueError):self.result()
    def test_unknown_time_not_zero(self):
        self.doc['data']['steps'][0]['human_minutes']=None;self.assertIsNone(self.gap()['weighted_minutes']['current']['human_minutes'])
    def test_write_without_receipt_rejected_as_gap(self):
        self.doc['data']['steps'][1]['mode']='proposed-write';self.gap()

if __name__=='__main__': unittest.main()
