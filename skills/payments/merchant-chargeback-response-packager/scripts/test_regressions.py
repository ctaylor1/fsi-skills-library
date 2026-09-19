"""Regression checks for role, deadline authority and evidence boundaries."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import build
from validate_input import validate as input_errors
from validate_output import validate

class RegressionTests(unittest.TestCase):
 def setUp(self):
  self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/disputes_example.json').read_text())
 def first(self):return build(self.doc)['packages'][0]
 def test_valid_merchant_and_acquirer(self):
  result=build(self.doc);self.assertEqual(validate(result),[])
  self.assertTrue(result['packages'][0]['packageable']);self.assertTrue(result['packages'][-1]['packageable']);self.assertEqual(result['packages'][-1]['role'],'acquirer')
 def test_missing_profile_never_defaults(self):
  self.doc.pop('rule_profile');self.assertFalse(self.first()['packageable']);self.assertEqual(self.first()['status'],'needs-data')
 def test_profile_scope_and_currency(self):
  for key,value in [('status','proposed'),('review_due','2020-01-01'),('participants',['issuer']),('jurisdictions',['GB'])]:
   d=copy.deepcopy(self.doc);d['rule_profile'][key]=value;self.assertFalse(build(d)['packages'][0]['packageable'])
 def test_missing_deadline_or_stage(self):
  for key in ('response_deadline','deadline_source_ref','stage'):
   d=copy.deepcopy(self.doc);d['disputes'][0].pop(key);self.assertFalse(build(d)['packages'][0]['packageable'])
 def test_issuer_does_not_get_representment(self):
  self.doc['disputes'][0]['role']='issuer';self.assertFalse(self.first()['packageable'])
 def test_compelling_count_is_not_eligibility(self):
  result=build(self.doc)['packages'][1]['compelling_evidence'];self.assertTrue(result['candidate_for_review']);self.assertEqual(result['eligibility_status'],'not-determined')
 def test_nonfinite_and_duplicate_exhibit_rejected(self):
  d=self.doc;d['disputes'][0]['dispute_amount']='NaN';self.assertTrue(input_errors(d)[0])
  self.setUp();d=self.doc;d['disputes'][0]['evidence'].append(copy.deepcopy(d['disputes'][0]['evidence'][0]));self.assertTrue(input_errors(d)[0])
 def test_no_source_promotion(self):
  result=build(self.doc);result['packages'][0]['deadline_source_ref']='';self.assertTrue(validate(result))
if __name__=='__main__':unittest.main()
