import copy
import json
import unittest
from pathlib import Path
from domain import evaluate, validate
from insurance_foundation import run, check_output
from insurance_contract import build_artifact

NAME = "claim-financial-evaluation-assistant"
INPUT = Path(__file__).resolve().parents[1] / "evals/files/example.json"


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(INPUT.read_text())

    def calc(self):
        return run(self.doc, NAME, evaluate, validate)

    def test_positive_and_recompute(self):
        out = self.calc()
        self.assertEqual(out["status"], "ready-for-review")
        self.assertFalse(out["action_taken"])
        self.assertTrue(out["human_review_required"])
        self.assertEqual(check_output(out, NAME, evaluate, validate), [])

    def test_resealed_output_mutation(self):
        out = self.calc()
        out["results"]["invented_approval"] = True
        out["artifact"] = build_artifact(
            self.doc,
            out,
            producer=NAME,
            artifact_type="insurance-workflow-review",
            completeness=out["completeness"],
            evaluability=out["evaluability"],
            issues=out["unresolved_issues"],
        )
        self.assertTrue(check_output(out, NAME, evaluate, validate))

    def test_missing_profile_stays_partial(self):
        del self.doc["rule_profile"]
        out = self.calc()
        self.assertEqual(out["completeness"], "partial")
        self.assertEqual(out["status"], "needs-data")

    def test_mismatched_profile_scope(self):
        self.doc["rule_profile"]["jurisdictions"] = ["US-CA"]
        self.assertEqual(self.calc()["status"], "needs-data")

    def test_duplicate_source_identity_rejected(self):
        self.doc["sources"].append(copy.deepcopy(self.doc["sources"][0]))
        with self.assertRaises(ValueError):
            self.calc()

    def test_unresolved_input_cannot_disappear(self):
        self.doc["unresolved_issues"] = ["Unverified witness statement"]
        out = self.calc()
        self.assertIn("Unverified witness statement", out["unresolved_issues"])
        self.assertEqual(out["status"], "needs-data")

    def test_cashflow_and_stock_not_double_counted(self):
        r = self.calc()["results"]
        s = r["scenarios"][0]
        self.assertEqual(r["current_position"]["reported_incurred_indemnity"], "100000.000000")
        self.assertEqual(s["projected_gross_total_indemnity"], "90000.000000")
        self.assertEqual(s["projected_gross_total_expense"], "12000.000000")
        self.assertEqual(s["proposed_change_in_case_indemnity"], "-10000.000000")
        self.assertEqual(s["proposed_change_in_case_expense"], "2000.000000")
        self.assertEqual(s["net_scenario_total"], "97000.000000")
        self.assertIsNone(r["selected_case_reserve"])

    def test_unknown_recovery_not_zero(self):
        self.doc["data"]["scenarios"][0]["expected_recovery"] = None
        self.assertIsNone(self.calc()["results"]["scenarios"][0]["net_scenario_total"])

    def test_mixed_currency_not_netted(self):
        self.doc["data"]["scenarios"][0]["currency"] = "CAD"
        self.assertIsNone(self.calc()["results"]["scenarios"][0]["net_scenario_total"])

    def test_future_financial_valuation_blocks(self):
        self.doc["data"]["position"]["valuation_date"] = "2026-09-19"
        self.assertIsNone(self.calc()["results"]["scenarios"][0]["net_scenario_total"])

    def test_negative_and_nonfinite_amounts_rejected(self):
        for value in [True, "NaN", "-1"]:
            with self.subTest(value=value):
                self.doc["data"]["position"]["paid_indemnity"] = value
                with self.assertRaises(ValueError):
                    self.calc()

    def test_wrong_scenario_basis_not_added(self):
        self.doc["data"]["scenarios"][0]["basis"] = "total_ultimate"
        self.assertIsNone(self.calc()["results"]["scenarios"][0]["net_scenario_total"])

    def test_ledger_without_source_not_computed(self):
        self.doc["data"]["position"]["source_refs"] = []
        self.assertIsNone(self.calc()["results"]["scenarios"][0]["net_scenario_total"])


if __name__ == "__main__":
    unittest.main()
