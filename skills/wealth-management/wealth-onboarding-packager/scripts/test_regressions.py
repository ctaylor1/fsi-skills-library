#!/usr/bin/env python3
"""Independent evidence completeness, applicability, authority and release boundaries."""

import copy
import json
import unittest
from pathlib import Path
from calculate_or_transform import compute
from validate_output import validate

BASE = json.loads((Path(__file__).resolve().parents[1] / "evals/files/onboarding_example.json").read_text())


class RegressionTests(unittest.TestCase):
    def doc(self):
        return copy.deepcopy(BASE)

    def assertGap(self, d, code):
        out = compute(d)
        self.assertEqual(out["status"], "needs-data")
        self.assertIn(code, [f["code"] for f in out["findings"]])
        return out

    def test_complete_package_is_reviewable_never_opened(self):
        out = compute(self.doc())
        self.assertEqual(out["status"], "review-ready")
        self.assertFalse(out["action_taken"])
        self.assertTrue(out["human_review_required"])
        self.assertEqual(out["delivery_status"], "not-delivered")
        self.assertEqual(validate(out), [])

    def test_missing_registration_checklist(self):
        d = self.doc()
        d["accounts"][0]["registration"] = "trust"
        self.assertGap(d, "policy-gap")

    def test_missing_authority(self):
        d = self.doc()
        d["accounts"][0].pop("authority_record_status")
        self.assertGap(d, "authority-gap")

    def test_owner_reference_unresolved(self):
        d = self.doc()
        d["accounts"][0]["owner_ids"] = ["UNKNOWN"]
        self.assertGap(d, "identity-gap")

    def test_missing_and_expired_document(self):
        d = self.doc()
        d["documents"].pop()
        self.assertGap(d, "document-gap")
        d = self.doc()
        d["documents"][0]["valid_until"] = "2026-09-15"
        self.assertGap(d, "document-gap")

    def test_conflicting_document_is_not_silently_overridden(self):
        d = self.doc()
        d["documents"].append({**d["documents"][0], "document_id": "CONFLICT", "status": "conflict"})
        self.assertGap(d, "document-gap")

    def test_declined_consent(self):
        d = self.doc()
        d["consents"][0]["status"] = "declined"
        self.assertGap(d, "consent-gap")

    def test_external_match_pending(self):
        d = self.doc()
        d["external_reviews"][0]["status"] = "escalated"
        self.assertGap(d, "external-review-gap")

    def test_completed_review_with_negative_outcome_remains_gap(self):
        d = self.doc()
        d["external_reviews"][0]["outcome"] = "rejected-by-owner"
        self.assertGap(d, "external-review-gap")

    def test_review_wrong_owner_scope(self):
        d = self.doc()
        d["external_reviews"][0]["party_ids"] = []
        self.assertGap(d, "external-review-gap")

    def test_no_universal_ria_aml_requirement(self):
        d = self.doc()
        self.assertEqual(compute(d)["status"], "review-ready")
        d["policy"]["external_review_requirements"]["kyc"] = {
            "required": True,
            "rationale": "Firm policy requires an external outcome",
        }
        self.assertGap(d, "external-review-gap")

    def test_applicability_is_explicit_not_inferred(self):
        d = self.doc()
        d["policy"]["external_review_requirements"].pop("kyc")
        self.assertGap(d, "policy-gap")

    def test_missing_applicability_does_not_hide_known_required_reviews(self):
        d = self.doc()
        d["policy"]["external_review_requirements"].pop("beneficial-ownership")
        d["policy"]["external_review_requirements"]["kyc"] = {
            "required": True,
            "rationale": "Supplied firm policy requires specialist outcome",
        }
        d["external_reviews"] = [
            {
                **d["external_reviews"][0],
                "kind": "kyc",
                "status": "pending",
                "outcome": "unresolved",
            }
        ]
        out = self.assertGap(d, "policy-gap")
        messages = [f["message"] for f in out["findings"] if f["code"] == "external-review-gap"]
        self.assertTrue(any("kyc is pending" in m for m in messages))
        self.assertTrue(any("sanctions outcome not supplied" in m for m in messages))

    def test_malformed_applicability_does_not_hide_other_required_review(self):
        d = self.doc()
        d["policy"]["external_review_requirements"]["beneficial-ownership"] = None
        d["external_reviews"] = []
        out = self.assertGap(d, "policy-gap")
        self.assertTrue(any("sanctions outcome not supplied" in f["message"] for f in out["findings"]))

    def test_mismatched_professional_capacity(self):
        d = self.doc()
        d["engagement"]["capacity"] = "trust"
        self.assertGap(d, "policy-scope")

    def test_empty_domain_is_needs_data(self):
        d = {
            k: v
            for k, v in self.doc().items()
            if k in ("schema_version", "request_id", "household_id", "as_of", "engagement", "sources")
        }
        self.assertGap(d, "policy-gap")

    def test_duplicate_record_id_rejected(self):
        d = self.doc()
        d["parties"].append(copy.deepcopy(d["parties"][0]))
        with self.assertRaises(ValueError):
            compute(d)

    def test_unknown_document_source(self):
        d = self.doc()
        d["documents"][0]["source_ids"] = ["UNKNOWN"]
        self.assertGap(d, "source-gap")

    def test_stale_and_future_sources_rejected(self):
        for field, value in (("valid_until", "2026-09-15"), ("as_of", "2026-09-17")):
            d = self.doc()
            d["sources"][0][field] = value
            with self.assertRaises(ValueError):
                compute(d)

    def test_external_owner_reference_required(self):
        d = self.doc()
        d["external_reviews"][0].pop("owner_reference")
        self.assertGap(d, "external-review-gap")

    def test_unsupported_jurisdiction_rejected(self):
        d = self.doc()
        d["engagement"]["jurisdiction"] = "UK"
        with self.assertRaises(ValueError):
            compute(d)

    def test_empty_output_and_false_ready_rejected(self):
        self.assertTrue(validate({}))
        d = self.doc()
        d["documents"] = []
        out = compute(d)
        out["status"] = "review-ready"
        out["findings"] = []
        self.assertTrue(validate(out))

    def test_input_bound_identity_changes(self):
        d = self.doc()
        first = compute(d)
        d["relationship"]["service_scope"] = "Revised scope"
        self.assertNotEqual(first["artifact_id"], compute(d)["artifact_id"])

    def test_action_and_delivery_claims_rejected(self):
        for field, value in (("action_taken", True), ("delivery_status", "sent"), ("human_review_required", False)):
            out = compute(self.doc())
            out[field] = value
            self.assertTrue(validate(out))

    def test_client_facing_narrative_cannot_bypass_draft_boundary(self):
        out = compute(self.doc())
        out["narrative"] = "Your account is approved and opened."
        self.assertTrue(validate(out))


if __name__ == "__main__":
    unittest.main(verbosity=2)
