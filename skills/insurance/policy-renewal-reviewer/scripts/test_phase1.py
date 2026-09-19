#!/usr/bin/env python3
"""Phase 1 behavioral regressions; synthetic artifacts only, no external actions."""
import copy,json,unittest
from pathlib import Path
from insurance_contract import build_artifact
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/'evals/files'/name).read_text())
def reseal(out):
    a=out['artifact'];source=out.get('calculation_inputs',out.get('source_document'))
    out['artifact']=build_artifact(source,out,producer=a['producer'],artifact_type=a['artifact_type'],completeness=a['completeness'],evaluability=a['evaluability'],issues=a['unresolved_issues'])
    return out
from calculate_or_transform import compute
from validate_output import validate
class Regression(unittest.TestCase):
    def test_no_synthetic_earned_premium(self):
        d=load('renewal_example.json');d.pop('earned_premium');o=compute(d)
        self.assertTrue(any(x['finding']=='loss_ratio_flag' for x in o['not_evaluable']))
        self.assertNotIn('loss_ratio_flag',o['fired_findings']);self.assertFalse(validate(o))
    def test_loss_window_filters_past_and_future(self):
        d=load('renewal_example.json');baseline=compute(d)
        d['claims'] += [{'claim_id':'old','date_of_loss':'2000-01-01','incurred':1e9,'status':'open','source_ref':'old'}, {'claim_id':'future','date_of_loss':'2030-01-01','incurred':1e9,'status':'open','source_ref':'future'}]
        o=compute(d);self.assertEqual(o['findings'],baseline['findings']);self.assertEqual(o['loss_window']['excluded_claim_count'],2)
    def test_missing_term_schedule_not_removed(self):
        d=load('renewal_example.json');d['proposed'].pop('coverages');o=compute(d)
        self.assertNotIn('coverage_removed',o['fired_findings']);self.assertTrue(any(x['finding']=='coverage_removed' for x in o['not_evaluable']))
    def test_incomplete_never_routine(self):
        d=load('renewal_example.json');d['proposed']=copy.deepcopy(d['expiring']);d.pop('claims');d.pop('earned_premium');o=compute(d)
        self.assertEqual(o['suggested_disposition'],'Incomplete');self.assertFalse(validate(o))
    def test_earned_period_mismatch(self):
        d=load('renewal_example.json');d['earned_premium']['period_start']='2020-01-01'
        self.assertTrue(any(x['finding']=='loss_ratio_flag' for x in compute(d)['not_evaluable']))

if __name__=='__main__':unittest.main()
