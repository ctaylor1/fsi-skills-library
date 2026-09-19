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
    return json.loads((ROOT / "evals/files/fnol_example.json").read_text())


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

    def test_notice_receipt_survives_missing_support(self):
        d = fixture()
        d.pop("claim_package")
        o = compute(d)
        self.assertEqual("recorded", o["intake_states"]["receipt"])
        self.assertEqual("unknown", o["intake_states"]["completeness"])
        self.assertFalse(o["notice_receipt_blocked"])
        self.assertEqual("exceptions-for-review", o["suggested_disposition"])

    def test_unknown_chronology_not_ready(self):
        d = fixture()
        d["claim_package"]["dates"].pop("policy_effective")
        o = compute(d)
        self.assertEqual("Unknown", o["submission_assessment"]["readiness_status"])
        self.assertEqual("unknown", o["intake_states"]["timeliness"])

    def test_empty_requirements_do_not_assert_completeness(self):
        d = fixture()
        d["claim_package"]["config"].pop("requirements")
        self.assertEqual("Unknown", compute(d)["submission_assessment"]["readiness_status"])

    def test_receipt_requires_timezone(self):
        d = fixture()
        d["raw_fnol"]["receipt"]["received_at"] = "2026-07-12T10:00:00"
        self.assertEqual("unverified", compute(d)["intake_states"]["receipt"])

    def test_different_claim_package_requires_review(self):
        d = fixture()
        d["claim_package"]["fnol_id"] = "other-notification"
        self.assertEqual("Unknown", compute(d)["submission_assessment"]["readiness_status"])

    def test_unknown_forced_ready_is_rejected(self):
        o = compute(fixture())
        o["submission_assessment"]["not_evaluable"] = [{"check": "deadlines", "why": "unknown"}]
        o["submission_assessment"]["readiness_status"] = "Ready"
        self.assertTrue(output_check.validate(reseal(o)))


if __name__ == "__main__":
    unittest.main()
