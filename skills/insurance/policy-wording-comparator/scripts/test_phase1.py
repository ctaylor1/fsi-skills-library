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
    def test_modified_clause_retains_both_sources(self):
        d=load('comparison_example.json');o=compute(d);f=next(f for f in o['findings'] if f['finding_type']=='modified')
        self.assertEqual({e['side'] for e in f['evidence']},{'baseline','subject'});self.assertTrue(all(e['source_text'] for e in f['evidence']));self.assertFalse(validate(o))
    def test_incomplete_not_clean_comparison(self):
        d=load('comparison_example.json');d['subject_form']=copy.deepcopy(d['baseline_form']);d.pop('required_clause_types',None)
        self.assertEqual(compute(d)['suggested_review_track'],'Incomplete comparison')
    def test_treaty_comparison_stays_in_comparator(self):
        d=load('comparison_example.json');d['contract_type']='reinsurance';d['baseline_form']['filing_status']='executed';o=compute(d)
        self.assertEqual(o['contract_type'],'reinsurance');self.assertFalse(o['baseline_form']['of_record'])

    def test_quoted_carrier_decision_preserved(self):
        d=load('comparison_example.json');d['subject_form']['clauses'][0]['text']='Coverage is approved under the following manuscript terms.'
        o=compute(d);self.assertFalse(validate(o));self.assertEqual(o['calculation_inputs']['subject_form']['clauses'][0]['text'],d['subject_form']['clauses'][0]['text'])

if __name__=='__main__' :unittest.main()
