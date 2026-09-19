"""Observable failure and financial/control boundary regressions."""

import json
from pathlib import Path
import unittest
from domain import evaluate, validate
from insurance_foundation import run, check_output

PRODUCER = "insurance-producer-onboarding-reviewer"


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

    def test_stale_license_is_unknown(self):
        self.doc["data"]["licenses"][0]["verified_on"] = "2026-01-01"
        out = self.out()
        self.assertEqual("unknown", out["results"]["scope_checks"][0]["checks"][0]["status"])

    def test_expired_is_observed_exception(self):
        self.doc["data"]["licenses"][0]["effective_to"] = "2026-09-17"
        self.assertEqual("observed-exception", self.out()["results"]["scope_checks"][0]["checks"][0]["status"])

    def test_missing_appointment_applicability(self):
        self.doc["data"]["requirements"][0]["appointment_required"] = None
        self.assertEqual("unknown", self.out()["results"]["scope_checks"][0]["checks"][1]["status"])

    def test_name_mismatch_is_not_clearance(self):
        self.doc["data"]["licenses"][0]["entity_name"] = "Other Person"
        self.assertEqual("unknown", self.out()["results"]["scope_checks"][0]["checks"][0]["status"])

    def test_multiple_records_not_silently_chosen(self):
        self.doc["data"]["licenses"].append(
            dict(self.doc["data"]["licenses"][0], record_id="conflict", status="revoked")
        )
        self.assertEqual("unknown", self.out()["results"]["scope_checks"][0]["checks"][0]["status"])

    def test_no_expiry_requires_explicit_evidence(self):
        self.doc["data"]["licenses"][0].pop("effective_to")
        self.assertEqual("unknown", self.out()["results"]["scope_checks"][0]["checks"][0]["status"])

    def test_not_required_still_needs_rule_evidence(self):
        self.doc["data"]["requirements"][1]["rule_source_ref"] = "unavailable"
        self.assertEqual("unknown", self.out()["results"]["scope_checks"][1]["checks"][1]["status"])

    def test_out_of_profile_jurisdiction(self):
        self.doc["data"]["requirements"][0]["jurisdiction"] = "OTHER"
        self.assertEqual("unknown", self.out()["results"]["scope_checks"][0]["checks"][0]["status"])

    def test_license_does_not_create_binding_authority(self):
        self.assertEqual("not-determined", self.out()["results"]["carrier_binding_authority"])


if __name__ == "__main__":
    unittest.main()
