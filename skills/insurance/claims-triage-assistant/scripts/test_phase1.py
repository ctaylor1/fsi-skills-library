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
    return json.loads((ROOT / "evals/files/claims_example.json").read_text())


def compute(doc):
    return engine.triage(doc)


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

    def test_liability_unknown_preserves_urgent_routes(self):
        d = fixture()
        c = d["claims"][0]
        d["claims"] = [c]
        c.update(
            claim_type="auto_liability",
            liability_clear=None,
            fatality=True,
            litigation=True,
            catastrophe_code="CAT-TEST",
            statutory_deadline_date="2026-07-14",
        )
        d["as_of"] = "2026-07-15"
        o = compute(d)["triage"][0]
        self.assertEqual("U1 (Immediate)", o["urgency_band"])
        self.assertTrue(o["deadline_overdue"])
        targets = " ".join(v["target"] for v in o["routes"])
        for expected in ("litigation", "catastrophe", "investigation"):
            self.assertIn(expected, targets)

    def test_unknown_responsibility_allows_neutral_fraud_and_recovery_referrals(self):
        d = fixture()
        d["claims"] = [d["claims"][0]]
        d["claims"][0].update(
            claim_type="auto_liability", liability_clear=None, fatality=True,
            injuries=True, fraud_indicators=["conflicting loss accounts"], subrogation_potential=True,
        )
        o = compute(d)
        record = o["triage"][0]
        targets = {r["target"] for r in record["routes"]}
        self.assertTrue({"insurance-fraud-referral-reviewer", "subrogation-opportunity-screener",
                         "claims investigation (human)"}.issubset(targets))
        self.assertEqual("U1 (Immediate)", record["urgency_band"])
        self.assertEqual("partial", record["classification_status"])
        self.assertEqual([], output_check.validate(o))
        self.assertEqual([], validate_artifact(o["artifact"], input_doc=d, output=o))
        for assertion in ("Triage concludes no fraud", "Possible recovery from an at-fault third party"):
            with self.subTest(assertion=assertion):
                mutated = copy.deepcopy(o)
                mutated["triage"][0]["routes"][0]["reason"] = assertion
                errors = output_check.validate(reseal(mutated))
                self.assertTrue(any("unsupported/unapproved claim" in e for e in errors), errors)

    def test_clock_uses_review_date(self):
        d = fixture()
        c = d["claims"][0]
        d["claims"] = [c]
        c.update(fatality=False, injuries=False, statutory_deadline_date="2026-08-01")
        d["as_of"] = "2026-07-15"
        near = compute(d)["triage"][0]
        d["as_of"] = "2026-01-01"
        far = compute(d)["triage"][0]
        self.assertGreater(near["urgency_score"], far["urgency_score"])

    def test_unmapped_type_preserves_urgency(self):
        d = fixture()
        d["claims"] = [d["claims"][0]]
        d["claims"][0].update(claim_type="unmapped-risk", fatality=True)
        o = compute(d)["triage"][0]
        self.assertIsNone(o["severity_band"])
        self.assertGreater(o["urgency_score"], 0)
        self.assertIn("Unknown", o["draft_summary"]["body"])

    def test_negative_exposure_rejected(self):
        d = fixture()
        d["claims"][0]["estimated_exposure"] = -1
        self.assertTrue(input_check.validate(d)[0])


if __name__ == "__main__":
    unittest.main()
