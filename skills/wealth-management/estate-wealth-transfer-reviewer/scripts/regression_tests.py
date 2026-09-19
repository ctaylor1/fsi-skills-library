#!/usr/bin/env python3
"""Executable regressions with independent business expectations, not just shape checks."""
import copy
import json
import unittest
import os
import subprocess
import sys
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

    def test_actual_schedule_preserved(self):
        row = build(self.doc)["result"]["asset_comparisons"][0]
        self.assertEqual(row["asset_id"], "IRA-1")
        self.assertEqual(row["recorded_designations"][0]["beneficiaries"][0]["party_id"], "P2")
        self.assertEqual(row["literal_differences"], [])
        self.assertEqual(row["legal_effect"], "not-determined")

    def test_literal_difference_and_no_normalization(self):
        self.doc["intentions"][0]["beneficiaries"][0]["party_id"] = "P3"
        self.doc["intentions"][0]["beneficiaries"][0]["share"] = 0.6
        self.assertIn("coordination-difference", self.codes())
        self.assertIn("allocation-total", self.codes())
        out = build(self.doc)
        self.assertEqual(out["result"]["asset_comparisons"][0]["intentions"][0]["beneficiaries"][0]["share"], 0.6)

    def test_equivalent_numeric_share_not_difference(self):
        self.doc["intentions"][0]["beneficiaries"][0]["share"] = 1.0
        self.assertNotIn("coordination-difference", self.codes())

    def test_competing_current_designation_never_chosen(self):
        another = copy.deepcopy(self.doc["designations"][0])
        another["designation_id"] = "B2"
        another["beneficiaries"][0]["party_id"] = "P3"
        self.doc["designations"].append(another)
        self.assertIn("designation-conflict", self.codes())
        self.assertEqual(len(build(self.doc)["result"]["asset_comparisons"][0]["recorded_designations"]), 2)

    def test_missing_beneficiary_sources_and_unknown_links(self):
        self.doc["designations"][0]["beneficiaries"][0]["source_ids"] = []
        self.doc["assets"][0]["owner_party_ids"] = ["unknown"]
        self.assertTrue({"evidence-gap", "unknown-party"}.issubset(self.codes()))

    def test_unknown_intention_not_none(self):
        self.doc["intentions"][0]["beneficiaries"] = None
        self.assertIn("beneficiary-intention-unknown", self.codes())

    def test_duplicate_and_bad_share_rejected(self):
        self.doc["parties"].append(copy.deepcopy(self.doc["parties"][0]))
        self.assertTrue(validate(self.doc))
        self.doc["parties"].pop()
        self.doc["intentions"][0]["beneficiaries"][0]["share"] = True
        self.assertTrue(validate(self.doc))

    def test_substantive_tamper_rejected(self):
        out = build(self.doc)
        out["result"]["asset_comparisons"][0]["recorded_designations"][0]["beneficiaries"][0]["share"] = 0.4
        self.assertTrue(validate_output(out))


    def test_cross_process_tier_finding_order(self):
        self.doc["designations"][0]["beneficiaries"][0]["share"] = 0.5
        self.doc["designations"][0]["beneficiaries"][1]["share"] = 0.5
        code = "import sys,json; sys.path.insert(0,'scripts'); from domain import build; print(json.dumps(build(json.load(sys.stdin)),sort_keys=True))"
        outputs = []
        for seed in (0, 1, 37, 112):
            proc = subprocess.run([sys.executable, "-B", "-c", code], input=json.dumps(self.doc), text=True,
                                  capture_output=True, cwd=FILES.parents[1], env=dict(os.environ, PYTHONHASHSEED=str(seed)))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            outputs.append(proc.stdout)
        self.assertTrue(all(value == outputs[0] for value in outputs))
        self.assertEqual(validate_output(json.loads(outputs[0])), [])

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Checks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("specialist regression checks passed")
    raise SystemExit(not result.wasSuccessful())
