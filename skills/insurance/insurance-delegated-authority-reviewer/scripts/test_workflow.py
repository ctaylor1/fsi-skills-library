"""Observable failure and financial/control boundary regressions."""

import json
from pathlib import Path
import unittest
from domain import evaluate, validate
from insurance_foundation import run, check_output

PRODUCER = "insurance-delegated-authority-reviewer"


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).parents[1] / "evals/files/normal.json").read_text())

    def out(self):
        return run(self.doc, PRODUCER, evaluate, validate)

    def test_normal_recomputes(self):
        out = self.out()
        self.assertEqual("ready-for-review", out["status"])
        self.assertEqual([], check_output(out, PRODUCER, evaluate, validate))
        self.assertFalse(out["action_taken"])
        self.assertEqual("not_performed", out["execution"])

    def test_missing_business_data_preserves_gap(self):
        self.doc["data"] = {}
        out = self.out()
        self.assertEqual("needs-data", out["status"])
        self.assertNotEqual("complete", out["completeness"])

    def test_resealed_tampering_rejected(self):
        from insurance_contract import build_artifact

        out = self.out()
        out["results"]["invented_approval"] = True
        out["artifact"] = build_artifact(
            out["source_document"], out, producer=PRODUCER, artifact_type="insurance-workflow-review"
        )
        self.assertTrue(check_output(out, PRODUCER, evaluate, validate))

    def test_stale_profile(self):
        self.doc["data"]["profile"]["effective_to"] = "2026-01-31"
        self.assertEqual("needs-data", self.out()["status"])

    def test_unresolved_upstream_issue_preserved(self):
        self.doc["unresolved_issues"] = ["Identity match is not settled"]
        out = self.out()
        self.assertIn("Identity match is not settled", out["unresolved_issues"])
        self.assertEqual("needs-data", out["status"])

    def test_malformed_structure_rejected(self):
        self.doc["data"] = []
        with self.assertRaises(ValueError):
            self.out()

    def test_arithmetic_preserves_basis(self):
        out = self.out()
        self.assertEqual("2000000", out["results"]["aggregate_remaining_before_request"])
        self.assertEqual("3750000", out["results"]["projected_aggregate_used"])

    def test_wrong_currency_withholds_capacity(self):
        self.doc["data"]["request"]["currency"] = "CAD"
        self.assertIsNone(self.out()["results"]["projected_aggregate_used"])

    def test_unknown_utilization_not_zero(self):
        self.doc["data"]["aggregate_ledger"]["used_amount"] = None
        self.assertIsNone(self.out()["results"]["aggregate_remaining_before_request"])

    def test_incomplete_ledger_withholds_capacity(self):
        self.doc["data"]["aggregate_ledger"]["complete"] = False
        self.assertIsNone(self.out()["results"]["projected_aggregate_used"])

    def test_already_counted_request_not_double_counted(self):
        self.doc["data"]["aggregate_ledger"]["includes_request"] = True
        self.assertIsNone(self.out()["results"]["projected_aggregate_used"])

    def test_over_aggregate_exception(self):
        self.doc["data"]["aggregate_ledger"]["used_amount"] = "4900000"
        out = self.out()
        self.assertEqual("needs-review", out["status"])
        self.assertFalse(out["results"]["authority_granted"])

    def test_wrong_action_referred(self):
        self.doc["data"]["request"]["action"] = "settle-claim"
        self.assertEqual("needs-review", self.out()["status"])

    def test_expired_authority_referred(self):
        self.doc["data"]["agreement"]["effective_to"] = "2026-09-17"
        self.assertEqual("needs-review", self.out()["status"])

    def test_signed_agreement_not_self_grant(self):
        self.doc["data"]["agreement"]["execution_status"] = "draft"
        self.assertFalse(self.out()["results"]["authority_granted"])

    def test_bordereaux_negative_variance_preserved(self):
        self.doc["data"]["bordereaux"][0]["reported_total"] = "800000"
        out = self.out()
        self.assertEqual("-200000", out["results"]["bordereaux_checks"][0]["reported_minus_expected"])
        self.assertEqual("needs-review", out["status"])

    def test_missing_report_not_clear(self):
        self.doc["data"].pop("bordereaux")
        self.assertEqual("needs-data", self.out()["status"])

    def test_future_ledger_does_not_establish_current_capacity(self):
        self.doc["data"]["request"]["transaction_date"] = "2026-10-01"
        self.doc["data"]["aggregate_ledger"]["as_of"] = "2026-10-01"
        self.assertIsNone(self.out()["results"]["projected_aggregate_used"])

    def test_ledger_request_inclusion_must_be_boolean(self):
        self.doc["data"]["aggregate_ledger"]["includes_request"] = "false"
        with self.assertRaises(ValueError):
            self.out()

    def test_premium_report_independent_of_insured_limit_authority(self):
        row = self.doc["data"]["bordereaux"][0]
        row.update(amount_basis="written-premium", expected_total="95000.00", reported_total="94750.50")
        out = self.out()
        result = out["results"]["bordereaux_checks"][0]
        self.assertEqual("-249.50", result["reported_minus_expected"])
        self.assertEqual("written-premium", result["amount_basis"])
        self.assertEqual("3750000", out["results"]["projected_aggregate_used"])
        self.assertEqual("needs-review", out["status"])

    def test_report_currency_independent_of_authority_currency(self):
        self.doc["data"]["bordereaux"][0]["currency"] = "CAD"
        result = self.out()["results"]["bordereaux_checks"][0]
        self.assertEqual("0", result["reported_minus_expected"])
        self.assertEqual("CAD", result["currency"])

    def test_report_control_currency_mismatch_withholds_delta(self):
        self.doc["data"]["bordereaux"][0]["expected_currency"] = "CAD"
        self.assertIsNone(self.out()["results"]["bordereaux_checks"][0]["reported_minus_expected"])

    def test_report_control_basis_mismatch_withholds_delta(self):
        self.doc["data"]["bordereaux"][0]["reported_amount_basis"] = "earned-premium"
        self.assertIsNone(self.out()["results"]["bordereaux_checks"][0]["reported_minus_expected"])

    def test_report_control_period_mismatch_withholds_delta(self):
        self.doc["data"]["bordereaux"][0]["expected_period_end"] = "2026-07-31"
        self.assertIsNone(self.out()["results"]["bordereaux_checks"][0]["reported_minus_expected"])

    def test_report_parent_agreement_mismatch_withholds_delta(self):
        self.doc["data"]["bordereaux"][0]["agreement_id"] = "OTHER-CONTRACT"
        self.assertIsNone(self.out()["results"]["bordereaux_checks"][0]["reported_minus_expected"])

    def test_aggregate_overrun_message_explains_known_excess(self):
        self.doc["data"]["aggregate_ledger"]["used_amount"] = "4310000"
        detail = next(r["detail"] for r in self.out()["results"]["authority_checks"] if r["check"] == "aggregate-limit")
        self.assertIn("exceeds the limit 5000000 by 60000", detail)
        self.assertNotIn("ledger excluding the request is needed", detail)


if __name__ == "__main__":
    unittest.main()
