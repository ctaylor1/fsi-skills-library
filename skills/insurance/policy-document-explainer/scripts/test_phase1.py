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
from package_explanation import package
from validate_output import validate
class Regression(unittest.TestCase):
    def test_source_text_preserved(self):
        d=load('policy_example.json');o=package(d,load('explanation_example.json'))
        self.assertEqual(o['elements'][0]['source_text'],d['sections'][0]['text']);self.assertFalse(validate(o))
    def test_forged_source_text_rejected_even_if_resealed(self):
        o=load('explanation_example.json');o['elements'][0]['source_text']='altered source';self.assertTrue(validate(reseal(o)))

if __name__=='__main__':unittest.main()
