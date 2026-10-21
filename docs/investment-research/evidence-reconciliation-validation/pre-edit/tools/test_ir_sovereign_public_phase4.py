#!/usr/bin/env python3
"""Independent numerical, period, missingness and evidence controls for Phase 4 credit."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOV = 'sovereign-credit-researcher'
PUB = 'public-finance-credit-researcher'


def package(name): return ROOT / 'skills/investment-research' / name

def fixture(name): return json.loads((package(name) / 'evals/files/input.json').read_text())


def call(name, module, function, *args):
    sys.path.insert(0, str(package(name) / 'scripts'))
    try:
        for key in ('domain', 'analysis_contract', 'research_runtime', 'native_integrity', 'validate_input', 'validate_output', 'calculate_or_transform'):
            sys.modules.pop(key, None)
        spec = importlib.util.spec_from_file_location(module, package(name) / 'scripts' / (module + '.py'))
        obj = importlib.util.module_from_spec(spec); sys.modules[module] = obj; spec.loader.exec_module(obj)
        return getattr(obj, function)(*args)
    finally: sys.path.pop(0)


def compute(name, doc=None): return call(name, 'calculate_or_transform', 'compute', fixture(name) if doc is None else doc)

def bad(name, doc): return call(name, 'validate_input', 'validate', doc)[0]


def revenue():
    d = fixture(PUB)
    d['financial_scope'].update(obligation_type='revenue', pledged_system_id='WATER', pledge_basis='net-revenues')
    f = d['financials']
    d['financials'] = {k: copy.deepcopy(f[k]) for k in ('period_start', 'period_end', 'known_at', 'evidence_refs')}
    d['financials'].update(gross_pledged_revenue=200, operating_costs=120, required_other_prior_payments=5,
                          available_debt_service_reserve=20, capital_needs=80, committed_capital_funding=50,
                          supplied_coverage_threshold=1.5)
    d['obligations'][0]['pledged_system_id'] = 'WATER'
    return d


class SovereignPhase4(unittest.TestCase):
    def test_independent_nominal_currency_cash_stock_flow_identity(self):
        out = compute(SOV); r = out['results']; y = r['scenario_paths'][0]['years'][0]
        # Opening 600 local + 200 FX; 10% FX move, interest 36+8.8,
        # surplus 20, cash adjustment 5, actual fiscal cash draw 10.
        self.assertAlmostEqual(y['interest_expense'], 44.8)
        self.assertAlmostEqual(y['fx_revaluation'], 20)
        self.assertAlmostEqual(y['net_debt_creating_flows_excluding_fx'], 19.8)
        self.assertAlmostEqual(y['domestic_debt'], 614.85)
        self.assertAlmostEqual(y['foreign_currency_debt_local'], 224.95)
        self.assertAlmostEqual(y['gross_debt'], 839.8)
        self.assertEqual(y['gdp'], 1050)
        self.assertAlmostEqual(y['debt_to_gdp'], 839.8 / 1050)
        self.assertAlmostEqual(y['debt_to_gdp_change'], 839.8 / 1050 - .8)
        self.assertAlmostEqual(sum(y['debt_ratio_change_components'].values()), y['debt_to_gdp_change'])
        self.assertAlmostEqual(y['debt_stabilizing_primary_balance'], 19.8)
        self.assertAlmostEqual(y['gross_financing_needs'], 131.8)
        self.assertAlmostEqual(y['uncommitted_funding_gap'], 21.8)
        self.assertEqual(out['status'], 'partial')
        self.assertEqual(out, json.loads((package(SOV) / 'evals/files/valid.json').read_text()))

    def test_primary_surplus_positive_and_deficit_negative(self):
        a = fixture(SOV); b = copy.deepcopy(a); b['scenarios'][0]['years'][0]['primary_balance'] = -20
        ya = compute(SOV, a)['results']['scenario_paths'][0]['years'][0]
        yb = compute(SOV, b)['results']['scenario_paths'][0]['years'][0]
        self.assertAlmostEqual(yb['gross_debt'] - ya['gross_debt'], 40)
        self.assertAlmostEqual(yb['gross_financing_needs'] - ya['gross_financing_needs'], 40)

    def test_noncash_recognition_changes_debt_not_gross_cash_needs(self):
        a = fixture(SOV); b = copy.deepcopy(a)
        b['scenarios'][0]['years'][0]['other_noncash_debt_creating_flows'] = 25
        ya = compute(SOV, a)['results']['scenario_paths'][0]['years'][0]
        yb = compute(SOV, b)['results']['scenario_paths'][0]['years'][0]
        self.assertAlmostEqual(yb['gross_debt'] - ya['gross_debt'], 25)
        self.assertEqual(yb['gross_financing_needs'], ya['gross_financing_needs'])
        self.assertAlmostEqual(yb['debt_stabilizing_primary_balance'] - ya['debt_stabilizing_primary_balance'], 25)
        b['scenarios'][0]['years'][0]['other_cash_debt_creating_flows'] += 25
        yc = compute(SOV, b)['results']['scenario_paths'][0]['years'][0]
        self.assertAlmostEqual(yc['gross_financing_needs'] - yb['gross_financing_needs'], 25)

    def test_unused_cash_headroom_does_not_reduce_debt_or_count_as_funding(self):
        a = fixture(SOV); b = copy.deepcopy(a); b['scenarios'][0]['years'][0]['usable_fiscal_cash'] = 100
        ya = compute(SOV, a)['results']['scenario_paths'][0]['years'][0]
        yb = compute(SOV, b)['results']['scenario_paths'][0]['years'][0]
        self.assertEqual(ya['gross_debt'], yb['gross_debt'])
        self.assertEqual(ya['uncommitted_funding_gap'], yb['uncommitted_funding_gap'])
        self.assertEqual(yb['unused_fiscal_cash_capacity'], 90)
        b['scenarios'][0]['years'][0]['fiscal_cash_draw'] = 30
        yc = compute(SOV, b)['results']['scenario_paths'][0]['years'][0]
        self.assertAlmostEqual(yb['gross_debt'] - yc['gross_debt'], 20)
        self.assertAlmostEqual(yb['uncommitted_funding_gap'] - yc['uncommitted_funding_gap'], 20)

    def test_cash_draw_bounds_and_funding_cannot_rewrite_debt_path(self):
        a = fixture(SOV); a['scenarios'][0]['years'][0]['fiscal_cash_draw'] = 11
        self.assertTrue(bad(SOV, a))
        a = fixture(SOV); a['scenarios'][0]['years'][0].update(usable_fiscal_cash=1000, fiscal_cash_draw=1000)
        self.assertTrue(bad(SOV, a))
        a = fixture(SOV); b = copy.deepcopy(a); b['scenarios'][0]['years'][0]['committed_financing'] = 500
        ya = compute(SOV, a)['results']['scenario_paths'][0]['years'][0]
        yb = compute(SOV, b)['results']['scenario_paths'][0]['years'][0]
        self.assertEqual(ya['gross_debt'], yb['gross_debt']); self.assertEqual(yb['uncommitted_funding_gap'], 0)
        self.assertAlmostEqual(yb['available_funding_surplus_over_modeled_gfn'], 378.2)

    def test_maturity_refinancing_does_not_double_count_net_debt(self):
        a = fixture(SOV); b = copy.deepcopy(a); b['scenarios'][0]['years'][0]['domestic_principal_due'] += 20
        ya = compute(SOV, a)['results']['scenario_paths'][0]['years'][0]
        yb = compute(SOV, b)['results']['scenario_paths'][0]['years'][0]
        self.assertEqual(ya['gross_debt'], yb['gross_debt'])
        self.assertAlmostEqual(yb['gross_financing_needs'] - ya['gross_financing_needs'], 20)
        b['scenarios'][0]['years'][0]['foreign_principal_due_local'] = 201
        self.assertTrue(bad(SOV, b))

    def test_gdp_growth_dilution_and_no_real_rate_substitution(self):
        a = fixture(SOV); a['scenarios'][0]['years'][0].update(nominal_gdp_growth=.1, primary_balance=0, other_cash_debt_creating_flows=0, domestic_effective_rate=0, foreign_effective_rate=0, fx_depreciation=0, fiscal_cash_draw=0)
        y = compute(SOV, a)['results']['scenario_paths'][0]['years'][0]
        self.assertEqual(y['gross_debt'], 800); self.assertEqual(y['gdp'], 1100)
        self.assertAlmostEqual(y['debt_ratio_change_components']['gdp_denominator_change'], -80/1100)
        self.assertAlmostEqual(y['debt_stabilizing_primary_balance'], -80)

    def test_multiyear_contiguous_recursion_and_fx_stock(self):
        d = fixture(SOV); first = d['scenarios'][0]['years'][0]
        nxt = dict(first, year=2027, nominal_gdp_growth=0, fx_depreciation=0, domestic_effective_rate=0, foreign_effective_rate=0, primary_balance=0, other_cash_debt_creating_flows=0, fiscal_cash_draw=0)
        d['scenarios'][0]['years'].append(nxt)
        ys = compute(SOV, d)['results']['scenario_paths'][0]['years']
        self.assertEqual(ys[0]['gross_debt'], ys[1]['opening_debt']); self.assertEqual(ys[0]['gross_debt'], ys[1]['gross_debt'])
        d['scenarios'][0]['years'][1]['year'] = 2028; self.assertTrue(bad(SOV, d))

    def test_retirement_allocation_and_nonnegative_stocks(self):
        d = fixture(SOV); y=d['scenarios'][0]['years'][0]
        y.update(primary_balance=500, fiscal_cash_draw=0, new_debt_foreign_share=1)
        self.assertTrue(bad(SOV, d))
        y.update(new_debt_foreign_share=0)
        out=compute(SOV,d); self.assertGreaterEqual(out['results']['scenario_paths'][0]['years'][0]['domestic_debt'],0)

    def test_external_scope_reserves_ratio_and_missingness(self):
        d=fixture(SOV); e=compute(SOV,d)['results']['external_liquidity']
        self.assertEqual(e['reserves_to_short_term_external_debt'], .75); self.assertEqual(e['reserve_import_months'],6)
        self.assertFalse(e['fiscal_availability_established'])
        d['external_liquidity']['reserves_available']=None
        out=compute(SOV,d);self.assertIsNone(out['results']['external_liquidity']['reserve_import_months']);self.assertEqual(out['status'],'partial')
        d['external_liquidity']=None;self.assertIsNone(compute(SOV,d)['results']['external_liquidity'])
        d=fixture(SOV);d['external_liquidity']['scope']='government';self.assertTrue(bad(SOV,d))
        d=fixture(SOV);d['external_liquidity']['currency']='EUR';self.assertTrue(bad(SOV,d))

    def test_zero_external_denominator_never_infinite_or_zero_coverage(self):
        d=fixture(SOV);d['external_liquidity'].update(short_term_external_debt_residual_maturity=0,imports_next_12_months=0)
        e=compute(SOV,d)['results']['external_liquidity'];self.assertIsNone(e['reserves_to_short_term_external_debt']);self.assertIsNone(e['reserve_import_months'])

    def test_scope_identity_numerics_and_annual_input_rejections(self):
        cases=[]
        for k,v in [('country_id','OTHER'),('debt_measure','net'),('accounting_basis',' unknown '),('currency','usd')]:
            d=fixture(SOV);d['sovereign_scope'][k]=v;cases.append(d)
        for k,v in [('gdp',None),('gdp',0),('domestic_debt',True),('balance_date','2025-09-30')]:
            d=fixture(SOV);d['baseline'][k]=v;cases.append(d)
        for k,v in [('fx_depreciation',-1),('nominal_gdp_growth',-1),('new_debt_foreign_share',1.01),('domestic_principal_due',601)]:
            d=fixture(SOV);d['scenarios'][0]['years'][0][k]=v;cases.append(d)
        for d in cases:self.assertTrue(bad(SOV,d))
        d=fixture(SOV);d['subject']={'type':'economy','id':'SYNTHETIC-SOVEREIGN'};self.assertFalse(bad(SOV,d))
        d['subject']={'type':'security','id':'BOND','issuer_id':'SYNTHETIC-SOVEREIGN'};self.assertFalse(bad(SOV,d))


class PublicFinancePhase4(unittest.TestCase):
    def test_go_arithmetic_distinguishes_pension_cash_and_debt_service(self):
        out=compute(PUB);r=out['results']['reported_metrics']
        self.assertEqual(r['supplied_direct_debt_outstanding'],400);self.assertEqual(r['supplied_direct_debt_service'],35)
        self.assertEqual(r['available_before_direct_debt_service'],80);self.assertEqual(r['recurrent_balance_after_direct_debt_service'],45)
        self.assertAlmostEqual(r['illustrative_general_resource_coverage'],80/35)
        self.assertEqual(r['pension_contribution_shortfall'],5);self.assertEqual(r['unfunded_pension_liability'],100)
        self.assertAlmostEqual(r['unrestricted_fund_balance_to_operating_costs'],60/220)
        self.assertEqual(r['direct_debt_to_assessed_tax_base'],.08);self.assertEqual(r['unfunded_capital_needs'],30)
        self.assertEqual(r['restricted_cash_excluded_from_available_funds'],30)
        self.assertFalse(r['covenant_compliance_established']);self.assertEqual(out['status'],'partial')
        self.assertEqual(out,json.loads((package(PUB)/'evals/files/valid.json').read_text()))

    def test_go_stress_holds_pension_and_principal_separate(self):
        r=compute(PUB)['results']['conditional_scenarios'][0]['metrics']
        self.assertEqual(r['general_revenue'],270);self.assertEqual(r['operating_costs_excluding_debt_service_and_pension'],210)
        self.assertEqual(r['supplied_direct_principal_due'],20);self.assertEqual(r['supplied_direct_interest_due'],18)
        self.assertEqual(r['available_before_direct_debt_service'],40);self.assertEqual(r['recurrent_balance_after_direct_debt_service'],2)
        self.assertEqual(r['supplied_pension_paid_contribution'],20);self.assertEqual(r['unfunded_capital_needs'],38)

    def test_net_revenue_pledge_prior_payments_and_reserve_exclusion(self):
        d=revenue();r=compute(PUB,d)['results']['reported_metrics']
        self.assertEqual(r['recurring_available_for_direct_debt_service'],75)
        self.assertAlmostEqual(r['illustrative_pledged_revenue_coverage'],75/35)
        self.assertAlmostEqual(r['numerical_margin_to_supplied_threshold'],75/35-1.5)
        d['financials']['available_debt_service_reserve']=1000
        self.assertEqual(compute(PUB,d)['results']['reported_metrics']['illustrative_pledged_revenue_coverage'],r['illustrative_pledged_revenue_coverage'])

    def test_gross_pledge_does_not_deduct_operating_costs_from_pledge(self):
        d=revenue();d['financial_scope']['pledge_basis']='gross-revenues';r=compute(PUB,d)['results']['reported_metrics']
        self.assertEqual(r['recurring_available_for_direct_debt_service'],195)
        self.assertAlmostEqual(r['illustrative_pledged_revenue_coverage'],195/35)
        self.assertEqual(r['system_operating_cash_after_operating_costs_and_debt_service'],40)
        d['financials']['operating_costs']=220;r=compute(PUB,d)['results']['reported_metrics']
        self.assertEqual(r['recurring_available_for_direct_debt_service'],195)
        self.assertEqual(r['system_operating_cash_after_operating_costs_and_debt_service'],-60)
        self.assertTrue(any('System operating costs' in x for x in compute(PUB,d)['unresolved_issues']))
        self.assertTrue(any('stressed system operating cash' in x for x in compute(PUB,d)['unresolved_issues']))

    def test_insufficient_pledged_flow_one_time_reserve_and_stress(self):
        d=revenue();d['financials'].update(gross_pledged_revenue=140,operating_costs=120,required_other_prior_payments=5)
        r=compute(PUB,d)['results']['reported_metrics']
        self.assertEqual(r['recurring_available_for_direct_debt_service'],15)
        self.assertEqual(r['recurring_cash_shortfall'],20);self.assertEqual(r['cash_shortfall_after_one_time_reserve'],0)
        self.assertAlmostEqual(r['illustrative_pledged_revenue_coverage'],15/35)
        self.assertEqual(compute(PUB,d)['status'],'partial')

    def test_incomplete_inventory_withholds_total_service_coverage(self):
        for d in [fixture(PUB),revenue()]:
            d['obligation_inventory_complete']=False;r=compute(PUB,d)['results']['reported_metrics']
            self.assertEqual(r['supplied_direct_debt_service'],35)
            field='illustrative_general_resource_coverage' if d['financial_scope']['obligation_type']=='general-obligation' else 'illustrative_pledged_revenue_coverage'
            self.assertIsNone(r[field]);self.assertEqual(compute(PUB,d)['status'],'partial')
            if field=='illustrative_general_resource_coverage':self.assertIsNone(r['direct_debt_to_assessed_tax_base']);self.assertIsNone(r['recurrent_balance_after_direct_debt_service'])

    def test_overlapping_contingent_exposures_never_double_counted(self):
        d=fixture(PUB);r=compute(PUB,d)['results'];x=r['separate_overlapping_contingent_exposures'][0]
        self.assertEqual(x['allocable_outstanding'],60);self.assertFalse(x['aggregated_with_direct_debt'])
        d['obligations'][1].update(scope='contingent',included_in_direct_debt=True)
        rr=compute(PUB,d)['results'];self.assertEqual(rr['reported_metrics']['supplied_direct_debt_outstanding'],400)
        self.assertTrue(rr['separate_overlapping_contingent_exposures'][0]['included_in_direct_debt'])

    def test_fiscal_period_and_security_binding(self):
        for key,value in [('period_start','2024-01-01'),('period_end','2026-12-31'),('security_id','SEC-GO1')]:
            d=fixture(PUB);d['obligations'][1][key]=value;self.assertTrue(bad(PUB,d))
        d=fixture(PUB);d['subject']={'type':'security','id':'SEC-GO1','issuer_id':'SYNTHETIC-CITY'};self.assertFalse(bad(PUB,d))
        d['subject']['id']='OTHER';self.assertTrue(bad(PUB,d))
        d=fixture(PUB);d['financials']['period_end']='2026-12-31';self.assertTrue(bad(PUB,d))

    def test_pledge_fallback_and_identity_not_allowed(self):
        cases=[]
        for key,value in [('entity_id','OTHER'),('pledge_basis','net-revenues'),('pledged_system_id','WATER'),('obligation_type','appropriation')]:
            d=fixture(PUB);d['financial_scope'][key]=value;cases.append(d)
        d=revenue();d['obligations'][0]['pledged_system_id']='SEWER';cases.append(d)
        d=revenue();d['financial_scope']['pledge_basis']='general-resources';cases.append(d)
        for d in cases:self.assertTrue(bad(PUB,d))

    def test_pension_missing_not_zero_and_negative_available_fund_balance(self):
        d=fixture(PUB);d['financials']['pension_paid_contribution']=None;r=compute(PUB,d)['results']['reported_metrics']
        self.assertIsNone(r['available_before_direct_debt_service']);self.assertIsNone(r['illustrative_general_resource_coverage']);self.assertIsNone(r['pension_contribution_shortfall'])
        d=fixture(PUB);d['financials']['unrestricted_available_fund_balance']=-10;r=compute(PUB,d)['results']['reported_metrics']
        self.assertAlmostEqual(r['unrestricted_fund_balance_to_operating_costs'],-10/220)

    def test_direct_zero_denominator_never_passing_coverage(self):
        d=fixture(PUB);d['obligations'][0].update(principal_due=0,interest_due=0)
        out=compute(PUB,d);self.assertIsNone(out['results']['reported_metrics']['illustrative_general_resource_coverage']);self.assertEqual(out['status'],'partial')

    def test_obligation_and_financial_numeric_adverse_cases(self):
        for key,value in [('principal_due',401),('allocable_share',.5),('included_in_direct_debt',True),('obligor_id','OTHER'),('outstanding',None),('interest_due',True)]:
            d=fixture(PUB);d['obligations'][0][key]=value;self.assertTrue(bad(PUB,d))
        d=fixture(PUB);d['financials']['top_ten_taxpayers_share']=2;self.assertTrue(bad(PUB,d))
        d=fixture(PUB);d['scenarios'][0]['revenue_change']=-1.1;self.assertTrue(bad(PUB,d))


class SharedPhase4CreditControls(unittest.TestCase):
    def test_required_qualitative_coverage_is_not_assumed(self):
        for name in (SOV,PUB):
            d=fixture(name);topic=d['coverage'][0]['topic'];d['coverage'].pop(0)
            out=compute(name,d);self.assertTrue(any(topic in i for i in out['unresolved_issues']))
            d=fixture(name);d['coverage'][0].update(status='not-reviewed',evidence_refs=[])
            self.assertEqual(compute(name,d)['status'],'partial')

    def test_citation_time_chain_and_precision(self):
        for name in (SOV,PUB):
            for target,key,value in [('source','known_at','2026-10-19T16:00:01Z'),('source','known_at','2026-10-19'),('row','known_at','2026-10-21T16:00:00Z'),('row','evidence_refs',[])]:
                d=fixture(name);row=d['sources'][0] if target=='source' else d['baseline'] if name==SOV else d['financials'];row[key]=value
                self.assertTrue(bad(name,d),(name,target,key,value))

    def test_source_denial_identity_and_expiry_withhold_projections(self):
        for name in (SOV,PUB):
            for key,value in [('permission_status','denied'),('classification','restricted'),('subject_ids',['OTHER']),('expires_on','2026-10-19')]:
                d=fixture(name);d['sources'][0][key]=value;out=compute(name,d)
                self.assertIsNone(out['results']);self.assertEqual(out['source_register'],[]);self.assertEqual(out['calculation_lineage'],[]);self.assertEqual(out['status'],'partial')

    def test_full_original_required_and_output_is_exact_reconstruction(self):
        for name in (SOV,PUB):
            d=fixture(name);out=compute(name,d)
            self.assertFalse(call(name,'validate_output','validate',out,d)[0])
            self.assertTrue(call(name,'validate_output','validate',out,None)[0])
            changed=copy.deepcopy(d);changed['unrelated_metadata']='different retained original'
            self.assertTrue(call(name,'validate_output','validate',out,changed)[0])
            for key in out:
                x=copy.deepcopy(out);del x[key];self.assertTrue(call(name,'validate_output','validate',x,d)[0],(name,key))
            for x in [dict(out,authority_granted=True),dict(out,source_input=d),dict(out,extra='approved')]:
                self.assertTrue(call(name,'validate_output','validate',x,d)[0])
            x=copy.deepcopy(out);x['results']['research_acceptance']='approved'
            self.assertTrue(call(name,'validate_output','validate',x,d)[0])

    def test_authority_and_inherited_issues_preserved(self):
        for name in (SOV,PUB):
            d=fixture(name);d['unresolved_issues']=['Independent inventory reconciliation pending']
            out=compute(name,d);self.assertIn(d['unresolved_issues'][0],out['unresolved_issues'])
            self.assertFalse(out['authority_granted']);self.assertFalse(out['action_taken']);self.assertNotIn('source_input',out)
            self.assertEqual(out['source_truth'],'unverified');self.assertEqual(out['professional_acceptance'],'not-established')

    def test_actual_cli_and_strict_json_reader(self):
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        with tempfile.TemporaryDirectory(prefix='ir-credit-phase4-') as temp:
            for name in (SOV,PUB):
                pkg=package(name);source=pkg/'evals/files/input.json';target=Path(temp)/(name+'.json')
                p=subprocess.run([sys.executable,'-B','scripts/calculate_or_transform.py',str(source)],cwd=pkg,env=env,capture_output=True,text=True)
                self.assertEqual(p.returncode,0,p.stdout+p.stderr);target.write_text(p.stdout)
                p=subprocess.run([sys.executable,'-B','scripts/validate_output.py',str(target),'--input',str(source)],cwd=pkg,env=env,capture_output=True,text=True)
                self.assertEqual(p.returncode,0,p.stdout+p.stderr)
                for raw in ['{"request_id":"one","request_id":"two"}','{"x":NaN}','{"x":Infinity}']:
                    f=Path(temp)/'bad.json';f.write_text(raw)
                    for script in ('validate_input.py','calculate_or_transform.py','validate_output.py'):
                        args=[sys.executable,'-B','scripts/'+script,str(f)]+(['--input',str(source)] if script=='validate_output.py' else [])
                        p=subprocess.run(args,cwd=pkg,env=env,capture_output=True,text=True)
                        self.assertEqual(p.returncode,1,p.stdout+p.stderr);self.assertIn('ERROR:',p.stdout);self.assertNotIn('Traceback',p.stdout+p.stderr)


if __name__ == '__main__': unittest.main(verbosity=2)
