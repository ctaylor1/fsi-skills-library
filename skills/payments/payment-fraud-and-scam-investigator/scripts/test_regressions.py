"""Payment-scam ownership and low-score deception regressions."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import investigate
from validate_input import validate as intake
from validate_output import validate

class RegressionTests(unittest.TestCase):
 def setUp(self):self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/cases_example.json').read_text())
 def scam(self):
  c=copy.deepcopy(self.doc['cases'][3]);c['flags']={'app_scam_reported':True};self.doc['cases']=[c];return c
 def test_baseline_roundtrip(self):self.assertEqual(validate(investigate(self.doc)),[])
 def test_non_email_app_retains_case(self):
  self.scam();r=investigate(self.doc)['cases'][0];self.assertEqual(r['disposition'],'needs-evidence');self.assertEqual(r['case_owner'],'payment-fraud-and-scam-investigator');self.assertFalse(r['consultations']);self.assertNotIn('route_specialist',r)
 def test_bec_consultation_needs_email_and_returns(self):
  c=self.scam();c['flags']['bec_indicator']=True;self.assertFalse(investigate(self.doc)['cases'][0]['consultations'])
  c['email_evidence_ref']='fixture://email/headers';r=investigate(self.doc)['cases'][0];self.assertEqual(r['consultations'][0]['target'],'phishing-and-bec-investigator');self.assertEqual(r['consultations'][0]['return_to'],r['case_owner'])
 def test_tampered_scam_legitimate_rejected(self):
  self.scam();out=investigate(self.doc);out['cases'][0]['disposition']='recommend-legitimate';self.assertTrue(validate(out))
 def test_offset_ordering(self):
  c=self.scam();c['timeline_events']=[{'ts':'2026-07-17T10:00:00-04:00','type':'later','source_ref':'fixture://later'},{'ts':'2026-07-17T13:30:00Z','type':'earlier','source_ref':'fixture://earlier'}]
  chronology=investigate(self.doc)['cases'][0]['evidence_bundle']['chronology'];types=[e['type'] for e in chronology];self.assertLess(types.index('earlier'),types.index('later'))
 def test_custom_band_thresholds_validate(self):
  self.doc['scoring_config']={'high_min':50,'low_max':20};self.assertEqual(validate(investigate(self.doc)),[])
 def test_local_case_id_not_persistence(self):
  r=investigate(self.doc)['cases'][0];self.assertIn('not registered',r['case_reference_origin'])
 def test_adverse_media_separate_target(self):
  c=self.scam();c['flags']={'adverse_media':True};self.assertEqual(investigate(self.doc)['cases'][0]['route_specialist'],'adverse-media-investigator')
 def test_zero_signals_still_have_supplied_evidence(self):
  c=copy.deepcopy(self.doc['cases'][3]);c['flags']={}
  for signals in c['evidence'].values():
   for key in signals:signals[key]=False
  c['linked_fraud_case_ids']=[];c['prior_fraud_cases_180d']=0;self.doc['cases']=[c]
  out=investigate(self.doc);self.assertEqual(validate(out),[]);self.assertEqual(out['cases'][0]['risk_score'],0)
 def test_string_false_not_treated_as_true(self):
  self.doc['cases'][0]['evidence']['device']['new_device']='false';self.assertTrue(intake(self.doc)[0])
 def test_missing_offset_rejected(self):
  self.doc['cases'][0]['opened_at']='2026-07-17T12:00';self.assertTrue(intake(self.doc)[0])
if __name__=='__main__':unittest.main()
