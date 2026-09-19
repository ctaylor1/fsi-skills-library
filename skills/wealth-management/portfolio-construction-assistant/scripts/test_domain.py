"""Expected-value and boundary tests for model-constrained construction."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from domain import compute, validate_input, validate_output

FILES = Path(__file__).resolve().parents[1] / "evals/files"


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((FILES / "request_example.json").read_text())

    def test_cap_redistribution_expected_values(self):
        out = compute(self.doc)
        candidate = out["result"]["candidates"][0]
        weights = {h["security_id"]: h["weight"] for h in candidate["holdings"]}
        self.assertEqual(weights, {"A": 0.3, "B": 0.3, "C": 0.35})
        self.assertEqual(candidate["cash_amount"], 50000)
        self.assertEqual(sum(h["amount"] for h in candidate["holdings"]), 950000)
        self.assertEqual(out["status"], "review-ready")
        self.assertEqual(validate_output(out), [])

    def test_cross_process_allocation_determinism(self):
        weights = [0.3, 0.2, 0.17, 0.11, 0.09, 0.07, 0.06]
        self.doc["mandate"]["class_bands"] = [
            {"asset_class": "equity", "min_weight": 0.9, "max_weight": 0.9, "source_ids": ["POLICY"]}
        ]
        self.doc["models"][0]["cash_weight"] = 0.1
        self.doc["models"][0]["allocations"] = [
            {"security_id": f"S{i}", "weight": w * 0.9, "source_ids": ["FACTS"]} for i, w in enumerate(weights)
        ]
        self.doc["universe"] = [
            {
                "security_id": f"S{i}",
                "asset_class": "equity",
                "eligible": True,
                "max_weight": 0.1 if i < 2 else 0.4,
                "source_ids": ["FACTS"],
            }
            for i in range(len(weights))
        ]
        script = Path(__file__).with_name("calculate_or_transform.py")
        results = []
        for seed in ("1", "2", "3", "17", "111"):
            env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
            results.append(
                json.loads(
                    subprocess.check_output(
                        [sys.executable, "-B", str(script)], input=json.dumps(self.doc), text=True, env=env
                    )
                )
            )
        self.assertTrue(all(result == results[0] for result in results[1:]))

    def test_restriction_does_not_invent_cross_class_replacement(self):
        out = compute(json.loads((FILES / "request_infeasible.json").read_text()))
        c = out["result"]["candidates"][0]
        weights = {h["security_id"]: h["weight"] for h in c["holdings"]}
        self.assertEqual(weights, {"A": 0, "B": 0.5, "C": 0.35})
        self.assertAlmostEqual(c["unallocated_by_class"]["equity"], 0.1)
        self.assertEqual(c["cash_weight"], 0.05)
        self.assertEqual(out["status"], "needs-data")

    def test_multiple_models_generate_distinct_candidates(self):
        model = copy.deepcopy(self.doc["models"][0])
        model["model_id"] = "MODEL-2"
        model["allocations"][0]["weight"] = 0.3
        model["allocations"][1]["weight"] = 0.3
        self.doc["models"].append(model)
        self.assertEqual(len(compute(self.doc)["result"]["candidates"]), 2)

    def test_unknown_eligibility_never_allocated(self):
        self.doc["universe"][0]["eligible"] = None
        out = compute(self.doc)
        self.assertEqual(
            next(h["weight"] for h in out["result"]["candidates"][0]["holdings"] if h["security_id"] == "A"), 0
        )
        self.assertEqual(out["status"], "needs-data")

    def test_missing_cap_does_not_get_default(self):
        self.doc["universe"][0]["max_weight"] = None
        out = compute(self.doc)
        self.assertEqual(out["result"]["candidates"][0]["holdings"], [])
        self.assertEqual(out["status"], "needs-data")

    def test_unknown_value_remains_null(self):
        self.doc["portfolio_value"] = None
        out = compute(self.doc)
        self.assertIsNone(out["result"]["candidates"][0]["holdings"][0]["amount"])
        self.assertEqual(out["status"], "needs-data")

    def test_nonunit_model_never_normalized(self):
        self.doc["models"][0]["allocations"][0]["weight"] = 0.8
        out = compute(self.doc)
        self.assertEqual(out["result"]["candidates"][0]["holdings"], [])
        self.assertTrue(any(f["code"] == "model-total" for f in out["findings"]))

    def test_missing_approval_is_not_recorded_as_approved(self):
        self.doc["models"][0]["approval_record"] = {}
        out = compute(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertIsNone(out["result"]["selected_candidate"])

    def test_empty_and_absent_asset_class_band(self):
        self.doc["mandate"]["class_bands"].append(
            {"asset_class": "real-assets", "min_weight": 0.1, "max_weight": 0.2, "source_ids": ["POLICY"]}
        )
        out = compute(self.doc)
        self.assertTrue(any(f["code"] == "class-constraint" for f in out["findings"]))

    def test_inverted_bands_are_unresolved(self):
        self.doc["mandate"]["cash_min"] = 0.9
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_unknown_security_does_not_crash(self):
        self.doc["models"][0]["allocations"][0]["security_id"] = "MISSING"
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_duplicate_model_and_invalid_number_rejected(self):
        self.doc["models"].append(copy.deepcopy(self.doc["models"][0]))
        self.assertTrue(validate_input(self.doc))
        for value in (True, -1, float("nan"), "0.2"):
            doc = json.loads((FILES / "request_example.json").read_text())
            doc["universe"][0]["max_weight"] = value
            self.assertTrue(validate_input(doc))

    def test_stale_or_unknown_sources(self):
        self.doc["sources"][0]["valid_until"] = "2026-09-15"
        self.assertTrue(validate_input(self.doc))
        self.doc = json.loads((FILES / "request_example.json").read_text())
        self.doc["models"][0]["source_ids"] = ["UNKNOWN"]
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_output_tamper_and_changed_intent(self):
        original = compute(self.doc)
        for mutation in ("weight", "selected", "findings", "empty"):
            out = copy.deepcopy(original)
            if mutation == "weight":
                out["result"]["candidates"][0]["holdings"][0]["weight"] = 0.8
            elif mutation == "selected":
                out["result"]["selected_candidate"] = "candidate-MODEL-1"
            elif mutation == "findings":
                out["findings"] = [{"code": "fake", "message": "fake"}]
            else:
                out = {}
            self.assertTrue(validate_output(out))
        self.doc["mandate"]["owner"] = "changed-owner"
        self.assertNotEqual(original["input_hash"], compute(self.doc)["input_hash"])

    def test_upstream_structure_is_explicit_and_typed(self):
        for value in (
            None,
            {},
            ["issue"],
            [{"artifact_id": "A", "code": "risk", "message": "Open", "status": "approved", "source_ids": ["FACTS"]}],
        ):
            doc = copy.deepcopy(self.doc)
            doc["upstream_issues"] = value
            self.assertTrue(validate_input(doc))
        doc = copy.deepcopy(self.doc)
        del doc["upstream_issues"]
        self.assertTrue(validate_input(doc))

    def test_upstream_ownership_and_risk_issues_prevent_readiness(self):
        doc = copy.deepcopy(self.doc)
        if "policy" in doc and "max_issuer_weight" in doc["policy"]:
            doc["policy"]["max_issuer_weight"] = 1
        self.assertEqual(compute(doc)["status"], "review-ready")
        issue_doc = json.loads((FILES / "request_upstream_issues.json").read_text())
        doc["upstream_issues"] = issue_doc["upstream_issues"]
        out = compute(doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(
            {f["upstream_code"] for f in out["findings"] if f["code"] == "upstream-unresolved"},
            {"ownership-conflict", "risk-capacity-conflict"},
        )
        self.assertEqual(out["result"]["upstream_issues"], doc["upstream_issues"])
        self.assertEqual(out["result"]["handoff_context"]["upstream_issues"], doc["upstream_issues"])
        self.assertEqual(validate_output(out), [])
        if "candidates" in out["result"]:
            self.assertTrue(all(c["status"] == "needs-review" for c in out["result"]["candidates"]))
            self.assertTrue(
                all(any(f["code"] == "upstream-unresolved" for f in c["findings"]) for c in out["result"]["candidates"])
            )

    def test_resolved_upstream_records_retained_without_claiming_authentication(self):
        doc = copy.deepcopy(self.doc)
        if "policy" in doc and "max_issuer_weight" in doc["policy"]:
            doc["policy"]["max_issuer_weight"] = 1
        issue = {
            "artifact_id": "source-artifact",
            "code": "ownership-conflict",
            "message": "Source reviewer recorded resolution",
            "status": "resolved",
            "source_ids": ["FACTS"],
        }
        doc["upstream_issues"] = [issue]
        out = compute(doc)
        self.assertEqual(out["status"], "review-ready")
        self.assertEqual(out["result"]["upstream_issues"], [issue])
        self.assertFalse(out["action_taken"])

    def test_upstream_unknown_citation_remains_a_gap(self):
        doc = copy.deepcopy(self.doc)
        doc["upstream_issues"] = [
            {
                "artifact_id": "source-artifact",
                "code": "risk",
                "message": "Source claim requires evidence",
                "status": "resolved",
                "source_ids": ["MISSING"],
            }
        ]
        out = compute(doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertTrue(any(f["code"] == "source-gap" for f in out["findings"]))
        self.assertEqual(validate_output(out), [])

    def test_dropped_upstream_context_or_findings_rejected(self):
        doc = json.loads((FILES / "request_upstream_issues.json").read_text())
        for mutation in ("context", "issue-list", "findings"):
            out = compute(doc)
            if mutation == "context":
                out["result"]["handoff_context"]["upstream_issues"] = []
            elif mutation == "issue-list":
                out["result"]["upstream_issues"] = []
            else:
                out["findings"] = []
                out["status"] = "review-ready"
            self.assertTrue(validate_output(out))

    def test_unmapped_issue_schema_is_not_silently_ignored(self):
        self.doc["unresolved_issues"] = [{"code": "risk", "message": "Upstream concern", "source_ids": ["FACTS"]}]
        self.assertTrue(validate_input(self.doc))


if __name__ == "__main__":
    unittest.main()
