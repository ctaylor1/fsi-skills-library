"""Observable failure and financial/control boundary regressions."""

import json
from pathlib import Path
import unittest
from domain import evaluate, validate
from insurance_foundation import run, check_output

PRODUCER = "life-annuity-sales-reviewer"


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

    def test_missing_guarantees_appear(self):
        self.doc["data"]["product_evidence"] = [
            r for r in self.doc["data"]["product_evidence"] if r["topic"] != "guarantees"
        ]
        out = self.out()
        row = next(r for r in out["results"]["product_matrix"] if r["topic"] == "guarantees")
        self.assertEqual("missing-or-unresolved", row["status"])
        self.assertIsNone(row["value"])

    def test_replacement_unknown_not_no(self):
        self.doc["data"]["transaction"]["replacement_status"] = "unknown"
        self.assertEqual("needs-data", self.out()["status"])

    def test_no_replacement_still_requires_evidence(self):
        self.doc["data"]["transaction"]["replacement_status"] = "no"
        self.doc["data"]["transaction"].pop("replacement_source_ref")
        self.assertEqual("needs-data", self.out()["status"])

    def test_missing_replacement_cost(self):
        self.doc["data"]["replacement_evidence"] = [
            r for r in self.doc["data"]["replacement_evidence"] if r["topic"] != "existing-charges"
        ]
        self.assertEqual("needs-data", self.out()["status"])

    def test_model_is_not_enacted_law(self):
        self.doc["data"]["applicability"][0]["authority_type"] = "naic-model"
        self.assertEqual("unknown", self.out()["results"]["applicability_matrix"][0]["status"])

    def test_variable_annuity_rule_not_applied_to_life(self):
        self.doc["data"]["applicability"].append(dict(self.doc["data"]["applicability"][0], rule_id="finra-2330"))
        row = self.out()["results"]["applicability_matrix"][-1]
        self.assertEqual("unknown", row["status"])

    def test_stale_customer_evidence_not_accepted(self):
        self.doc["data"]["consumer_evidence"][0]["verified_on"] = "2025-01-01"
        self.assertEqual("needs-data", self.out()["status"])

    def test_conflicting_evidence_not_chosen(self):
        self.doc["data"]["consumer_evidence"].append(
            dict(self.doc["data"]["consumer_evidence"][0], value="Different stated need")
        )
        self.assertEqual("missing-or-unresolved", self.out()["results"]["consumer_matrix"][0]["status"])

    def test_alternatives_and_rationale_required(self):
        self.doc["data"]["alternatives"] = []
        self.doc["data"]["recommendation_rationale"] = {}
        self.assertEqual("needs-data", self.out()["status"])

    def test_no_suitability_score_or_approval(self):
        out = self.out()
        self.assertEqual("not-made", out["results"]["suitability_or_best_interest_decision"])
        self.assertEqual("not-performed", out["results"]["principal_approval"])
        self.assertNotIn("score", out["results"])


if __name__ == "__main__":
    unittest.main()
