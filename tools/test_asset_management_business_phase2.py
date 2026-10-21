#!/usr/bin/env python3
"""Independent expected economics, scope, workflow and source-control cases."""
import copy,importlib.util,json,sys,unittest
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CASES={
 'economics':('asset-manager-economics-analyzer','economics'),
 'lifecycle':('investment-product-lifecycle-planner','lifecycle'),
 'distribution':('investment-distribution-planner','distribution'),
 'service':('investment-client-service-preparer','service'),
 'report':('investment-investor-report-builder','investor_report'),
 'rfp':('institutional-proposal-responder','rfp'),
 'institutional':('investment-manager-due-diligence-reviewer','institutional'),
 'public':('investment-committee-memo-builder','public-security'),
 'manager':('investment-committee-memo-builder','manager'),
 'allocation':('investment-committee-memo-builder','allocation'),
}
EXPANDED={'institutional-proposal-responder','investment-manager-due-diligence-reviewer','investment-committee-memo-builder'}

def load(name,file):
 folder=ROOT/'skills/asset-management'/name/'scripts'
 for key in ('domain','phase2_domain','business_evidence','foundation_contract','native_integrity'):
  sys.modules.pop(key,None)
 sys.path.insert(0,str(folder))
 try:
  spec=importlib.util.spec_from_file_location('business_case_'+name.replace('-','_')+file.replace('.','_'),folder/file)
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
 finally:sys.path.pop(0)

def fixture(key):
 name,file=CASES[key];return json.loads((ROOT/'skills/asset-management'/name/'evals/files'/(file+'.json')).read_text())

def compute(key,doc=None):
 name,_=CASES[key];module=load(name,'phase2_domain.py' if name in EXPANDED else 'domain.py')
 return module.compute(fixture(key) if doc is None else doc)

def validate(key,output,doc):
 name,_=CASES[key]
 if name=='investment-manager-due-diligence-reviewer':
  folder=ROOT/'skills/asset-management'/name/'scripts';sys.path.insert(0,str(folder))
  try:return load(name,'domain.py').validate_output(output,doc)
  finally:sys.path.pop(0)
 folder=ROOT/'skills/asset-management'/name/'scripts';sys.path.insert(0,str(folder))
 try:return load(name,'validate_output.py').validate(output,doc)
 finally:sys.path.pop(0)

def change(doc,row,**updates):
 row['data'].update(updates)
 source=next(s for s in doc['sources'] if s['source_ref']==row['source_ref'])
 source['claims'][row['claim_id']]=copy.deepcopy(row['data'])

def source(doc,row):return next(s for s in doc['sources'] if s['source_ref']==row['source_ref'])

class BusinessPhase2(unittest.TestCase):
 def test_expanded_public_interfaces_reject_unknown_modes(self):
  for key in ('rfp','institutional','public'):
   name,_=CASES[key]
   for mode in ('unimplemented-mode',[],False):
    doc=fixture(key);doc['mode']=mode
    folder=ROOT/'skills/asset-management'/name/'scripts';sys.path.insert(0,str(folder))
    try:
     if key=='institutional':
      module=load(name,'domain.py');errors=module.validate(doc);calculate=module.build
     else:
      errors=load(name,'validate_input.py').validate(doc)[0];calculate=load(name,'calculate_or_transform.py').assemble
     self.assertTrue(errors)
     with self.assertRaises((ValueError,TypeError)):calculate(doc)
    finally:sys.path.pop(0)

 def test_all_modes_validate_and_reject_added_claims_and_different_original(self):
  for key in CASES:
   with self.subTest(mode=key):
    doc=fixture(key);out=compute(key,doc)
    self.assertEqual([],validate(key,out,doc));self.assertFalse(out['action_taken']);self.assertTrue(out['human_review_required'])
    self.assertNotIn('source_input',out);self.assertEqual('unverified',out['source_truth'])
    bad=copy.deepcopy(out);bad['invented_claim']='New unsupported business assertion'
    self.assertTrue(validate(key,bad,doc));self.assertTrue(validate(key,out,None))
    changed=copy.deepcopy(doc);changed['request_id']='other-request';self.assertTrue(validate(key,out,changed))

 def test_single_method_packages_reject_supplied_mode(self):
  for key in ('economics','lifecycle','distribution','service','report'):
   doc=fixture(key);doc['mode']='invented-algorithm'
   with self.subTest(skill=key),self.assertRaises(ValueError):compute(key,doc)

 def test_revenue_mix_uses_unrounded_revenue(self):
  doc=fixture('economics');change(doc,doc['products'][0],average_fee_aum='0.000049',fee_bps='100',other_revenue='0')
  product=compute('economics',doc)['results']['products'][0]
  self.assertEqual('0.000000',product['annualized_fee_revenue'])
  self.assertEqual(Decimal(1),Decimal(product['revenue_mix']))

 def test_aum_fee_profit_and_scenario_independent_numbers(self):
  result=compute('economics')['results'];product=result['products'][0]
  self.assertEqual('120000000.000000',product['expected_closing_aum'])
  self.assertEqual('15000000.000000',product['net_flows']);self.assertEqual('450000.000000',product['annualized_fee_revenue'])
  self.assertEqual('200000.000000',product['annualized_profit']);self.assertEqual('30000000.000000',product['capacity_headroom'])
  scenario=result['scenarios'][0];self.assertEqual('91400000.000000',scenario['scenario_aum']);self.assertEqual('88500.000000',scenario['annualized_profit'])

 def test_aum_break_withholds_book_total_and_scenario(self):
  doc=fixture('economics');change(doc,doc['products'][0],closing_aum=125000000)
  result=compute('economics',doc);self.assertFalse(result['results']['products'][0]['aum_reconciled'])
  self.assertIsNone(result['results']['totals']);self.assertEqual([],result['results']['scenarios']);self.assertTrue(result['unresolved_issues'])

 def test_missing_quantity_and_nonfinite_not_zero(self):
  for value in (None,True,'not available',float('inf')):
   doc=fixture('economics');change(doc,doc['products'][0],opening_aum=value)
   with self.subTest(value=value),self.assertRaises((ValueError,ArithmeticError)):compute('economics',doc)

 def test_economics_restricted_row_has_no_values_ids_or_ledger(self):
  doc=fixture('economics');row=doc['products'][0];change(doc,row,id='PRIVATE-PRODUCT-SECRET',closing_aum=123456789)
  s=source(doc,row);s['permitted_audiences']=['restricted-committee'];s['source_ref']='SECRET-SOURCE';row['source_ref']='SECRET-SOURCE'
  out=compute('economics',doc);blob=json.dumps(out)
  for secret in ('PRIVATE-PRODUCT-SECRET','SECRET-SOURCE','123456789'):self.assertNotIn(secret,blob)
  self.assertIsNone(out['results']['totals'])

 def test_lifecycle_launch_break_even_and_first_year(self):
  out=compute('lifecycle')['results'];self.assertEqual('100000.000000',out['economics']['first_year_contribution'])
  self.assertEqual(Decimal('50000000'),Decimal(out['economics']['break_even_aum']));self.assertEqual('eligible-for-human-review',out['review_readiness'])

 def test_lifecycle_missing_gate_and_no_default_approval(self):
  doc=fixture('lifecycle');doc['gates'].pop();out=compute('lifecycle',doc)
  self.assertEqual('blocked',out['results']['review_readiness']);self.assertEqual('unknown',out['results']['gates'][-1]['status'])
  doc=fixture('lifecycle');source(doc,doc['policy']).pop('approval_status');self.assertTrue(compute('lifecycle',doc)['unresolved_issues'])

 def test_lifecycle_merge_and_close_arithmetic(self):
  doc=fixture('lifecycle');doc['action']='merge';out=compute('lifecycle',doc)['results']['economics']
  self.assertEqual('90000000.000000',out['retained_aum']);self.assertEqual(Decimal(1),Decimal(out['payback_years']))
  doc['action']='close';out=compute('lifecycle',doc)['results']['economics'];self.assertEqual('750000.000000',out['modeled_residual'])

 def test_distribution_exact_policy_and_net_fees(self):
  out=compute('distribution')['results']['opportunities'][0]
  self.assertEqual('meets-supplied-policy',out['eligibility']);self.assertEqual('8000.000000',out['annual_net_fee'])
  doc=fixture('distribution');change(doc,doc['opportunities'][0],jurisdiction='GB')
  self.assertEqual('unknown',compute('distribution',doc)['results']['opportunities'][0]['eligibility'])

 def test_distribution_conflict_rebate_and_duplicate_policy(self):
  for update in ({'conflict_disclosed':False},{'rebate_bps':60},{'eligibility_confirmed':False}):
   doc=fixture('distribution');change(doc,doc['opportunities'][0],**update)
   self.assertEqual('blocked',compute('distribution',doc)['results']['opportunities'][0]['eligibility'])
  doc=fixture('distribution');other=copy.deepcopy(doc['policies'][0]);other['claim_id']='COPY';other['data']['id']='SECOND';source(doc,other)['claims']['COPY']=copy.deepcopy(other['data']);doc['policies'].append(other)
  self.assertEqual('unknown',compute('distribution',doc)['results']['opportunities'][0]['eligibility'])

 def test_service_calendar_and_sla_days(self):
  out=compute('service')['results'];self.assertEqual('2026-10-01',out['reporting_calendar'][0]['next_due'])
  self.assertEqual('2026-09-30',out['action_plan'][0]['sla_due']);self.assertFalse(out['action_plan'][0]['overdue'])
  doc=fixture('service');change(doc,doc['issues'][0],opened_at='2026-09-01',due_at='2026-09-15');out=compute('service',doc)
  self.assertTrue(out['results']['action_plan'][0]['sla_breached']);self.assertTrue(out['results']['action_plan'][0]['overdue'])

 def test_service_unverified_resolution_never_closes_case(self):
  doc=fixture('service');change(doc,doc['issues'][0],status='resolved',resolution_evidence_recorded=False)
  out=compute('service',doc);self.assertEqual('resolution-unverified',out['results']['action_plan'][0]['status']);self.assertFalse(out['results']['client_contacted'])

 def test_unverified_resolution_retains_overdue_and_sla_alerts(self):
  doc=fixture('service');change(doc,doc['issues'][0],status='resolved',resolution_evidence_recorded=False,opened_at='2026-09-01',due_at='2026-09-15')
  out=compute('service',doc);row=out['results']['action_plan'][0]
  self.assertEqual('resolution-unverified',row['status']);self.assertTrue(row['overdue']);self.assertTrue(row['sla_breached'])
  self.assertEqual('review-resolution-evidence',row['proposed_action'])
  self.assertIn('service action overdue',out['unresolved_issues']);self.assertIn('service issue exceeds supplied SLA',out['unresolved_issues'])

 def test_report_capital_and_performance_independent_arithmetic(self):
  r=compute('report')['results'];self.assertEqual('1200.000000',r['capital_bridge']['expected_closing']);self.assertEqual('150.000000',r['capital_bridge']['net_contributions'])
  self.assertEqual('0.020000',r['performance']['arithmetic_excess']);self.assertEqual('0.019048',r['performance']['relative_return']);self.assertEqual('not-authorized',r['publication_status'])

 def test_report_wrong_share_class_unreconciled_capital_and_gross_only(self):
  doc=fixture('report');change(doc,doc['performance'],share_class='OTHER');self.assertIsNone(compute('report',doc)['results']['performance'])
  doc=fixture('report');change(doc,doc['capital'],closing=9999);self.assertIsNone(compute('report',doc)['results']['capital_bridge'])
  doc=fixture('report');change(doc,doc['performance'],fund_net_return=None)
  with self.assertRaises(ValueError):compute('report',doc)

 def test_report_restricted_content_never_in_ledger(self):
  doc=fixture('report');row=doc['commentary'][0];change(doc,row,text='SECRET-CLIENT-NARRATIVE',id='SECRET-CONTENT-ID');s=source(doc,row);s['permitted_audiences']=['other-client'];s['source_ref']='SECRET-REF';row['source_ref']='SECRET-REF'
  blob=json.dumps(compute('report',doc))
  for secret in ('SECRET-CLIENT-NARRATIVE','SECRET-CONTENT-ID','SECRET-REF'):self.assertNotIn(secret,blob)

 def test_rfp_owner_data_commercial_and_approval_workflow(self):
  r=compute('rfp')['results'];self.assertEqual('drafted',r['responses'][0]['status']);self.assertEqual(0.06,r['data_appendix'][0]['value'])
  self.assertEqual('25000.000000',r['commercial_review']['annual_revenue']);self.assertEqual('15000.000000',r['commercial_review']['annual_contribution'])
  self.assertEqual('recorded-supplied',r['approval_queue'][0]['status']);self.assertEqual('not-performed',r['submission'])

 def test_rfp_missing_data_unknown_eligibility_and_self_approval(self):
  doc=fixture('rfp');doc['data_points']=[];doc['eligibility']=[];change(doc,doc['approvals'][0],actor='RFP analyst')
  r=compute('rfp',doc)['results'];self.assertIsNone(r['responses'][0]['text']);self.assertEqual('unknown',r['eligibility'][0]['status']);self.assertEqual('outstanding',r['approval_queue'][0]['status'])

 def test_actual_observations_cannot_postdate_their_source_knowledge(self):
  for key,rows in [('economics',['products']),('service',['issues','reports']),('report',['capital','performance']),('institutional',['performance'])]:
   doc=fixture(key)
   for entry in doc['sources']:entry['known_at']='2026-01-01';entry['as_of']='2026-01-01'
   if key=='economics':
    with self.assertRaises(ValueError):compute(key,doc)
   else:
    out=compute(key,doc);self.assertTrue(out['unresolved_issues'])
    if key=='service':self.assertEqual([],out['results']['action_plan']);self.assertEqual([],out['results']['reporting_calendar'])
    if key=='report':self.assertIsNone(out['results']['capital_bridge']);self.assertIsNone(out['results']['performance'])
    if key=='institutional':self.assertIsNone(out['results']['performance'])

 def test_rfp_approval_cannot_postdate_knowledge_cutoff_or_source(self):
  for cutoff,source_known in [('2026-09-15','2026-09-15'),('2026-09-21','2026-09-15')]:
   doc=fixture('rfp');doc['knowledge_cutoff']=cutoff
   for entry in doc['sources']:entry['known_at']=source_known;entry['as_of']='2026-09-15'
   change(doc,doc['approvals'][0],recorded_at='2026-09-20')
   out=compute('rfp',doc)
   with self.subTest(cutoff=cutoff,known=source_known):
    self.assertEqual('outstanding',out['results']['approval_queue'][0]['status'])
    self.assertEqual('blocked',out['results']['review_readiness'])

 def test_rfp_approval_requires_named_actor(self):
  doc=fixture('rfp');change(doc,doc['approvals'][0],actor='')
  out=compute('rfp',doc);self.assertEqual('outstanding',out['results']['approval_queue'][0]['status'])
  self.assertEqual('blocked',out['results']['review_readiness'])

 def test_rfp_expired_content_and_below_policy_fees(self):
  doc=fixture('rfp');change(doc,doc['answers'][0],expires='2026-01-01');change(doc,doc['commercial'],fee_bps=5)
  r=compute('rfp',doc)['results'];self.assertIsNone(r['responses'][0]['text']);self.assertFalse(r['commercial_review']['meets_policy'])

 def test_institutional_six_dimensions_fees_and_capacity(self):
  r=compute('institutional')['results'];self.assertEqual(6,len(r['criteria']));self.assertEqual(Decimal(1),Decimal(r['policy_score']))
  self.assertEqual('120000.000000',r['fees']['annual_flat_fee']);self.assertEqual('30000000.000000',r['capacity']['post_commitment_headroom']);self.assertEqual('0.020000',r['performance']['arithmetic_excess'])

 def test_institutional_unknown_or_nonindependent_evidence_not_eligible(self):
  doc=fixture('institutional');change(doc,doc['evidence'][1],origin='manager-reported')
  r=compute('institutional',doc)['results'];self.assertIsNone(r['policy_score']);self.assertEqual('unknown',r['criteria'][1]['status']);self.assertEqual('unresolved',r['eligibility'])
  doc=fixture('institutional');doc['policy']=None;r=compute('institutional',doc)['results'];self.assertIsNone(r['policy_score']);self.assertEqual([],r['criteria'])

 def test_ic_public_security_expected_return_and_sector_weight(self):
  r=compute('public')['results'];self.assertEqual(Decimal('0.2'),Decimal(r['analysis']['expected_total_return']));self.assertEqual('0.220000',r['analysis']['sector_weight_after']);self.assertEqual('pending',r['committee_decision'])

 def test_ic_missing_scenario_and_hard_limit_blocks(self):
  doc=fixture('public');doc['scenarios'].pop();change(doc,doc['proposal'],proposed_weight=0.1)
  r=compute('public',doc)['results'];self.assertIsNone(r['analysis']['expected_total_return']);self.assertEqual('blocked',r['review_readiness'])

 def test_ic_manager_wrong_diligence_scope_blocks(self):
  doc=fixture('manager');change(doc,doc['manager_evidence'],manager_id='OTHER')
  out=compute('manager',doc);self.assertTrue(out['unresolved_issues']);self.assertEqual('pending',out['results']['committee_decision'])

 def test_ic_allocation_return_turnover_and_missing_weight(self):
  r=compute('allocation')['results']['analysis'];self.assertEqual('0.060000',r['expected_return']);self.assertEqual('0.100000',r['one_way_turnover'])
  doc=fixture('allocation');change(doc,doc['allocations'][0],proposed_weight=0.8);r=compute('allocation',doc)['results']['analysis'];self.assertIsNone(r['expected_return']);self.assertIsNone(r['one_way_turnover'])

 def test_known_citation_does_not_validate_changed_claim_content(self):
  doc=fixture('service');doc['messages'][0]['data']['text']='An unsupported confident service claim'
  out=compute('service',doc);self.assertEqual([],out['results']['approved_content_draft']);self.assertNotIn('unsupported confident',json.dumps(out))

 def test_cross_object_currency_future_source_and_external_audience(self):
  for field,value in [('object_id','OTHER'),('currency','EUR')]:
   doc=fixture('economics');source(doc,doc['products'][0])[field]=value;self.assertEqual([],compute('economics',doc)['results']['products'])
  for key in CASES:
   doc=fixture(key);doc['sources'][0]['known_at']='2099-01-01'
   with self.subTest(mode=key),self.assertRaises(ValueError):compute(key,doc)
   doc=fixture(key);doc['audience']='public'
   with self.subTest(mode=key),self.assertRaises(ValueError):compute(key,doc)

if __name__=='__main__':unittest.main(verbosity=2)
