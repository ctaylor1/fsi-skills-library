import copy,json,unittest
from pathlib import Path
from domain import compute
from validate_input import validate
from validate_output import validate as output_validate
FIXTURE=Path(__file__).resolve().parents[1]/'evals/files/request.json'
class SustainabilityTests(unittest.TestCase):
 def setUp(self):self.doc=json.loads(FIXTURE.read_text())
 def metric(self):return compute(self.doc)['results']['metrics'][0]
 def test_weighted_metric_and_estimation(self):
  r=self.metric();self.assertEqual(r['weighted_metric'],'133.333333333333');self.assertEqual(r['coverage_fraction'],'1.000000000000');self.assertEqual(r['estimated_market_value'],'30');self.assertTrue(r['meets_supplied_limit'])
 def test_portfolio_denominator_includes_declared_cash_only_when_explicit(self):
  self.doc['metrics'][0]['denominator_basis']='total-market-value';self.assertEqual(self.metric()['weighted_metric'],'120.000000000000')
 def test_missing_data_not_zero_or_reweighted_full_claim(self):
  self.doc['observations'].pop();r=self.metric();self.assertIsNone(r['weighted_metric']);self.assertIsNone(r['meets_supplied_limit']);self.assertEqual(r['covered_only_mean'],'100.000000000000');self.assertEqual(r['coverage_fraction'],'0.666666666667')
 def test_old_vintage_withheld(self):
  self.doc['observations'][1]['vintage']=2024;self.assertIsNone(self.metric()['weighted_metric'])
 def test_disallowed_estimate_withheld(self):
  self.doc['metrics'][0]['estimates_allowed']=False;r=self.metric();self.assertIsNone(r['weighted_metric']);self.assertIn('estimated metric is not permitted',r['unavailable_observations'][0]['reasons'])
 def test_exact_limit_not_rounded_comparison(self):
  self.doc['metrics'][0]['limit']='133.333333333333';self.assertFalse(self.metric()['meets_supplied_limit'])
 def test_exclusion_exposure(self):
  self.doc['exclusions'][0]['threshold']='180';r=compute(self.doc)['results']['exclusions'][0];self.assertEqual(r['known_breached_market_value'],'30');self.assertEqual(r['known_breached_fraction_of_eligible'],'0.333333333333');self.assertEqual(r['status'],'breach')
 def test_missing_exclusion_evidence_undetermined(self):
  self.doc['observations'].pop();self.assertEqual(compute(self.doc)['results']['exclusions'][0]['status'],'undetermined')
 def test_expired_mandate_withholds_exclusion_but_retains_known_match(self):
  self.doc['mandate']['effective_to']='2026-10-03';self.doc['exclusions'][0]['threshold']='180'
  r=compute(self.doc)['results']['exclusions'][0];self.assertEqual(r['status'],'undetermined');self.assertEqual(r['known_breached_market_value'],'30');self.assertEqual(len(r['breached_holding_ids']),1)
 def test_unreviewed_mandate_cannot_establish_active_exclusion(self):
  self.doc['mandate']['review_status']='unreviewed';self.doc['exclusions'][0]['threshold']='180'
  self.assertEqual(compute(self.doc)['results']['exclusions'][0]['status'],'undetermined')
 def test_unresolved_scope_withholds_exclusion_conclusion(self):
  self.doc['unresolved_issues']=['Which mandate version governs is unresolved'];self.doc['exclusions'][0]['threshold']='180'
  self.assertEqual(compute(self.doc)['results']['exclusions'][0]['status'],'undetermined')
 def test_known_breach_survives_other_missing_observation_under_valid_mandate(self):
  self.doc['observations'].pop(0);self.doc['exclusions'][0]['threshold']='180'
  r=compute(self.doc)['results']['exclusions'][0];self.assertEqual(r['status'],'breach');self.assertEqual(r['known_breached_market_value'],'30')
 def test_bad_denominator_rejected(self):
  self.doc['portfolio']['total_market_value']='99';self.assertTrue(validate(self.doc))
 def test_short_position_unsupported(self):
  self.doc['holdings'][0]['market_value']='-60';self.assertTrue(validate(self.doc))
 def test_unit_mismatch_rejected(self):
  self.doc['observations'][0]['unit']='percent';self.assertTrue(validate(self.doc))
 def test_duplicate_holding_metric_rejected(self):
  r=copy.deepcopy(self.doc['observations'][0]);r['observation_id']='NEW';self.doc['observations'].append(r);self.assertTrue(validate(self.doc))
 def test_source_restriction_rejected(self):
  self.doc['sources'][0]['permitted_audiences']=['external'];self.assertTrue(validate(self.doc))
 def test_future_observation_rejected(self):
  self.doc['observations'][0]['observed_on']='2026-10-05';self.assertTrue(validate(self.doc))
 def test_unreviewed_mandate_cannot_pass_limit(self):
  self.doc['mandate']['review_status']='unreviewed';self.assertIsNone(self.metric()['meets_supplied_limit'])
 def test_zero_denominator_unknown(self):
  for r in self.doc['holdings']:r['market_value']='0'
  self.doc['portfolio']['total_market_value']='0';self.assertIsNone(self.metric()['weighted_metric'])
 def test_no_certification(self):
  r=compute(self.doc);self.assertFalse(r['action_taken']);self.assertFalse(r['results']['compliance_certified']);self.assertIsNone(r['results']['generic_esg_score'])
 def test_output_reconstruction(self):
  r=compute(self.doc);self.assertEqual(output_validate(r,self.doc),[]);r['results']['metrics'][0]['meets_supplied_limit']=False;self.assertTrue(output_validate(r,self.doc))
if __name__=='__main__':unittest.main()
