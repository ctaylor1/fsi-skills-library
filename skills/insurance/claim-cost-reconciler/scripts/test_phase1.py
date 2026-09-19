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

    def test_distinct_provider_or_currency_never_duplicate(self):
        for field, value in (
            ("provider_id", "different-provider"),
            ("currency", "EUR"),
            ("service_date", "2026-06-29"),
            ("unit", "hour"),
            ("quantity", 2),
        ):
            d = fixture()
            d["line_items"][3][field] = value
            self.assertEqual(0, compute(d)["finding_counts"].get("duplicate", 0))

    def test_unknown_comparison_key_is_not_clean(self):
        d = fixture()
        d["line_items"][0].pop("provider_id")
        self.assertEqual("not-evaluable", compute(d)["suggested_disposition"])

    def test_document_reference_must_resolve(self):
        d = fixture()
        d["line_items"][0]["supported_by"] = "missing-document"
        self.assertGreater(compute(d)["finding_counts"]["unsupported"], 1)

    def test_superseded_version_excluded(self):
        d = fixture()
        d["documents"][1]["supersedes"] = "EST-A"
        o = compute(d)
        self.assertTrue(o["not_evaluable"])
        self.assertEqual(0, o["finding_counts"].get("difference", 0))

    def test_invalid_document_date_is_not_evaluable(self):
        d = fixture()
        d["documents"][0]["document_date"] = "2026-02-30"
        self.assertTrue(compute(d)["not_evaluable"])


if __name__ == "__main__":
    unittest.main()
