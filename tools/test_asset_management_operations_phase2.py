#!/usr/bin/env python3
"""Independent arithmetic/behavior regressions for eight bounded AM Phase2 packages."""
import copy
from decimal import Decimal as Dec
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "performance": "portfolio-performance-measurer", "private": "private-fund-performance-analyzer",
    "accounting": "fund-accounting-preparer", "servicing": "investment-asset-servicing-reviewer",
    "investor": "fund-investor-operations-reviewer", "provider": "fund-service-provider-oversight-reviewer",
    "index": "index-portfolio-reviewer", "etf": "etf-operations-reviewer",
}


def engine(key):
    scripts = ROOT / "skills/asset-management" / PACKAGES[key] / "scripts"
    for name in ("native_integrity", "foundation_contract", "performance_math", "calculate_or_transform"):
        sys.modules.pop(name, None)
    sys.path.insert(0, str(scripts))
    try:
        spec = importlib.util.spec_from_file_location("calculate_or_transform", scripts / "calculate_or_transform.py")
        module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
        import foundation_contract
        return module.compute, foundation_contract.validate_result
    finally:
        sys.path.pop(0)


def fixture(key, mode):
    return json.loads((ROOT / "skills/asset-management" / PACKAGES[key] / "evals/files" / (mode + "_input.json")).read_text())


class Phase2Operations(unittest.TestCase):
    def run_case(self, key, mode):
        compute, validate = engine(key); doc = fixture(key, mode); result = compute(doc)
        self.assertEqual(validate(result, doc, compute), [])
        self.assertTrue(result["draft"]); self.assertFalse(result["action_taken"])
        self.assertTrue(result["human_review_required"]); self.assertNotIn("source_input", result)
        return doc, result, compute, validate

    def test_twr_independent_linkage(self):
        _, out, _, _ = self.run_case("performance", "twr")
        self.assertEqual(Dec(out["results"]["cumulative_twr"]), Dec(".21"))

    def test_twr_boundary_mismatch_rejected(self):
        compute, _ = engine("performance"); doc = fixture("performance", "twr")
        doc["subperiods"][1]["begin_value_after_flow"] = "129"
        with self.assertRaisesRegex(ValueError, "does not reconcile"): compute(doc)

    def test_dietz_independent_weights(self):
        _, out, _, _ = self.run_case("performance", "modified_dietz")
        self.assertEqual(Dec(out["results"]["weighted_flow"]), Dec(5))
        self.assertEqual(Dec(out["results"]["denominator"]), Dec(105))
        self.assertLess(abs(Dec(out["results"]["modified_dietz_return"]) - Dec(10) / Dec(105)), Dec("1e-24"))

    def test_nonpositive_dietz_denominator_unavailable(self):
        doc = fixture("performance", "modified_dietz"); doc["cash_flows"][0]["amount"] = "-250"
        compute, _ = engine("performance"); out = compute(doc)
        self.assertIsNone(out["results"]["modified_dietz_return"])
        self.assertEqual(out["status"], "needs-review")

    def test_one_year_xirr_independent_rate(self):
        _, out, _, _ = self.run_case("performance", "money_weighted")
        self.assertLess(abs(Dec(out["results"]["irr"]["annual_xirr"]) - Dec(".1")), Dec("1e-23"))

    def test_multiple_xirr_roots_not_guessed(self):
        compute, _ = engine("performance"); doc = fixture("performance", "money_weighted")
        doc["period_start"] = "2024-09-20"
        doc["cash_flows"] = [{"flow_id": str(i), "date": day, "amount": amount, "source_ref": "records"}
                             for i, (day, amount) in enumerate([(doc["period_start"], "-100"), ("2025-09-20", "230"), ("2026-09-20", "-132")])]
        irr = compute(doc)["results"]["irr"]
        self.assertEqual(irr["status"], "unavailable"); self.assertIsNone(irr["annual_xirr"])

    def test_private_multiples_and_irr(self):
        _, out, _, _ = self.run_case("private", "investor_net"); result = out["results"]
        self.assertEqual([Dec(result[k]) for k in ("dpi", "rvpi", "tvpi")], [Dec(".2"), Dec(1), Dec("1.2")])
        self.assertLess(abs(Dec(result["irr"]["annual_xirr"]) - Dec(".2")), Dec("1e-23"))

    def test_private_zero_paid_in_does_not_become_zero_multiple(self):
        compute, _ = engine("private"); doc = fixture("private", "investor_net")
        doc["cash_flows"][0]["amount"] = "0"
        out = compute(doc); self.assertIsNone(out["results"]["tvpi"])
        self.assertEqual(out["results"]["irr"]["status"], "unavailable")

    def test_journal_trial_balance_independent_rollforward(self):
        _, out, _, _ = self.run_case("accounting", "journal_trial_balance")
        balances = {r["account_id"]: Dec(r["closing_debit_balance"]) for r in out["results"]["accounts"]}
        self.assertEqual(balances, {"CASH": Dec(90), "CAPITAL": Dec(-100), "EXPENSE": Dec(10)})
        self.assertEqual(Dec(out["results"]["closing_trial_balance"]), 0)

    def test_unbalanced_journal_and_unbalanced_opening_fail(self):
        compute, _ = engine("accounting")
        for kind in ("journal", "opening"):
            doc = fixture("accounting", "journal_trial_balance")
            if kind == "journal": doc["journals"][0]["lines"][0]["debit"] = "11"
            else: doc["accounts"][0]["opening_debit_balance"] = "101"
            with self.assertRaises(ValueError): compute(doc)

    def test_actual_365_accrual(self):
        _, out, _, _ = self.run_case("accounting", "accrual")
        self.assertEqual(Dec(out["results"]["total_expense_accrual"]), Dec(300))

    def test_nav_classes_and_external_benchmark(self):
        _, out, _, _ = self.run_case("accounting", "nav_workpaper"); result = out["results"]
        self.assertEqual(Dec(result["indicative_fund_nav"]), Dec(1035))
        self.assertEqual([Dec(r["net_assets"]) for r in result["classes"]], [Dec(620), Dec(415)])
        self.assertEqual([Dec(r["indicative_nav_per_share"]) for r in result["classes"]], [Dec(10), Dec(10)])
        self.assertFalse(result["within_supplied_tolerance"]); self.assertFalse(result["authoritative_nav_struck"])

    def test_nav_benchmark_wrong_object_rejected(self):
        compute, _ = engine("accounting"); doc = fixture("accounting", "nav_workpaper")
        doc["system_of_record_benchmark"]["object_id"] = "OTHER-FUND"
        with self.assertRaisesRegex(ValueError, "benchmark object"): compute(doc)

    def test_entitlement_cash_and_split(self):
        _, out, _, _ = self.run_case("servicing", "entitlements"); dividend, split = out["results"]["events"]
        self.assertEqual(Dec(dividend["expected_net_cash"]), Dec(45)); self.assertEqual(Dec(dividend["difference"]), Dec(-1))
        self.assertEqual(dividend["reconciliation_status"], "exception")
        self.assertEqual(Dec(split["post_split_total_units"]), Dec(150)); self.assertEqual(Dec(split["expected_additional_units"]), Dec(50))

    def test_missing_receipt_due_is_not_zero_received(self):
        compute, _ = engine("servicing"); doc = fixture("servicing", "entitlements"); doc["events"][0]["received_amount"] = None
        event = compute(doc)["results"]["events"][0]
        self.assertIsNone(event["received"]); self.assertIsNone(event["difference"]); self.assertEqual(event["reconciliation_status"], "due-unreceived")

    def test_dealing_arithmetic_and_no_late_pricing(self):
        _, out, _, _ = self.run_case("investor", "dealing_review"); sub, red, late = out["results"]["orders"]
        self.assertEqual(Dec(sub["indicative_units"]), Dec("9.9")); self.assertEqual(Dec(red["indicative_net_cash"]), Dec(99))
        self.assertIsNone(late["indicative_units"]); self.assertIsNone(late["indicative_net_cash"])
        self.assertTrue(all(not row["accepted"] for row in out["results"]["orders"]))

    def test_dealing_unknown_aml_and_missing_nav_no_calculation(self):
        compute, _ = engine("investor"); doc = fixture("investor", "dealing_review")
        doc["orders"][0]["aml_evidence_status"] = "unknown"; doc["orders"][1]["nav_per_unit"] = None
        rows = compute(doc)["results"]["orders"]
        self.assertIsNone(rows[0]["indicative_units"]); self.assertIsNone(rows[1]["indicative_net_cash"])

    def test_timezone_aware_cutoff_equivalence(self):
        compute, _ = engine("investor"); doc = fixture("investor", "dealing_review")
        doc["orders"][0]["received_at"] = "2026-09-18T11:00:00-04:00"
        self.assertTrue(compute(doc)["results"]["orders"][0]["on_time"])
        doc["orders"][0]["received_at"] = "2026-09-18T11:00:00"
        with self.assertRaises(ValueError): compute(doc)

    def test_provider_sla_and_age(self):
        _, out, _, _ = self.run_case("provider", "service_oversight"); result = out["results"]
        self.assertEqual(Dec(result["services"][0]["observed_failure_rate"]), Dec(".02"))
        self.assertEqual(result["services"][0]["sla_status"], "exception")
        self.assertEqual(result["services"][0]["assurance_status"], "expired")
        self.assertIsNone(result["services"][1]["observed_failure_rate"])
        self.assertEqual(result["open_issues"][0]["days_overdue"], 5)

    def test_tracking_sample_std_and_compounded_difference(self):
        _, out, _, _ = self.run_case("index", "tracking"); result = out["results"]
        self.assertEqual(Dec(result["cumulative_tracking_difference"]), Dec("-.000101"))
        self.assertLess(abs(Dec(result["sample_annualized_tracking_error"]) - Dec(".158745078663875435430092")), Dec("1e-21"))

    def test_single_tracking_observation_unavailable(self):
        compute, _ = engine("index"); doc = fixture("index", "tracking"); doc["periods"] = doc["periods"][:1]
        self.assertIsNone(compute(doc)["results"]["sample_annualized_tracking_error"])

    def test_weight_union_and_half_l1(self):
        doc, out, compute, _ = self.run_case("index", "weights")
        self.assertEqual(Dec(out["results"]["half_l1_weight_distance"]), Dec(".1"))
        doc["weights"].pop()
        with self.assertRaises(ValueError): compute(doc)

    def test_etf_basket_and_cash_fee(self):
        _, out, _, _ = self.run_case("etf", "basket_control"); result = out["results"]
        self.assertEqual(Dec(result["total_etf_shares"]), Dec(200)); self.assertEqual(Dec(result["basket_securities_per_creation_unit"]), Dec(900))
        self.assertEqual(Dec(result["value_difference_per_creation_unit"]), Dec(0)); self.assertEqual(Dec(result["indicative_ap_cash"]), Dec(205))
        self.assertFalse(result["accepted"]); self.assertFalse(result["settlement_performed"])

    def test_etf_redemption_fee_direction_and_missing_price(self):
        compute, _ = engine("etf"); doc = fixture("etf", "basket_control"); doc["direction"] = "redemption"
        self.assertEqual(Dec(compute(doc)["results"]["indicative_ap_cash"]), Dec(195))
        doc["components"][0]["price"] = None
        result = compute(doc)["results"]
        self.assertIsNone(result["basket_securities_per_creation_unit"]); self.assertIsNone(result["within_supplied_tolerance"])

    def test_etf_secondary_market_ratios(self):
        _, out, _, _ = self.run_case("etf", "secondary_market")
        self.assertEqual(Dec(out["results"]["premium_discount"]), Dec(".01"))
        self.assertLess(abs(Dec(out["results"]["quoted_spread_to_midpoint"]) - Dec(".4") / Dec("20.2")), Dec("1e-12"))

    def test_common_source_temporal_audience_and_tampering(self):
        modes = {"performance": "twr", "private": "investor_net", "accounting": "nav_workpaper", "servicing": "entitlements", "investor": "dealing_review", "provider": "service_oversight", "index": "tracking", "etf": "basket_control"}
        for key, mode in modes.items():
            with self.subTest(key=key):
                doc, out, compute, validate = self.run_case(key, mode)
                for mutation in ("known-future", "withheld", "unregistered", "numeric-bound", "source-before-observation"):
                    invalid = copy.deepcopy(doc)
                    if mutation == "known-future": invalid["sources"][0]["known_at"] = "2026-09-21"
                    elif mutation == "withheld": invalid["sources"][0]["permitted_audiences"] = ["different-audience"]
                    elif mutation == "unregistered": invalid["sources"][0]["source_ref"] = "DIFFERENT"
                    elif mutation == "source-before-observation": invalid["sources"][0]["known_at"] = "2026-09-19"
                    else: invalid["as_of"] = "2026-02-30"
                    with self.assertRaises(ValueError): compute(invalid)
                for field, value in (("action_taken", True), ("narrative", "Approved for execution"), ("source_input", doc)):
                    altered = copy.deepcopy(out); altered[field] = value
                    self.assertTrue(validate(altered, doc, compute))
                self.assertTrue(validate(out, None, compute))
                changed = copy.deepcopy(doc); changed["unresolved_issues"] = ["OPEN-SOURCE-GAP"]
                changed_out = compute(changed)
                self.assertNotEqual(changed_out["input_hash"], out["input_hash"])
                self.assertIn("OPEN-SOURCE-GAP", changed_out["unresolved_issues"])

    def test_actual_observations_cannot_postdate_knowledge_or_own_source(self):
        modes = {"performance": ["twr", "modified_dietz", "money_weighted"],
                 "private": ["investor_net"], "accounting": ["journal_trial_balance", "accrual", "nav_workpaper"],
                 "servicing": ["entitlements"], "investor": ["dealing_review"], "provider": ["service_oversight"],
                 "index": ["tracking", "weights"], "etf": ["basket_control", "secondary_market"]}
        for key, variants in modes.items():
            for mode in variants:
                for boundary in ("knowledge-cutoff", "source-known-at"):
                    if key == "accounting" and mode == "accrual" and boundary == "source-known-at":
                        continue  # A computed accrual can use previously known fixed terms.
                    with self.subTest(package=key, mode=mode, boundary=boundary):
                        doc = fixture(key, mode)
                        for source in doc["sources"]:
                            source["as_of"] = source["known_at"] = "2000-01-01"
                        if boundary == "knowledge-cutoff": doc["knowledge_cutoff"] = "2000-01-01"
                        compute, _ = engine(key)
                        with self.assertRaisesRegex(ValueError, "actual.*date|actual.*observation|known_at|knowledge"):
                            compute(doc)

    def test_future_contractual_dates_remain_valid(self):
        doc = fixture("servicing", "entitlements")
        for event in doc["events"]:
            event["payable_date"] = "2026-12-31"
            event["received_amount"] = None
        compute, _ = engine("servicing")
        self.assertTrue(all(row["reconciliation_status"] == "not-yet-due" for row in compute(doc)["results"]["events"]))
        doc = fixture("provider", "service_oversight")
        doc["issues"][0]["due_date"] = "2026-12-31"
        compute, _ = engine("provider")
        self.assertEqual(compute(doc)["results"]["open_issues"][0]["days_overdue"], 0)

    def test_accrual_can_use_terms_known_before_calculation_end(self):
        doc = fixture("accounting", "accrual")
        doc["accruals"] = [{"accrual_id": "PRIOR-KNOWN-TERMS", "principal": "365000", "annual_rate": "0.1",
                            "start": "2026-09-01", "end": "2026-09-20", "day_count": "ACT/365", "source_ref": "records"}]
        for source in doc["sources"]:
            source["as_of"] = source["known_at"] = "2026-09-01"
        compute, _ = engine("accounting")
        self.assertEqual(Dec(compute(doc)["results"]["total_expense_accrual"]), Dec("1900"))


if __name__ == "__main__": unittest.main(verbosity=2)
