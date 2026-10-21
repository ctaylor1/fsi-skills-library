"""Native behavior and evidence regressions; no professional acceptance claim."""
import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from domain import evaluate, validate
from workflow_contract import build_artifact
from workflow_foundation import run, check_output
NAME = 'operations-performance-analyzer'
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

    def test_queue_and_completed_cohort(self):
        x=self.result()['results'];self.assertEqual(x['queue_counts'],{'opening':1,'arrivals':2,'completed':2,'cancelled':0,'closing':1});self.assertEqual(x['queue_conservation_difference'],0);self.assertEqual(Decimal(x['mean_elapsed_hours']),24);self.assertEqual(Decimal(x['p95_elapsed_hours_nearest_rank']),36);self.assertEqual(Decimal(x['sla_fraction']),Decimal('.5'));self.assertEqual(Decimal(x['cost_per_completed']),75)
    def test_empty_complete_not_bad_zero_ratios(self):
        self.doc['data'].update(episodes=[],reported_opening=0,reported_closing=0);x=self.result()['results'];self.assertIsNone(x['mean_elapsed_hours']);self.assertIsNone(x['sla_fraction']);self.assertEqual(x['queue_counts']['closing'],0)
    def test_incomplete_snapshot_no_window_metrics(self):
        self.doc['data']['inventory_complete']=False;self.assertIsNone(self.gap()['queue_counts'])
    def test_offset_timestamps_same_instant(self):
        self.doc['data']['episodes'][0]['exited_at']='2026-09-18T08:00:00-04:00';self.assertEqual(Decimal(self.result()['results']['mean_elapsed_hours']),24)
    def test_exit_at_window_end_remains_backlog(self):
        self.doc['data']['episodes'][0]['exited_at']='2026-09-20T00:00:00Z';x=self.result()['results'];self.assertEqual(x['queue_counts']['closing'],2);self.assertEqual(x['queue_counts']['completed'],1)
    def test_cancellation_not_completed_mean(self):
        self.doc['data']['episodes'][0]['exit_kind']='cancelled';x=self.result()['results'];self.assertEqual(Decimal(x['mean_elapsed_hours']),12);self.assertEqual(x['queue_counts']['cancelled'],1)
    def test_no_timezone_rejected(self):
        self.doc['data']['episodes'][0]['created_at']='2026-09-17T00:00:00'
        with self.assertRaises(ValueError):self.result()
    def test_negative_duration_withheld(self):
        self.doc['data']['episodes'][0]['exited_at']='2026-09-16T00:00:00Z';self.assertIsNone(self.gap()['mean_elapsed_hours'])
    def test_zero_capacity_not_zero_utilization(self):
        self.doc['data'].update(available_labor_hours=0,worked_labor_hours=0);self.assertIsNone(self.result()['results']['labor_utilization'])

    def test_control_break_preserves_only_unreconciled_extract_measures(self):
        self.doc['data']['reported_closing']=9
        output=self.result()
        self.assertEqual(output['status'],'needs-review')
        self.assertFalse(output['results']['snapshot_reconciled'])
        self.assertEqual(output['results']['queue_counts']['closing'],1)

    def test_open_episode_unknown_cost_does_not_hide_completed_metrics(self):
        self.doc['data']['episodes'][2]['cost']=None
        self.doc['data']['episodes'][2]['human_minutes']=None
        x=self.result()
        self.assertEqual(x['status'],'ready-for-review')
        self.assertEqual(Decimal(x['results']['cost_per_completed']),75)
        self.assertEqual(x['results']['queue_counts']['closing'],1)

if __name__=='__main__': unittest.main()
