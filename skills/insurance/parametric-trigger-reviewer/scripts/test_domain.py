"""Source identity, finality, aggregate accounting and recomputation regressions."""

import copy
import json
import unittest
from pathlib import Path
from domain import evaluate, validate
from workflow_foundation import run, check_output
from workflow_contract import build_artifact

NAME = "parametric-trigger-reviewer"


class Native(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).parents[1] / "evals/files/input.json").read_text())
        self.d = self.doc["data"]
        self.c = self.d["contract"]
        self.reading = self.d["readings"][0]

    def result(self):
        return run(self.doc, NAME, evaluate, validate)

    def gap(self):
        out = self.result()
        self.assertEqual(out["status"], "needs-data", out["findings"])
        for k in ("index_value", "gross_event_scenario", "aggregate_remaining", "provisional_unpaid_scenario"):
            self.assertIsNone(out["results"][k])
        return out

    def test_normal_reconciles_caps_and_current_paid(self):
        out = self.result()
        self.assertEqual(out["status"], "ready-for-review")
        self.assertEqual(check_output(out, NAME, evaluate, validate), [])
        x = out["results"]
        self.assertEqual(
            (
                x["gross_event_scenario"],
                x["current_event_recorded_paid"],
                x["aggregate_remaining"],
                x["provisional_unpaid_scenario"],
            ),
            ("80000", "10000", "60000", "60000"),
        )

    def test_wrong_capacity(self):
        self.doc["context"]["capacity"] = "member"
        self.gap()

    def test_wrong_line(self):
        self.doc["context"]["line_of_business"] = "health"
        self.gap()

    def test_wrong_object(self):
        self.doc["context"]["object_id"] = "unrelated"
        self.gap()

    def test_high_precision_paid_preserved(self):
        self.d["aggregate_ledger"][0]["cumulative_net_paid"] = "30000.000000000000000000000000000001"
        self.assertEqual(self.result()["results"]["aggregate_remaining"], "59999.999999999999999999999999999999")

    def test_arithmetic_rounding_rejected(self):
        self.d["aggregate_ledger"][0]["cumulative_net_paid"] = "0." + "0" * 260 + "1"
        with self.assertRaises(ValueError):
            self.result()

    def test_no_authority(self):
        out = self.result()
        self.assertFalse(out["action_taken"])
        self.assertFalse(out["results"]["payment_authorized"])

    def test_source_preserved(self):
        before = copy.deepcopy(self.doc)
        self.assertEqual(self.result()["source_document"], before)
        self.assertEqual(self.doc, before)

    def test_unknown_value(self):
        self.reading["value"] = None
        self.gap()

    def test_fractional_json_float_rejected(self):
        self.reading["value"] = 120.5
        with self.assertRaises(ValueError):
            self.result()

    def test_exact_fractional_value(self):
        self.reading["value"] = "119.999999999999999999"
        self.assertEqual(self.result()["results"]["gross_event_scenario"], "40000")

    def test_threshold_equal_strict(self):
        self.c["operator"] = ">"
        self.assertEqual(self.result()["results"]["gross_event_scenario"], "40000")

    def test_known_zero_not_missing(self):
        self.reading["value"] = "80"
        self.d["aggregate_ledger"] = []
        self.assertEqual(self.result()["results"]["provisional_unpaid_scenario"], "0")

    def test_decreasing_trigger(self):
        self.c["operator"] = "<="
        self.c["tiers"][0]["threshold"] = "140"
        self.c["tiers"][1]["threshold"] = "120"
        self.assertEqual(self.result()["results"]["matched_tier_id"], "T2")

    def test_inverted_tiers(self):
        self.c["tiers"].reverse()
        self.gap()

    def test_no_unit_conversion(self):
        self.reading["unit"] = "other"
        self.gap()

    def test_different_station(self):
        self.reading["location"] = "other"
        self.gap()

    def test_window_boundary(self):
        self.d["event"]["occurred_at"] = self.d["event"]["window_end_at"]
        self.gap()

    def test_contract_coverage(self):
        self.c["coverage_start_at"] = "2026-10-01T01:00:00Z"
        self.gap()

    def test_preliminary(self):
        self.reading["finality"] = "preliminary"
        self.gap()

    def test_retracted(self):
        self.reading["finality"] = "retracted"
        self.gap()

    def test_issued_before_window_end(self):
        self.reading["issued_at"] = "2026-10-01T22:00:00Z"
        self.gap()

    def test_status_before_window_end(self):
        self.d["verifier_status"][0]["observed_at"] = "2026-10-01T22:00:00Z"
        self.gap()

    def test_competing_finals(self):
        row = copy.deepcopy(self.reading)
        row["reading_id"] = "R2"
        self.d["readings"].append(row)
        self.gap()

    def revision(self):
        row = copy.deepcopy(self.reading)
        row.update(reading_id="R2", revision="2", supersedes_reading_id="R1", issued_at="2026-10-03T02:00:00Z")
        self.d["readings"].append(row)
        return row

    def test_revision_selected(self):
        self.revision()
        self.d["selected_reading_id"] = "R2"
        self.assertEqual(self.result()["status"], "ready-for-review")

    def test_obsolete_selection(self):
        self.revision()
        self.gap()

    def test_preliminary_supersedes_final(self):
        self.revision()["finality"] = "preliminary"
        self.d["selected_reading_id"] = "R2"
        self.gap()

    def test_dangling_predecessor(self):
        self.reading["supersedes_reading_id"] = "missing"
        self.gap()

    def test_cycle(self):
        self.revision()
        self.reading["supersedes_reading_id"] = "R2"
        self.gap()

    def test_revision_branch(self):
        self.revision()
        row = copy.deepcopy(self.d["readings"][1])
        row["reading_id"] = "R3"
        self.d["readings"].append(row)
        self.gap()

    def fallback(self):
        self.reading["verifier_id"] = "VERIFIER-B"
        self.d["verifier_status"][0]["available"] = False
        row = copy.deepcopy(self.d["verifier_status"][0])
        row.update(verifier_id="VERIFIER-B", available=True)
        self.d["verifier_status"].append(row)

    def test_explicit_fallback(self):
        self.fallback()
        self.assertEqual(self.result()["status"], "ready-for-review")

    def test_fallback_unknown_primary(self):
        self.fallback()
        self.d["verifier_status"][0]["available"] = None
        self.gap()

    def test_fallback_contrary_primary(self):
        self.fallback()
        row = copy.deepcopy(self.reading)
        row.update(reading_id="PRIMARY", verifier_id="VERIFIER-A")
        self.d["readings"].append(row)
        self.gap()

    def test_unauthorized_verifier(self):
        self.reading["verifier_id"] = "other"
        self.gap()

    def test_bare_completeness_flags(self):
        self.d.pop("inventory")
        self.gap()

    def test_unknown_empty_ledger_not_zero(self):
        self.d["aggregate_ledger"] = []
        self.d["inventory"]["ledger_statement"] = None
        self.gap()

    def test_wrong_inventory_period(self):
        self.d["inventory"]["aggregate_period_id"] = "prior"
        self.gap()

    def test_inventory_no_locator(self):
        self.d["inventory"]["locator"] = None
        self.gap()

    def test_unknown_inventory(self):
        self.d["reading_inventory_complete"] = None
        self.gap()

    def test_unknown_ledger(self):
        self.d["aggregate_ledger_complete"] = None
        self.gap()

    def test_duplicate_economic_event(self):
        row = copy.deepcopy(self.d["aggregate_ledger"][0])
        row["entry_id"] = "L3"
        self.d["aggregate_ledger"].append(row)
        self.gap()

    def test_other_currency(self):
        self.d["aggregate_ledger"][0]["currency"] = "EUR"
        self.gap()

    def test_other_aggregate_period(self):
        self.d["aggregate_ledger"][0]["aggregate_period_id"] = "AGG-2025"
        self.gap()

    def test_aggregate_event_outside(self):
        self.c["aggregate_period_end"] = "2026-09-30"
        self.gap()

    def test_ledger_date_outside_period(self):
        self.d["aggregate_ledger"][0]["paid_through"] = "2025-12-31"
        self.gap()

    def test_paid_before_current_event(self):
        self.d["aggregate_ledger"][1]["paid_through"] = "2026-09-30"
        self.gap()

    def test_exhausted_aggregate(self):
        self.d["aggregate_ledger"][0]["cumulative_net_paid"] = "90000"
        self.assertEqual(self.result()["results"]["provisional_unpaid_scenario"], "0")

    def test_overpaid_needs_review(self):
        self.d["aggregate_ledger"][1]["cumulative_net_paid"] = "90000"
        self.assertEqual(self.result()["status"], "needs-review")

    def test_expired_profile(self):
        self.d["profile"]["effective_to"] = "2025-12-31"
        self.gap()

    def test_different_program(self):
        self.d["program"] = "different"
        self.gap()

    def test_missing_profile_basis(self):
        self.d["profile"]["rule_basis"] = None
        self.gap()

    def test_unknown_source(self):
        self.reading["source_refs"] = ["missing"]
        self.gap()

    def test_future_source(self):
        self.doc["sources"][0]["as_of"] = "2026-10-05"
        self.gap()

    def test_inherited_issue(self):
        self.doc["unresolved_issues"] = ["Verifier not reconciled"]
        self.gap()

    def test_resealed_tampering(self):
        out = self.result()
        out["results"]["provisional_unpaid_scenario"] = "70000"
        out["artifact"] = build_artifact(
            out["source_document"],
            out,
            producer=NAME,
            artifact_type="workflow-review",
            completeness=out["completeness"],
            evaluability=out["evaluability"],
            issues=out["unresolved_issues"],
        )
        self.assertTrue(check_output(out, NAME, evaluate, validate))


if __name__ == "__main__":
    unittest.main()
