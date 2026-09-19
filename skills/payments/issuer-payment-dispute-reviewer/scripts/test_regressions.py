"""Issuer duties remain distinct from network recovery and merchant response."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import run
from validate_input import validate as intake
from validate_output import validate

class RegressionTests(unittest.TestCase):
 def setUp(self):self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/cases_example.json').read_text())
 def first(self):return run(self.doc)['cases'][0]
 def test_current_profile_checklist(self):
  out=run(self.doc);self.assertEqual(validate(out),[]);self.assertEqual(out['cases'][0]['disposition'],'draft-ready-for-review')
 def test_acquirer_routes_to_merchant_packager(self):
  r=run(self.doc)['cases'][1];self.assertEqual(r['route_specialist'],'merchant-chargeback-response-packager');self.assertIsNone(r['draft_response'])
 def test_no_legal_profile_no_invented_clock(self):
  self.doc['cases'][0].pop('statutory_profile');r=self.first();self.assertEqual(r['disposition'],'legal-profile-unresolved');self.assertIsNone(r['draft_response'])
 def test_scheme_profile_cannot_supply_statutory_obligations(self):
  c=self.doc['cases'][0];c['scheme_profile']=c.pop('statutory_profile');c['scheme_clocks']=c.pop('statutory_clocks');self.assertEqual(self.first()['disposition'],'legal-profile-unresolved')
 def test_business_day_clock_needs_calendar(self):
  self.doc['cases'][0]['statutory_clocks'][0]['day_basis']='business-days';self.assertEqual(self.first()['disposition'],'legal-profile-unresolved')
 def test_scheme_clock_survives_absent_profile(self):
  case=self.doc['cases'][0];case.pop('scheme_profile',None)
  case['scheme_clocks']=copy.deepcopy(case['statutory_clocks'])
  case['scheme_clocks'][0]['name']='supplied-recovery-deadline'
  result=self.first()['scheme_review']
  self.assertEqual(result['status'],'unresolved')
  self.assertEqual(result['clocks'][0]['name'],'supplied-recovery-deadline')
  self.assertTrue(result['issues'])
 def test_fraud_consultation_does_not_drop_issuer_clocks(self):
  r=run(self.doc)['cases'][5];self.assertEqual(r['case_owner'],'issuer-payment-dispute-reviewer');self.assertTrue(r['statutory_review']['clocks']);self.assertEqual(r['consultations'][0]['target'],'payment-fraud-and-scam-investigator')
 def test_overdue_does_not_deny_customer(self):
  r=run(self.doc)['cases'][3];self.assertEqual(r['disposition'],'deadline-review-required');self.assertEqual(r['recommended_action'],'urgent-issuer-review')
 def test_proposed_or_wrong_rail_unresolved(self):
  self.assertEqual(run(self.doc)['cases'][4]['disposition'],'legal-profile-unresolved')
  self.doc['cases'][0]['rail']='ach';self.assertEqual(self.first()['disposition'],'legal-profile-unresolved')
 def test_tampered_authorization_or_profile_rejected(self):
  out=run(self.doc);out['cases'][0]['draft_response']['authorized_submission']=True;self.assertTrue(validate(out))
  out=run(self.doc);out['cases'][0]['statutory_review']['profile']['status']='withdrawn';self.assertTrue(validate(out))
 def test_nonfinite_money_rejected(self):
  self.doc['cases'][0]['dispute_amount']='Infinity';self.assertTrue(intake(self.doc)[0])
if __name__=='__main__':unittest.main()
