"""PCI evidence collection must not imply sufficiency or N/A."""
import json,unittest
from pathlib import Path
from calculate_or_transform import build_package
from validate_input import validate as intake
from validate_output import validate

class RegressionTests(unittest.TestCase):
 def setUp(self):self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/requirements_example.json').read_text())
 def test_baseline(self):self.assertEqual(intake(self.doc)[0],[]);self.assertEqual(validate(build_package(self.doc)),[])
 def test_correct_sad_requirement_not_na(self):
  r=next(r for r in build_package(self.doc)['requirements'] if r['req_id']=='3.3.1');self.assertEqual(r['evidence_status'],'evidence-present');self.assertFalse(r['sufficiency_assessed'])
 def test_asserted_na_requires_review(self):
  self.doc['requirements'][-1].update(not_applicable=True,na_justification='No SAD retained');r=build_package(self.doc)['requirements'][-1];self.assertEqual(r['evidence_status'],'needs-data')
 def test_single_recent_log_does_not_prove_period(self):
  r=next(r for r in build_package(self.doc)['requirements'] if r['req_id']=='10.4.1');self.assertEqual(r['evidence_status'],'evidence-present');self.assertFalse(r['period_coverage_assessed'])
 def test_future_evidence_not_fresh(self):
  self.doc['controls'][0]['evidence'][0]['effective_date']='2030-01-01';self.assertEqual(build_package(self.doc)['requirements'][0]['evidence_status'],'evidence-stale')
 def test_duplicate_evidence_id_rejected(self):
  self.doc['controls'][1]['evidence'][0]['id']=self.doc['controls'][0]['evidence'][0]['id'];self.assertTrue(intake(self.doc)[0])
 def test_wrong_v4_requirement_rejected(self):
  self.doc['requirements'][-1]['req_id']='3.2.1';self.assertTrue(intake(self.doc)[0])
 def test_sufficiency_tamper_rejected(self):
  out=build_package(self.doc);out['requirements'][0]['sufficiency_assessed']=True;self.assertTrue(validate(out))
if __name__=='__main__':unittest.main()
