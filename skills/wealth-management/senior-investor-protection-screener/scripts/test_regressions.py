#!/usr/bin/env python3
"""Executed counterexamples for windowing, unknown evidence and immutable draft identity."""

import copy
import json
import unittest
from pathlib import Path
from calculate_or_transform import compute
from validate_output import validate

BASE = json.loads((Path(__file__).resolve().parents[1] / "evals/files/case_example.json").read_text())


class RegressionTests(unittest.TestCase):
    def doc(self):
        return copy.deepcopy(BASE)

    def signal(self, out, name):
        return next(s for s in out["result"]["signals"] if s["signal"] == name)

    def test_golden_has_actual_concerns_without_decision(self):
        out = compute(self.doc())
        self.assertEqual(out["status"], "review-ready")
        self.assertEqual(out["result"]["suggested_disposition"], "Escalate")
        self.assertEqual(
            out["result"]["fired_signals"], ["unusual_disbursement", "new_external_payee", "rapid_liquidation"]
        )
        self.assertEqual(validate(out), [])
        self.assertIs(out["action_taken"], False)

    def test_proposed_focal_is_screened_but_not_counted_as_executed(self):
        d = self.doc()
        d["transactions"][-1]["lifecycle"] = "proposed"
        out = compute(d)
        self.assertTrue(self.signal(out, "unusual_disbursement")["fired"])
        self.assertTrue(self.signal(out, "new_external_payee")["fired"])
        self.assertFalse(self.signal(out, "rapid_liquidation")["fired"])
        self.assertEqual(self.signal(out, "rapid_liquidation")["basis"]["total_out"], 0)
        self.assertEqual(out["result"]["focal_activity"][0]["lifecycle"], "proposed")
        self.assertEqual(out["result"]["suggested_disposition"], "Review")

    def test_pending_and_cancelled_history_do_not_contaminate_executed_baseline(self):
        d = self.doc()
        for index, state in enumerate(("proposed", "pending", "cancelled")):
            d["transactions"].append(
                {
                    **d["transactions"][-1],
                    "txn_id": f"NONEXEC-{index}",
                    "date": "2026-09-14T10:00:00Z",
                    "amount": 1000000,
                    "lifecycle": state,
                }
            )
        out = compute(d)
        self.assertEqual(out["result"]["window"]["baseline_count"], 12)
        self.assertEqual(self.signal(out, "unusual_disbursement")["basis"]["mean"], 155)
        self.assertEqual(self.signal(out, "rapid_liquidation")["basis"]["total_out"], 85000)

    def test_lifecycle_must_be_explicit_and_supported(self):
        for state in (None, "unknown", "executed-maybe"):
            d = self.doc()
            if state is None:
                d["transactions"][-1].pop("lifecycle")
            else:
                d["transactions"][-1]["lifecycle"] = state
            with self.assertRaisesRegex(ValueError, "lifecycle"):
                compute(d)

    def test_pending_focal_and_same_day_executed_outflow_remain_separate(self):
        d = self.doc()
        d["transactions"][-1]["lifecycle"] = "pending"
        d["transactions"].append(
            {
                **d["transactions"][-1],
                "txn_id": "ACTUAL-1",
                "date": "2026-09-16T10:00:00Z",
                "amount": 30000,
                "lifecycle": "executed",
            }
        )
        out = compute(d)
        self.assertTrue(self.signal(out, "rapid_liquidation")["fired"])
        self.assertEqual(self.signal(out, "rapid_liquidation")["basis"]["total_out"], 30000)
        self.assertEqual([t["txn_id"] for t in self.signal(out, "rapid_liquidation")["evidence"]], ["ACTUAL-1"])

    def test_missing_observations_are_unknown(self):
        d = self.doc()
        d.pop("observations")
        out = compute(d)
        for name in ("third_party_influence", "capacity_concern_indicators", "communication_red_flags"):
            self.assertIsNone(self.signal(out, name)["fired"])
            self.assertIn(name, out["result"]["not_evaluable"])
        self.assertEqual(out["status"], "needs-data")

    def test_partial_observation_is_not_assessed_absent(self):
        d = self.doc()
        d["observations"].pop("confusion_observed")
        out = compute(d)
        self.assertIsNone(self.signal(out, "capacity_concern_indicators")["fired"])

    def test_real_concern_is_not_hidden_by_missing_flags(self):
        d = self.doc()
        d["observations"].pop("requests_secrecy")
        d["observations"]["unusual_urgency"] = True
        self.assertIs(self.signal(compute(d), "communication_red_flags")["fired"], True)

    def test_lookback_excludes_old_baseline(self):
        d = self.doc()
        d["lookback_days"] = 2
        out = compute(d)
        self.assertEqual(out["result"]["window"]["baseline_count"], 0)
        self.assertIsNone(self.signal(out, "unusual_disbursement")["fired"])

    def test_post_focal_rows_cannot_contaminate_baseline(self):
        d = self.doc()
        d["transactions"].append(
            {**d["transactions"][-1], "txn_id": "LATER", "date": "2026-09-15T10:00:00Z", "amount": 1e8}
        )
        out = compute(d)
        self.assertEqual(out["result"]["window"]["baseline_count"], 12)
        self.assertEqual(self.signal(out, "unusual_disbursement")["basis"]["mean"], 155)

    def test_same_day_focal_is_included(self):
        d = self.doc()
        d["transactions"][-1]["date"] = "2026-09-16T23:00:00Z"
        self.assertEqual(self.signal(compute(d), "rapid_liquidation")["basis"]["total_out"], 85000)

    def test_future_focal_is_rejected(self):
        d = self.doc()
        d["transactions"][-1]["date"] = "2026-09-17"
        with self.assertRaises(ValueError):
            compute(d)

    def test_empty_output_rejected(self):
        self.assertTrue(validate({"suggested_disposition": "Monitor", "disclaimer": "safe"}))

    def test_tampered_fired_set_and_readiness_rejected(self):
        out = compute(self.doc())
        out["result"]["fired_signals"] = []
        self.assertTrue(validate(out))
        d = self.doc()
        d.pop("observations")
        out = compute(d)
        out["findings"] = []
        out["status"] = "review-ready"
        self.assertTrue(validate(out))

    def test_artifact_changes_for_new_input(self):
        d = self.doc()
        before = compute(d)
        d["transactions"][-1]["amount"] += 1
        self.assertNotEqual(before["artifact_id"], compute(d)["artifact_id"])

    def test_unknown_source_requires_data(self):
        d = self.doc()
        d["transactions"][-1]["source_ids"] = ["not-registered"]
        self.assertEqual(compute(d)["status"], "needs-data")

    def test_stale_and_future_source_rejected(self):
        for field, value in (("valid_until", "2026-09-15"), ("as_of", "2026-09-17")):
            d = self.doc()
            d["sources"][0][field] = value
            with self.assertRaises(ValueError):
                compute(d)

    def test_no_config_fallback(self):
        d = self.doc()
        d.pop("config")
        out = compute(d)
        self.assertEqual(out["status"], "needs-data")
        self.assertIsNone(self.signal(out, "unusual_disbursement")["fired"])

    def test_invalid_threshold_and_nonfinite_rejected(self):
        for value in (-5, float("nan"), "3", 100):
            d = self.doc()
            d["config"]["amount_k"] = value
            with self.assertRaises(ValueError):
                compute(d)

    def test_unknown_age_is_not_false_applicability(self):
        d = self.doc()
        d["client"].pop("age")
        self.assertIsNone(compute(d)["result"]["screening_context"]["specified_adult_context"])

    def test_younger_adult_unknown_impairment_stays_unknown(self):
        d = self.doc()
        d["client"]["age"] = 30
        d["client"].pop("impairment_flag")
        self.assertIsNone(compute(d)["result"]["screening_context"]["specified_adult_context"])

    def test_minor_impairment_is_not_specified_adult(self):
        d = self.doc()
        d["client"]["age"] = 15
        d["client"]["impairment_flag"] = True
        out = compute(d)
        self.assertIs(out["result"]["screening_context"]["specified_adult_context"], False)
        self.assertEqual(out["status"], "needs-data")

    def test_known_absent_flags_not_clearance(self):
        d = self.doc()
        d["transactions"][-1].update(amount=100, counterparty="Known payee")
        out = compute(d)
        self.assertEqual(out["result"]["suggested_disposition"], "Monitor")
        self.assertTrue(out["human_review_required"])

    def test_declined_trusted_contact_is_not_exploitation_concern(self):
        d = self.doc()
        d["transactions"][-1].update(amount=100, counterparty="Known payee")
        d["trusted_contact"] = {"on_file": False, "collection_status": "declined", "source_ids": ["crm"]}
        out = compute(d)
        self.assertEqual(out["result"]["fired_signals"], ["trusted_contact_gap"])
        self.assertEqual(out["result"]["suggested_disposition"], "Monitor")

    def test_incomplete_history_not_green(self):
        d = self.doc()
        d["history_coverage"]["start"] = "2026-08-01"
        out = compute(d)
        self.assertEqual(out["status"], "needs-data")
        self.assertIsNone(self.signal(out, "new_external_payee")["fired"])

    def test_free_text_action_addition_rejected(self):
        out = compute(self.doc())
        out["narrative"] = "I opened the account and filed the report."
        self.assertTrue(validate(out))


if __name__ == "__main__":
    unittest.main(verbosity=2)
