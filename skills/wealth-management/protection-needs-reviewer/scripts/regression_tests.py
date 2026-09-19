#!/usr/bin/env python3
"""Executable regressions with independent business expectations, not just shape checks."""
import copy
import json
import unittest
from pathlib import Path
from domain import build, validate, validate_output

FILES = Path(__file__).resolve().parents[1] / "evals/files"


class Checks(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((FILES / "request.json").read_text())

    def codes(self, doc=None):
        return {f["code"] for f in build(doc or self.doc)["findings"]}

    def test_golden_output_and_posture(self):
        out = build(self.doc)
        self.assertEqual(out, json.loads((FILES / "output.json").read_text()))
        self.assertEqual(validate_output(out), [])
        self.assertEqual(out["status"], "review-ready")
        self.assertIs(out["action_taken"], False)
        self.assertIs(out["human_review_required"], True)
        self.assertEqual(out["delivery_status"], "not-delivered")

    def test_stale_and_future_registry_rejected(self):
        self.doc["sources"][0]["valid_until"] = "2026-09-01"
        self.assertTrue(validate(self.doc))
        self.doc["sources"][0]["valid_until"] = "2026-12-31"
        self.doc["sources"][0]["as_of"] = "2026-09-17"
        self.assertTrue(validate(self.doc))

    def test_scope_mismatch_and_malformed_capacity(self):
        self.doc["policy"]["capacity"] = "brokerage"
        self.assertTrue(validate(self.doc))
        self.doc["engagement"]["capacity"] = []
        self.assertTrue(validate(self.doc))

    def test_upstream_issue_propagates(self):
        self.doc["upstream_issues"] = [{"artifact_id": "previous-case", "code": "unverified", "message": "Evidence conflict unresolved", "status": "unresolved", "source_ids": ["records"]}]
        out = build(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertIn("upstream-unresolved", self.codes())
        self.assertEqual(out["result"]["upstream_issues"], self.doc["upstream_issues"])
        self.assertEqual(validate_output(out), [])

    def test_nonfinite_input_rejected(self):
        self.doc["untrusted_extension"] = float("nan")
        self.assertTrue(validate(self.doc))

    def test_tamper_identity_findings_and_content(self):
        out = build(self.doc)
        for key, value in (("household_id", "another-household"), ("action_taken", True), ("input_hash", "0" * 64)):
            bad = copy.deepcopy(out)
            bad[key] = value
            self.assertTrue(validate_output(bad))
        bad = copy.deepcopy(out)
        bad["result"]["invented_approval"] = "approved"
        self.assertTrue(validate_output(bad))

    def test_incomplete_fixture_retained(self):
        doc = json.loads((FILES / "missing.json").read_text())
        out = build(doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(out["result"]["input_snapshot"], doc)
        self.assertEqual(validate_output(out), [])

    def test_four_independent_arithmetic_expectations(self):
        rows = build(self.doc)["result"]["scenarios"]
        expected = [("620000.00", "300000.00", "220000.00"), ("96000.00", "63000.00", "23000.00"), ("360000.00", "180000.00", "130000.00"), ("1600000.00", "1300000.00", "200000.00")]
        for row, amounts in zip(rows, expected):
            calc = row["calculation"]
            self.assertEqual((calc["gross_scenario_need"], calc["modeled_insurance_offset"], calc["remaining_scenario_gap"]), amounts)
        self.assertIsNone(build(self.doc)["result"]["portfolio_total"])

    def test_waiting_period_longer_than_event(self):
        self.doc["scenarios"][1]["assumptions"]["waiting_months"] = 36
        result = build(self.doc)["result"]["scenarios"][1]["calculation"]
        self.assertEqual(result["modeled_insurance_offset"], "0.00")
        self.assertEqual(result["remaining_scenario_gap"], "86000.00")

    def test_missing_cap_or_sources_suppresses_calculation(self):
        self.doc["scenarios"][2]["assumptions"]["lifetime_benefit_cap"] = None
        self.doc["scenarios"][0]["assumptions"]["source_ids"] = ["nonexistent"]
        out = build(self.doc)
        self.assertIsNone(out["result"]["scenarios"][0]["calculation"])
        self.assertIsNone(out["result"]["scenarios"][2]["calculation"])
        self.assertTrue({"unknown-assumption", "evidence-gap"}.issubset(self.codes()))

    def test_uncertain_resources_and_shared_resources(self):
        self.doc["scenarios"][1]["designated_resources"][0]["resource_id"] = "R1"
        out = build(self.doc)
        self.assertEqual(out["result"]["resource_reuse"][0]["scenario_ids"], ["S1", "S2"])
        self.doc["scenarios"][0]["designated_resources"][0]["availability"] = "uncertain"
        self.assertIsNone(build(self.doc)["result"]["scenarios"][0]["calculation"])

    def test_zero_is_distinct_from_missing(self):
        self.doc["scenarios"][0]["assumptions"]["life_benefit"] = 0
        result = build(self.doc)["result"]["scenarios"][0]["calculation"]
        self.assertEqual(result["remaining_scenario_gap"], "520000.00")
        self.assertEqual(result["modeled_insurance_offset"], "0.00")

    def test_negative_bool_duplicate_and_fractional_months_rejected(self):
        for value in (-1, True, 1.5):
            bad = copy.deepcopy(self.doc)
            bad["scenarios"][1]["assumptions"]["waiting_months"] = value
            self.assertTrue(validate(bad))
        self.doc["scenarios"][0]["designated_resources"].append(copy.deepcopy(self.doc["scenarios"][0]["designated_resources"][0]))
        self.assertTrue(validate(self.doc))

    def test_missing_required_type_and_tampered_calculation(self):
        self.doc["scenarios"].pop()
        self.assertIn("missing-scenario-type", self.codes())
        out = build(self.doc)
        out["result"]["scenarios"][0]["calculation"]["remaining_scenario_gap"] = "0.00"
        self.assertTrue(validate_output(out))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Checks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("specialist regression checks passed")
    raise SystemExit(not result.wasSuccessful())
