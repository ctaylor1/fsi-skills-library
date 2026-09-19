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
    def test_fee_tamper_rejected(self):
        o=compute(load('rating_example.json'));o['coverages'][0]['fees_total']+=100
        self.assertTrue(validate(reseal(o)))
    def test_missing_factor_never_defaults(self):
        d=load('rating_example.json');d['coverages'][0]['factors'][0]['value']=None
        with self.assertRaises(ValueError):compute(d)
    def test_nan_rejected(self):
        d=load('rating_example.json');d['coverages'][0]['base_rate']=float('nan')
        with self.assertRaises(ValueError):compute(d)

    def test_original_source_decision_is_evidence_not_agent_assertion(self):
        d=load('rating_example.json');d['retained_source_note']={'verbatim':'policy issued','source_ref':'synthetic-record'}
        o=compute(d);self.assertEqual(o['calculation_inputs']['retained_source_note'],d['retained_source_note']);self.assertFalse(validate(o))
        o['narrative']='policy issued';self.assertTrue(validate(reseal(o)))

if __name__=='__main__' :unittest.main()
