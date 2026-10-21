#!/usr/bin/env python3
"""Behavioral regressions for bounded investment analytics; no external systems."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import runpy
import unittest

from asset_management_test_support import package, script as script_path
FIXTURES = {
    "counterparty-exposure-monitor": ("exposures_example.json", "pack_example.json"),
    "hedge-analysis-support-packet": ("hedge_input_example.json", "hedge_packet_example.json"),
    "liquidity-stress-analyzer": ("portfolio_example.json", "analysis_example.json"),
    "mandate-compliance-monitor": ("run_example.json", "pack_example.json"),
    "performance-attribution-builder": ("attribution_intake_example.json", "attribution_example.json"),
    "portfolio-cashflow-liquidity-forecaster": ("forecast_input_example.json", "forecast_pack_example.json"),
    "portfolio-drift-monitor": ("drift_input_example.json", "packet_example.json"),
    "portfolio-exposure-analyzer": ("portfolio_example.json", "pack_example.json"),
    "portfolio-risk-contribution-packet": ("risk_input_example.json", "risk_pack_example.json"),
    "portfolio-stress-test-runner": ("stress_input_example.json", "stress_pack_example.json"),
}


def module(name, script):
    return runpy.run_path(str(script_path(name, f"{script}.py")))


def source(name):
    return json.loads((package(name) / "evals/files" / FIXTURES[name][0]).read_text())


def compute(name, doc):
    return module(name, "calculate_or_transform")["compute"](doc)


class InvestmentPhase1(unittest.TestCase):
    def test_all_golden_results_require_original_and_reject_tampering(self):
        for name in FIXTURES:
            with self.subTest(name=name):
                doc = source(name)
                out = compute(name, doc)
                validate = module(name, "validate_output")["validate"]
                self.assertEqual([], validate(out, doc))
                self.assertTrue(validate(out))
                changed = copy.deepcopy(out)
                changed["unreviewed_narrative"] = "An unsupported source claim"
                self.assertTrue(validate(changed, doc))
                changed = copy.deepcopy(doc)
                changed["config_version"] = "different-config"
                self.assertTrue(validate(out, changed))
                self.assertEqual(out, json.loads((package(name) / "evals/files" / FIXTURES[name][1]).read_text()))

    def test_nonfinite_and_impossible_dates_fail(self):
        for name in FIXTURES:
            with self.subTest(name=name):
                doc = source(name)
                doc["invalid_number"] = float("nan")
                self.assertTrue(module(name, "validate_input")["validate"](doc)[0])
                doc = source(name)
                doc["as_of"] = "2026-02-30"
                self.assertTrue(module(name, "validate_input")["validate"](doc)[0])

    def mandate(self):
        name = "mandate-compliance-monitor"
        doc = source(name)
        doc["portfolios"] = [{"portfolio_id": "P", "mandate_id": "M", "nav": 100,
                              "holdings_as_of": doc["as_of"], "prices_as_of": doc["as_of"],
                              "holdings_source_ref": "test:holdings", "holdings": [
                                  {"security_id": "EQ", "issuer": "I", "sector": "Tech",
                                   "asset_class": "equity", "market_value": 100}]}]
        doc["rules"] = [{"rule_id": "CASH", "type": "guideline", "scope": "asset_class",
                         "target_bucket": "cash", "min_pct": 5, "source_ref": "test:rule",
                         "applies_to": {"mandate_ids": ["M"]}}]
        return name, doc

    def test_absent_minimum_and_applicability(self):
        name, doc = self.mandate()
        out = compute(name, doc)
        self.assertEqual([(0, "cash", "BREACH")], [(a["measured_pct"], a["bucket"], a["status"]) for a in out["alerts"]])
        doc["rules"][0]["applies_to"] = {"mandate_ids": ["OTHER"]}
        out = compute(name, doc)
        self.assertEqual([], out["alerts"])
        self.assertEqual("not_applicable", out["rule_results"][0]["status"])

    def test_target_limit_does_not_apply_to_other_bucket(self):
        name, doc = self.mandate()
        doc["rules"][0].pop("min_pct")
        doc["rules"][0]["max_pct"] = 5
        self.assertEqual([], compute(name, doc)["alerts"])

    def test_pretrade_minimum_and_existing_breach_worsening(self):
        name, doc = self.mandate()
        pf = doc["portfolios"][0]
        pf["holdings"] = [{"security_id": "CASH", "issuer": "C", "sector": "Cash", "asset_class": "cash", "market_value": 10}]
        pf["proposed_trades"] = [{"trade_id": "T", "security_id": "CASH", "issuer": "C", "sector": "Cash", "asset_class": "cash", "side": "sell", "market_value": 8, "as_of": doc["as_of"], "source_ref": "test:trade"}]
        alerts = compute(name, doc)["alerts"]
        self.assertEqual([("pre_trade", 2)], [(a["breach_type"], a["measured_pct"]) for a in alerts])
        pf["holdings"][0]["market_value"] = 4
        pf["proposed_trades"][0]["market_value"] = 1
        self.assertEqual({"position", "pre_trade"}, {a["breach_type"] for a in compute(name, doc)["alerts"]})

    def test_unsupported_rule_is_unavailable_not_pass(self):
        name, doc = self.mandate()
        doc["rules"][0]["scope"] = "tracking_error"
        result = compute(name, doc)
        self.assertEqual("not_evaluable", result["rule_results"][0]["status"])
        self.assertEqual([], result["alerts"])

    def test_exposure_complete_country_and_exempt_assets(self):
        name = "portfolio-exposure-analyzer"
        out = compute(name, source(name))
        self.assertEqual(100, sum(b["pct"] for b in out["exposures"]["country"]))
        self.assertIn("US Treasury", [b["bucket"] for b in out["exposures"]["issuer"]])
        self.assertFalse(any(f["bucket"] == "US Treasury" for f in out["findings"]))

    def test_partial_lookthrough_preserves_residual_and_wrapper(self):
        name = "portfolio-exposure-analyzer"
        doc = source(name)
        p = next(p for p in doc["positions"] if p.get("look_through"))
        p["look_through"] = p["look_through"][:1]
        out = compute(name, doc)
        self.assertEqual(72000, out["dimension_coverage"]["country"]["unknown_market_value"])
        self.assertEqual(210000, next(b["market_value"] for b in out["exposures"]["asset_class"] if b["bucket"] == "fund"))

    def test_authoritative_nav_is_not_inferred_cash(self):
        name = "portfolio-exposure-analyzer"
        doc = source(name)
        doc["nav"] = 1100000
        out = compute(name, doc)
        self.assertEqual(-100000, out["nav_reconciliation"]["difference"])
        self.assertFalse(out["nav_reconciliation"]["reconciled"])
        self.assertIn("nav_reconciliation", [x["dimension"] for x in out["not_evaluable"]])

    def test_covariance_symmetry_and_positive_semidefinite(self):
        name = "portfolio-risk-contribution-packet"
        doc = source(name)
        doc["covariance"]["matrix"][0][1] = .019
        self.assertRaises(ValueError, compute, name, doc)
        doc = source(name)
        doc["positions"] = doc["positions"][:3]
        doc["covariance"]["order"] = doc["covariance"]["order"][:3]
        doc["covariance"]["matrix"] = [[1, -.9, -.9], [-.9, 1, -.9], [-.9, -.9, 1]]
        self.assertRaises(ValueError, compute, name, doc)

    def test_risk_measure_cannot_mislabel_volatility(self):
        name = "portfolio-risk-contribution-packet"
        doc = source(name)
        doc["risk_measure"] = "expected_shortfall"
        self.assertRaises(ValueError, compute, name, doc)

    def test_hedge_cost_and_units_bind_hash(self):
        name = "hedge-analysis-support-packet"
        doc = source(name)
        baseline = compute(name, doc)
        doc["candidate_hedges"][0]["cost"]["value"] = 999
        self.assertNotEqual(baseline["input_hash"], compute(name, doc)["input_hash"])
        self.assertTrue(any("normalization" in w for w in baseline["input_warnings"]))

    def test_liquidity_missing_spread_negative_adv_and_nav_fail(self):
        name = "liquidity-stress-analyzer"
        for mutation in ("spread", "adv", "nav"):
            doc = source(name)
            if mutation == "spread": doc["positions"][0].pop("spread_bps")
            elif mutation == "adv": doc["positions"][0]["adv_value"] = -1
            else: doc["nav"] += 1
            self.assertRaises(ValueError, compute, name, doc)

    def test_counterparty_missing_feed_and_pfe_fail(self):
        name = "counterparty-exposure-monitor"
        doc = source(name)
        doc["feeds"] = []
        self.assertRaises(ValueError, compute, name, doc)

        doc = source(name)
        doc["exposures"][0].pop("pfe_addon")
        self.assertRaises(ValueError, compute, name, doc)

    def test_concentration_inherits_denominator_freshness(self):
        name = "counterparty-exposure-monitor"
        result = compute(name, source(name))
        concentration = [a for a in result["alerts"] if a["alert_type"] == "concentration"]
        self.assertTrue(concentration)
        self.assertTrue(all(a["freshness"] == "stale" for a in concentration))

    def test_unknown_credit_rating_is_not_silent_clearance(self):
        name = "counterparty-exposure-monitor"
        doc = source(name)
        doc["counterparties"][0]["rating"] = "OTHER-SCALE"
        out = compute(name, doc)
        self.assertTrue(any(x["dimension"] == "rating_floor" for x in out["not_evaluable"]))

    def test_daily_cash_deficit_survives_positive_bucket_close(self):
        name = "portfolio-cashflow-liquidity-forecaster"
        doc = source(name)
        doc["opening_cash"]["value"] = 10
        doc["cashflows"] = [dict(doc["cashflows"][0], id="OUT", category="redemption", amount=20, date="2026-07-21"),
                            dict(doc["cashflows"][0], id="IN", category="subscription", amount=30, date="2026-07-22")]
        doc["scenarios"] = {"base": {"provenance": "test", "citation": "test:base"}}
        s = compute(name, doc)["scenarios"][0]
        self.assertEqual(20, s["buckets"][0]["closing_balance"])
        self.assertEqual(-10, s["minimum_daily_balance"])
        self.assertEqual("2026-07-21", s["first_shortfall_date"])

    def test_fractional_date_shift_and_negative_multiplier_fail(self):
        name = "portfolio-cashflow-liquidity-forecaster"
        doc = source(name)
        doc["scenarios"]["base"]["category_date_shift_days"] = {"redemption": .9}
        self.assertRaises(ValueError, compute, name, doc)
        doc = source(name)
        doc["scenarios"]["base"]["category_multipliers"] = {"redemption": -1}
        self.assertRaises(ValueError, compute, name, doc)

    def test_drift_model_mismatch_fails(self):
        name = "portfolio-drift-monitor"
        doc = source(name)
        doc["prior"]["basis"]["model_version"] = "different-model"
        self.assertRaises(ValueError, compute, name, doc)

    def test_stress_missing_approval_evidence_fails(self):
        name = "portfolio-stress-test-runner"
        doc = source(name)
        doc["scenarios"][0].pop("approval_ref")
        self.assertRaises(ValueError, compute, name, doc)

    def test_stress_consistent_altered_numbers_fail_original_reconstruction(self):
        name = "portfolio-stress-test-runner"
        doc = source(name)
        out = compute(name, doc)
        s = out["scenarios"][1]
        s["scenario_pnl"] *= 2
        s["pnl_pct"] *= 2
        s["stressed_value"] = out["portfolio_base_value"] + s["scenario_pnl"]
        for p in s["attribution_by_position"]:
            p["pnl"] *= 2
            p["pnl_pct_of_base"] *= 2
            p["factor_contributions"] = {k: v * 2 for k, v in p["factor_contributions"].items()}
        for f in s["attribution_by_factor"]:
            f["pnl"] *= 2
            f["pnl_pct_of_base"] *= 2
        self.assertTrue(module(name, "validate_output")["validate"](out, doc))

    def test_attribution_rejects_unbalanced_weights(self):
        name = "performance-attribution-builder"
        doc = source(name)
        doc["segments"][0]["weight_port"] += .1
        self.assertRaises(ValueError, compute, name, doc)


if __name__ == "__main__":
    unittest.main()
