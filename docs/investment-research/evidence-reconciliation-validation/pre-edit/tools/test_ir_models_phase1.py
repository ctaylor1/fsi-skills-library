#!/usr/bin/env python3
"""Independent arithmetic, source-bound mutation and failure-path regressions for IR Phase 1.

Uses synthetic supplied evidence only. Passing does not authenticate sources, establish
professional acceptance or provide independent institutional model assurance.
"""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "three-statement-model-builder": ("investment-research", "model_input_example.json", "build"),
    "dcf-modeler": ("investment-research", "dcf_input_example.json", "compute"),
    "comps-analysis-builder": ("investment-research", "comps_intake_example.json", "build"),
    "scenario-sensitivity-generator": ("investment-research", "model_example.json", "compute"),
    "kpi-segment-bridge-builder": ("investment-research", "kpi_bridge_input.json", "compute"),
    "model-roll-forward-auditor": ("investment-research", "model_example.json", "compute"),
    "financials-normalizer": ("finance-operations", "financials_example.json", "compute"),
}


def package(name):
    domain, fixture, function = PACKAGES[name]
    base = ROOT / "skills" / domain / name
    prefix=''
    if not base.is_dir():
        from resolve_skill import resolve
        selected=resolve(name);base=ROOT/selected['path'];prefix=(selected.get('mode') or '')+'_'
    def load(filename):
        spec = importlib.util.spec_from_file_location(name.replace("-", "_") + filename, base / "scripts" / (prefix+filename))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return base, json.loads((base / "evals" / "files" / fixture).read_text()), load("validate_input.py"), getattr(load("calculate_or_transform.py"), function), load("validate_output.py")


class ModelsPhase1(unittest.TestCase):
    def test_source_binding_and_complete_mutation_detection(self):
        for name in PACKAGES:
            with self.subTest(package=name):
                _, original, vi, calculate, vo = package(name)
                self.assertEqual([], vi.validate(original)[0])
                result = calculate(original)
                self.assertEqual([], vo.validate(result, original))
                self.assertTrue(vo.validate(result), "original input must be required")
                self.assertEqual("unverified", result["source_truth"])
                self.assertNotIn("source_input", result)
                changed = copy.deepcopy(result)
                changed.pop(next(k for k in changed if k not in ("input_hash", "source_truth")))
                self.assertTrue(vo.validate(changed, original), "omitted output accepted")
                changed = copy.deepcopy(result)
                changed["unreviewed_extra_claim"] = "approved"
                self.assertTrue(vo.validate(changed, original), "extra output accepted")
                changed = copy.deepcopy(result)
                changed["source_truth"] = "authenticated"
                self.assertTrue(vo.validate(changed, original), "source authentication claim accepted")
                other = copy.deepcopy(original)
                other["config_version"] = "different-context" if "config_version" in other else "added-context"
                self.assertTrue(vo.validate(result, other), "different original/context accepted")

    def test_bad_shapes_nonfinite_and_duplicate_json_are_rejected(self):
        for name in PACKAGES:
            with self.subTest(package=name):
                base, original, vi, calculate, _ = package(name)
                for malformed in (None, [], [original], "object", {**original, "config_version": float("nan")}):
                    self.assertTrue(vi.validate(malformed)[0])
                    with self.assertRaises(ValueError):
                        calculate(malformed)
                for script in ("validate_input.py", "calculate_or_transform.py"):
                    for text in ('[1,2]', '{"a":1,"a":2}'):
                        failed = subprocess.run([sys.executable, "-B", str(base / "scripts" / script)], input=text, text=True, capture_output=True)
                        self.assertEqual(1, failed.returncode, failed.stdout + failed.stderr)
                        self.assertIn("ERROR", failed.stdout + failed.stderr)
                        self.assertNotIn("Traceback", failed.stdout + failed.stderr)
                with self.assertRaises(ValueError):
                    vi._strict_json('{"a":1,"a":2}')
                with self.assertRaises(ValueError):
                    vi._strict_json('{"a":NaN}')
                for script in ("validate_input.py", "calculate_or_transform.py", "validate_output.py"):
                    done = subprocess.run([sys.executable, "-B", str(base / "scripts" / script), "--selftest"], text=True, capture_output=True)
                    self.assertEqual(0, done.returncode, done.stdout + done.stderr)
                    self.assertNotIn("Traceback", done.stdout + done.stderr)

    def test_pe_is_equity_price_not_enterprise_value(self):
        _, d, _, calculate, vo = package("comps-analysis-builder")
        peer = copy.deepcopy(d["peers"][0])
        peer.update(ticker="ONLY", share_price=52, diluted_shares=100)
        peer["ltm"]["eps"] = 4
        d["peers"] = [peer]
        d["config"]["implied_multiples"] = ["P/E LTM"]
        result = calculate(d)
        row = next(r for r in result["sections"]["implied_valuation"] if r.get("basis") == "median")
        self.assertEqual(13, row["basis_multiple"])
        self.assertEqual(65, row["implied_share_price_cross_check"])
        self.assertEqual(6500, row["implied_equity_value"])
        self.assertIsNone(row["implied_enterprise_value"])
        self.assertEqual([], vo.validate(result, d))
        for key in ("total_debt", "cash_and_equivalents", "preferred_equity", "minority_interest"):
            missing = copy.deepcopy(d)
            missing["subject"].pop(key)
            with self.assertRaises(ValueError):
                calculate(missing)

    def test_dcf_independent_one_year_case_and_bridge(self):
        _, d, vi, calculate, vo = package("dcf-modeler")
        d.update(base_year_revenue=100, forecast_years=1, shares_outstanding=2)
        d["discounting"] = {"convention":"end_year"}
        for key, value in {"revenue_growth":0,"ebit_margin":.1,"tax_rate":0,"da_pct_revenue":0,"capex_pct_revenue":0,"nwc_pct_of_revenue_change":0}.items():
            d["drivers"][key]["value"] = value
        source = {"provenance":"synthetic-assumption", "citation":"synthetic:one-year-case"}
        d["wacc"] = {"override": {"value":.1, **source}}
        d["terminal"] = {"method":"exit_multiple", "exit_multiple":{"value":1, **source}}
        d["scenario_adjustments"] = {"upside":{}, "downside":{}}
        for key in d["bridge"]:
            d["bridge"][key]["value"] = {"total_debt":2,"cash_and_equivalents":1}.get(key,0)
        result = calculate(d)
        row = result["scenarios"][0]
        self.assertEqual(10, row["years"][0]["ufcf"])
        self.assertAlmostEqual(18.1818, row["enterprise_value"], places=4)
        self.assertAlmostEqual(17.1818, row["equity_value"], places=4)
        self.assertAlmostEqual(8.5909, row["value_per_share"], places=4)
        self.assertEqual("standalone-ratio-fcff", result["forecast_mode"])
        self.assertFalse(result["upstream_forecast_consumed"])
        self.assertEqual([], vo.validate(result,d))
        missing = copy.deepcopy(d); missing.pop("bridge")
        self.assertTrue(vi.validate(missing)[0])
        altered = copy.deepcopy(result); altered["wacc"] = .7
        self.assertTrue(vo.validate(altered,d))
        upstream = copy.deepcopy(d); upstream["upstream_model_id"] = "3sm-model"
        self.assertTrue(vi.validate(upstream)[0])

    def test_three_statement_independent_case_and_negative_cash_is_not_feasibility(self):
        _, d, vi, calculate, vo = package("three-statement-model-builder")
        d["forecast_years"] = 1
        d["historical"]["income_statement"] = dict(revenue=100,cogs=60,opex=20,depreciation=7,interest_expense=2,tax=2.75,net_income=8.25)
        d["historical"]["balance_sheet"] = dict(cash=10,accounts_receivable=10,inventory=10,other_current_assets=0,ppe_net=70,other_assets=0,accounts_payable=10,other_current_liabilities=0,debt=20,other_liabilities=0,equity=70)
        values = dict(revenue_growth=0,gross_margin=.4,opex_pct_revenue=.2,depreciation_rate=.1,capex_pct_revenue=.1,dso=36.5,dio=365/6,dpo=365/6,other_current_assets_pct_revenue=0,other_current_liabilities_pct_revenue=0,tax_rate=.25,interest_rate=.1,debt_repayment=2,dividend_payout_ratio=0)
        d["drivers"] = {key:{"value":value,"source":"synthetic:one-year-case"} for key,value in values.items()}
        d["scenarios"] = {name:{"revenue_growth_delta":0,"gross_margin_delta":0} for name in ("base","upside","downside")}
        result = calculate(d)
        self.assertAlmostEqual(8.25,result["income_statement"][0]["net_income"])
        self.assertAlmostEqual(13.25,result["balance_sheet"][0]["cash"])
        self.assertAlmostEqual(73,result["balance_sheet"][0]["ppe_net"])
        self.assertEqual([],vo.validate(result,d))
        d["drivers"]["capex_pct_revenue"]["value"] = 1.2
        stressed = calculate(d)
        self.assertTrue(stressed["all_balanced"])
        self.assertTrue(stressed["negative_cash_years"])
        self.assertEqual("not-assessed-no-funding-engine",stressed["financing_feasibility"])
        missing = copy.deepcopy(d); missing.pop("scenarios")
        self.assertTrue(vi.validate(missing)[0])
        boolean = copy.deepcopy(d); boolean["forecast_years"] = True
        self.assertTrue(vi.validate(boolean)[0])

    def test_scenario_arithmetic_and_omission(self):
        _, _, vi, calculate, vo = package("scenario-sensitivity-generator")
        d = dict(model_id="linear",as_of="2026-10-20",config_version="v1",drivers=[dict(name="x",base=3,source_ref="synthetic:x")],outputs=[dict(name="y",formula="2*x+1")],scenarios=[dict(name="higher",overrides=dict(x=4))],sensitivities=[dict(driver="x",output="y",points=[0,2])])
        result = calculate(d)
        self.assertEqual(7,result["base_case"]["y"])
        self.assertEqual(9,result["scenarios"][0]["outputs"]["y"])
        self.assertEqual("supplied-formula-graph-only",result["integration_status"])
        self.assertEqual([],vo.validate(result,d))
        altered = copy.deepcopy(result); altered["scenarios"]=[]
        self.assertTrue(vo.validate(altered,d))
        for value in (True,float("inf"),"3"):
            bad = copy.deepcopy(d); bad["drivers"][0]["base"]=value
            self.assertTrue(vi.validate(bad)[0])
        for formula in ("True+1", "1<<2", "abs(2,3)", "max(2)"):
            bad=copy.deepcopy(d); bad["outputs"][0]["formula"]=formula
            self.assertTrue(vi.validate(bad)[0])

    def test_nonmonotonic_roots_are_unknown_without_a_sign_change_bracket(self):
        _,_,vi,calculate,vo=package("scenario-sensitivity-generator")
        d=dict(model_id="nonmonotonic",as_of="2026-10-20",config_version="v1",drivers=[dict(name="units",base=200,source_ref="synthetic:units")],outputs=[dict(name="profit",formula="(units-100)*(300-units)")],breakevens=[dict(driver="units",output="profit",target=0,lo=0,hi=400)],decision_thresholds=[dict(driver="units",output="profit",target=0,lo=0,hi=400)])
        result=calculate(d)
        # Algebra gives roots100 and300 even though both endpoints have value-30000.
        self.assertEqual(-30000, (0-100)*(300-0))
        self.assertEqual(-30000, (400-100)*(300-400))
        for row in result["breakevens"]+result["decision_thresholds"]:
            self.assertFalse(row["converged"])
            self.assertEqual("not-bracketed",row["search_status"])
            self.assertIn("unknown",row["note"])
            self.assertNotIn("no crossing",row["note"].lower())
        self.assertIsNone(result["breakevens"][0]["solution"])
        self.assertIsNone(result["decision_thresholds"][0]["threshold_value"])
        self.assertEqual([],vo.validate(result,d))
        d["breakevens"][0]["hi"]=200
        d["decision_thresholds"][0]["lo"]=200
        bracketed=calculate(d)
        self.assertAlmostEqual(100,bracketed["breakevens"][0]["solution"])
        self.assertAlmostEqual(300,bracketed["decision_thresholds"][0]["threshold_value"])
        d["two_way"]=[dict(row_driver="units",col_driver="units",output="profit",row_points=[100,200],col_points=[200,300])]
        self.assertTrue(any("must be distinct" in e for e in vi.validate(d)[0]))
        with self.assertRaises(ValueError):
            calculate(d)

    def test_kpi_effective_mapping_totals_and_context(self):
        _,d,vi,calculate,vo=package("kpi-segment-bridge-builder")
        result=calculate(d)
        self.assertFalse(result["model_checks"]["all_reconciled"],"unrequested totals are not reconciled")
        self.assertEqual([],vo.validate(result,d))
        future=copy.deepcopy(d); future["approved_mappings"][0]["effective_date"]="2099-01-01"
        self.assertTrue(vi.validate(future)[0])
        missing=copy.deepcopy(d); missing.pop("reported_totals")
        self.assertTrue(vi.validate(missing)[0])
        changed=copy.deepcopy(d);changed["reported_totals"]["prior_revenue"]["citation"]+=";different-source"
        self.assertNotEqual(result["inputs_hash"],calculate(changed)["inputs_hash"])
        duplicate=copy.deepcopy(d);duplicate["bridges"][0]["components"].append(copy.deepcopy(duplicate["bridges"][0]["components"][0]))
        self.assertTrue(vi.validate(duplicate)[0])

    def test_continuity_break_status_and_tolerance(self):
        _,d,vi,calculate,vo=package("model-roll-forward-auditor")
        result=calculate(d)
        self.assertEqual(-20,result["line_items"][2]["residual"])
        self.assertEqual(1,result["break_count"])
        self.assertEqual("breaks-for-review",result["suggested_disposition"])
        altered=copy.deepcopy(result);altered["breaks"]=[];altered["suggested_disposition"]="tied"
        self.assertTrue(vo.validate(altered,d))
        bad=copy.deepcopy(d);bad["roll_forward"][0]["tolerance"]=-1
        self.assertTrue(vi.validate(bad)[0])

    def test_normalized_balance_identity_is_reconstructed_per_period(self):
        _,_,vi,calculate,vo=package("financials-normalizer")
        d=dict(entity_id="synthetic",as_of="2026-10-20",config_version="v1",reporting_framework="supplied",currency="USD",mapping=[],line_items=[],adjustments=[])
        for account in ("cash","debt","equity"):
            d["mapping"].append(dict(source_label=account,std_account=account,statement="balance_sheet"))
        for period,values in (("2024",(100,40,60)),("2025",(120,50,70))):
            for account,value,role in zip(("cash","debt","equity"),values,("total_assets","total_liabilities","total_equity")):
                lid=period+account
                d["line_items"].append(dict(line_id=lid,raw_label=account,statement="balance_sheet",period=period,value=value,source_ref="synthetic:"+lid))
                d["line_items"].append(dict(line_id=lid+"total",raw_label=role,statement="balance_sheet",period=period,value=value,source_ref="synthetic:"+lid,is_subtotal=True,role=role,components=[lid]))
        d["adjustments"]=[dict(adj_id="cash-adjust",std_account="cash",statement="balance_sheet",type="reclass",period="2025",amount=10,rationale="synthetic unbalanced adjustment",source_ref="synthetic:adjustment",approver="supplied-reviewer")]
        self.assertEqual([],vi.validate(d)[0])
        result=calculate(d)
        self.assertTrue(all(r["within_tolerance"] for r in result["reported_balance_sheet_checks"]))
        self.assertEqual([0,10],[r["diff"] for r in result["normalized_balance_sheet_checks"]])
        self.assertEqual("Hold - tie-out break",result["suggested_readiness"])
        account=next(r for r in result["normalized_accounts"] if r["std_account"]=="cash" and r["period"]=="2025")
        self.assertEqual(130,account["normalized_value"])
        self.assertEqual("balance_sheet",account["adjustments"][0]["statement"])
        self.assertEqual([],vo.validate(result,d))
        bad=copy.deepcopy(d);bad["mapping"].append(copy.deepcopy(bad["mapping"][0]))
        self.assertTrue(vi.validate(bad)[0])
        bad=copy.deepcopy(d);bad["adjustments"][0].pop("statement")
        self.assertTrue(vi.validate(bad)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
