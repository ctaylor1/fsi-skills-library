import copy
import json
import unittest
from pathlib import Path
from domain import evaluate, validate
from insurance_foundation import run, check_output
from insurance_contract import build_artifact

NAME = "claim-handling-plan-builder"
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

    def test_completed_dependency_allows_work(self):
        r = self.calc()["results"]["task_queue"][1]
        self.assertTrue(r["ready_to_work"])
        self.assertEqual(r["blocked_by"], [])

    def test_missing_completion_evidence_blocks_dependency(self):
        del self.doc["data"]["tasks"][0]["completion_evidence"]
        r = self.calc()["results"]["task_queue"][1]
        self.assertFalse(r["ready_to_work"])
        self.assertEqual(r["blocked_by"], ["T-1"])

    def test_cycle_rejected(self):
        self.doc["data"]["tasks"][0]["depends_on"] = ["T-2"]
        with self.assertRaises(ValueError):
            self.calc()

    def test_unknown_dependency_rejected(self):
        self.doc["data"]["tasks"][0]["depends_on"] = ["absent"]
        with self.assertRaises(ValueError):
            self.calc()

    def test_overdue_kept_when_dependency_blocked(self):
        self.doc["data"]["tasks"][0]["state"] = "open"
        self.doc["data"]["tasks"][1]["due_date"] = "2026-09-16"
        out = self.calc()
        r = out["results"]["task_queue"][1]
        self.assertTrue(r["overdue"])
        self.assertFalse(r["ready_to_work"])
        self.assertIn("overdue", [x["code"] for x in out["findings"]])

    def test_unknown_deadline_not_current(self):
        del self.doc["data"]["tasks"][1]["due_date"]
        self.assertIsNone(self.calc()["results"]["task_queue"][1]["overdue"])


if __name__ == "__main__":
    unittest.main()
