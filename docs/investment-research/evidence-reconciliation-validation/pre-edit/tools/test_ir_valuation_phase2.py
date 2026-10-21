#!/usr/bin/env python3
"""Independent arithmetic, parity, model-linked and adversarial supplied-input checks."""
from __future__ import annotations
import copy, importlib.util, json, math, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NEW=('research-financial-model-reviewer','dividend-residual-income-modeler','asset-based-valuation-modeler','sum-of-the-parts-valuation-builder','valuation-reconciliation-analyzer')
EXISTING=('three-statement-model-builder','dcf-modeler','comps-analysis-builder','scenario-sensitivity-generator','kpi-segment-bridge-builder')
def fixture(name):
    p=ROOT/'skills/investment-research'/name
    return json.loads((p/'evals/files'/('input.json' if name in NEW else 'phase2-input.json')).read_text())
def legacy_base():
    active=ROOT/'skills/investment-research/model-roll-forward-auditor'
    return active if active.exists() else ROOT/'docs/investment-research/phase2-validation/legacy-auditor'
def load(name,filename='domain.py'):
    p=(legacy_base() if name=='model-roll-forward-auditor' else ROOT/'skills/investment-research'/name)/'scripts';sys.path.insert(0,str(p));sys.modules.pop('domain',None)
    try:
        spec=importlib.util.spec_from_file_location(name.replace('-','_')+'_'+filename,p/filename);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    finally:sys.path.remove(str(p))
def method(name):return load(name,'domain.py' if name in NEW else 'phase2_domain.py')
class ValuationPhase2(unittest.TestCase):
    def test_ddm_and_residual_income_independent_math(self):
        n='dividend-residual-income-modeler';d=fixture(n);r=method(n).compute(d)['results']
        expected=100+5/1.1+5/1.1**2+(5*1.02/.08)/1.1**2
        self.assertAlmostEqual(expected,r['equity_value'])
        d['method']='dividend-discount';r=method(n).compute(d)['results']
        self.assertAlmostEqual(5/1.1+6/1.1**2+(6*1.02/.08)/1.1**2,r['equity_value'])
        d['terminal_growth']=.1
        with self.assertRaises(ValueError):method(n).compute(d)
    def test_clean_surplus_cannot_hide_equity_movements(self):
        n='dividend-residual-income-modeler';d=fixture(n);d['forecasts'][0]['other_equity_movements']=2
        with self.assertRaises(ValueError):method(n).compute(d)
        d=fixture(n);d['forecasts'][1]['beginning_book_value']=111
        with self.assertRaises(ValueError):method(n).compute(d)
    def test_asset_nav_and_negative_equity(self):
        n='asset-based-valuation-modeler';d=fixture(n);r=method(n).compute(d)['results'];self.assertEqual(130,r['equity_value']);self.assertEqual(13,r['value_per_share'])
        d['liabilities'][0]['amount']=500;r=method(n).compute(d)['results'];self.assertEqual(-320,r['equity_value'])
        d['assets'][0]['haircut']=1.01
        with self.assertRaises(ValueError):method(n).compute(d)
    def test_sotp_prevents_overlaps_and_double_debt(self):
        n='sum-of-the-parts-valuation-builder';d=fixture(n);r=method(n).compute(d)['results'];self.assertEqual(240,r['equity_value'])
        d['segments'][1]['debt_included_in_group_bridge']=5
        with self.assertRaises(ValueError):method(n).compute(d)
        d=fixture(n);d['segments'][1]['component_ids']=['business-A']
        with self.assertRaises(ValueError):method(n).compute(d)
    def test_reconciliation_has_no_forced_midpoint(self):
        n='valuation-reconciliation-analyzer';d=fixture(n);r=method(n).compute(d)['results'];self.assertEqual(-20,r['comparisons'][0]['equity_value_difference']);self.assertIsNone(r['blended_midpoint']);self.assertEqual({'low':100,'high':120},r['comparable_range'])
        d['methods'][1]['accounting_basis']='US-GAAP';out=method(n).compute(d);self.assertIsNone(out['results']['comparable_range']);self.assertIsNone(out['results']['comparisons'][0]['equity_value_difference']);self.assertEqual('partial',out['status'])
    def test_reviewer_recomputes_formula_graph_and_funding(self):
        n='research-financial-model-reviewer';d=fixture(n);r=method(n).compute(d)['results'];self.assertEqual(1,r['findings_count']);self.assertFalse(r['economic_results'][0]['within_supplied_bounds'])
        d['cells'][2]['value']=99;r=method(n).compute(d)['results'];self.assertEqual(40,r['formula_results'][0]['recomputed_value']);self.assertEqual(59,r['formula_results'][0]['residual']);self.assertTrue(r['reconciliations'][0]['within_tolerance'])
        d['cells'][2]['formula']='__import__("os").system("false")'
        with self.assertRaises(ValueError):method(n).compute(d)
    def test_reviewer_cycles_unknown_names_bounds_and_boolean_rejected(self):
        n='research-financial-model-reviewer';d=fixture(n)
        for formula in ('profit+1','unknown+1','1e999','revenue**999999','True'):
            altered=copy.deepcopy(d);altered['cells'][2]['formula']=formula
            with self.subTest(formula=formula),self.assertRaises(ValueError):method(n).compute(altered)
        d['assumptions'][0]['value']=1;r=method(n).compute(d)['results'];self.assertFalse(r['assumption_results'][0]['within_supplied_bounds'])
    def test_exact_legacy_parity_rounding_null_structure_and_ids(self):
        n='research-financial-model-reviewer';legacy=json.loads((legacy_base()/'evals/files/model_example.json').read_text())
        cases=[legacy,dict(legacy,roll_forward=[{'line_item':'cash','prior_ending':None,'current_opening':10,'tolerance':0},{'line_item':'debt','prior_ending':10,'current_opening':None,'tolerance':.01}]),dict(legacy,roll_forward=[{'line_item':'rounding','prior_ending':0,'current_opening':.00000049,'tolerance':0},{'line_item':'boundary','prior_ending':10,'current_opening':10.000001,'tolerance':.000001}])]
        old=load('model-roll-forward-auditor','calculate_or_transform.py');new=method(n)
        for original in cases:
            out=new.compute({'mode':'legacy-roll-forward','input':original});self.assertEqual(old.compute(original),out['legacy_result']);self.assertFalse(out['authority_granted']);self.assertNotIn('source_input',out)
    def test_integrated_forecast_ufcf_matches_independent_schedules(self):
        n='three-statement-model-builder';d=fixture(n);out=method(n).compute(d)['results'];r=out['forecast_rows'][0];m=out['native_model'];h=d['model_input']['historical']['balance_sheet'];b=m['balance_sheet'][0]
        wc=lambda row:row['accounts_receivable']+row['inventory']+row['other_current_assets']-row['accounts_payable']-row['other_current_liabilities']
        self.assertAlmostEqual(wc(b)-wc(h),r['delta_nwc']);self.assertAlmostEqual(r['ebit']*(1-r['tax_rate'])+r['depreciation']-r['capex']-r['delta_nwc'],r['ufcf'])
        d['model_input']['company_id']='OTHER'
        with self.assertRaises(ValueError):method(n).compute(d)
    def test_dcf_discount_timing_and_no_constant_margin_proxy(self):
        n='dcf-modeler';d=fixture(n);r=method(n).compute(d)['results'];pv=sum(x['ufcf']/(1+d['wacc'])**(t-.5) for t,x in enumerate(d['forecast_rows'],1));terminal=d['forecast_rows'][-1]['ufcf']*1.02/.08
        self.assertAlmostEqual(pv+terminal/1.1**len(d['forecast_rows']),r['enterprise_value']);self.assertEqual(d['forecast_rows'][0]['ebit'],r['forecast_rows'][0]['ebit'])
        d['forecast_rows'][0]['ufcf']+=1
        with self.assertRaises(ValueError):method(n).compute(d)
    def test_financial_sector_comps_equity_only_with_metric_basis(self):
        n='comps-analysis-builder';d=fixture(n);r=method(n).compute(d)['results'];self.assertEqual(1.75,r['median_multiple']);self.assertEqual(35,r['implied_value_per_share']);self.assertIsNone(r['enterprise_value'])
        d['peers'][0]['denominator_per_share']=0;out=method(n).compute(d);self.assertIsNone(out['results']['median_multiple'])
        d=fixture(n);d['multiple']='EV/EBITDA'
        with self.assertRaises(ValueError):method(n).compute(d)
    def test_actual_model_reruns_and_invalid_gordon_guard(self):
        n='scenario-sensitivity-generator';d=fixture(n);r=method(n).compute(d)['results'];dcf=method('dcf-modeler');x=copy.deepcopy(d['base_input']);x['wacc']=.12;expected=dcf.compute(x)['results'];self.assertAlmostEqual(expected['equity_value'],r['scenarios'][0]['equity_value']);self.assertLess(r['scenarios'][0]['equity_value'],r['base_result']['equity_value'])
        d['scenarios'][0]['overrides']={'terminal_growth':.2}
        with self.assertRaises(ValueError):method(n).compute(d)
    def test_segment_ebit_decomposition_and_reconciliation(self):
        n='kpi-segment-bridge-builder';d=fixture(n);r=method(n).compute(d)['results'];s=r['segments'][0];self.assertAlmostEqual(4,s['revenue_effect']);self.assertAlmostEqual(6,s['margin_effect']);self.assertTrue(r['all_reconciled'])
        d['reported_totals']['current_ebit']=31;out=method(n).compute(d);self.assertFalse(out['results']['all_reconciled']);self.assertEqual('partial',out['status'])
        d=fixture(n);d['mappings'][0]['effective_from']='2025-01-01'
        with self.assertRaises(ValueError):method(n).compute(d)
    def test_restricted_future_and_unlicensed_evidence_withheld(self):
        for n in NEW+EXISTING:
            for field,value in [('classification','restricted'),('known_at','2026-10-21T00:00:00Z'),('permission_status','denied')]:
                d=fixture(n);d['sources'][0][field]=value
                if n=='scenario-sensitivity-generator':d['base_input']['sources']=copy.deepcopy(d['sources'])
                out=method(n).compute(d)
                with self.subTest(skill=n,field=field):self.assertIsNone(out['results']);self.assertFalse(out['authority_granted'])
    def test_indexed_timing_rejects_distant_first_year_and_spot_blend(self):
        for n,key in [('dividend-residual-income-modeler','forecasts'),('dcf-modeler','forecast_rows')]:
            d=fixture(n)
            for i,row in enumerate(d[key]):
                row['year']=2030+i
                if key=='forecast_rows':row['period_start']=str(2030+i)+'-01-01';row['period_end']=str(2030+i)+'-12-31'
            with self.subTest(skill=n),self.assertRaises(ValueError):method(n).compute(d)
        n='valuation-reconciliation-analyzer';d=fixture(n);d['methods'][0].update(valuation_timing='annual-period-index',discount_origin='immediately-before-forecast-period-1',first_forecast_year=2027)
        out=method(n).compute(d);self.assertEqual('partial',out['status']);self.assertIsNone(out['results']['comparable_range']);self.assertIsNone(out['results']['comparisons'][0]['equity_value_difference'])
    def test_valuation_security_share_class_and_currency_cannot_drift(self):
        n='valuation-reconciliation-analyzer';d=fixture(n);d['methods'][1]['valuation_subject']=dict(d['valuation_subject'],share_class='preferred-B')
        with self.assertRaises(ValueError):method(n).compute(d)
        n='sum-of-the-parts-valuation-builder';d=fixture(n);d['segments'][0]['currency']='EUR'
        with self.assertRaises(ValueError):method(n).compute(d)
        n='asset-based-valuation-modeler';d=fixture(n);d['liabilities'][0]['currency']='EUR'
        with self.assertRaises(ValueError):method(n).compute(d)
    def test_bundled_sensitivity_model_is_exact_reviewed_dcf_resource(self):
        b=ROOT/'skills/investment-research';self.assertEqual((b/'dcf-modeler/scripts/phase2_domain.py').read_bytes(),(b/'scenario-sensitivity-generator/scripts/model_dcf.py').read_bytes())
    def test_complete_output_binding_and_mutations(self):
        for n in NEW+EXISTING:
            d=fixture(n);out=method(n).compute(d);validator=load(n,'validate_output.py');response=validator.validate(out,d);errors=response[0] if isinstance(response,tuple) else response;self.assertEqual([],errors,n)
            altered=copy.deepcopy(out);altered['authority_granted']=True;response=validator.validate(altered,d);errors=response[0] if isinstance(response,tuple) else response;self.assertTrue(errors,n)
            response=validator.validate(out);errors=response[0] if isinstance(response,tuple) else response;self.assertTrue(errors,n)
if __name__=='__main__':unittest.main()
