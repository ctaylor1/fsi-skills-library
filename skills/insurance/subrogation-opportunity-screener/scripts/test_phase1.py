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

    def test_unknown_waiver_and_prior_never_available(self):
        for field in ("waiver_of_subrogation", "prior_recovery"):
            d = fixture()
            d.pop(field, None)
            o = compute(d)
            self.assertEqual("unknown", o["recovery_availability"])
            self.assertEqual("Review", o["screening_band"])
            self.assertNotIn("recovery_not_waived", o["fired_signals"])

    def test_confirmed_absence_can_establish_availability(self):
        d = fixture()
        d.update(
            waiver_of_subrogation=False,
            prior_recovery={"status": "none"},
            recovery_status_source_ref="synthetic:status",
        )
        self.assertEqual("available", compute(d)["recovery_availability"])

    def test_missing_deductible_cannot_be_zero_economics(self):
        d = fixture()
        d.pop("recovery_deductible", None)
        o = compute(d)
        self.assertIsNone(o["referral_economics"]["net_expected"])
        self.assertEqual("Review", o["screening_band"])

    def test_explicit_unknown_amounts_preserve_reviewable_screen(self):
        for unknown_fields in (("paid_to_date",), ("recovery_deductible",), ("paid_to_date", "recovery_deductible")):
            with self.subTest(unknown_fields=unknown_fields):
                d = fixture()
                d.update({field: None for field in unknown_fields})
                errors, warnings = input_check.validate(d)
                self.assertEqual([], errors)
                self.assertTrue(warnings)
                o = compute(d)
                self.assertEqual("Review", o["screening_band"])
                self.assertEqual("not_evaluable", o["referral_economics"]["evaluability"])
                for field in ("recovery_base", "liability_share", "gross_expected", "net_expected"):
                    self.assertIsNone(o["referral_economics"][field])
                self.assertFalse({"recovery_above_floor", "positive_expected_recovery"} & set(o["fired_signals"]))
                self.assertIn("supporting_evidence_present", o["fired_signals"])
                self.assertEqual([], output_check.validate(o))
                self.assertEqual([], validate_artifact(o["artifact"], input_doc=d, output=o))

    def test_malformed_nonnull_amounts_remain_rejected(self):
        for field in ("paid_to_date", "recovery_deductible"):
            for value in ("unknown", "", True, "NaN", "Infinity", [], {}):
                with self.subTest(field=field, value=value):
                    d = fixture()
                    d[field] = value
                    self.assertTrue(input_check.validate(d)[0])
                    with self.assertRaises(ValueError):
                        compute(d)

    def test_unknown_economics_cannot_be_resealed_as_zero(self):
        d = fixture()
        d["paid_to_date"] = None
        o = compute(d)
        o["referral_economics"]["recovery_base"] = 0
        errors = output_check.validate(reseal(o))
        self.assertTrue(any("unknown economics" in error for error in errors), errors)

    def test_unknown_forged_availability_rejected(self):
        d = fixture()
        d.pop("waiver_of_subrogation", None)
        o = compute(d)
        for s in o["signals"]:
            if s["signal"] == "recovery_not_waived":
                s["fired"] = True
        o["fired_signals"].append("recovery_not_waived")
        self.assertTrue(output_check.validate(reseal(o)))


if __name__ == "__main__":
    unittest.main()
