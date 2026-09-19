import copy
import json
import unittest
from pathlib import Path
from domain import evaluate, validate
from insurance_foundation import run, check_output
from insurance_contract import build_artifact

NAME = "claim-payment-closure-reviewer"
INPUT = Path(__file__).resolve().parents[1] / "evals/files/example.json"


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(INPUT.read_text())

    def calc(self):
        return run(self.doc, NAME, evaluate, validate)

    def test_positive_and_recompute(self):
        out = self.calc()
        self.assertEqual(out["status"], "needs-review")
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

    def test_ready_draft_never_executes(self):
        r = self.calc()["results"]
        self.assertEqual(r["payment_review_status"], "ready_for_authorized_review")
        self.assertEqual(r["closure_review_status"], "blocked")
        self.assertFalse(r["payment_executed"])
        self.assertFalse(r["claim_closed"])

    def test_duplicate_pending_payment_blocks(self):
        self.doc["data"]["payment_history"] = [
            {**self.doc["data"]["payment_request"], "state": "pending", "source_refs": ["LEDGER"]}
        ]
        self.assertEqual(self.calc()["results"]["payment_review_status"], "blocked")

    def test_authority_amount_exceeded_blocks(self):
        self.doc["data"]["payment_request"]["amount"] = "10001"
        self.assertEqual(self.calc()["results"]["payment_review_status"], "blocked")

    def test_authority_expiry_blocks(self):
        self.doc["data"]["authority"]["expiry"] = "2026-09-17"
        self.assertEqual(self.calc()["results"]["payment_review_status"], "blocked")

    def test_missing_gate_not_pass(self):
        self.doc["data"]["gates"].pop()
        self.assertEqual(self.calc()["results"]["payment_review_status"], "blocked")

    def test_unknown_history_not_empty(self):
        del self.doc["data"]["payment_history"]
        self.assertEqual(self.calc()["results"]["payment_review_status"], "blocked")

    def test_open_obligation_only_blocks_closure(self):
        self.doc["data"]["closure"]["open_obligations"] = ["Supplier recovery pending"]
        r = self.calc()["results"]
        self.assertEqual(r["closure_review_status"], "blocked")
        self.assertEqual(r["payment_review_status"], "ready_for_authorized_review")

    def test_unknown_reserve_blocks_closure(self):
        self.doc["data"]["closure"]["remaining_case_reserve"] = None
        self.assertEqual(self.calc()["results"]["closure_review_status"], "blocked")

    def test_settled_payment_allows_closure_not_repeat_payment(self):
        self.doc["data"]["payment_history"] = [
            {**self.doc["data"]["payment_request"], "state": "settled", "source_refs": ["LEDGER"]}
        ]
        r = self.calc()["results"]
        self.assertEqual(r["closure_review_status"], "ready_for_authorized_review")
        self.assertEqual(r["payment_review_status"], "blocked")
        self.assertEqual(r["reconciled_payment_ids"], ["PAY-1"])

    def test_different_id_same_obligation_blocks_repeat_payment(self):
        self.doc["data"]["payment_history"] = [
            {
                **self.doc["data"]["payment_request"],
                "payment_id": "OLD-PAY",
                "state": "settled",
                "source_refs": ["LEDGER"],
            }
        ]
        r = self.calc()["results"]
        self.assertEqual(r["payment_review_status"], "blocked")
        self.assertEqual(r["closure_review_status"], "blocked")

    def test_reopening_requires_condition_owner_routing_and_evidence(self):
        self.doc["data"]["payment_history"] = [
            {**self.doc["data"]["payment_request"], "state": "settled", "source_refs": ["LEDGER"]}
        ]
        complete = copy.deepcopy(self.doc["data"]["closure"]["reopen_triggers"][0])
        for field in ("trigger", "owner", "routing", "source_refs"):
            with self.subTest(field=field):
                row = dict(complete, **{field: None})
                self.doc["data"]["closure"]["reopen_triggers"] = [row]
                result = self.calc()
                self.assertEqual(result["results"]["closure_review_status"], "blocked")
                self.assertEqual(result["status"], "needs-data")
        for row in ("", "Owner to be assigned", {}, {**complete, "source_refs": ["MISSING"]}):
            with self.subTest(row=row):
                self.doc["data"]["closure"]["reopen_triggers"] = [row]
                self.assertEqual(self.calc()["results"]["closure_review_status"], "blocked")

    def test_settled_wrong_amount_blocks_closure(self):
        self.doc["data"]["payment_history"] = [
            {**self.doc["data"]["payment_request"], "amount": "4999", "state": "settled", "source_refs": ["LEDGER"]}
        ]
        self.assertEqual(self.calc()["results"]["closure_review_status"], "blocked")

    def test_boolean_payment_rejected(self):
        self.doc["data"]["payment_request"]["amount"] = True
        with self.assertRaises(ValueError):
            self.calc()


if __name__ == "__main__":
    unittest.main()
