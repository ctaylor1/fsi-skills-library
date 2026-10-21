"""Bounded native regressions; professional acceptance is separate."""

import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from domain import evaluate, validate
from workflow_contract import build_artifact
from workflow_foundation import run, check_output

NAME = "health-plan-pricing-reviewer"
FILES = Path(__file__).parents[1] / "evals/files"


class Native(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((FILES / "input.json").read_text())

    def result(self):
        return run(self.doc, NAME, evaluate, validate)

    def gap(self):
        out = self.result()
        self.assertEqual(out["status"], "needs-data", out["findings"])
        self.assertFalse(out["action_taken"])
        return out["results"]

    def test_native_roundtrip(self):
        out = self.result()
        self.assertEqual(out["status"], "ready-for-review", out["findings"])
        self.assertEqual(check_output(out, NAME, evaluate, validate), [])

    def test_source_immutable(self):
        before = copy.deepcopy(self.doc)
        out = self.result()
        self.assertEqual(self.doc, before)
        self.assertEqual(out["source_document"], before)

    def test_unknown_profile(self):
        self.doc["data"]["profile"] = None
        self.gap()

    def test_unsupported_method(self):
        self.doc["data"]["profile"]["method"] = "unsupported"
        self.gap()

    def test_wrong_market(self):
        self.doc["data"]["market"] = "OTHER"
        self.gap()

    def test_wrong_program(self):
        self.doc["data"]["program"] = "OTHER"
        self.gap()

    def test_wrong_product(self):
        self.doc["data"]["product"] = "OTHER"
        self.gap()

    def test_expired_profile(self):
        self.doc["data"]["profile"]["effective_to"] = "2025-12-31"
        self.gap()

    def test_future_source(self):
        self.doc["sources"][0]["as_of"] = "2026-10-05"
        self.gap()

    def test_source_date_unknown(self):
        del self.doc["sources"][0]["as_of"]
        self.gap()

    def test_source_locator_missing(self):
        del self.doc["sources"][0]["locator"]
        self.gap()

    def test_unknown_source(self):
        self.doc["data"]["source_refs"] = ["unregistered"]
        self.gap()

    def test_duplicate_source(self):
        self.doc["sources"].append(copy.deepcopy(self.doc["sources"][0]))
        self.assertRaises(ValueError, self.result)

    def test_inherited_issues(self):
        self.doc["unresolved_issues"] = ["Unresolved population ownership"]
        self.gap()
        self.assertIn("Unresolved population ownership", self.result()["unresolved_issues"])

    def test_unknown_owner(self):
        self.doc["data"]["owner"] = None
        self.gap()

    def test_missing_completeness_statement(self):
        self.doc["data"]["inventory_statement"] = None
        self.gap()

    def test_resealed_result_tampering(self):
        out = self.result()
        out["results"]["invented"] = True
        out["artifact"] = build_artifact(
            out["source_document"],
            out,
            producer=NAME,
            artifact_type="workflow-review",
            completeness=out["completeness"],
            evaluability=out["evaluability"],
            issues=out["unresolved_issues"],
        )
        self.assertTrue(check_output(out, NAME, evaluate, validate))

    def test_no_execution_authority(self):
        out = self.result()
        out["execution"] = "performed"
        self.assertTrue(check_output(out, NAME, evaluate, validate))

    def test_golden_output(self):
        self.assertEqual(self.result(), json.loads((FILES / "output.json").read_text()))

    def test_adverse_output(self):
        self.doc = json.loads((FILES / "adverse-input.json").read_text())
        self.gap()
        self.assertEqual(self.result(), json.loads((FILES / "adverse-output.json").read_text()))

    def metrics(self):
        return self.result()["results"]["metrics"]

    def test_reconciled_math(self):
        m = self.metrics()
        self.assertEqual(Decimal(m["net_incurred"]), 120000)
        self.assertEqual(Decimal(m["adjusted_incurred"]), 119000)
        self.assertEqual(Decimal(m["projected_claim_pmpm"]), Decimal("134.078"))
        self.assertEqual(Decimal(m["nonpremium_expense_pmpm"]), 15)
        self.assertEqual(m["conditional_premium_pmpm"], "175.38588235294117647058823529411764705882352941176")
        self.assertEqual(m["descriptive_incurred_to_earned_premium"], "0.8")

    def test_all_unknown_numeric_dependencies_withhold(self):
        positions = (
            [("exposure", None, k) for k in ("member_months", "earned_premium")]
            + [("projection", None, k) for k in ("member_months", "current_premium_pmpm")]
            + [("expenses", None, k) for k in ("fixed_total", "pmpm", "premium_proportion", "margin_proportion")]
            + [
                ("categories", 0, k)
                for k in ("paid", "case_outstanding", "ibnr", "recoveries", "cost_factor", "utilization_factor")
            ]
            + [("adjustments", 0, "amount")]
        )
        original = copy.deepcopy(self.doc)
        for parent, index, key in positions:
            with self.subTest(parent=parent, key=key):
                self.doc = copy.deepcopy(original)
                row = self.doc["data"][parent]
                row = row[index] if index is not None else row
                row[key] = None
                self.assertTrue(all(v is None for v in self.gap()["metrics"].values()))

    def test_fractional_float_rejected(self):
        self.doc["data"]["categories"][0]["cost_factor"] = 1.1
        self.assertRaises(ValueError, self.result)

    def test_high_precision_fractional_float_rejected(self):
        self.doc["data"]["expenses"]["pmpm"] = 0.10000000000000002
        self.assertRaises(ValueError, self.result)

    def test_boolean_money_rejected(self):
        self.doc["data"]["categories"][0]["paid"] = True
        self.assertRaises(ValueError, self.result)

    def test_zero_base_exposure(self):
        self.doc["data"]["exposure"]["member_months"] = 0
        self.assertIsNone(self.gap()["metrics"]["conditional_premium_pmpm"])

    def test_zero_projected_exposure(self):
        self.doc["data"]["projection"]["member_months"] = 0
        self.gap()

    def test_snapshot_enrollment_rejected(self):
        self.doc["data"]["exposure"]["exposure_unit"] = "members"
        self.gap()

    def test_projected_snapshot_enrollment_rejected(self):
        self.doc["data"]["projection"]["exposure_unit"] = "members"
        self.gap()

    def test_claim_period_mismatch(self):
        self.doc["data"]["categories"][0]["period_end"] = "2025-11-30"
        self.gap()

    def test_currency_mismatch(self):
        self.doc["data"]["categories"][0]["currency"] = "EUR"
        self.gap()

    def test_population_mismatch(self):
        self.doc["data"]["exposure"]["population_basis"] = "subset"
        self.gap()

    def test_missing_category_not_treated_as_zero(self):
        self.doc["data"]["categories"].pop()
        self.gap()

    def test_duplicate_category_rejected(self):
        self.doc["data"]["categories"].append(copy.deepcopy(self.doc["data"]["categories"][0]))
        self.assertRaises(ValueError, self.result)

    def test_duplicate_economic_event(self):
        self.doc["data"]["categories"][1]["economic_event_ids"] = self.doc["data"]["categories"][0][
            "economic_event_ids"
        ]
        self.gap()

    def test_adjustment_event_already_counted(self):
        self.doc["data"]["adjustments"][0]["economic_event_id"] = self.doc["data"]["categories"][0][
            "economic_event_ids"
        ][0]
        self.gap()

    def test_duplicate_adjustment_event(self):
        self.doc["data"]["adjustments"][1]["economic_event_id"] = self.doc["data"]["adjustments"][0][
            "economic_event_id"
        ]
        self.gap()

    def test_already_net_recovery_not_deducted_twice(self):
        self.doc["data"]["categories"][0]["recovery_basis"] = "net-recoveries-already-included"
        self.gap()

    def test_explicit_net_basis(self):
        c = self.doc["data"]["categories"][0]
        c["paid"] = "89000"
        c["recoveries"] = "0"
        c["recovery_basis"] = "net-recoveries-already-included"
        self.assertEqual(self.metrics()["net_incurred"], "120000")

    def test_no_ibnr_double_count(self):
        self.doc["data"]["categories"][0]["case_excludes_ibnr"] = False
        self.gap()

    def test_trend_horizon_mismatch(self):
        self.doc["data"]["categories"][0]["trend_to"] = "2026-07-01"
        self.gap()

    def test_no_annual_trend_inference(self):
        self.doc["data"]["categories"][0]["cost_factor"] = None
        self.gap()

    def test_missing_projection_population_bridge(self):
        self.doc["data"]["projection"]["population_bridge_reviewed"] = None
        self.gap()

    def test_exhaustive_adjustments_required(self):
        self.doc["data"]["adjustments_complete"] = False
        self.gap()

    def test_explicit_empty_adjustments_supported(self):
        self.doc["data"]["adjustments"] = []
        self.assertEqual(Decimal(self.metrics()["projected_claim_pmpm"]), Decimal("133.2"))

    def test_premium_denominator_zero(self):
        self.doc["data"]["expenses"]["margin_proportion"] = ".90"
        self.gap()

    def test_premium_denominator_negative(self):
        self.doc["data"]["expenses"]["margin_proportion"] = ".95"
        self.gap()

    def test_negative_incurred_unsupported(self):
        self.doc["data"]["categories"][0]["recoveries"] = "9999999"
        self.gap()

    def test_nonnegative_cost_factor(self):
        self.doc["data"]["categories"][0]["cost_factor"] = "-1"
        self.assertRaises(ValueError, self.result)

    def test_zero_cost_factor_not_accepted(self):
        self.doc["data"]["categories"][0]["cost_factor"] = "0"
        self.gap()

    def test_scalar_source_reference_rejected(self):
        self.doc["data"]["source_refs"] = "SYN-SOURCE"
        self.assertRaises(ValueError, self.result)

    def test_duplicate_source_reference_rejected(self):
        self.doc["data"]["source_refs"] = ["SYN-SOURCE", "SYN-SOURCE"]
        self.assertRaises(ValueError, self.result)

    def test_wrong_professional_capacity(self):
        self.doc["context"]["capacity"] = "claimant"
        self.gap()

    def test_wrong_line_even_with_modified_profile(self):
        self.doc["context"]["line_of_business"] = "pc"
        self.doc["data"]["profile"]["lines_of_business"] = ["pc"]
        self.gap()

    def test_wrong_object(self):
        self.doc["context"]["object_id"] = "OTHER"
        self.gap()

    def test_review_predates_underlying_evidence(self):
        self.doc["data"]["reviewed_on"] = "2026-01-01"
        self.gap()

    def test_large_and_small_money_sum_keeps_fraction(self):
        c = self.doc["data"]["categories"][0]
        c.update(paid="10000000000000000000000000000000000000000.01", case_outstanding="0", ibnr="0", recoveries="0")
        self.assertEqual(self.metrics()["net_incurred"], "10000000000000000000000000000000000020000.01")

    def test_high_precision_product_preserved(self):
        self.doc["data"]["categories"][0]["cost_factor"] = "1.0000000000000000000000000000000000000001"
        self.assertEqual(
            self.result()["results"]["categories"][0]["projected_pmpm"],
            "102.980000000000000000000000000000000000010098",
        )

    def test_numeric_precision_bound(self):
        self.doc["data"]["expenses"]["pmpm"] = "1." + "1" * 256
        self.assertRaises(ValueError, self.result)


if __name__ == "__main__":
    unittest.main()
