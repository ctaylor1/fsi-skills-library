"""Expected-value cash, lot and transition regressions; no execution integration."""

import copy
import json
from pathlib import Path
import unittest
from domain import compute, validate_input, validate_output

FILES = Path(__file__).resolve().parents[1] / "evals/files"


class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((FILES / "request_example.json").read_text())

    def specified(self):
        out = compute(self.doc)
        self.doc["intent"]["mode"] = "validate"
        self.doc["intent"]["lot_selection"] = "specified"
        keys = (
            "trade_id",
            "security_id",
            "side",
            "quantity",
            "fee_amount",
            "settles_on",
            "lot_allocations",
            "source_ids",
        )
        self.doc["trades"] = [{key: t[key] for key in keys} for t in out["result"]["trades"]]
        return self.doc

    def test_generated_economics_and_oldest_lot_expected_values(self):
        out = compute(self.doc)
        p = out["result"]
        self.assertEqual(
            [(t["side"], t["security_id"], t["quantity"]) for t in p["trades"]], [("sell", "A", 200), ("buy", "B", 200)]
        )
        self.assertEqual(p["pre_nav"], 160000)
        self.assertEqual(p["post_nav"], 160000)
        self.assertEqual(p["post_cash"], 10000)
        self.assertEqual(p["post_positions_plus_cash"], 160000)
        self.assertEqual(p["sell_turnover"], 0.125)
        self.assertEqual(p["lot_gain_loss"][0]["allocated_basis"], 16000)
        self.assertEqual(p["lot_gain_loss"][0]["gross_gain_loss"], 4000)
        self.assertEqual(out["status"], "review-ready")
        self.assertEqual(p["execution_status"], "not-supported")
        self.assertEqual(validate_output(out), [])

    def test_supplied_trade_and_lot_choices_preserved(self):
        doc = self.specified()
        doc["trades"][0]["lot_allocations"] = [{"lot_id": "A2", "quantity": 200, "source_ids": ["FACTS"]}]
        out = compute(doc)
        self.assertEqual(out["result"]["lot_gain_loss"][0]["allocated_basis"], 22000)
        self.assertEqual(out["result"]["lot_gain_loss"][0]["gross_gain_loss"], -2000)
        self.assertEqual(out["result"]["trades"][0]["lot_allocations"][0]["lot_id"], "A2")

    def test_fee_reserve_and_costs_reduce_nav(self):
        self.doc["intent"]["transaction_cost_budget"] = 100
        for security in self.doc["universe"]:
            security["fee_bps"] = 10
        out = compute(self.doc)
        p = out["result"]
        self.assertEqual(p["transaction_fees"], 40)
        self.assertEqual(p["post_nav"], 159960)
        self.assertEqual(p["post_cash"], 10160)
        self.assertEqual(p["post_positions_plus_cash"], p["post_nav"])
        self.assertEqual(out["status"], "review-ready")

    def test_settlement_gap_not_cured_by_final_cash(self):
        out = compute(json.loads((FILES / "request_settlement_gap.json").read_text()))
        self.assertEqual(out["result"]["post_cash"], 10000)
        self.assertEqual(out["result"]["settlement_ledger"][0]["closing_cash"], -10000)
        self.assertTrue(any(f["code"] == "settlement-funding" for f in out["findings"]))

    def test_prefund_policy_does_not_use_same_day_sale_credit(self):
        self.doc["intent"]["settlement_policy"] = "prefund-buys"
        self.assertTrue(any(f["code"] == "settlement-funding" for f in compute(self.doc)["findings"]))

    def test_cumulative_oversell_and_lot_reuse_detected(self):
        self.specified()
        sale = self.doc["trades"][0]
        sale["quantity"] = 600
        sale["lot_allocations"][0]["quantity"] = 600
        sale2 = copy.deepcopy(sale)
        sale2["trade_id"] = "SALE2"
        self.doc["trades"] = [sale, sale2]
        out = compute(self.doc)
        self.assertTrue({"oversell", "lot-overallocation"}.issubset({f["code"] for f in out["findings"]}))
        self.assertIsNone(out["result"]["post_nav"])

    def test_restrictions_unknown_and_denied_not_cleared(self):
        for value in (False, None):
            doc = copy.deepcopy(self.doc)
            doc["policy"]["restrictions"][1]["buy_allowed"] = value
            out = compute(doc)
            self.assertTrue(any(f["code"] == "restricted-transition" for f in out["findings"]))
            self.assertFalse(out["action_taken"])

    def test_position_and_account_totals_reconciled(self):
        for mutation in ("position", "nav", "lots", "basis"):
            doc = copy.deepcopy(self.doc)
            if mutation == "position":
                doc["portfolio"]["positions"][0]["reported_market_value"] = 1
            elif mutation == "nav":
                doc["portfolio"]["reported_total_value"] = 1
            elif mutation == "lots":
                doc["portfolio"]["positions"][0]["lots"][0]["quantity"] = 500
            else:
                doc["portfolio"]["positions"][0]["reported_cost_basis"] = 1
            self.assertEqual(compute(doc)["status"], "needs-data")

    def test_missing_price_disables_generation(self):
        self.doc["universe"][0]["price"] = None
        p = compute(self.doc)["result"]
        self.assertEqual(p["trades"], [])
        self.assertIsNone(p["pre_nav"])
        self.assertIsNone(p["post_nav"])

    def test_missing_fee_not_zero(self):
        self.doc["universe"][0]["fee_bps"] = None
        out = compute(self.doc)
        self.assertIsNone(out["result"]["transaction_fees"])
        self.assertIsNone(out["result"]["post_cash"])
        self.assertIsNone(out["result"]["sell_turnover"])
        self.assertFalse(out["result"]["settlement_ledger_complete"])
        self.assertIsNone(out["result"]["settlement_ledger"][0]["closing_cash"])
        self.assertEqual(out["status"], "needs-data")

    def test_missing_lots_not_estimated_from_position_average(self):
        self.doc["portfolio"]["positions"][0]["lots"] = []
        out = compute(self.doc)
        self.assertEqual(out["result"]["lot_gain_loss"], [])
        self.assertIsNone(out["result"]["trades"][0]["gross_gain_loss"])
        self.assertEqual(out["status"], "needs-data")

    def test_unknown_snapshot_never_assumes_absent_zero(self):
        self.doc["portfolio"]["positions_complete"] = None
        out = compute(self.doc)
        self.assertIsNone(out["result"]["pre_nav"])
        self.assertEqual(out["result"]["trades"], [])

    def test_no_trade_transition_can_be_review_ready(self):
        self.doc["target"]["allocations"][0]["weight"] = 0.625
        self.doc["target"]["allocations"][1]["weight"] = 0.3125
        self.doc["policy"]["max_position_weight"] = 0.7
        out = compute(self.doc)
        self.assertEqual(out["result"]["trades"], [])
        self.assertEqual(out["status"], "review-ready")

    def test_new_security_and_explicit_exit_are_generated(self):
        security = copy.deepcopy(self.doc["universe"][1])
        security["security_id"] = "C"
        security["tax_identity_group"] = "C"
        self.doc["universe"].append(security)
        self.doc["target"]["allocations"][1]["weight"] = 0
        self.doc["target"]["allocations"].append({"security_id": "C", "weight": 0.4375, "source_ids": ["FACTS"]})
        restriction = copy.deepcopy(self.doc["policy"]["restrictions"][1])
        restriction["security_id"] = "C"
        self.doc["policy"]["restrictions"].append(restriction)
        self.doc["policy"]["max_sell_turnover"] = 1
        self.doc["policy"]["max_order_notional"] = 100000
        out = compute(self.doc)
        self.assertEqual(
            {(t["side"], t["security_id"], t["quantity"]) for t in out["result"]["trades"]},
            {("sell", "A", 200), ("sell", "B", 500), ("buy", "C", 700)},
        )
        self.assertEqual(out["result"]["post_positions_plus_cash"], 160000)
        self.assertEqual(out["status"], "review-ready")

    def test_unmapped_target_never_silently_exits(self):
        self.doc["target"]["allocations"].pop()
        out = compute(self.doc)
        self.assertEqual(out["result"]["trades"], [])
        self.assertEqual(out["status"], "needs-data")

    def test_supplied_buy_outside_target_is_in_projected_economics(self):
        self.specified()
        security = copy.deepcopy(self.doc["universe"][1])
        security["security_id"] = "C"
        self.doc["universe"].append(security)
        self.doc["trades"][1]["security_id"] = "C"
        out = compute(self.doc)
        self.assertTrue(any(f["code"] == "target-coverage" for f in out["findings"]))
        self.assertIn("C", {p["security_id"] for p in out["result"]["positions"]})
        self.assertEqual(out["result"]["post_positions_plus_cash"], 160000)

    def test_fee_increment_and_limit_breaches(self):
        self.specified()
        self.doc["trades"][0]["fee_amount"] = 100
        self.doc["trades"][1]["quantity"] = 200.5
        self.doc["policy"]["max_order_notional"] = 10000
        self.doc["policy"]["max_sell_turnover"] = 0.01
        codes = {f["code"] for f in compute(self.doc)["findings"]}
        self.assertTrue({"fee-reconciliation", "quantity-increment", "order-limit", "turnover-limit"}.issubset(codes))

    def test_loss_repurchase_group_is_review_signal_not_tax_clearance(self):
        self.specified()
        self.doc["trades"][0]["lot_allocations"] = [{"lot_id": "A2", "quantity": 200, "source_ids": ["FACTS"]}]
        self.doc["universe"][1]["tax_identity_group"] = "A"
        out = compute(self.doc)
        self.assertTrue(any(f["code"] == "same-plan-loss-repurchase" for f in out["findings"]))
        self.assertEqual(out["result"]["approval_status"], "not-authenticated")

    def test_legacy_approval_and_malformed_values_reject(self):
        self.doc["approval"] = {"advisor": {"token": "fake", "status": "approved"}}
        self.assertTrue(validate_input(self.doc))
        self.doc.pop("approval")
        for value in (True, -1, "100", float("nan")):
            doc = copy.deepcopy(self.doc)
            doc["portfolio"]["cash"] = value
            self.assertTrue(validate_input(doc))
        self.doc["universe"][0]["tax_identity_group"] = []
        self.assertTrue(validate_input(self.doc))

    def test_full_intent_binding_and_tampered_output(self):
        original = compute(self.doc)
        for mutation in ("policy", "account", "settlement", "reason"):
            doc = copy.deepcopy(self.doc)
            if mutation == "policy":
                doc["policy"]["max_order_notional"] = 100000
            elif mutation == "account":
                doc["account"]["account_id"] = "OTHER"
            elif mutation == "settlement":
                doc["universe"][0]["settles_on"] = "2026-09-18"
            else:
                doc["intent"]["reason"] = "changed intent"
            changed = compute(doc)
            self.assertNotEqual(original["input_hash"], changed["input_hash"])
            self.assertNotEqual(
                original["result"]["trades"][0]["intent_binding"], changed["result"]["trades"][0]["intent_binding"]
            )
        for mutation in ("cash", "quantity", "lot", "execution", "empty"):
            out = copy.deepcopy(original)
            if mutation == "cash":
                out["result"]["post_cash"] = 999
            elif mutation == "quantity":
                out["result"]["trades"][0]["quantity"] = 1
            elif mutation == "lot":
                out["result"]["lot_gain_loss"][0]["allocated_basis"] = 1
            elif mutation == "execution":
                out["action_taken"] = True
                out["result"]["execution_status"] = "executed"
            else:
                out = {}
            self.assertTrue(validate_output(out))

    def test_upstream_structure_is_explicit_and_typed(self):
        for value in (
            None,
            {},
            ["issue"],
            [{"artifact_id": "A", "code": "risk", "message": "Open", "status": "approved", "source_ids": ["FACTS"]}],
        ):
            doc = copy.deepcopy(self.doc)
            doc["upstream_issues"] = value
            self.assertTrue(validate_input(doc))
        doc = copy.deepcopy(self.doc)
        del doc["upstream_issues"]
        self.assertTrue(validate_input(doc))

    def test_upstream_ownership_and_risk_issues_prevent_readiness(self):
        doc = copy.deepcopy(self.doc)
        if "policy" in doc and "max_issuer_weight" in doc["policy"]:
            doc["policy"]["max_issuer_weight"] = 1
        self.assertEqual(compute(doc)["status"], "review-ready")
        issue_doc = json.loads((FILES / "request_upstream_issues.json").read_text())
        doc["upstream_issues"] = issue_doc["upstream_issues"]
        out = compute(doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(
            {f["upstream_code"] for f in out["findings"] if f["code"] == "upstream-unresolved"},
            {"ownership-conflict", "risk-capacity-conflict"},
        )
        self.assertEqual(out["result"]["upstream_issues"], doc["upstream_issues"])
        self.assertEqual(out["result"]["handoff_context"]["upstream_issues"], doc["upstream_issues"])
        self.assertEqual(validate_output(out), [])
        if "candidates" in out["result"]:
            self.assertTrue(all(c["status"] == "needs-review" for c in out["result"]["candidates"]))
            self.assertTrue(
                all(any(f["code"] == "upstream-unresolved" for f in c["findings"]) for c in out["result"]["candidates"])
            )

    def test_resolved_upstream_records_retained_without_claiming_authentication(self):
        doc = copy.deepcopy(self.doc)
        if "policy" in doc and "max_issuer_weight" in doc["policy"]:
            doc["policy"]["max_issuer_weight"] = 1
        issue = {
            "artifact_id": "source-artifact",
            "code": "ownership-conflict",
            "message": "Source reviewer recorded resolution",
            "status": "resolved",
            "source_ids": ["FACTS"],
        }
        doc["upstream_issues"] = [issue]
        out = compute(doc)
        self.assertEqual(out["status"], "review-ready")
        self.assertEqual(out["result"]["upstream_issues"], [issue])
        self.assertFalse(out["action_taken"])

    def test_upstream_unknown_citation_remains_a_gap(self):
        doc = copy.deepcopy(self.doc)
        doc["upstream_issues"] = [
            {
                "artifact_id": "source-artifact",
                "code": "risk",
                "message": "Source claim requires evidence",
                "status": "resolved",
                "source_ids": ["MISSING"],
            }
        ]
        out = compute(doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertTrue(any(f["code"] == "source-gap" for f in out["findings"]))
        self.assertEqual(validate_output(out), [])

    def test_dropped_upstream_context_or_findings_rejected(self):
        doc = json.loads((FILES / "request_upstream_issues.json").read_text())
        for mutation in ("context", "issue-list", "findings"):
            out = compute(doc)
            if mutation == "context":
                out["result"]["handoff_context"]["upstream_issues"] = []
            elif mutation == "issue-list":
                out["result"]["upstream_issues"] = []
            else:
                out["findings"] = []
                out["status"] = "review-ready"
            self.assertTrue(validate_output(out))

    def test_unmapped_issue_schema_is_not_silently_ignored(self):
        self.doc["unresolved_issues"] = [{"code": "risk", "message": "Upstream concern", "source_ids": ["FACTS"]}]
        self.assertTrue(validate_input(self.doc))


if __name__ == "__main__":
    unittest.main()
