import copy
import json
import unittest
from pathlib import Path
from domain import evaluate, validate
from insurance_foundation import run, check_output
from insurance_contract import build_artifact

NAME = "insurance-product-design-reviewer"
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

    def test_failed_claims_operating_test_surfaces(self):
        self.doc["data"]["features"][0]["claims_test_status"] = "fail"
        out = self.calc()
        self.assertEqual(out["status"], "needs-review")
        self.assertFalse(out["results"]["launch_authorized"])

    def test_missing_review_category(self):
        self.doc["data"]["requirements"].pop()
        self.assertEqual(self.calc()["status"], "needs-data")

    def test_missing_wording_is_traceability_gap(self):
        del self.doc["data"]["features"][0]["wording_ref"]
        self.assertEqual(self.calc()["results"]["feature_matrix"][0]["traceability"], "partial")

    def test_unregistered_evidence_not_complete(self):
        self.doc["data"]["features"][0]["source_refs"] = ["not-present"]
        self.assertEqual(self.calc()["status"], "needs-data")

    def test_duplicate_feature_rejected(self):
        self.doc["data"]["features"] *= 2
        with self.assertRaises(ValueError):
            self.calc()


if __name__ == "__main__":
    unittest.main()
