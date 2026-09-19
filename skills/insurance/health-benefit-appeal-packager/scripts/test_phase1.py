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
    return json.loads((ROOT / "evals/files/denial_example.json").read_text())


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

    def test_document_type_never_proves_plan_criteria(self):
        d = fixture()
        d["reason_evidence"] = []
        o = compute(d)
        self.assertTrue(all(not a["argument_points"] for a in o["appeal_arguments"]))
        self.assertEqual("gaps_present", o["readiness"])

    def test_unrelated_policy_not_attached_to_every_reason(self):
        o = compute(fixture())
        self.assertEqual([], o["appeal_arguments"][1]["supporting_policy_refs"])

    def test_nonhealth_rejected(self):
        d = fixture()
        d["insurance_segment"] = "property_casualty"
        self.assertTrue(input_check.validate(d)[0])

    def test_unknown_reason_requires_review(self):
        d = fixture()
        d["denial_reasons"][0]["code"] = "new-plan-reason"
        self.assertIn("reason_code_requires_plan_specific_review", compute(d)["appeal_arguments"][0]["evidence_gaps"])

    def test_receipt_date_deadline_uses_supplied_basis(self):
        d = fixture()
        d["deadline_basis"].update(start_event="receipt_date", start_date="2026-06-10")
        o = compute(d)
        self.assertEqual("2026-12-07", o["appeal_deadline"])
        self.assertEqual([], output_check.validate(o))

    def test_unsupported_argument_rejected_even_resealed(self):
        o = compute(fixture())
        a = o["appeal_arguments"][1]
        a["argument_points"] = ["Please reconsider based on the attached file."]
        self.assertTrue(output_check.validate(reseal(o)))


if __name__ == "__main__":
    unittest.main()
