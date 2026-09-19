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
from calculate_or_transform import compile_workbench
from validate_output import validate
class Regression(unittest.TestCase):
    def test_future_source_never_fresh(self):
        d=load('submissions_example.json');d['submissions'][0]['risk_sections']['property']['as_of']='2099-01-01';o=compile_workbench(d)
        self.assertEqual(o['profiles'][0]['recommended_disposition'],'needs-data');self.assertFalse(validate(o))
    def test_authority_referral_not_treaty_determination(self):
        o=compile_workbench(load('submissions_example.json'));p=o['profiles'][2]
        self.assertNotIn('reinsurance-contract-reviewer',p['decision_rationale']['routes'])
    def test_non_property_profile_rejected(self):
        d=load('submissions_example.json');d['submissions'][0]['line_of_business']='life'
        with self.assertRaises(ValueError):compile_workbench(d)

    def test_present_section_without_measure_is_not_complete(self):
        d=load('submissions_example.json');d['submissions'][0]['risk_sections']['financial'].pop('credit_score')
        self.assertEqual(compile_workbench(d)['profiles'][0]['recommended_disposition'],'needs-data')

if __name__=='__main__' :unittest.main()
