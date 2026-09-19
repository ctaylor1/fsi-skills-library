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

    def test_five_dimensions_fee_and_liquidity_arithmetic(self):
        out = build(self.doc)["result"]
        self.assertEqual(set(out["diligence_by_dimension"]), {"investment", "operations", "fees", "liquidity", "evidence"})
        fees = out["fee_illustration"]
        self.assertEqual(fees["base_fee"], "10000.00")
        self.assertEqual(fees["incentive_fee"], "6000.00")
        self.assertEqual(fees["total_illustrated_fee"], "16000.00")
        self.assertEqual(fees["illustrated_net_gain"], "64000.00")
        self.assertEqual(out["household_liquidity_review"][1]["cumulative_amount"], "300000.00")
        self.assertEqual(out["monitoring_plan"]["next_scheduled_review"], "2026-12-15")
        self.assertEqual(out["selection_decision"], "not-made")

    def test_independent_requirement_and_manager_assertion(self):
        self.doc["evidence"][1]["origin"] = "manager-reported"
        out = build(self.doc)
        self.assertEqual(out["result"]["diligence_by_dimension"]["operations"][0]["result"], "not-evaluable")
        self.assertIn("diligence-data-gap", self.codes())

    def test_threshold_concern_and_missing_source(self):
        self.doc["evidence"][0]["value"] = 2
        self.doc["evidence"][2]["source_ids"] = ["unknown"]
        self.assertTrue({"diligence-concern", "evidence-gap", "diligence-data-gap"}.issubset(self.codes()))

    def test_duplicate_observations_and_old_observation_not_chosen(self):
        e = copy.deepcopy(self.doc["evidence"][0])
        e["evidence_id"] = "OTHER"
        e["value"] = 11
        self.doc["evidence"].append(e)
        self.doc["evidence"][1]["review_by"] = "2026-09-01"
        self.assertTrue({"diligence-data-gap", "evidence-date-gap"}.issubset(self.codes()))

    def test_fee_loss_no_incentive_and_missing_fee_not_zero(self):
        self.doc["fee_illustration"]["gross_return"] = -0.1
        calc = build(self.doc)["result"]["fee_illustration"]
        self.assertEqual(calc["incentive_fee"], "0.00")
        self.assertEqual(calc["illustrated_net_gain"], "-110000.00")
        self.doc["fee_illustration"]["other_bps"] = None
        self.assertIsNone(build(self.doc)["result"]["fee_illustration"])

    def test_liquidity_gate_late_settlement_and_cumulative_shortfall(self):
        self.doc["liquidity"]["gate_or_suspension_possible"] = True
        self.doc["liquidity"]["expected_settlement_date"] = "2026-11-15"
        self.doc["liquidity"]["amount_under_review"] = 250000
        self.assertTrue({"contingent-liquidity", "household-liquidity-concern"}.issubset(self.codes()))
        out = build(self.doc)["result"]["household_liquidity_review"]
        self.assertIs(out[0]["modeled_timing_fit"], False)
        self.assertIs(out[1]["modeled_amount_fit"], False)

    def test_unknown_prior_need_prevents_false_cumulative_fit(self):
        self.doc["household_liquidity_needs"][0]["amount"] = None
        rows = build(self.doc)["result"]["household_liquidity_review"]
        self.assertTrue(all(r["assessment"] == "not-evaluable" for r in rows))

    def test_malformed_operator_and_unsupported_fee_model(self):
        self.doc["policy"]["criteria"][0]["operator"] = []
        self.assertTrue(validate(self.doc))
        self.doc["policy"]["criteria"][0]["operator"] = "minimum"
        self.doc["fee_illustration"]["method"] = "high-water-mark"
        self.assertTrue(validate(self.doc))

    def test_substantive_fee_tamper_rejected(self):
        out = build(self.doc)
        out["result"]["fee_illustration"]["total_illustrated_fee"] = "0.00"
        self.assertTrue(validate_output(out))


    def test_documented_negative_boolean_is_a_concern(self):
        self.doc["evidence"][1]["value"] = False
        out = build(self.doc)
        self.assertEqual(out["result"]["diligence_by_dimension"]["operations"][0]["result"], "criterion-concern")
        self.assertIn("diligence-concern", self.codes())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Checks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("specialist regression checks passed")
    raise SystemExit(not result.wasSuccessful())
