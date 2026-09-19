"""Regression tests for evidence completeness and source-bound review artifacts."""
import copy
import json
from pathlib import Path
import unittest

from domain import CHECK_ITEMS, compute, validate_input, validate_output

FILES = Path(__file__).resolve().parents[1] / "evals/files"


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((FILES / "request_example.json").read_text())

    def test_complete_review_has_exact_inventory_and_no_determination(self):
        pack = compute(self.doc)
        self.assertEqual(pack["status"], "review-ready")
        self.assertEqual(pack["result"]["counts"], {"documented": 9, "missing": 0, "incomplete": 0, "not-applicable": 2})
        self.assertEqual({c["check_id"] for c in pack["result"]["checks"]}, set(CHECK_ITEMS))
        self.assertEqual(pack["result"]["determination"], "not-made")
        self.assertEqual(validate_output(pack), [])

    def test_profile_reviewer_cannot_fill_unknown_evidence_review(self):
        record = self.doc["evidence"][0]
        record["reviewed_by"] = None
        record["recorded_on"] = None
        pack = compute(self.doc)
        self.assertEqual(pack["status"], "needs-data")
        check = next(c for c in pack["result"]["checks"] if c["check_id"] == record["check_id"])
        self.assertEqual(check["status"], "incomplete")
        self.assertTrue(any("reviewer is missing" in issue for issue in check["issues"]))
        self.assertTrue(any("dated evidence is missing" in issue for issue in check["issues"]))
        saved = pack["result"]["input_snapshot"]["evidence"][0]
        self.assertIsNone(saved["reviewed_by"])
        self.assertIsNone(saved["recorded_on"])
        self.assertEqual(validate_output(pack), [])

    def test_cost_conflict_supervision_absence_never_ready(self):
        pack = compute(json.loads((FILES / "request_missing_evidence.json").read_text()))
        self.assertEqual(pack["status"], "needs-data")
        self.assertEqual({c["check_id"] for c in pack["result"]["checks"] if c["status"] == "missing"},
                         {"costs", "conflicts", "supervision"})
        self.assertEqual(len(pack["findings"]), 3)
        self.assertEqual(validate_output(pack), [])

    def test_empty_output_rejected(self):
        self.assertTrue(validate_output({"checks": [], "disposition": "Evidence-complete"}))

    def test_deleted_check_or_findings_rejected(self):
        for mutation in ("check", "finding"):
            pack = compute(json.loads((FILES / "request_missing_evidence.json").read_text()))
            if mutation == "check":
                pack["result"]["checks"].pop()
            else:
                pack["findings"] = []
                pack["status"] = "review-ready"
            self.assertTrue(validate_output(pack))

    def test_disclosure_after_policy_deadline_is_unresolved(self):
        pack = compute(json.loads((FILES / "request_late_disclosure.json").read_text()))
        check = next(c for c in pack["result"]["checks"] if c["check_id"] == "disclosures")
        self.assertEqual(check["status"], "incomplete")
        self.assertEqual(pack["status"], "needs-data")

    def test_item_source_cannot_be_fabricated_or_missing(self):
        for ids in ([], ["NONEXISTENT"], ["ANALYSIS", "ANALYSIS"]):
            doc = copy.deepcopy(self.doc)
            doc["evidence"][0]["items"][0]["source_ids"] = ids
            pack = compute(doc)
            self.assertEqual(pack["status"], "needs-data")
            self.assertNotIn("?@", json.dumps(pack))

    def test_wrong_recommendation_evidence_is_unresolved(self):
        self.doc["evidence"][0]["items"][0]["subject_id"] = "OTHER"
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_regime_mismatch_needs_human_profile(self):
        self.doc["applicability"]["basis"] = "brokerage_reg_bi"
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_retirement_requires_current_applicability_and_comparison(self):
        self.doc["recommendation"]["action"] = "rollover"
        self.doc["applicability"]["context"] = "retirement"
        out = compute(self.doc)
        missing = {c["check_id"] for c in out["result"]["checks"] if c["status"] == "missing"}
        self.assertEqual(missing, {"rollover_comparison", "retirement_applicability"})

    def test_stale_registry_and_unknown_jurisdiction_rejected(self):
        for mutation in ("stale", "jurisdiction"):
            doc = copy.deepcopy(self.doc)
            if mutation == "stale":
                doc["sources"][0]["valid_until"] = "2026-09-12"
            else:
                doc["engagement"]["jurisdiction"] = "GB"
            self.assertTrue(validate_input(doc))

    def test_typed_inventory_rejects_duplicate_unknown_and_malformed(self):
        for value in ("invented_check", {}, None):
            doc = copy.deepcopy(self.doc)
            doc["evidence"][0]["check_id"] = value
            self.assertTrue(validate_input(doc))
        self.doc["evidence"].append(copy.deepcopy(self.doc["evidence"][0]))
        self.assertTrue(validate_input(self.doc))

    def test_boolean_only_does_not_replace_item_level_evidence(self):
        self.doc["evidence"][0]["items"] = []
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_upstream_risk_concerns_override_documented_assessment(self):
        doc = json.loads((FILES / "request_unresolved_risk.json").read_text())
        pack = compute(doc)
        record = next(x for x in doc["evidence"] if x["check_id"] == "customer_alignment")
        check = next(x for x in pack["result"]["checks"] if x["check_id"] == "customer_alignment")
        self.assertEqual(record["assessment"], "documented")
        self.assertEqual(check["status"], "incomplete")
        self.assertEqual(check["unresolved_issues"], record["unresolved_issues"])
        self.assertEqual(pack["status"], "needs-data")
        self.assertEqual(validate_output(pack), [])

    def test_removed_upstream_concerns_rejected_in_output_or_snapshot(self):
        doc = json.loads((FILES / "request_unresolved_risk.json").read_text())
        for mutation in ("result", "findings", "snapshot"):
            pack = compute(doc)
            if mutation == "result":
                check = next(x for x in pack["result"]["checks"] if x["check_id"] == "customer_alignment")
                check["unresolved_issues"] = []
            elif mutation == "findings":
                pack["findings"] = []
                pack["status"] = "review-ready"
            else:
                record = next(x for x in pack["result"]["input_snapshot"]["evidence"]
                              if x["check_id"] == "customer_alignment")
                record["unresolved_issues"] = []
            self.assertTrue(validate_output(pack), mutation)

    def test_unresolved_issue_list_and_structural_fields_required(self):
        issue = {"code": "source-conflict", "message": "Professional review has not resolved the conflict",
                 "source_ids": ["CLIENT"], "origin": "source-review"}
        for mutation in ("missing-list", "null-list", "non-object", "code", "message", "source_ids", "origin"):
            doc = copy.deepcopy(self.doc)
            record = doc["evidence"][0]
            record["unresolved_issues"] = [copy.deepcopy(issue)]
            if mutation == "missing-list":
                del record["unresolved_issues"]
            elif mutation == "null-list":
                record["unresolved_issues"] = None
            elif mutation == "non-object":
                record["unresolved_issues"] = ["concern"]
            else:
                del record["unresolved_issues"][0][mutation]
            self.assertTrue(validate_input(doc), mutation)

    def test_upstream_artifact_reference_is_required_and_typed(self):
        base = json.loads((FILES / "request_unresolved_risk.json").read_text())
        for value in (None, {}, {"skill": "risk", "artifact_id": "A", "input_hash": "not-a-hash"}):
            doc = copy.deepcopy(base)
            record = next(x for x in doc["evidence"] if x["check_id"] == "customer_alignment")
            record["unresolved_issues"][0]["upstream_artifact"] = value
            self.assertTrue(validate_input(doc))

    def test_source_review_concerns_and_unknown_citations_remain_unresolved(self):
        self.doc["evidence"][0]["unresolved_issues"] = [
            {"code": "unresolved-capacity", "message": "Capacity statement conflicts with cash needs",
             "source_ids": ["UNKNOWN"], "origin": "source-review"}]
        pack = compute(self.doc)
        self.assertEqual(pack["status"], "needs-data")
        self.assertTrue(any("UNKNOWN" in f["message"] for f in pack["findings"]))
        self.assertEqual(validate_output(pack), [])

    def test_conditional_inapplicability_cannot_suppress_recorded_concern(self):
        self.doc["evidence"].append({
            "check_id": "retirement_applicability", "assessment": "documented", "items": [],
            "reviewed_by": "human", "recorded_on": "2026-09-15", "source_ids": ["POLICY"],
            "unresolved_issues": [{"code": "retirement-context-disputed", "message": "Context requires review",
                                   "source_ids": ["POLICY"], "origin": "source-review"}]})
        pack = compute(self.doc)
        check = next(x for x in pack["result"]["checks"] if x["check_id"] == "retirement_applicability")
        self.assertEqual(check["status"], "incomplete")
        self.assertEqual(pack["status"], "needs-data")

    def test_hash_and_action_claim_tampering_rejected(self):
        pack = compute(self.doc)
        pack["result"]["determination"] = "approved"
        pack["action_taken"] = True
        self.assertTrue(validate_output(pack))
        changed = copy.deepcopy(self.doc)
        changed["applicability"]["version"] = "new-version"
        self.assertNotEqual(pack["input_hash"], compute(changed)["input_hash"])


if __name__ == "__main__":
    unittest.main()
