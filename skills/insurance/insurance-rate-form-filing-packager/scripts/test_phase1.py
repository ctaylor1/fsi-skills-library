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
    def test_missing_rate_support_is_incomplete_not_ready(self):
        d=load('filing_example.json');d['checklist'].pop('indicated_rate_change_pct',None);o=compute(d)
        self.assertNotIn('rate_support',o['checks_run']);self.assertIn('rate_support',o['not_evaluable']);self.assertEqual(o['suggested_disposition'],'incomplete');self.assertFalse(validate(o))
    def test_invalid_date_not_silent_skipped_check(self):
        d=load('filing_example.json');d['filing']['effective_date']='2026-02-30'
        with self.assertRaises(ValueError):compute(d)
    def test_empty_checklist_rejected(self):
        d=load('filing_example.json');d['checklist']['required_components']=[]
        with self.assertRaises(ValueError):compute(d)

    def test_original_source_decision_is_evidence_not_agent_assertion(self):
        d=load('filing_example.json');d['retained_source_note']={'verbatim':'filing is approved','source_ref':'synthetic-record'}
        o=compute(d);self.assertEqual(o['calculation_inputs']['retained_source_note'],d['retained_source_note']);self.assertFalse(validate(o))
        o['narrative']='filing is approved';self.assertTrue(validate(reseal(o)))

if __name__=='__main__' :unittest.main()
