import copy
import json
import unittest
from pathlib import Path
from domain import evaluate, validate
from insurance_foundation import run, check_output
from insurance_contract import build_artifact

NAME = "pc-rate-adequacy-analyzer"
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

    def test_indication_arithmetic(self):
        r = self.calc()["results"]
        self.assertEqual(r["current_adjusted_premium_per_exposure"], "1122.000000")
        self.assertEqual(r["credibility_blended_loss_lae_per_exposure"], "752.500000")
        self.assertEqual(r["indicated_premium_per_exposure"], "1116.666667")
        self.assertEqual(r["indicated_change"], "-0.004753")

    def test_period_mismatch_suppresses_indication(self):
        self.doc["data"]["premium"]["period_start"] = "2024-01-01"
        self.assertIsNone(self.calc()["results"]["indicated_change"])

    def test_mixed_currency_suppresses_indication(self):
        self.doc["data"]["losses"]["currency"] = "CAD"
        self.assertIsNone(self.calc()["results"]["indicated_change"])

    def test_unknown_cat_not_zero(self):
        self.doc["data"]["assumptions"]["catastrophe_provision_per_exposure"] = None
        self.assertIsNone(self.calc()["results"]["indicated_change"])

    def test_invalid_numeric_values(self):
        for value in [True, "NaN", "Infinity", "-1"]:
            with self.subTest(value=value):
                self.doc["data"]["premium"]["amount"] = value
                with self.assertRaises(ValueError):
                    self.calc()

    def test_nonpositive_expense_denominator(self):
        self.doc["data"]["assumptions"]["variable_expense_ratio"] = "0.95"
        self.assertIsNone(self.calc()["results"]["indicated_change"])

    def test_complement_required_only_below_full_credibility(self):
        del self.doc["data"]["assumptions"]["complement_loss_and_lae_per_exposure"]
        self.assertIsNone(self.calc()["results"]["indicated_change"])
        self.doc["data"]["assumptions"]["credibility"] = "1"
        self.assertIsNotNone(self.calc()["results"]["indicated_change"])

    def test_future_source_suppresses_indication(self):
        self.doc["sources"][3]["as_of"] = "2026-09-19"
        self.assertIsNone(self.calc()["results"]["indicated_change"])


if __name__ == "__main__":
    unittest.main()
