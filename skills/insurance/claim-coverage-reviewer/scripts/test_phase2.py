import copy
import json
import unittest
from pathlib import Path
from domain import evaluate, validate
from insurance_foundation import run, check_output
from insurance_contract import build_artifact

NAME = "claim-coverage-reviewer"
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

    def test_coverage_not_decided_from_period(self):
        r = self.calc()["results"]
        self.assertTrue(r["loss_within_supplied_period"])
        self.assertEqual(r["coverage_determination"], "not_made")

    def test_contrary_evidence_preserved(self):
        self.doc["data"]["facts"].append(
            {"fact_id": "F-2", "quote": "Alternative ignition source remains unresolved", "source_refs": ["CLAIM"]}
        )
        self.doc["data"]["hypotheses"][0]["contrary_fact_ids"] = ["F-2"]
        out = self.calc()
        self.assertEqual(out["status"], "needs-review")
        self.assertEqual(out["results"]["coverage_hypotheses"][0]["contrary_fact_ids"], ["F-2"])

    def test_unknown_clause_reference_rejected(self):
        self.doc["data"]["hypotheses"][0]["clause_ids"] = ["nonexistent"]
        with self.assertRaises(ValueError):
            self.calc()

    def test_claims_made_requires_trigger_dates(self):
        self.doc["data"]["policy"]["coverage_trigger"] = "claims_made"
        self.assertEqual(self.calc()["status"], "needs-data")

    def test_expiry_boundary_not_coverage_determination(self):
        self.doc["data"]["loss_date"] = "2027-01-01"
        r = self.calc()["results"]
        self.assertFalse(r["loss_within_supplied_period"])
        self.assertEqual(r["coverage_determination"], "not_made")

    def test_insured_mismatch_review(self):
        self.doc["data"]["reported_insured_id"] = "different-party"
        self.assertEqual(self.calc()["status"], "needs-review")


if __name__ == "__main__":
    unittest.main()
