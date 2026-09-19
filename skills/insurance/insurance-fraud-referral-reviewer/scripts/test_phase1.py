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
    return engine.transform(doc)


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

    def clean(self):
        d = fixture()
        c = d["claims"][0]
        d["claims"] = [c]
        c.update(
            loss_date="2026-07-01",
            report_date="2026-07-02",
            policy_inception_date="2020-01-01",
            coverage_increase_date=None,
            prior_claims_24m=0,
            statement_inconsistencies=0,
            reportable_loss=False,
            police_report=True,
            documentation_complete=True,
            coverage_lapse_reinstatement=False,
            prior_siu_flag=False,
        )
        return d

    def test_history_is_not_referral_override(self):
        d = self.clean()
        d["claims"][0].update(prior_siu_flag=True, prior_siu_status="open", prior_siu_source_ref="synthetic:history")
        o = compute(d)["referrals"][0]
        self.assertEqual(3, o["indicator_score"])
        self.assertEqual("monitor", o["recommendation"])

    def test_unknown_police_report_not_adverse_indicator(self):
        d = self.clean()
        d["claims"][0].update(reportable_loss=True, police_report=None)
        o = compute(d)["referrals"][0]
        self.assertNotIn("FR-NO-REPORT", [i["id"] for i in o["indicators_triggered"]])
        self.assertEqual("needs-data", o["recommendation"])

    def test_counterevidence_survives_draft(self):
        d = fixture()
        o = compute(d)["referrals"][0]
        self.assertEqual(d["claims"][0]["counterevidence"], o["counterevidence"])
        self.assertIn("Counterevidence", o["referral_document"])

    def test_invalid_threshold_order_rejected(self):
        d = self.clean()
        d["indicator_config"] = {"monitor_min": 7, "refer_min": 3}
        self.assertTrue(input_check.validate(d)[0])

    def test_wrong_score_rejected_independently(self):
        o = compute(fixture())
        o["referrals"][0]["indicator_score"] += 1
        self.assertTrue(output_check.validate(reseal(o)))


if __name__ == "__main__":
    unittest.main()
