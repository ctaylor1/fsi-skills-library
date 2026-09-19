#!/usr/bin/env python3
"""Independent cash identities and spending-versus-depletion regression expectations."""

import copy
import json
import unittest
from pathlib import Path
from decimal import Decimal
from calculate_or_transform import compute
from validate_output import validate


class Regression(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / "evals/files/request_example.json").read_text())

    def scenario(self):
        return compute(self.doc)["result"]["scenarios"][0]

    def test_base_gross_up(self):
        r = self.scenario()["annual_rows"][0]
        self.assertEqual((r["gross_withdrawals"], r["withdrawal_tax"], r["net_withdrawals"]), (125, 25, 100))

    def test_terminal_independent(self):
        self.assertEqual(self.scenario()["summary"]["terminal_portfolio"], 675)  # 1000 -125 -100 -100

    def test_return_timing(self):
        self.doc["accounts"][0]["annual_return"] = 0.1
        self.assertEqual(self.scenario()["annual_rows"][0]["ending_portfolio"], 962.5)
        self.assertEqual(self.scenario()["summary"]["terminal_portfolio"], 933.63)

    def test_fixed_percent_shortfall_not_depletion(self):
        self.doc["withdrawal_policy"].update(strategy="fixed-percentage", annual_percentage=0.001)
        self.doc["income"] = []
        s = self.scenario()["summary"]
        self.assertEqual(s["first_spending_shortfall_age"], 65)
        self.assertEqual(s["terminal_portfolio"], 997)
        self.assertIsNone(s["first_asset_depletion_age"])
        self.assertFalse(s["assets_depleted_by_horizon"])

    def test_depletion_at_horizon_not_before(self):
        self.doc["projection"]["end_age"] = 66
        self.doc["income"] = []
        self.doc["accounts"][0].update(balance=200, effective_withdrawal_tax_rate=0)
        s = self.scenario()["summary"]
        self.assertEqual(s["first_asset_depletion_age"], 66)
        self.assertFalse(s["assets_depleted_before_horizon"])
        self.assertTrue(s["assets_depleted_by_horizon"])
        self.assertIsNone(s["first_spending_shortfall_age"])

    def test_early_depletion(self):
        self.doc["income"] = []
        self.doc["accounts"][0].update(balance=100, effective_withdrawal_tax_rate=0)
        s = self.scenario()["summary"]
        self.assertTrue(s["assets_depleted_before_horizon"])
        self.assertEqual(s["first_spending_shortfall_age"], 66)

    def test_future_income_first_payment_not_preinflated(self):
        self.doc["income"][0].update(start_age=67, annual_cola=0.1, annual_gross_at_start=20)
        rows = self.scenario()["annual_rows"]
        self.assertEqual(rows[0]["net_income"], 0)
        self.assertEqual(rows[2]["net_income"], 20)

    def test_existing_income_cola_from_own_start(self):
        self.doc["income"][0].update(start_age=64, annual_cola=0.1, annual_gross_at_start=100)
        self.assertEqual(self.scenario()["annual_rows"][0]["net_income"], 110)

    def test_income_surplus_not_hidden(self):
        self.doc["income"][0].update(start_age=65, annual_gross_at_start=200)
        row = self.scenario()["annual_rows"][0]
        self.assertEqual(row["surplus_not_reinvested"], 100)
        self.assertEqual(row["ending_portfolio"], 1000)

    def test_order_and_tax_accounting(self):
        self.doc["income"] = []
        self.doc["projection"]["end_age"] = 65
        self.doc["accounts"][0]["balance"] = 100
        self.doc["accounts"].append(
            {
                "account_id": "A2",
                "type": "tax-free",
                "balance": 50,
                "annual_return": 0,
                "effective_withdrawal_tax_rate": 0,
                "source_ids": ["custody"],
            }
        )
        self.doc["withdrawal_policy"]["account_order"] = ["A2", "A1"]
        row = self.scenario()["annual_rows"][0]
        self.assertEqual(row["gross_withdrawals"], 112.5)
        self.assertEqual(row["withdrawal_tax"], 12.5)
        self.assertEqual(row["ending_portfolio"], 37.5)

    def test_all_annual_identities_independently(self):
        for row in self.scenario()["annual_rows"]:
            d = lambda k: Decimal(str(row[k]))
            self.assertEqual(
                d("beginning_portfolio") - d("gross_withdrawals") + d("investment_return"), d("ending_portfolio")
            )
            self.assertEqual(d("gross_withdrawals") - d("withdrawal_tax"), d("net_withdrawals"))
            self.assertEqual(
                d("net_income") + d("net_withdrawals") + d("spending_shortfall"),
                d("net_spending_need") + d("surplus_not_reinvested"),
            )

    def test_sequence_overrides_early_year_only(self):
        s = copy.deepcopy(self.doc["scenarios"][0])
        s.update(
            scenario_id="shock",
            return_sequences=[{"account_id": "A1", "annual_returns": [-0.5], "source_ids": ["model"]}],
        )
        self.doc["scenarios"].append(s)
        rows = compute(self.doc)["result"]["scenarios"][1]["annual_rows"]
        self.assertEqual(rows[0]["ending_portfolio"], 437.5)
        self.assertEqual(rows[1]["ending_portfolio"], 337.5)

    def test_sequence_beyond_horizon_rejected(self):
        self.doc["scenarios"].append(
            {
                "scenario_id": "shock",
                "label": "x",
                "return_adjustment": 0,
                "inflation_adjustment": 0,
                "return_sequences": [{"account_id": "A1", "annual_returns": [0, 0, 0, 0], "source_ids": ["model"]}],
                "source_ids": ["model"],
            }
        )
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_combined_bad_rate(self):
        self.doc["scenarios"].append(
            {
                "scenario_id": "bad",
                "label": "x",
                "return_adjustment": -1,
                "inflation_adjustment": 0,
                "return_sequences": [],
                "source_ids": ["model"],
            }
        )
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_missing_rate_no_default(self):
        del self.doc["accounts"][0]["annual_return"]
        self.assertEqual(self.scenario()["model_status"], "not-evaluable")

    def test_missing_income_unknown_not_zero(self):
        del self.doc["income"]
        self.assertEqual(self.scenario()["model_status"], "not-evaluable")

    def test_missing_limitation(self):
        self.doc["model"]["limitations"].pop()
        self.assertEqual(self.scenario()["model_status"], "not-evaluable")

    def test_opening_balance_date(self):
        self.doc["projection"]["opening_balance_date"] = "2026-09-15"
        self.assertEqual(self.scenario()["model_status"], "not-evaluable")

    def test_duplicate_order_rejected(self):
        self.doc["withdrawal_policy"]["account_order"] = ["A1", "A1"]
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_unused_fixed_percentage_rejected(self):
        self.doc["withdrawal_policy"]["annual_percentage"] = 0.04
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_tax_free_proxy_consistent(self):
        self.doc["accounts"][0]["type"] = "tax-free"
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_shortfall_total_reconciles(self):
        self.doc["accounts"][0]["balance"] = 0
        self.doc["income"] = []
        self.assertEqual(self.scenario()["summary"]["total_spending_shortfall"], 300)

    def test_tampered_summary(self):
        out = compute(self.doc)
        out["result"]["scenarios"][0]["summary"]["terminal_portfolio"] = 999999
        self.assertTrue(validate(out))

    def test_tampered_account_row(self):
        out = compute(self.doc)
        out["result"]["scenarios"][0]["annual_rows"][0]["accounts"][0]["withdrawal_tax"] = 0
        self.assertTrue(validate(out))

    def test_full_assumption_hash(self):
        old = compute(self.doc)["artifact_id"]
        self.doc["income"][0]["start_age"] = 67
        self.assertNotEqual(old, compute(self.doc)["artifact_id"])

    def test_stale_source(self):
        self.doc["sources"][0]["valid_until"] = "2026-09-15"
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_missing_one_scenario_preserves_base(self):
        self.doc["scenarios"].append({"scenario_id": "incomplete", "source_ids": ["model"]})
        out = compute(self.doc)
        self.assertEqual(out["result"]["scenarios"][0]["summary"]["terminal_portfolio"], 675)
        self.assertEqual(out["result"]["scenarios"][1]["model_status"], "not-evaluable")

    def test_empty_and_approval_fail(self):
        self.assertTrue(validate({}))
        out = compute(self.doc)
        out["status"] = "approved"
        self.assertTrue(validate(out))

    def test_roundtrip(self):
        self.assertEqual(validate(compute(self.doc)), [])

    def test_placeholder_text_missing(self):
        self.doc["sources"][0]["owner"] = "synthetic owner"
        self.doc["income"][0]["label"] = "unknown"
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_claiming_rmd_modeled_rejected(self):
        self.doc["model"]["limitations"][0]["treatment"] = "modeled"
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
