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

    def test_latest_stock_plus_paid_not_stock_history_sum(self):
        d = fixture()
        new = copy.deepcopy(d["reserves"][0])
        new.update(amount=25000, as_of="2026-07-01")
        d["reserves"].append(new)
        o = compute(d)
        self.assertEqual("evaluable", o["financial_status"])
        self.assertEqual(43000, o["incurred"]["total_incurred"])

    def test_movement_cannot_be_added_as_stock(self):
        d = fixture()
        d["reserves"][0]["entry_type"] = "reserve_movement"
        o = compute(d)
        self.assertEqual("not_evaluable", o["financial_status"])
        self.assertIsNone(o["incurred"]["total_incurred"])

    def test_duplicate_payment_and_mixed_currency_block_totals(self):
        for mode in ("duplicate", "currency"):
            d = fixture()
            if mode == "duplicate":
                d["payments"].append(copy.deepcopy(d["payments"][0]))
            else:
                d["payments"][0]["currency"] = "EUR"
            self.assertIsNone(compute(d)["incurred"]["total_incurred"])

    def test_unconfirmed_empty_ledger_is_unknown(self):
        d = fixture()
        d["financial_collections_complete"] = False
        d["payments"] = []
        d["reserves"] = []
        self.assertEqual("not_evaluable", compute(d)["financial_status"])


if __name__ == "__main__":
    unittest.main()
