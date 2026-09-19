#!/usr/bin/env python3
"""Independent numeric expectations and adversarial domain regressions."""

import copy
import json
import unittest
from pathlib import Path
from calculate_or_transform import compute, debt_projection
from validate_output import validate


class Regression(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / "evals/files/request_example.json").read_text())

    def result(self):
        return compute(self.doc)["result"]

    def test_monthly_budget(self):
        row = self.result()["cash_flow"]
        self.assertEqual(row["surplus_before_goals"], 1650)
        self.assertEqual(row["remaining_after_goals"], 900)

    def test_unknown_priority_stays_missing_and_preserves_independent_math(self):
        self.doc["goals"][0]["priority"] = None
        out = compute(self.doc)
        self.assertIsNone(out["input_snapshot"]["goals"][0]["priority"])
        self.assertEqual(out["status"], "needs-data")
        self.assertTrue(any(f["path"] == "goals[0].priority" for f in out["findings"]))
        self.assertEqual(out["result"]["goal_progress"][0]["projection_status"], "not-evaluable")
        self.assertEqual(out["result"]["cash_flow"]["remaining_after_goals"], 900)
        self.assertEqual(out["result"]["debt_analysis"][0]["payoff_months"], 12)
        self.assertEqual(validate(out), [])

    def test_unknown_pool_membership_never_becomes_account_identity(self):
        self.doc["asset_pools"][0]["account_ids"] = None
        out = compute(self.doc)
        self.assertIsNone(out["input_snapshot"]["asset_pools"][0]["account_ids"])
        self.assertEqual(out["result"]["funding_ledger"][0]["status"], "not-evaluable")
        self.assertTrue(any(f["path"] == "asset_pools[0].account_ids" for f in out["findings"]))
        self.assertEqual(validate(out), [])

    def test_zero_rate_goal(self):
        g = self.result()["goal_progress"][0]
        self.assertEqual(g["projected_value"], 10000)
        self.assertEqual(g["extension_months"], 0)

    def test_pool_conservation(self):
        p = self.result()["funding_ledger"][0]
        self.assertEqual(p["balance"], p["reserved_amount"] + p["assigned_amount"] + p["unassigned_amount"])

    def test_shared_pool_overbooking(self):
        self.doc["goals"][0]["allocations"][0]["amount"] = 5000
        out = compute(self.doc)
        self.assertTrue(any(f["code"] == "shared-pool-overallocated" for f in out["findings"]))
        self.assertEqual(out["result"]["goal_progress"][1]["projection_status"], "not-evaluable")

    def test_same_account_twice(self):
        p = copy.deepcopy(self.doc["asset_pools"][0])
        p["pool_id"] = "P2"
        self.doc["asset_pools"].append(p)
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_cash_overcommit(self):
        self.doc["goals"][0]["monthly_contribution"] = 2000
        out = compute(self.doc)
        self.assertEqual(out["result"]["cash_flow"]["remaining_after_goals"], -600)
        self.assertEqual(out["status"], "needs-data")

    def test_debt_payment_zero_rate(self):
        d = self.result()["debt_analysis"][0]
        self.assertEqual((d["payoff_months"], d["total_interest"]), (12, 0))

    def test_debt_interest_and_final_cap(self):
        d = debt_projection(
            {
                "debt_id": "D",
                "balance": 100,
                "apr": 0.12,
                "minimum_monthly_payment": 150,
                "additional_monthly_payment": 0,
            }
        )
        self.assertEqual((d["payoff_months"], d["total_interest"], d["current_month_payment"]), (1, 1, 101))

    def test_non_amortizing_debt(self):
        self.doc["debts"][0].update(apr=0.12, minimum_monthly_payment=12)
        out = compute(self.doc)
        self.assertTrue(any(f["code"] == "debt-payment-insufficient" for f in out["findings"]))
        self.assertEqual(out["result"]["cash_flow"]["monthly_debt_service"], 12)

    def test_missing_debt_list_unknown(self):
        del self.doc["debts"]
        self.assertEqual(self.result()["cash_flow"]["status"], "not-evaluable")

    def test_missing_cash_flow_preserves_goal(self):
        del self.doc["cash_flow"]
        self.assertEqual(self.result()["goal_progress"][0]["projected_value"], 10000)

    def test_missing_one_goal_preserves_other(self):
        del self.doc["goals"][1]["target_amount"]
        rows = self.result()["goal_progress"]
        self.assertEqual(rows[0]["projected_value"], 10000)
        self.assertEqual(rows[1]["projection_status"], "not-evaluable")

    def test_missing_assumption_no_default(self):
        del self.doc["assumptions"]["annual_inflation"]
        self.assertEqual(self.result()["goal_progress"][0]["projection_status"], "not-evaluable")

    def test_goal_progress_mode(self):
        self.doc["mode"] = "goal_progress"
        del self.doc["cash_flow"]
        del self.doc["debts"]
        out = compute(self.doc)
        self.assertEqual(out["status"], "review-ready")
        self.assertEqual(out["result"]["cash_flow"]["status"], "not-assessed-in-goal-progress-mode")

    def test_exact_extension_zero_rate(self):
        g = self.doc["goals"][0]
        g.update(target_amount=11000)
        row = self.result()["goal_progress"][0]
        self.assertEqual(row["extension_months"], 2)
        self.assertAlmostEqual(row["illustrative_additional_monthly_contribution"], 83.33)

    def test_real_extension_inflates_through_extension(self):
        self.doc["as_of"] = "2026-07-17"
        for s in self.doc["sources"]:
            s["as_of"] = "2026-07-17"
        self.doc["assumptions"].update(nominal_annual_return=0.05, annual_inflation=0.025)
        self.doc["asset_pools"][0].update(balance=600000, reserved_amount=0)
        self.doc["goals"] = self.doc["goals"][:1]
        self.doc["goals"][0].update(
            target_amount=1650000, target_date="2046-07-01", target_basis="as_of_real", monthly_contribution=2500
        )
        self.doc["goals"][0]["allocations"][0]["amount"] = 520000
        row = self.result()["goal_progress"][0]
        self.assertEqual(row["months_to_target"], 239)
        self.assertEqual(row["extension_months"], 36)
        # Independent closed-form check at the last failing and first passing month.
        for n, passes in [(274, False), (275, True)]:
            amount = 520000 * (1 + 0.05 / 12) ** n + 2500 * ((1 + 0.05 / 12) ** n - 1) / (0.05 / 12)
            target = 1650000 * 1.025 ** (n / 12)
            self.assertEqual(amount >= target, passes)

    def test_extension_limit_explicit(self):
        self.doc["goals"][0]["target_amount"] = 1000000
        self.doc["assumptions"]["extension_limit_months"] = 1
        self.assertIsNone(self.result()["goal_progress"][0]["extension_months"])

    def test_at_date_no_annuity_division(self):
        self.doc["goals"][0]["target_date"] = self.doc["as_of"]
        row = self.result()["goal_progress"][0]
        self.assertIsNone(row["illustrative_additional_monthly_contribution"])

    def test_past_goal_unknown(self):
        self.doc["goals"][0]["target_date"] = "2026-09-15"
        self.assertEqual(self.result()["goal_progress"][0]["projection_status"], "not-evaluable")

    def test_unknown_source(self):
        self.doc["goals"][0]["source_ids"] = ["missing"]
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_nonfinite_or_bool(self):
        for value in [True, float("inf")]:
            self.doc["goals"][0]["target_amount"] = value
            with self.assertRaises(ValueError):
                compute(self.doc)

    def test_source_freshness(self):
        self.doc["sources"][0]["valid_until"] = "2026-09-15"
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_full_hash_binding(self):
        old = compute(self.doc)["artifact_id"]
        self.doc["goals"][0]["label"] = "Changed documented objective"
        self.assertNotEqual(old, compute(self.doc)["artifact_id"])

    def test_tampered_projection(self):
        out = compute(self.doc)
        out["result"]["goal_progress"][0]["projected_value"] = 999999
        self.assertTrue(validate(out))

    def test_tampered_snapshot(self):
        out = compute(self.doc)
        out["input_snapshot"]["goals"][0]["target_amount"] = 2
        self.assertTrue(validate(out))

    def test_posture_and_empty(self):
        self.assertTrue(validate({}))
        out = compute(self.doc)
        out["action_taken"] = True
        self.assertTrue(validate(out))

    def test_roundtrip(self):
        self.assertEqual(validate(compute(self.doc)), [])

    def test_placeholder_text_missing(self):
        self.doc["sources"][0]["owner"] = "synthetic owner"
        self.doc["goals"][0]["label"] = "TBD"
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_unknown_allocation_not_free_money(self):
        del self.doc["goals"][1]["allocations"]
        row = self.result()["funding_ledger"][0]
        self.assertIsNone(row["unassigned_amount"])
        self.assertEqual(row["status"], "allocation-coverage-incomplete")

    def test_money_requires_cents(self):
        self.doc["asset_pools"][0]["balance"] = 100.001
        with self.assertRaises(ValueError):
            compute(self.doc)

    def issue(self, status="unresolved"):
        return {
            "artifact_id": "ownership-artifact-7",
            "code": "ownership-conflict",
            "message": "Ownership of the funding account remains unresolved.",
            "status": status,
            "source_ids": ["client"],
        }

    def test_upstream_inventory_required(self):
        del self.doc["upstream_issues"]
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertTrue(any(f["path"] == "upstream_issues" for f in out["findings"]))
        self.assertIsNone(out["result"]["upstream_issues"])

    def test_upstream_origin_and_status_preserved(self):
        self.doc["upstream_issues"] = [self.issue()]
        out = compute(self.doc)
        finding = next(f for f in out["findings"] if f["code"] == "upstream-unresolved")
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(
            (finding["origin_artifact_id"], finding["origin_code"], finding["origin_status"]),
            ("ownership-artifact-7", "ownership-conflict", "unresolved"),
        )
        self.assertEqual(finding["source_ids"], ["client"])
        self.assertEqual(out["result"]["upstream_issues"], self.doc["upstream_issues"])

    def test_upstream_status_not_invented(self):
        row = self.issue()
        del row["status"]
        self.doc["upstream_issues"] = [row]
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertNotIn("status", out["result"]["upstream_issues"][0])

    def test_upstream_unsupported_status_rejected(self):
        self.doc["upstream_issues"] = [self.issue("approved")]
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_upstream_unknown_source_cannot_clear(self):
        row = self.issue()
        row["source_ids"] = ["unknown-source"]
        self.doc["upstream_issues"] = [row]
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertTrue(any(f["code"] == "source-gap" for f in out["findings"]))

    def test_upstream_resolved_label_needs_evidence(self):
        self.doc["upstream_issues"] = [self.issue("resolved")]
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_upstream_sourced_resolution_is_attributed(self):
        row = self.issue("resolved")
        row["resolution"] = {
            "owner": "External reviewer",
            "reference": "synthetic:ownership-resolution-v2",
            "as_of": "2026-09-16",
            "source_ids": ["client"],
        }
        self.doc["upstream_issues"] = [row]
        out = compute(self.doc)
        self.assertEqual(out["status"], "review-ready")
        self.assertEqual(out["result"]["upstream_issues"][0], row)
        self.assertFalse(out["action_taken"])

    def test_upstream_future_resolution_not_accepted(self):
        row = self.issue("resolved")
        row["resolution"] = {
            "owner": "External reviewer",
            "reference": "synthetic:future-resolution",
            "as_of": "2026-09-17",
            "source_ids": ["client"],
        }
        self.doc["upstream_issues"] = [row]
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_upstream_removal_fails_reconstruction(self):
        self.doc["upstream_issues"] = [self.issue()]
        out = compute(self.doc)
        out["result"]["upstream_issues"] = []
        self.assertTrue(validate(out))


if __name__ == "__main__":
    unittest.main()
