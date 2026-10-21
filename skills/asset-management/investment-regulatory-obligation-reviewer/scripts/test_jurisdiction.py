import copy,json,unittest
from pathlib import Path
from calculate_or_transform import compute,validate
from validate_output import validate as output_validate
FIXTURE=Path(__file__).resolve().parents[1]/'evals/files/jurisdiction_request.json'
class JurisdictionTests(unittest.TestCase):
 def setUp(self):self.doc=json.loads(FIXTURE.read_text())
 def row(self):return compute(self.doc)['results']['obligations'][0]
 def test_explicit_conditions_and_deadline(self):
  r=self.row();self.assertEqual(r['state'],'applicable-under-supplied-profile');self.assertEqual(r['days_until_due_calendar'],6);self.assertFalse(r['overdue_under_supplied_deadline'])
 def test_missing_activity_never_inferred_from_geography(self):
  self.doc['review_scopes'][0]['activity']=None;self.assertEqual(self.row()['state'],'undetermined')
 def test_wrong_product_not_applicable(self):
  self.doc['review_scopes'][0]['product_type']='OTHER';self.assertEqual(self.row()['state'],'not-applicable')
 def test_domestic_scope_not_crossborder(self):
  self.doc['review_scopes'][0]['home_jurisdiction']='TEST-HOST';self.assertEqual(self.row()['state'],'not-applicable')
 def test_proposed_rule_not_binding(self):
  self.doc['jurisdiction_profiles'][0]['status']='proposed';self.assertEqual(self.row()['state'],'not-binding')
 def test_future_effective_rule_not_applied(self):
  self.doc['jurisdiction_profiles'][0]['effective_from']='2026-11-01';self.assertEqual(self.row()['state'],'not-effective')
 def test_overdue_absolute_date(self):
  self.doc['jurisdiction_profiles'][0]['deadline']['due_date']='2026-10-03';r=self.row();self.assertTrue(r['overdue_under_supplied_deadline']);self.assertEqual(r['days_until_due_calendar'],-1)
 def test_due_today_not_overdue(self):
  self.doc['jurisdiction_profiles'][0]['deadline']['due_date']='2026-10-04';self.assertFalse(self.row()['overdue_under_supplied_deadline'])
 def test_missing_required_deadline_retained(self):
  self.doc['jurisdiction_profiles'][0]['deadline']=None;self.assertIn('reviewed deadline evidence missing',' '.join(compute(self.doc)['unresolved_issues']))
 def test_conflicts_not_resolved_by_stricter_rule(self):
  r=copy.deepcopy(self.doc['jurisdiction_profiles'][0]);r.update(profile_id='CONFLICT',version='2',treatment='prohibited');self.doc['jurisdiction_profiles'].append(r);out=compute(self.doc)['results']['profile_comparisons'][0];self.assertTrue(out['potential_conflict_requires_review']);self.assertIsNone(out['resolution']);self.assertFalse(out['stricter_rule_automatically_selected'])
 def test_authority_source_binding(self):
  self.doc['jurisdiction_profiles'][0]['primary_authority']['version']='2';self.assertTrue(validate(self.doc))
 def test_future_source_rejected(self):
  self.doc['sources'][0]['known_at']='2026-10-05';self.assertTrue(validate(self.doc))
 def test_deadline_before_trigger_rejected(self):
  self.doc['jurisdiction_profiles'][0]['deadline']['due_date']='2026-09-30';self.assertTrue(validate(self.doc))
 def test_wrong_entity_rejected(self):
  self.doc['review_scopes'][0]['entity_id']='OTHER';self.assertTrue(validate(self.doc))
 def test_unknown_extension_rejected(self):
  self.doc['extension']='future-mode';self.assertTrue(validate(self.doc))
 def test_original_legacy_interface_preserved(self):
  old=json.loads((FIXTURE.parent/'input.json').read_text());r=compute(old);self.assertNotIn('extension',r['results']);self.assertEqual(r['method']['id'],'supplied-rule-applicability')
 def test_no_legal_approval_and_detached_tampering(self):
  r=compute(self.doc);self.assertEqual(output_validate(r,self.doc),[]);self.assertIsNone(r['results']['legal_conclusion']);self.assertFalse(r['results']['market_access_authorized']);r['results']['market_access_authorized']=True;self.assertTrue(output_validate(r,self.doc))
if __name__=='__main__':unittest.main()
