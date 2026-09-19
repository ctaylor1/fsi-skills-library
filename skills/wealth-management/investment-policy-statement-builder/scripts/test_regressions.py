#!/usr/bin/env python3
"""Substantive artifact, independent allocation and evidence-integrity expectations."""

import json
import unittest
from pathlib import Path
from calculate_or_transform import compute
from validate_output import validate


class Regression(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / "evals/files/request_example.json").read_text())

    def result(self):
        return compute(self.doc)["result"]

    def test_substantive_sections(self):
        sections = self.result()["sections"]
        self.assertEqual(len(sections), 13)
        self.assertEqual(
            sections[2]["content"]["spending_objective"], self.doc["mandate"]["objectives"]["spending_objective"]
        )
        self.assertIn("24000", self.result()["draft_markdown"])

    def test_governance_retained(self):
        self.assertIn("decision_authority", self.result()["sections"][1]["content"])

    def test_unknown_priority_cannot_become_a_sourced_ranking(self):
        self.doc["mandate"]["objectives"]["items"][0]["priority"] = None
        out = compute(self.doc)
        self.assertIsNone(out["input_snapshot"]["mandate"]["objectives"]["items"][0]["priority"])
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(out["result"]["sections"][2]["state"], "needs-data")
        self.assertTrue(any(f["path"] == "mandate.objectives.items[0].priority" for f in out["findings"]))
        self.assertEqual(validate(out), [])

    def test_actual_disclosure_text(self):
        self.assertIn("Investment values may decline.", self.result()["draft_markdown"])

    def test_risk_dimensions_not_inferred_rating(self):
        risk = self.result()["sections"][3]["content"]
        self.assertEqual(len(risk["dimensions"]), 6)
        self.assertNotIn("overall", risk)

    def test_upstream_risk_findings_remain_open(self):
        self.doc["mandate"]["risk_profile"]["unresolved_findings"] = [
            {"description": "Growth willingness exceeds assessed capacity", "source_ids": ["client"]}
        ]
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertIn("Growth willingness", out["result"]["draft_markdown"])

    def test_missing_tax_not_complete(self):
        del self.doc["mandate"]["tax"]
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(out["result"]["sections"][6]["state"], "needs-data")

    def test_missing_profile_dimension(self):
        self.doc["mandate"]["risk_profile"]["dimensions"].pop()
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_no_implicit_constraints_none(self):
        del self.doc["mandate"]["constraints"]["none_identified"]
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_contradictory_constraints(self):
        self.doc["mandate"]["constraints"]["none_identified"] = True
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_allocation_sum(self):
        self.assertEqual(self.result()["allocation_checks"]["target_sum"], 100)

    def test_no_auto_reweight(self):
        self.doc["mandate"]["allocation"][0]["target_pct"] = 49
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(out["result"]["allocation_checks"]["target_sum"], 99)

    def test_invalid_band_flag(self):
        self.doc["mandate"]["allocation"][0]["min_pct"] = 55
        self.assertFalse(self.result()["allocation_checks"]["within_bands"])

    def test_percentage_range(self):
        self.doc["mandate"]["allocation"][0]["target_pct"] = -5
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_duplicate_asset_class(self):
        self.doc["mandate"]["allocation"][1]["asset_class"] = "DIVERSIFIED EQUITY"
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_template_contract(self):
        self.doc["template"]["required_sections"].pop()
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_missing_version(self):
        del self.doc["template"]["version"]
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_account_tax_scope(self):
        self.doc["mandate"]["tax"]["account_treatments"][0]["account_id"] = "OTHER"
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_pending_approvals(self):
        self.assertTrue(
            all(a["status"] == "pending" and a["effective_date"] is None for a in self.result()["approvals"])
        )

    def test_cannot_grant_approval(self):
        self.doc["mandate"]["approvals"][0]["status"] = "approved"
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_unknown_source(self):
        self.doc["mandate"]["governance"]["source_ids"] = ["unknown"]
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_stale_source(self):
        self.doc["sources"][0]["valid_until"] = "2026-09-15"
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_full_source_binding(self):
        old = compute(self.doc)["artifact_id"]
        self.doc["mandate"]["objectives"]["return_objective"] = "Changed objective"
        self.assertNotEqual(old, compute(self.doc)["artifact_id"])

    def test_removed_section_fails(self):
        out = compute(self.doc)
        out["result"]["sections"].pop()
        self.assertTrue(validate(out))

    def test_changed_mandate_fails(self):
        out = compute(self.doc)
        out["result"]["draft_markdown"] += "\nIPS is now approved."
        self.assertTrue(validate(out))

    def test_empty_and_delivery_fail(self):
        self.assertTrue(validate({}))
        out = compute(self.doc)
        out["delivery_status"] = "delivered"
        self.assertTrue(validate(out))

    def test_roundtrip(self):
        self.assertEqual(validate(compute(self.doc)), [])

    def test_placeholder_text_missing(self):
        self.doc["sources"][0]["owner"] = "synthetic owner"
        self.doc["mandate"]["objectives"]["return_objective"] = "TBD"
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def issue(self, status="unresolved"):
        return {
            "artifact_id": "ownership-artifact-7",
            "code": "ownership-conflict",
            "message": "Ownership of the funding account remains unresolved.",
            "status": status,
            "source_ids": ["client"],
        }

    def test_upstream_inventory_required(self):
        del self.doc["upstream_issues"]
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertTrue(any(f["path"] == "upstream_issues" for f in out["findings"]))
        self.assertIsNone(out["result"]["upstream_issues"])

    def test_upstream_origin_and_status_preserved(self):
        self.doc["upstream_issues"] = [self.issue()]
        out = compute(self.doc)
        finding = next(f for f in out["findings"] if f["code"] == "upstream-unresolved")
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(
            (finding["origin_artifact_id"], finding["origin_code"], finding["origin_status"]),
            ("ownership-artifact-7", "ownership-conflict", "unresolved"),
        )
        self.assertEqual(finding["source_ids"], ["client"])
        self.assertEqual(out["result"]["upstream_issues"], self.doc["upstream_issues"])

    def test_upstream_status_not_invented(self):
        row = self.issue()
        del row["status"]
        self.doc["upstream_issues"] = [row]
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertNotIn("status", out["result"]["upstream_issues"][0])

    def test_upstream_unsupported_status_rejected(self):
        self.doc["upstream_issues"] = [self.issue("approved")]
        with self.assertRaises(ValueError):
            compute(self.doc)

    def test_upstream_unknown_source_cannot_clear(self):
        row = self.issue()
        row["source_ids"] = ["unknown-source"]
        self.doc["upstream_issues"] = [row]
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertTrue(any(f["code"] == "source-gap" for f in out["findings"]))

    def test_upstream_resolved_label_needs_evidence(self):
        self.doc["upstream_issues"] = [self.issue("resolved")]
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_upstream_sourced_resolution_is_attributed(self):
        row = self.issue("resolved")
        row["resolution"] = {
            "owner": "External reviewer",
            "reference": "synthetic:ownership-resolution-v2",
            "as_of": "2026-09-16",
            "source_ids": ["client"],
        }
        self.doc["upstream_issues"] = [row]
        out = compute(self.doc)
        self.assertEqual(out["status"], "review-ready")
        self.assertEqual(out["result"]["upstream_issues"][0], row)
        self.assertFalse(out["action_taken"])

    def test_upstream_future_resolution_not_accepted(self):
        row = self.issue("resolved")
        row["resolution"] = {
            "owner": "External reviewer",
            "reference": "synthetic:future-resolution",
            "as_of": "2026-09-17",
            "source_ids": ["client"],
        }
        self.doc["upstream_issues"] = [row]
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_upstream_removal_fails_reconstruction(self):
        self.doc["upstream_issues"] = [self.issue()]
        out = compute(self.doc)
        out["result"]["upstream_issues"] = []
        self.assertTrue(validate(out))

    def test_approval_party_must_be_declared(self):
        self.doc["mandate"]["approvals"][0]["party_id"] = "UNKNOWN-APPROVER"
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertTrue(any(f["code"] == "approval-party-gap" for f in out["findings"]))

    def test_approval_role_must_match_party(self):
        self.doc["mandate"]["approvals"][0]["party_id"] = "CLIENT"
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_refresh_requires_prior_artifact(self):
        self.doc["revision"] = 2
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertTrue(any(f["code"] == "revision-lineage-gap" for f in out["findings"]))
        self.doc["supersedes_artifact_id"] = "prior-IPS-artifact"
        self.assertEqual(compute(self.doc)["status"], "review-ready")

    def test_first_revision_lineage_conflict(self):
        self.doc["supersedes_artifact_id"] = "prior-IPS-artifact"
        self.assertEqual(compute(self.doc)["status"], "needs-data")


if __name__ == "__main__":
    unittest.main()
