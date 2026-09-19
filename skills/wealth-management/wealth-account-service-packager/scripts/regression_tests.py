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

    def test_four_requests_and_aggregate_cash(self):
        out = build(self.doc)
        self.assertEqual(len(out["result"]["service_packages"]), 4)
        self.assertEqual(out["result"]["aggregate_cash_requests"][0]["requested_cash_total"], "7500.00")
        self.assertEqual(out["result"]["submission_status"], "not-submitted")

    def test_individually_funded_requests_exceed_aggregate(self):
        self.doc["requests"][0]["details"]["amount"] = 8000
        self.assertIn("aggregate-cash-shortfall", self.codes())
        self.assertNotIn("cash-shortfall", self.codes())

    def test_in_kind_quantities_and_duplicate_combined_requests(self):
        r = self.doc["requests"][0]
        r["details"].update(method="in-kind", amount=None, positions=[{"security_id": "SEC1", "quantity": 70, "source_ids": ["records"]}])
        other = copy.deepcopy(r)
        other["service_request_id"] = "Q5"
        self.doc["requests"].append(other)
        self.assertIn("aggregate-position-shortfall", self.codes())
        r["details"]["positions"][0]["quantity"] = 101
        self.assertIn("position-data-gap", self.codes())

    def test_full_transfer_does_not_infer_or_liquidate(self):
        self.doc["requests"][0]["details"].update(transfer_scope="full", amount=None)
        self.assertIn("unknown-amount", self.codes())
        self.assertIn("full-cash-scope-review", self.codes())

    def test_uncited_condition_and_tax_unknown_remain_open(self):
        self.doc["conditions"][0]["source_ids"] = []
        self.doc["requests"][1]["details"]["tax_instruction_ref"] = None
        self.assertTrue({"condition-gap", "evidence-gap", "tax-instruction-gap"}.issubset(self.codes()))
        row = build(self.doc)["result"]["service_packages"][0]["condition_matrix"][0]
        self.assertIs(row["recorded"], False)

    def test_beneficiary_total_and_authority_replacement(self):
        self.doc["requests"][3]["details"]["beneficiaries"][0]["share"] = 0.5
        self.doc["requests"][2]["details"]["change"] = "replace"
        self.assertTrue({"beneficiary-total", "authority-replacement-gap"}.issubset(self.codes()))

    def test_ownership_change_and_unknown_cash(self):
        self.doc["requests"][0]["details"]["destination_owner_party_ids"] = ["P2"]
        self.doc["accounts"][0]["available_cash"] = None
        self.assertTrue({"ownership-change-review", "cash-data-gap"}.issubset(self.codes()))

    def test_duplicate_request_and_nonpositive_amount_rejected(self):
        self.doc["requests"][0]["details"]["amount"] = True
        self.assertTrue(validate(self.doc))
        self.doc["requests"][0]["details"]["amount"] = 0
        self.assertTrue(validate(self.doc))

    def test_substantive_cash_tamper_rejected(self):
        out = build(self.doc)
        out["result"]["aggregate_cash_requests"][0]["requested_cash_total"] = "1.00"
        self.assertTrue(validate_output(out))


    def test_cross_process_tier_finding_order(self):
        self.doc["requests"][3]["details"]["beneficiaries"] = [
            {"party_id": "P2", "tier": "primary", "share": 0.5, "source_ids": ["records"]},
            {"party_id": "P1", "tier": "contingent", "share": 0.5, "source_ids": ["records"]}]
        code = "import sys,json; sys.path.insert(0,'scripts'); from domain import build; print(json.dumps(build(json.load(sys.stdin)),sort_keys=True))"
        outputs = []
        for seed in (0, 1, 37, 112):
            proc = subprocess.run([sys.executable, "-B", "-c", code], input=json.dumps(self.doc), text=True,
                                  capture_output=True, cwd=FILES.parents[1], env=dict(os.environ, PYTHONHASHSEED=str(seed)))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            outputs.append(proc.stdout)
        self.assertTrue(all(value == outputs[0] for value in outputs))
        self.assertEqual(validate_output(json.loads(outputs[0])), [])

    def test_extra_conflicting_condition_cannot_be_review_ready(self):
        self.doc["conditions"].append({"condition_id": "EXTRA", "service_request_id": "Q1", "requirement": "destination-review", "status": "conflicting", "description": "Custodian destination records disagree", "source_ids": ["records"]})
        self.assertIn("condition-conflict", self.codes())
        self.assertEqual(build(self.doc)["status"], "needs-data")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Checks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("specialist regression checks passed")
    raise SystemExit(not result.wasSuccessful())
