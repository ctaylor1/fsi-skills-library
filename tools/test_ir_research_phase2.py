#!/usr/bin/env python3
"""Independent quantitative and adverse checks for Phase 2 research methods."""
import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NEW=('research-coverage-planner','research-universe-screener','company-business-model-analyzer','financial-statement-analyzer','earnings-quality-analyzer','investment-thesis-developer')
EXPANDED=('company-profile-builder','coverage-initiation-researcher','market-landscape-researcher','market-sizing-builder','filing-disclosure-change-detector')
ALL=NEW+EXPANDED
def package(name):return ROOT/'skills/investment-research'/name
def fixture(name):return json.loads((package(name)/'evals/files'/('input.json' if name in NEW else 'phase2-input.json')).read_text())
def call(name,script,doc,args=()):
    return subprocess.run([sys.executable,'-B',str(package(name)/'scripts'/script),*args],input=json.dumps(doc,allow_nan=True),text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
def calculate(name,doc):
    result=call(name,'calculate_or_transform.py',doc)
    if result.returncode:raise AssertionError(result.stdout+result.stderr)
    return json.loads(result.stdout)
def output_check(name,doc,result):
    with tempfile.TemporaryDirectory(prefix='ir-research-p2-') as temp:
        original=Path(temp)/'original.json';original.write_text(json.dumps(doc))
        return call(name,'validate_output.py',result,('--input',str(original)))

class ResearchPhase2(unittest.TestCase):
    def test_coverage_dependencies_and_critical_gaps(self):
        n='research-coverage-planner';d=fixture(n);r=calculate(n,d)['results']
        self.assertEqual(r['execution_order'],['Q1','Q2']);self.assertEqual(r['supplied_answer_coverage'],0.5);self.assertEqual(r['critical_gaps'],[])
        d['questions'][0]['answer_status']='unanswered';r=calculate(n,d)['results'];self.assertEqual(r['critical_gaps'],['Q1']);self.assertEqual(r['question_plan'][1]['state'],'dependency-blocked');self.assertEqual(r['decision_readiness'],'defer-for-evidence')
    def test_coverage_cycle_rejected(self):
        n='research-coverage-planner';d=fixture(n);d['questions'][0]['depends_on']=['Q2'];self.assertEqual(call(n,'calculate_or_transform.py',d).returncode,1)
    def test_coverage_supplied_answer_needs_actual_answer(self):
        n='research-coverage-planner';d=fixture(n);d['questions'][0].pop('answer');self.assertEqual(call(n,'calculate_or_transform.py',d).returncode,1)
    def test_universe_inclusion_missing_and_failure_registers(self):
        n='research-universe-screener';d=fixture(n);r=calculate(n,d)['results'];self.assertEqual(r['included_security_ids'],['ACME-A']);self.assertEqual(r['not_evaluable_security_ids'],['BETA-A'])
        d['universe'][1]['metrics']['revenue']['value']=0;r=calculate(n,d)['results'];self.assertEqual(r['excluded_security_ids'],['BETA-A']);self.assertEqual(r['not_evaluable_security_ids'],[])
    def test_universe_stale_future_and_incomparable_values(self):
        n='research-universe-screener'
        for changes in ({'observed_on':'2025-01-01'},{'observed_on':'2026-10-21'},{'currency':'EUR'},{'period_id':'FY2024'}):
            d=fixture(n);d['universe'][0]['metrics']['revenue'].update(changes);r=calculate(n,d)['results'];self.assertIn('ACME-A',r['not_evaluable_security_ids'])
    def test_universe_source_identity_must_name_constituent(self):
        n='research-universe-screener';d=fixture(n);d['sources'][0]['subject_ids']=['TEST-UNIVERSE'];self.assertEqual(call(n,'calculate_or_transform.py',d).returncode,1)
    def test_business_unit_economics_and_reconciliation(self):
        n='company-business-model-analyzer';r=calculate(n,fixture(n))['results'];s=r['segments'][0]
        self.assertEqual(s['contribution_profit'],90);self.assertEqual(s['contribution_margin'],0.75);self.assertEqual(s['revenue_per_unit'],2);self.assertEqual(s['share_of_consolidated_revenue'],0.6);self.assertEqual(r['segment_reconciliation']['residual'],0);self.assertEqual(r['named_customer_exposures'][0]['share_of_consolidated_revenue'],0.15)
    def test_business_missing_inputs_and_unsourced_claims_withheld(self):
        n='company-business-model-analyzer';d=fixture(n);d['segments'][0]['revenue']=None;d['business_claims'][0]['evidence_refs']=[];r=calculate(n,d)
        self.assertIsNone(r['results']['segment_reconciliation']['residual']);self.assertEqual(r['results']['business_claims'],[]);self.assertEqual(r['status'],'partial')
        d=fixture(n);d['segments'][0]['evidence_refs']=[];r=calculate(n,d)['results'];self.assertIsNone(r['segments'][0]['revenue']);self.assertIsNone(r['segments'][0]['contribution_profit'])
    def test_statement_ratios_growth_cash_and_balance(self):
        n='financial-statement-analyzer';r=calculate(n,fixture(n))['results']['period_analysis'];p=r[1]
        self.assertAlmostEqual(p['ratios']['gross_margin'],0.6);self.assertEqual(p['ratios']['current_ratio'],2);self.assertEqual(p['free_cash_flow'],12);self.assertEqual(p['balance_residual'],0);self.assertAlmostEqual(p['trends']['revenue']['growth'],0.2)
    def test_statement_nonpositive_denominators_are_not_ratios(self):
        n='financial-statement-analyzer';d=fixture(n);d['periods'][1]['metrics'].update(net_income=-2,equity=-10,interest_expense=0,current_liabilities=0);r=calculate(n,d)['results']['period_analysis'][1]
        for k in ('cash_conversion','debt_to_equity','interest_coverage','current_ratio'):self.assertIsNone(r['ratios'][k])
        self.assertLess(r['ratios']['net_margin'],0)
    def test_statement_sector_and_period_guards(self):
        n='financial-statement-analyzer'
        for changes in ({'issuer_profile':'bank'},{'capex_sign_convention':'negative-outflow'}):
            d=fixture(n);d.update(changes);self.assertEqual(call(n,'calculate_or_transform.py',d).returncode,1)
        d=fixture(n);d['periods'][1]['start']='2024-12-31';self.assertEqual(call(n,'calculate_or_transform.py',d).returncode,1)
    def test_statement_missing_evidence_does_not_produce_ratios(self):
        n='financial-statement-analyzer';d=fixture(n);d['periods'][1]['evidence_refs']=[];r=calculate(n,d)['results']['period_analysis'][1];self.assertTrue(all(v is None for v in r['metrics'].values()));self.assertIsNone(r['free_cash_flow'])
    def test_quality_accruals_and_recurring_addbacks(self):
        n='earnings-quality-analyzer';r=calculate(n,fixture(n))['results'];self.assertEqual(r['average_assets'],120);self.assertEqual(r['total_accruals'],4);self.assertAlmostEqual(r['accrual_ratio'],1/30);self.assertAlmostEqual(r['cash_conversion'],2/3);self.assertEqual(r['supplied_adjusted_income'],17);self.assertEqual(r['provisional_normalized_income'],15);self.assertEqual(r['evidence_supported_nonrecurring_adjustments'],['A1'])
    def test_quality_adjustment_period_tax_and_negative_income(self):
        n='earnings-quality-analyzer'
        for change in ({'period_id':'FY2024'},{'amount_basis':'pretax'}):
            d=fixture(n);d['adjustments'][0].update(change);self.assertEqual(call(n,'calculate_or_transform.py',d).returncode,1)
        d=fixture(n);d['net_income']=-10;r=calculate(n,d)['results'];self.assertIsNone(r['cash_conversion']);self.assertEqual(r['provisional_normalized_income'],-7)
    def test_thesis_variant_and_invalidation(self):
        n='investment-thesis-developer';r=calculate(n,fixture(n))['results'];self.assertEqual(r['variant_expectations'][0]['analyst_minus_consensus'],20);self.assertEqual(r['variant_expectations'][0]['relative_gap'],0.2);self.assertTrue(r['falsifiers'][0]['triggered']);self.assertEqual(r['review_state'],'revisit-thesis');self.assertEqual(len(r['counter_evidence']),1)
    def test_thesis_missing_consensus_and_overdue_catalyst(self):
        n='investment-thesis-developer';d=fixture(n);d['variant_expectations'][0]['consensus']=None;d['catalysts'][0]['expected_on']='2026-10-01';d['falsifiers'][0]['observed']=None;r=calculate(n,d)['results'];self.assertIsNone(r['variant_expectations'][0]['analyst_minus_consensus']);self.assertEqual(r['catalysts'][0]['review_state'],'overdue-unresolved');self.assertIsNone(r['falsifiers'][0]['triggered'])
    def test_profile_scaled_productivity_and_incomplete_section(self):
        n='company-profile-builder';d=fixture(n);r=calculate(n,d)['results'];self.assertEqual(r['quantified_profile']['revenue_per_employee'][0]['revenue_per_employee'],400000)
        d['observations'][0]['evidence_refs']=[];r=calculate(n,d);self.assertEqual(r['results']['quantified_profile']['revenue_per_employee'],[]);self.assertEqual(r['status'],'partial')
    def test_initiation_method_comparability_and_optional_weighting(self):
        n='coverage-initiation-researcher';d=fixture(n);r=calculate(n,d)['results'];self.assertEqual(r['valuation']['range'],{'low':48,'high':52});self.assertEqual(r['valuation']['weighted_midpoint'],50)
        d.pop('weights');d['method_outputs'][1]['currency']='EUR';r=calculate(n,d)['results'];self.assertEqual(r['valuation']['range'],{'low':48,'high':48});self.assertIsNone(r['valuation']['weighted_midpoint']);self.assertEqual(r['readiness'],'analyst-review')
    def test_initiation_share_class_and_model_issues(self):
        n='coverage-initiation-researcher';d=fixture(n);d['method_outputs'][1]['valuation_subject']['share_count_basis']='basic';d['model_review']['issues']=['funding infeasible'];r=calculate(n,d);self.assertEqual(len(r['results']['valuation']['excluded_methods']),1);self.assertIn('funding infeasible',r['unresolved_issues']);self.assertIsNone(r['results']['valuation']['weighted_midpoint'])
    def test_landscape_comparability_tail_bounds_and_no_normalization(self):
        n='market-landscape-researcher';r=calculate(n,fixture(n))['results'];self.assertEqual(r['named_share_sum_pct'],70);self.assertEqual(r['unattributed_tail_pct'],30);self.assertEqual(r['named_hhi_lower_bound'],2500);self.assertEqual(r['hhi_upper_bound_unknown_tail'],3400);self.assertEqual(len(r['excluded_shares']),1)
    def test_landscape_excess_comparable_shares_rejected(self):
        n='market-landscape-researcher';d=fixture(n);d['competitors'][0]['share_pct']=80;self.assertEqual(call(n,'calculate_or_transform.py',d).returncode,1)
        d=fixture(n);d['share_basis']=' Unknown ';self.assertEqual(call(n,'calculate_or_transform.py',d).returncode,1)
    def test_sizing_reconciliation_and_one_driver_sensitivity(self):
        n='market-sizing-builder';r=calculate(n,fixture(n))['results'];self.assertEqual(r['bottom_up'],{'tam':1000,'sam':500,'som':100});self.assertEqual(r['reconciliation'][0]['difference'],0);self.assertAlmostEqual(r['sensitivity'][0]['levels']['tam'],1050);self.assertAlmostEqual(r['sensitivity'][0]['levels']['som'],105);self.assertEqual(r['sensitivity'][1]['levels']['tam'],900)
    def test_sizing_dimensions_overlap_and_evidence(self):
        n='market-sizing-builder';d=fixture(n);d['segments'][0]['unit_denominator']='transactions';self.assertEqual(call(n,'calculate_or_transform.py',d).returncode,1)
        d=fixture(n);d['segments_disjoint']=False;r=calculate(n,d);self.assertIn('bottom-up segment overlap unresolved',r['unresolved_issues'])
        d=fixture(n);d['segments'][0]['evidence_refs']=[];r=calculate(n,d);self.assertIsNone(r['results']);self.assertEqual(r['status'],'partial')
    def test_filing_incomplete_inventory_and_materiality_triage(self):
        n='filing-disclosure-change-detector';r=calculate(n,fixture(n));self.assertEqual([x['type'] for x in r['results']['findings']],['changed']);self.assertEqual(r['results']['findings'][0]['priority'],'specialist-review');self.assertEqual(r['results']['quantitative_triage'][0]['relative_change'],0.2);self.assertEqual(r['results']['quantitative_triage'][0]['priority'],'threshold-review');self.assertEqual(r['status'],'partial')
    def test_filing_complete_inventory_adds_removal_and_zero_prior_unknown(self):
        n='filing-disclosure-change-detector';d=fixture(n);d['current']['inventory_complete']=True;d['quantitative_changes'][0]['prior_value']=0;r=calculate(n,d)['results'];self.assertIn('removed',{x['type'] for x in r['findings']});self.assertIsNone(r['quantitative_triage'][0]['relative_change'])

def bound_roundtrip(name):
    def test(self):
        d=fixture(name);r=calculate(name,d);self.assertEqual(output_check(name,d,r).returncode,0)
        self.assertFalse(r['authority_granted']);self.assertFalse(r['action_taken']);self.assertEqual(r['professional_acceptance'],'not-established')
        for mutation in ('drop','extra','tamper','wrong-original'):
            output=copy.deepcopy(r);original=copy.deepcopy(d)
            if mutation=='drop':output.pop('calculation_lineage')
            elif mutation=='extra':output['approved']=True
            elif mutation=='tamper':output['authority_granted']=True
            else:original['request_id']='different-original'
            result=output_check(name,original,output);self.assertEqual(result.returncode,1,mutation);self.assertNotIn('Traceback',result.stderr)
    return test
def source_controls(name):
    def test(self):
        for field,value in (('known_at','2027-01-01'),('permission_status','denied'),('classification','restricted'),('expires_on','2026-10-19'),('subject_ids',['OTHER'])):
            d=fixture(name);d['sources'][0][field]=value
            if name=='research-universe-screener' and field=='subject_ids':
                self.assertEqual(call(name,'calculate_or_transform.py',d).returncode,1);continue
            r=calculate(name,d);self.assertIsNone(r['results'],field);self.assertEqual(r['source_register'],[]);self.assertEqual(r['evidence_refs'],[]);self.assertEqual(r['status'],'partial')
    return test
NUMERIC_PATHS={
 'research-universe-screener':('universe',0,'metrics','revenue','value'),
 'company-business-model-analyzer':('segments',0,'revenue'),
 'financial-statement-analyzer':('periods',0,'metrics','revenue'),
 'earnings-quality-analyzer':('net_income',),
 'investment-thesis-developer':('variant_expectations',0,'analyst'),
 'company-profile-builder':('observations',0,'value'),
 'coverage-initiation-researcher':('method_outputs',0,'value_per_share'),
 'market-landscape-researcher':('competitors',0,'share_pct'),
 'market-sizing-builder':('segments',0,'units'),
 'filing-disclosure-change-detector':('quantitative_changes',0,'prior_value')}
def bad_numbers(name,path):
    def test(self):
        for value in (True,float('nan'),float('inf'),'120'):
            d=fixture(name);target=d
            for key in path[:-1]:target=target[key]
            target[path[-1]]=value
            result=call(name,'calculate_or_transform.py',d);self.assertEqual(result.returncode,1,repr(value));self.assertNotIn('Traceback',result.stderr)
    return test
def unknown_basis(name,path):
    def test(self):
        for value in ('unknown',' UNKNOWN ','unspecified','n/a'):
            d=fixture(name);target=d
            for key in path[:-1]:target=target[key]
            target[path[-1]]=value
            result=call(name,'calculate_or_transform.py',d);self.assertEqual(result.returncode,1,repr(value))
    return test
for name in ALL:
    setattr(ResearchPhase2,'test_bound_reconstruction_'+name.replace('-','_'),bound_roundtrip(name))
    setattr(ResearchPhase2,'test_source_controls_'+name.replace('-','_'),source_controls(name))
for name,path in NUMERIC_PATHS.items():setattr(ResearchPhase2,'test_numeric_guards_'+name.replace('-','_'),bad_numbers(name,path))
for name,path in {
 'company-business-model-analyzer':('accounting_basis',),
 'financial-statement-analyzer':('accounting_basis',),
 'earnings-quality-analyzer':('accounting_basis',),
 'investment-thesis-developer':('variant_expectations',0,'accounting_basis'),
 'research-universe-screener':('universe',0,'metrics','revenue','accounting_basis'),
 'company-profile-builder':('observations',0,'accounting_basis'),
 'coverage-initiation-researcher':('accounting_basis',),
 'market-sizing-builder':('accounting_basis',),
 'filing-disclosure-change-detector':('quantitative_changes',0,'accounting_basis')}.items():setattr(ResearchPhase2,'test_basis_guards_'+name.replace('-','_'),unknown_basis(name,path))

if __name__=='__main__':unittest.main()
