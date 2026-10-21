"""Independent expected portfolio/governance cases, not golden reconstruction oracles."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES=['institutional-investment-policy-builder','asset-allocation-planner','portfolio-construction-analyzer','portfolio-rebalancing-planner','tax-aware-portfolio-implementation-reviewer','buy-side-trading-planner','investment-regulatory-obligation-reviewer','investment-disclosure-reviewer']
def fixture(name):return json.loads((ROOT/'skills/asset-management'/name/'evals/files/input.json').read_text())
def compute(name,d):
 p=ROOT/'skills/asset-management'/name
 r=subprocess.run([sys.executable,'-B',str(p/'scripts/calculate_or_transform.py')],input=json.dumps(d),capture_output=True,text=True)
 if r.returncode:raise ValueError(r.stdout+r.stderr)
 return json.loads(r.stdout)
class PortfolioFoundations(unittest.TestCase):
 def test_all_native_independent_cases(self):
  for name in NAMES:
   p=ROOT/'skills/asset-management'/name
   r=subprocess.run([sys.executable,'-B','scripts/selftest.py'],cwd=p,capture_output=True,text=True)
   self.assertEqual(r.returncode,0,name+r.stdout+r.stderr)
 def test_infeasible_policy_ranges_and_missing_owner(self):
  n=NAMES[0];d=fixture(n);d['constraints']['allocation_ranges'][0]['minimum']='.9';d['constraints']['allocation_ranges'][0]['maximum']='1';d['governance'].pop('approval_owner')
  r=compute(n,d);self.assertTrue(any('cannot fund' in x for x in r['unresolved_issues']));self.assertTrue(any('approval_owner' in x for x in r['unresolved_issues']));self.assertEqual(r['results']['approval_state'],'not-approved')
 def test_covariance_psd_and_weight_feasibility(self):
  for n in NAMES[1:3]:
   d=fixture(n);d['covariance']=[['.01','.03'],['.03','.01']]
   with self.assertRaises(ValueError):compute(n,d)
   d=fixture(n);d['candidates'][0]['weights']['EQ']='.7'
   with self.assertRaises(ValueError):compute(n,d)
   d=fixture(n);d['constraints']['max_position']='.5';r=compute(n,d)
   self.assertFalse(r['results']['candidates'][0]['feasible_under_supplied_constraints']);self.assertIsNone(r['results']['selection'])
 def test_optimization_no_silent_fallback(self):
  n='portfolio-construction-analyzer';d=fixture(n);d['optimization_requested']=True;r=compute(n,d)
  self.assertEqual(r['results']['engine_state'],'unavailable');self.assertIsNone(r['results']['selection'])
  d['engine_result']={'engine_id':'X','engine_version':'1','method_id':'qp','method_version':'1','acceptance_ref':'unverified','input_hash':'wrong','candidate_id':'balanced'}
  with self.assertRaises(ValueError):compute(n,d)
 def test_nav_gap_costs_and_unavailable_proceeds(self):
  n='portfolio-rebalancing-planner';d=fixture(n);d['target_cash_weight']='.2';d['holdings'][0]['target_weight']='.8';r=compute(n,d)
  self.assertEqual(r['results']['trades'][0]['quantity_delta'],'-1');self.assertEqual(r['results']['projected_cash'],'199.9');self.assertEqual(r['results']['total_fees'],'0.1');self.assertTrue(any('availability' in x for x in r['unresolved_issues']))
  d['nav']='1100';r=compute(n,d);self.assertEqual(r['results']['nav_residual'],'-100')
 def test_cash_negative_after_fee_blocks_draft(self):
  n='portfolio-rebalancing-planner';d=fixture(n);d.update(target_cash_weight='0',cash_buffer='0');d['holdings'][0]['target_weight']='1';r=compute(n,d)
  self.assertEqual(r['results']['projected_cash'],'-0.1');self.assertEqual(r['results']['implementation_status'],'blocked-for-review')
 def test_tax_no_inferred_loss_benefit_and_window_boundary(self):
  n='tax-aware-portfolio-implementation-reviewer';d=fixture(n);d['related_purchases'][0]['trade_date']='2026-08-21';r=compute(n,d)
  self.assertEqual(r['results']['lots'][0]['loss_status'],'window-incomplete');self.assertIsNone(r['results']['lots'][0]['recognized_loss_deduction'])
  d['related_purchases'][0]['trade_date']='2026-08-22';r=compute(n,d);self.assertEqual(r['results']['lots'][0]['loss_status'],'potential-wash-sale')
  d['selected_lots'][0]['sale_quantity']='11'
  with self.assertRaises(ValueError):compute(n,d)
 def test_trade_participation_and_quote_cost(self):
  n='buy-side-trading-planner';d=fixture(n);d['intentions'][0]['quantity']='300';r=compute(n,d)
  self.assertEqual(r['results']['estimated_total_cost'],'12');self.assertEqual(r['results']['intent_review'][0]['adv_fraction'],'0.150000000000');self.assertTrue(r['unresolved_issues']);self.assertFalse(r['results']['routing_performed'])
 def test_rule_missing_fact_proposed_not_applicable(self):
  n='investment-regulatory-obligation-reviewer';d=fixture(n);del d['entity_facts']['registration'];r=compute(n,d);self.assertEqual(r['results']['obligations'][0]['state'],'undetermined')
  d['rules'][0]['status']='proposed';r=compute(n,d);self.assertEqual(r['results']['obligations'][0]['state'],'not-binding');self.assertFalse(r['results']['obligations'][0]['overdue'])
  d['rules'][0]['status']='final';d['entity_facts']['registration']='STATE';r=compute(n,d);self.assertEqual(r['results']['obligations'][0]['state'],'not-applicable')
 def test_disclosure_unsupported_text_never_leaks(self):
  n='investment-disclosure-reviewer';d=fixture(n);r=compute(n,d);self.assertNotIn('UNSUPPORTED-SECRET-CLAIM',json.dumps(r));self.assertFalse(r['results']['publication_authorized'])
  d['sources'][0]['permitted_audiences']=['internal-review'];r=compute(n,d);self.assertEqual(r['results']['supported_claims'],[]);self.assertEqual(r['results']['disclosures'],[])
 def test_restricted_observation_source_rejected_all(self):
  for n in NAMES:
   d=fixture(n);d['sources'][0]['permitted_audiences']=['other-team']
   with self.assertRaises(ValueError):compute(n,d)
 def independent_request(self,case):
  return json.loads((ROOT/'docs/asset-management/phase2-validation/portfolio-independent'/(case+'.request.json')).read_text())
 def test_independent_missing_domain_provenance_rejects(self):
  cases=[('c01','institutional-investment-policy-builder'),('c03','asset-allocation-planner'),('c06','portfolio-rebalancing-planner'),('c07','tax-aware-portfolio-implementation-reviewer'),('c09','buy-side-trading-planner')]
  for prefix,n in cases:
   with self.subTest(skill=n),self.assertRaises(ValueError):compute(n,self.independent_request(prefix+'-missing-observation-refs'))
 def test_independent_trade_control_references_resolve(self):
  with self.assertRaises(ValueError):compute('buy-side-trading-planner',self.independent_request('c09-unknown-approval-refs'))
 def test_independent_empty_tax_scope_rejects(self):
  with self.assertRaises(ValueError):compute('tax-aware-portfolio-implementation-reviewer',self.independent_request('c07-empty-lots'))
 def test_independent_wrong_subject_claim_withheld(self):
  r=compute('investment-disclosure-reviewer',self.independent_request('g02-wrong-subject-source'))
  self.assertEqual([],r['results']['supported_claims']);self.assertTrue(r['unresolved_issues'])
 def test_independent_completion_and_owner_gap_retained(self):
  r=compute('investment-regulatory-obligation-reviewer',self.independent_request('g01-unsupported-completion'))
  self.assertTrue(any('owner' in x for x in r['unresolved_issues']));self.assertTrue(any('completion' in x for x in r['unresolved_issues']))
  self.assertTrue(r['results']['obligations'][0]['overdue'])
 def test_independent_volatility_limit_before_display_rounding(self):
  r=compute('portfolio-construction-analyzer',self.independent_request('c04-volatility-boundary'))
  c=r['results']['candidates'][0];self.assertEqual('0.100000000000',c['annualized_volatility'])
  self.assertFalse(c['feasible_under_supplied_constraints']);self.assertIn('volatility exceeds supplied limit',c['constraint_findings'])
 def test_actual_market_and_tax_observations_cannot_exceed_linked_knowledge(self):
  for name in ['portfolio-rebalancing-planner','buy-side-trading-planner','tax-aware-portfolio-implementation-reviewer']:
   for boundary in ['cutoff','source']:
    with self.subTest(skill=name,boundary=boundary):
     doc=fixture(name);doc['sources'][0]['known_at']='2026-09-01'
     if boundary=='cutoff':doc['knowledge_cutoff']='2026-09-01'
     with self.assertRaises(ValueError):compute(name,doc)
 def test_actual_disclosed_performance_respects_source_knowledge(self):
  name='investment-disclosure-reviewer';doc=fixture(name)
  performance=dict(gross_return='.02',net_return='.018',period_start='2026-09-01',period_end='2026-09-20',net_period_start='2026-09-01',net_period_end='2026-09-20',fee_basis='net of supplied expenses',hypothetical=False)
  doc['claims']=[dict(claim_id='P',content='Supplied period return.',kind='performance',source_ref='S1',performance=performance)]
  doc['sources'][0]['claims']['P']='Supplied period return.';doc['sources'][0]['performance']={'P':performance}
  self.assertEqual(len(compute(name,doc)['results']['supported_claims']),1)
  doc['sources'][0]['known_at']='2026-09-10'
  with self.assertRaises(ValueError):compute(name,doc)
if __name__=='__main__':unittest.main()
