#!/usr/bin/env python3
"""Behavioral regressions for Phase 1 contracts and domain boundary cases."""

import copy
import json
import unittest
from pathlib import Path

import calculate_or_transform as engine
import validate_input as input_check
import validate_output as output_check
from insurance_contract import stable_hash, validate_artifact

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "evals/files/claim_example.json").read_text())


def compute(doc):
    return engine.compute(doc)


def reseal(output):
    output["artifact"]["output_hash"] = stable_hash({k: v for k, v in output.items() if k != "artifact"})
    output["artifact"]["artifact_hash"] = stable_hash(
        {k: v for k, v in output["artifact"].items() if k != "artifact_hash"}
    )
    return output


class Phase1(unittest.TestCase):
    def test_native_contract_and_determinism(self):
        doc = fixture()
        first = compute(doc)
        self.assertEqual(first, compute(copy.deepcopy(doc)))
        self.assertEqual([], output_check.validate(first))
        self.assertEqual([], validate_artifact(first["artifact"], input_doc=doc, output=first))
        self.assertEqual("not_requested", first["artifact"]["approval"])
        self.assertEqual("not_performed", first["artifact"]["execution"])
        changed = copy.deepcopy(doc)
        changed["sources"][0]["version"] = "another-version"
        self.assertNotEqual(first["artifact"]["artifact_hash"], compute(changed)["artifact"]["artifact_hash"])

    def test_inherited_unknown_cannot_be_complete(self):
        doc = fixture()
        doc["unresolved_issues"] = ["source completeness not independently confirmed"]
        result = compute(doc)
        self.assertIn(doc["unresolved_issues"][0], result["artifact"]["unresolved_issues"])
        result["artifact"]["approval"] = "approved"
        self.assertTrue(output_check.validate(result))

    def test_malformed_input_fails_without_traceback(self):
        self.assertTrue(input_check.validate([])[0])
        self.assertTrue(output_check.validate([]))

    def ready(self):
        d = fixture()
        d["coverage_confirmation"] = True
        d["coverage_source_ref"] = "synthetic:coverage-review-1"
        return d

    def test_ready_request_selects_smallest_valid_tier(self):
        o = compute(self.ready())
        self.assertEqual(2, o["required_authority_tier"])
        self.assertEqual("packet-ready", o["suggested_disposition"])

    def test_wrong_tier_rejected_independently(self):
        o = compute(self.ready())
        o["required_authority_tier"] = 1
        o["required_approver"] = "senior_adjuster"
        self.assertTrue(output_check.validate(reseal(o)))

    def test_missing_amount_not_zero(self):
        d = self.ready()
        d["evaluation"]["expense_estimate"] = None
        self.assertTrue(input_check.validate(d)[0])
        with self.assertRaises(ValueError):
            compute(d)

    def test_bool_and_infinite_amount_rejected(self):
        for value in (True, float("inf"), float("nan")):
            d = self.ready()
            d["evaluation"]["expense_estimate"] = value
            self.assertTrue(input_check.validate(d)[0])

    def test_above_highest_cap_does_not_assign_highest_authority(self):
        d = self.ready()
        d["evaluation"]["indemnity_estimate"] = 2000000
        o = compute(d)
        self.assertTrue(o["exceeds_matrix"])
        self.assertIsNone(o["required_authority_tier"])

    def test_expired_matrix_and_incomplete_checklist_not_ready(self):
        d = self.ready()
        d["authority_matrix"]["effective_to"] = "2025-12-31"
        self.assertEqual("gaps-for-review", compute(d)["suggested_disposition"])


if __name__ == "__main__":
    unittest.main()
