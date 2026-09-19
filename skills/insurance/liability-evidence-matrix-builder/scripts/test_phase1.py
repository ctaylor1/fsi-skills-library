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

    def test_legacy_id_link_is_not_source_proof(self):
        d = fixture()
        d["evidence"][0].pop("relations")
        d["evidence"][0]["supports"] = ["F1"]
        o = compute(d)
        self.assertTrue(any(g["type"] == "unverified_legacy_relation" for g in o["gaps"]))

    def test_contrary_evidence_preserved_and_requires_review(self):
        o = compute(fixture())
        row = next(r for r in o["matrix"] if r["fact_id"] == "F2")
        self.assertEqual("contested", row["status"])
        self.assertTrue(row["contradicting"])
        self.assertEqual("gaps-for-review", o["suggested_disposition"])

    def test_false_supported_status_rejected_even_resealed(self):
        o = compute(fixture())
        o["matrix"][2]["status"] = "supported"
        self.assertTrue(output_check.validate(reseal(o)))

    def test_quote_preserves_fault_assertion_as_evidence(self):
        d = fixture()
        d["evidence"][0]["relations"][0]["source_quote"] = "The other driver was at fault and is liable."
        o = compute(d)
        self.assertEqual([], output_check.validate(o))
        self.assertIn("at fault", o["matrix"][0]["supporting"][0]["source_quote"])
        o["narrative"] = "The other driver is at fault and is liable."
        self.assertTrue(output_check.validate(reseal(o)))

    def test_missing_quote_does_not_support_fact(self):
        d = fixture()
        d["evidence"] = [d["evidence"][0]]
        d["evidence"][0]["relations"][0].pop("source_quote")
        self.assertEqual("unsupported", compute(d)["matrix"][0]["status"])


if __name__ == "__main__":
    unittest.main()
