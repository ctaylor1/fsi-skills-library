"""Independent expected costs/exposures and missingness regression checks."""

import copy
import json
from pathlib import Path
import unittest
from domain import compute, validate_input, validate_output

FILES = Path(__file__).resolve().parents[1] / "evals/files"


class ComparatorTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((FILES / "request_example.json").read_text())

    def test_known_cost_components_and_symmetric_difference(self):
        out = compute(self.doc)
        a, b = [p["metrics"] for p in out["result"]["proposals"]]
        self.assertEqual(a["weighted_expense_bps"], 6)
        self.assertEqual(a["ongoing_cost_bps"], 61)
        self.assertEqual(a["first_year_cost_amount"], 6200)
        self.assertEqual(b["ongoing_cost_bps"], 50)
        self.assertEqual(b["first_year_cost_amount"], 5200)
        self.assertEqual(out["result"]["pairwise_differences"][0]["first_year_cost_amount"], -1000)
        self.assertEqual(out["result"]["pairwise_differences"][0]["ongoing_cost_bps"], -11)
        self.assertEqual(validate_output(out), [])

    def test_fund_plus_direct_issuer_aggregates(self):
        out = compute(self.doc)
        concentration = out["result"]["proposals"][1]["metrics"]["exposures"]["issuer_id"]
        self.assertEqual(concentration["known_weights"]["ISSUER-X"], 0.75)
        self.assertEqual(concentration["max_weight"], 0.75)
        self.assertTrue(any(f["code"] == "concentration-review" for f in out["findings"]))

    def test_missing_product_data_stays_unknown(self):
        out = compute(json.loads((FILES / "request_unknown.json").read_text()))
        m = out["result"]["proposals"][0]["metrics"]
        self.assertIsNone(m["weighted_expense_bps"])
        self.assertIsNone(m["first_year_cost_amount"])
        self.assertIsNone(m["illiquid_weight"])
        self.assertIsNone(m["conflicts"]["proprietary"]["weight"])
        self.assertIsNone(m["exposures"]["issuer_id"]["max_weight"])
        self.assertEqual(m["exposures"]["issuer_id"]["coverage_weight"], 0.4)
        self.assertIsNone(out["result"]["pairwise_differences"][0]["first_year_cost_amount"])
        self.assertEqual(out["status"], "needs-data")

    def test_missing_fee_is_not_zero(self):
        del self.doc["proposals"][0]["custody_fee_bps"]
        m = compute(self.doc)["result"]["proposals"][0]["metrics"]
        self.assertIsNone(m["ongoing_cost_bps"])
        self.assertEqual(m["weighted_expense_bps"], 6)

    def test_partial_lookthrough_reports_known_lower_bound(self):
        self.doc["proposals"][0]["holdings"][0]["exposures"].pop()
        m = compute(self.doc)["result"]["proposals"][0]["metrics"]["exposures"]["issuer_id"]
        self.assertAlmostEqual(m["coverage_weight"], 0.7)
        self.assertIsNone(m["max_weight"])
        self.assertEqual(m["known_max_lower_bound"], 0.4)

    def test_overfilled_constituents_not_normalized(self):
        self.doc["proposals"][0]["holdings"][0]["exposures"][0]["weight"] = 0.8
        m = compute(self.doc)["result"]["proposals"][0]["metrics"]["exposures"]["issuer_id"]
        self.assertEqual(m["coverage_weight"], 0.4)
        self.assertIsNone(m["max_weight"])

    def test_diversified_label_cannot_suppress_real_exposure(self):
        self.doc["proposals"][1]["holdings"][0]["diversified"] = True
        self.doc["proposals"][1]["holdings"][0]["sector"] = "broad"
        m = compute(self.doc)["result"]["proposals"][1]["metrics"]["exposures"]["issuer_id"]
        self.assertEqual(m["max_weight"], 0.75)

    def test_weight_and_reported_amount_mismatches(self):
        for field, value in [("reported_first_year_cost_amount", 1), ("portfolio_value", 2000000)]:
            doc = copy.deepcopy(self.doc)
            doc["proposals"][0][field] = value
            self.assertTrue(any(f["code"] == "economic-total" for f in compute(doc)["findings"]))
        self.doc["proposals"][0]["holdings"][0]["weight"] = 0.4
        self.assertIsNone(compute(self.doc)["result"]["proposals"][0]["metrics"]["ongoing_cost_bps"])

    def test_explicit_conflict_and_illiquidity_are_visible(self):
        h = self.doc["proposals"][0]["holdings"][0]
        h["proprietary"] = True
        h["liquidity_days"] = 180
        out = compute(self.doc)
        self.assertEqual(out["result"]["proposals"][0]["metrics"]["illiquid_weight"], 0.6)
        self.assertTrue({"conflict-review", "liquidity-review"}.issubset({f["code"] for f in out["findings"]}))

    def test_no_implicit_policy_defaults(self):
        self.doc["policy"] = {}
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertIsNone(out["result"]["proposals"][0]["metrics"]["illiquid_weight"])

    def test_different_currency_dollars_not_compared(self):
        self.doc["proposals"][1]["currency"] = "EUR"
        out = compute(self.doc)
        self.assertIsNone(out["result"]["pairwise_differences"][0]["first_year_cost_amount"])
        self.assertEqual(out["result"]["pairwise_differences"][0]["ongoing_cost_bps"], -11)

    def test_invalid_types_and_duplicate_rows_reject(self):
        for value in (True, -1, float("inf"), "0.6"):
            doc = copy.deepcopy(self.doc)
            doc["proposals"][0]["holdings"][0]["weight"] = value
            self.assertTrue(validate_input(doc))
        self.doc["proposals"][0]["holdings"].append(copy.deepcopy(self.doc["proposals"][0]["holdings"][0]))
        self.assertTrue(validate_input(self.doc))

    def test_unknown_constituent_citation_removes_coverage(self):
        self.doc["proposals"][0]["holdings"][0]["exposures"][0]["source_ids"] = ["INVENTED"]
        m = compute(self.doc)["result"]["proposals"][0]["metrics"]["exposures"]["issuer_id"]
        self.assertEqual(m["coverage_weight"], 0.7)
        self.assertIsNone(m["max_weight"])

    def test_single_candidate_not_fabricated(self):
        self.doc["proposals"].pop()
        self.assertTrue(validate_input(self.doc))

    def test_empty_or_changed_output_rejected(self):
        self.assertTrue(validate_output({}))
        for mutation in ("cost", "exposure", "findings", "decision"):
            out = compute(self.doc)
            if mutation == "cost":
                out["result"]["proposals"][0]["metrics"]["first_year_cost_amount"] = 1
            elif mutation == "exposure":
                out["result"]["proposals"][1]["metrics"]["exposures"]["issuer_id"]["max_weight"] = 0
            elif mutation == "findings":
                out["findings"] = []
                out["status"] = "review-ready"
            else:
                out["result"]["selected_proposal"] = "P-A"
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
