#!/usr/bin/env python3
"""Phase 1 behavioral regressions; synthetic artifacts only, no external actions."""
import json,unittest
from pathlib import Path
from insurance_contract import build_artifact
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/'evals/files'/name).read_text())
def reseal(out):
    a=out['artifact'];source=out.get('calculation_inputs',out.get('source_document'))
    out['artifact']=build_artifact(source,out,producer=a['producer'],artifact_type=a['artifact_type'],completeness=a['completeness'],evaluability=a['evaluability'],issues=a['unresolved_issues'])
    return out
from calculate_or_transform import compute,_normalize
from validate_output import validate
class Regression(unittest.TestCase):
    def test_percentage_not_hundredfold(self):
        self.assertEqual(_normalize('prior_loss_ratio','72%'),.72);self.assertIsNone(_normalize('insured_state',None));self.assertIsNone(_normalize('total_insured_value',True))
    def test_conflict_stays_unresolved(self):
        o=compute(load('submission_example.json'));self.assertTrue(any(r['status']=='mismatch' for r in o['reconciliation']))
        self.assertTrue(o['routing_recommendation'].startswith('Incomplete'));self.assertFalse(validate(o));self.assertEqual(o['artifact']['completeness'],'partial')
    def test_no_unapproved_default_appetite(self):
        d=load('submission_example.json');d.pop('config')
        with self.assertRaises(ValueError):compute(d)

if __name__=='__main__':unittest.main()
