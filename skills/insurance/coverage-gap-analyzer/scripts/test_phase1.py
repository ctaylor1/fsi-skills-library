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
from calculate_or_transform import compute
from validate_output import validate
class Regression(unittest.TestCase):
    def test_endorsement_presence_not_unqualified_buyback(self):
        d=load('needs_and_policy_example.json');peril=d['policy']['exclusions'][0]['peril'];d['policy'].setdefault('endorsements',[]).append({'adds':peril,'source_ref':'conditional-endorsement'})
        o=compute(d);f=next(g for g in o['gaps'] if g['gap_type']=='exclusion_match');self.assertEqual(f['basis']['buy_backs'],[])
        self.assertTrue(any(x['gap_type']=='endorsement_effect' for x in o['not_evaluable']));self.assertFalse(validate(o))
    def test_missing_schedule_not_missing_coverage(self):
        d=load('needs_and_policy_example.json');d['policy'].pop('coverages');o=compute(d)
        self.assertNotIn('missing_coverage',o['fired_gaps'])

if __name__=='__main__':unittest.main()
