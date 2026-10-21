"""Native behavior and evidence regressions; no professional acceptance claim."""
import copy
import json
import unittest
from pathlib import Path
from domain import evaluate, validate
from workflow_contract import build_artifact
from workflow_foundation import run, check_output
NAME = 'insurance-data-product-designer'
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

    def test_temporal_sample(self):
        x=self.result()['results'];self.assertEqual([v['value'] for v in x['resolved_sample']],['in-force','open'])
    def test_record_not_known_at_query(self):
        self.doc['data']['known_on']='2026-08-01';x=self.gap();self.assertTrue(all(v['value'] is None for v in x['resolved_sample']))
    def test_effective_end_exclusive(self):
        self.doc['data']['records'][0]['valid_to']='2026-09-01';self.gap()
    def test_active_conflict_not_latest_wins(self):
        a=copy.deepcopy(self.doc['data']['records'][0]);a.update(record_id='conflict',value='cancelled',recorded_on='2026-09-19');self.doc['data']['records'].append(a);self.assertTrue(all(v['value'] is None for v in self.gap()['resolved_sample']))
    def test_many_to_one_not_many_to_many(self):
        a=copy.deepcopy(self.doc['data']['links'][0]);a['link_id']='L2';self.doc['data']['links'].append(a);self.gap()
    def test_wrong_entity_type(self):
        self.doc['data']['records'][0]['entity_id']='CL-1';self.gap()
    def test_future_record_not_used(self):
        self.doc['data']['records'][0]['recorded_on']='2026-09-21';self.gap()
    def test_unlicensed_standard_not_certified(self):
        self.assertEqual(self.result()['results']['acord_conformance'],'not_assessed')

if __name__=='__main__': unittest.main()
