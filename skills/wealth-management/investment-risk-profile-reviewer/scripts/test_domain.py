"""Regression tests for separate risk dimensions and meaningful consistency checks."""
import copy
import json
from pathlib import Path
import unittest

from domain import compute, validate_input, validate_output

FILES = Path(__file__).resolve().parents[1] / "evals/files"


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((FILES / "request_example.json").read_text())

    def test_independent_dimensions_and_known_arithmetic(self):
        pack = compute(self.doc)
        self.assertEqual(pack["status"], "review-ready")
        self.assertEqual(len(pack["result"]["dimensions"]), 6)
        self.assertEqual(pack["result"]["metrics"], {"capacity_loss_pct": 20, "willingness_loss_amount": 150000,
                                                  "liquidity_shortfall": 0})
        self.assertIsNone(pack["result"]["assigned_risk_rating"])
        self.assertEqual(validate_output(pack), [])

    def test_conflicts_survive_and_no_rating_is_chosen(self):
        pack = compute(json.loads((FILES / "request_conflicts.json").read_text()))
        codes = {f["code"] for f in pack["findings"]}
        self.assertTrue({"willingness_capacity_conflict", "liquidity_shortfall", "exposure_capacity_conflict",
                         "horizon_lockup_conflict", "liquidity_lockup_conflict", "experience_review"} <= codes)
        self.assertEqual(pack["status"], "needs-data")
        self.assertIsNone(pack["result"]["assigned_risk_rating"])
        self.assertEqual(validate_output(pack), [])

    def test_missing_horizon_and_method_approval_unresolved(self):
        pack = compute(json.loads((FILES / "request_missing_facts.json").read_text()))
        self.assertEqual(pack["status"], "needs-data")
        self.assertIn("missing_dimension", {f["code"] for f in pack["findings"]})
        self.assertIn("method_approval", {f["code"] for f in pack["findings"]})

    def test_no_source_no_recorded_dimension(self):
        self.doc["dimensions"]["willingness"]["source_ids"] = ["INVENTED"]
        out = compute(self.doc)
        self.assertEqual(out["result"]["dimensions"][0]["status"], "incomplete")

    def test_finite_numbers_and_booleans_not_numbers(self):
        for value in (float("nan"), float("inf"), True, "100"):
            doc = copy.deepcopy(self.doc)
            doc["dimensions"]["loss_capacity"]["investable_assets"] = value
            self.assertTrue(validate_input(doc))

    def test_zero_assets_and_capacity_exceeds_assets_unresolved(self):
        for assets in (0, 100000):
            doc = copy.deepcopy(self.doc)
            doc["dimensions"]["loss_capacity"]["investable_assets"] = assets
            self.assertEqual(compute(doc)["status"], "needs-data")

    def test_currency_mismatch_prevents_loss_comparison(self):
        self.doc["proposed_exposure"]["currency"] = "EUR"
        out = compute(self.doc)
        self.assertIn("currency_mismatch", {f["code"] for f in out["findings"]})

    def test_constraints_none_attestation_is_required(self):
        self.doc["dimensions"]["constraints"]["items"] = []
        self.assertEqual(compute(self.doc)["status"], "needs-data")
        self.doc["dimensions"]["constraints"]["none_identified"] = True
        self.assertEqual(compute(self.doc)["status"], "review-ready")

    def test_stale_registry_invalid_and_future_assessment_unresolved(self):
        doc = copy.deepcopy(self.doc)
        doc["sources"][0]["valid_until"] = "2026-09-12"
        self.assertTrue(validate_input(doc))
        self.doc["dimensions"]["horizon"]["recorded_on"] = "2026-09-17"
        self.assertEqual(compute(self.doc)["status"], "needs-data")

    def test_missing_all_dimensions_does_not_default_to_moderate(self):
        self.doc["dimensions"] = {}
        self.doc.pop("proposed_exposure")
        out = compute(self.doc)
        self.assertEqual(len(out["findings"]), 6)
        self.assertEqual(out["status"], "needs-data")
        self.assertIsNone(out["result"]["assigned_risk_rating"])

    def test_output_omission_false_rating_and_metric_tampering_rejected(self):
        for key in ("dimension", "metric", "rating", "findings"):
            out = compute(json.loads((FILES / "request_conflicts.json").read_text()))
            if key == "dimension":
                out["result"]["dimensions"].pop()
            elif key == "metric":
                out["result"]["metrics"]["capacity_loss_pct"] = 99
            elif key == "rating":
                out["result"]["assigned_risk_rating"] = "aggressive"
            else:
                out["findings"] = []
                out["status"] = "review-ready"
            self.assertTrue(validate_output(out))

    def test_empty_output_rejected(self):
        self.assertTrue(validate_output({}))


if __name__ == "__main__":
    unittest.main()
