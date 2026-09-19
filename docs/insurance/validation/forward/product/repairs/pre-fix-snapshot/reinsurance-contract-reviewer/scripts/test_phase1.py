#!/usr/bin/env python3
"""Phase 1 behavioral regressions; synthetic artifacts only, no external actions."""
import copy,json,unittest
from pathlib import Path
from insurance_contract import build_artifact,validate_artifact
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/'evals/files'/name).read_text())
def reseal(out):
    a=out['artifact'];source=out.get('calculation_inputs',out.get('source_document'))
    out['artifact']=build_artifact(source,out,producer=a['producer'],artifact_type=a['artifact_type'],completeness=a['completeness'],evaluability=a['evaluability'],issues=a['unresolved_issues'])
    return out
from calculate_or_transform import transform
from validate_output import validate
class Regression(unittest.TestCase):
    def test_xol_and_reinstatement_first_erosion(self):
        out,errors=transform(load('treaty_example.json'));self.assertFalse(errors);ill=out['recovery_illustration']
        self.assertEqual(ill['occurrences'][0]['ceded_recovery'],7000000);self.assertEqual(ill['occurrences'][0]['reinstatement_premium'],1400000)
        self.assertEqual(ill['total_reinstatement_premium'],2000000);self.assertEqual(ill['total_ceded'],17000000)
    def test_quota_share_not_processed_as_xol(self):
        d=load('treaty_example.json');d['treaty_type']='quota_share';o,e=transform(d)
        self.assertIsNone(o['recovery_illustration']);self.assertEqual(o['illustration_status'],'not_evaluable')
    def test_unknown_eligibility_or_basis_blocks_aggregate(self):
        d=load('treaty_example.json');d['losses'][0].pop('eligible_for_illustration');self.assertIsNone(transform(d)[0]['recovery_illustration'])
        d=load('treaty_example.json');d['layer']['reinstatement_basis']='pro_rata_time';self.assertIsNone(transform(d)[0]['recovery_illustration'])
    def test_reinstatement_premium_tamper_rejected(self):
        o=load('interpretation_example.json');o['recovery_illustration']['total_reinstatement_premium']-=1e6
        self.assertTrue(validate(reseal(o)))
    def test_loss_outside_period_not_implicitly_covered(self):
        d=load('treaty_example.json');d['losses'][0]['date']='2025-12-31';self.assertIsNone(transform(d)[0]['recovery_illustration'])

if __name__=='__main__':unittest.main()
