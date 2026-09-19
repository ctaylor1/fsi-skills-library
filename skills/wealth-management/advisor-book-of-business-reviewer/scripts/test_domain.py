#!/usr/bin/env python3
"""Independent financial identities, calendar/capacity bounds and evidence regressions."""

import copy
import json
from pathlib import Path
import unittest
from decimal import Decimal
from book_review import build, validate
from validate_output import validate as validate_output


class BookTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / "evals/files/request.json").read_text())

    def result(self):
        return build(self.doc)["result"]

    def has(self, code):
        return any(f["code"] == code for f in build(self.doc)["findings"])

    def test_complete_example(self):
        self.assertEqual(build(self.doc)["status"], "review-ready")

    def test_exact_service_due_dates(self):
        dates = {r["household_id"]: r["next_review_due_on"] for r in self.result()["review_calendar"]}
        self.assertEqual(dates["HH-1"], "2026-09-19")
        self.assertEqual(dates["HH-2"], "2026-09-21")
        self.assertEqual(dates["HH-4"], "2026-09-20")

    def test_initial_review_not_absent_evidence(self):
        h = self.doc["households"][3]
        h["review_history"]["status"] = "unknown"
        row = next(r for r in self.result()["review_calendar"] if r["household_id"] == "HH-4")
        self.assertIsNone(row["next_review_due_on"])
        self.assertTrue(self.has("review-coverage-unknown"))

    def test_due_today_not_overdue(self):
        self.doc["households"][0]["review_history"]["last_completed_on"] = "2026-08-18"
        self.assertEqual(self.result()["review_calendar"][0]["coverage_state"], "due-today")
        self.assertFalse(self.has("review-overdue"))

    def test_overdue_days(self):
        self.doc["households"][0]["review_history"]["last_completed_on"] = "2026-08-01"
        self.assertEqual(self.result()["review_calendar"][0]["days_overdue"], 17)
        self.assertTrue(self.has("review-overdue"))

    def test_departed_household_no_routine_task(self):
        self.assertFalse(any(a["household_id"] == "HH-3" for a in self.result()["action_plan"]))

    def test_tier_coverage(self):
        self.assertEqual(self.result()["tier_coverage"]["STANDARD"]["active_received_households"], 2)
        self.assertEqual(self.result()["tier_coverage"]["STANDARD"]["policy_cadence_coverage_fraction"], 1)

    def test_cohort_retention_not_current_client_ratio(self):
        c = self.result()["cohort"]
        self.assertEqual(c["starting_household_ids"], ["HH-1", "HH-2", "HH-3"])
        self.assertAlmostEqual(c["starting_cohort_retention_fraction"], 2 / 3)
        self.assertEqual(c["new_household_ids"], ["HH-4"])

    def test_population_unknown_withholds_rates(self):
        self.doc["population_complete"] = None
        r = self.result()
        self.assertIsNone(r["cohort"]["starting_cohort_retention_fraction"])
        self.assertIsNone(r["economics"]["revenue"])
        self.assertEqual(r["economics"]["known_subtotals"]["recognized_revenue"], "380.00")

    def test_scope_citation_required_for_book_totals(self):
        self.doc["scope_source_ids"] = []
        r = self.result()
        self.assertIsNone(r["cohort"]["starting_cohort_retention_fraction"])
        self.assertIsNone(r["economics"]["net_external_flows"])

    def test_unknown_start_does_not_assume_cohort(self):
        self.doc["households"][0]["joined_on"] = None
        self.assertIsNone(self.result()["cohort"]["starting_cohort_retention_fraction"])

    def test_uncited_relationship_dates_withhold_complete_economics(self):
        self.doc["households"][0]["source_ids"] = []
        result = self.result()
        self.assertIsNone(result["economics"]["net_external_flows"])
        self.assertIsNone(result["economics"]["complete_totals"]["recognized_revenue"])
        self.assertEqual(result["economics"]["known_subtotals"]["recognized_revenue"], "380.00")

    def test_missing_tier_becomes_collection_task(self):
        self.doc["households"][0]["tier_id"] = "UNKNOWN"
        r = self.result()
        self.assertTrue(any(a["action_id"] == "review-evidence:HH-1" for a in r["action_plan"]))
        self.assertTrue(self.has("tier-unknown"))

    def test_no_fabricated_owner(self):
        self.doc["households"][0]["owner_id"] = "MISSING"
        r = self.result()
        self.assertTrue(
            all(
                a["work_status"] == "blocked-evidence-or-owner" for a in r["action_plan"] if a["household_id"] == "HH-1"
            )
        )

    def test_capacity_net_of_unrelated_work(self):
        a, b = self.result()["owner_workloads"]
        self.assertEqual(
            (a["available_before_queue_minutes"], a["draft_allocated_minutes"], a["unallocated_capacity_minutes"]),
            (180, 180, 0),
        )
        self.assertEqual((b["draft_allocated_minutes"], b["unallocated_capacity_minutes"]), (135, 45))

    def test_daily_capacity_never_exceeded(self):
        for owner in self.doc["owners"]:
            for slot in owner["availability"]:
                used = sum(
                    w["minutes"]
                    for a in self.result()["action_plan"]
                    if a["owner_id"] == owner["owner_id"]
                    for w in a["work_allocations"]
                    if w["date"] == slot["date"]
                )
                self.assertLessEqual(used, slot["working_minutes"] - slot["unrelated_committed_minutes"])

    def test_partial_task_does_not_claim_completion(self):
        self.doc["owners"][1]["availability"] = self.doc["owners"][1]["availability"][:1]
        growth = next(a for a in self.result()["action_plan"] if a["category"] == "growth")
        self.assertEqual(growth["work_status"], "capacity-shortfall")
        self.assertIsNone(growth["planned_completion_on"])
        self.assertTrue(self.has("capacity-shortfall"))

    def test_later_capacity_does_not_cure_deadline(self):
        self.doc["owners"][0]["availability"] = [
            {"date": "2026-09-21", "working_minutes": 300, "unrelated_committed_minutes": 0, "source_ids": ["case"]}
        ]
        self.assertTrue(self.has("planned-deadline-miss"))

    def test_incomplete_availability_not_zero_capacity(self):
        self.doc["owners"][0]["availability_complete"] = False
        r = self.result()
        self.assertIsNone(r["owner_workloads"][0]["available_before_queue_minutes"])
        self.assertEqual(r["owner_workloads"][0]["known_available_minutes"], 180)
        self.assertTrue(
            all(a["work_status"] == "capacity-not-evaluable" for a in r["action_plan"] if a["owner_id"] == "ADVISOR-A")
        )

    def test_commitment_overlap_must_be_reviewed(self):
        self.doc["owners"][0]["queue_overlap_reviewed"] = None
        self.assertTrue(self.has("capacity-unknown"))

    def test_existing_commitment_excess_visible(self):
        self.doc["owners"][0]["availability"][0]["unrelated_committed_minutes"] = 240
        self.assertTrue(self.has("capacity-overcommitted"))

    def test_unknown_effort_visible_in_workload(self):
        self.doc["signals"][2]["estimated_minutes"] = None
        self.assertEqual(self.result()["owner_workloads"][1]["unknown_effort_actions"], 1)

    def test_growth_last_by_explicit_policy(self):
        actions = self.result()["action_plan"]
        self.assertEqual(actions[-1]["category"], "growth")
        self.assertTrue(all(a["priority_rank"] < actions[-1]["priority_rank"] for a in actions[:-1]))

    def test_policy_cannot_put_growth_before_service(self):
        next(r for r in self.doc["policy"]["priority_rules"] if r["trigger"] == "client-requested-growth")["rank"] = 1
        self.assertTrue(validate(self.doc))

    def test_growth_needs_confirmed_client_interest(self):
        self.doc["signals"][2]["client_interest_confirmed"] = None
        row = next(a for a in self.result()["action_plan"] if a["category"] == "growth")
        self.assertEqual(row["work_allocations"], [])
        self.assertTrue(self.has("growth-interest-unconfirmed"))

    def test_economics_and_sensitive_attributes_cannot_change_priority(self):
        prior = [a["action_id"] for a in self.result()["action_plan"]]
        self.doc["economics"]["household_records"][1]["recognized_revenue"] = 999999
        self.doc["households"][1].update(age=80, religion="synthetic-private-data", segment_id="DIFFERENT")
        self.assertEqual(prior, [a["action_id"] for a in self.result()["action_plan"]])

    def test_future_signal_retained_outside_work_window(self):
        self.doc["signals"][2]["due_on"] = "2026-10-01"
        r = self.result()
        self.assertEqual(len(r["signals_register"]), 3)
        self.assertFalse(any(a["action_id"] == "signal:GROWTH-2" for a in r["action_plan"]))

    def test_net_flows_exclude_market_fees_and_internal(self):
        self.assertEqual(self.result()["economics"]["net_external_flows"], "-24000.00")

    def test_practice_contribution_exact(self):
        e = self.result()["economics"]
        self.assertEqual(e["revenue"], "380.00")
        self.assertEqual(e["direct_contribution"], "195.00")
        self.assertIsNone(e["asset_return"])

    def test_all_asset_bridges_and_book_identity(self):
        e = self.result()["economics"]
        self.assertTrue(all(r["asset_bridge_difference"] == "0.00" for r in e["household_register"]))
        t = {k: Decimal(v) for k, v in e["complete_totals"].items()}
        self.assertEqual(
            t["closing_assets"],
            t["opening_assets"]
            + t["external_inflows"]
            - t["external_outflows"]
            + t["internal_net_transfer"]
            + t["market_change"]
            - t["fees_debited"],
        )

    def test_broken_asset_bridge(self):
        self.doc["economics"]["household_records"][0]["closing_assets"] += 100
        self.assertTrue(self.has("asset-bridge-mismatch"))

    def test_internal_transfer_not_double_counted(self):
        self.doc["economics"]["household_records"][0]["internal_net_transfer"] = 6000
        self.doc["economics"]["household_records"][0]["closing_assets"] += 1000
        self.assertTrue(self.has("internal-transfer-mismatch"))
        self.assertEqual(self.result()["economics"]["net_external_flows"], "-24000.00")

    def test_unknown_economics_preserves_independent_metrics(self):
        self.doc["economics"]["household_records"][0]["recognized_revenue"] = None
        e = self.result()["economics"]
        self.assertIsNone(e["revenue"])
        self.assertIsNone(e["direct_contribution"])
        self.assertEqual(e["net_external_flows"], "-24000.00")

    def test_economic_scope_cannot_omit_departed_client(self):
        self.doc["economics"]["household_records"].pop(2)
        self.assertTrue(self.has("economic-scope-gap"))
        self.assertIsNone(self.result()["economics"]["net_external_flows"])

    def test_not_provided_economics_not_zero(self):
        self.doc["economics"] = {
            "status": "not-provided",
            "reason": "No approved economic records supplied.",
            "source_ids": ["case"],
        }
        self.assertIsNone(self.result()["economics"]["revenue"])
        self.assertEqual(build(self.doc)["status"], "review-ready")

    def test_decimal_string_equivalence(self):
        expected = self.result()["economics"]["complete_totals"]
        self.doc["economics"]["household_records"][0]["recognized_revenue"] = "100.00"
        self.assertEqual(self.result()["economics"]["complete_totals"], expected)

    def test_upstream_carries_owner_and_origin(self):
        issue = {
            "artifact_id": "ORIGIN",
            "code": "ownership-conflict",
            "message": "Ownership needs review",
            "status": "unresolved",
            "source_ids": ["case"],
        }
        self.doc["upstream_issues"] = [issue]
        out = build(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(out["result"]["upstream_issues"], [issue])
        self.assertTrue(any(a["trigger"] == "upstream-issue" for a in out["result"]["action_plan"]))

    def test_missing_upstream_inventory_rejected(self):
        del self.doc["upstream_issues"]
        self.assertTrue(validate(self.doc))

    def test_caller_resolved_label_not_enough(self):
        self.doc["upstream_issues"] = [
            {
                "artifact_id": "ORIGIN",
                "code": "ownership-conflict",
                "message": "Ownership needs review",
                "status": "resolved",
                "source_ids": ["case"],
            }
        ]
        self.assertTrue(validate(self.doc))

    def test_source_gap_is_not_ready(self):
        self.doc["signals"][0]["source_ids"] = ["missing"]
        self.assertEqual(build(self.doc)["status"], "needs-data")

    def test_stale_source_rejected(self):
        self.doc["sources"][0]["valid_until"] = "2026-09-16"
        self.assertTrue(validate(self.doc))

    def test_future_signal_observation_rejected(self):
        self.doc["signals"][0]["observed_on"] = "2026-09-18"
        self.assertTrue(validate(self.doc))

    def test_book_marker_must_not_be_real_client(self):
        self.doc["household_id"] = "HH-1"
        self.assertTrue(validate(self.doc))

    def test_collection_marker_cannot_occupy_household_record(self):
        self.doc["households"][0]["household_id"] = "book:OTHER"
        self.assertTrue(validate(self.doc))

    def test_signal_cannot_route_on_uncited_household_owner(self):
        self.doc["households"][0]["source_ids"] = []
        action = next(a for a in self.result()["action_plan"] if a["action_id"] == "signal:RETENTION-1")
        self.assertEqual(action["work_status"], "blocked-evidence-or-owner")

    def test_calendar_and_action_cite_policy_inputs(self):
        self.assertIn("policy", self.result()["review_calendar"][0]["source_ids"])
        self.assertIn(
            "policy", next(a for a in self.result()["action_plan"] if a["action_id"] == "review:HH-1")["source_ids"]
        )

    def test_policy_capacity_must_match(self):
        self.doc["policy"]["capacity"] = "brokerage"
        self.assertTrue(validate(self.doc))

    def test_policy_expiry_bounds_planning(self):
        self.doc["policy"]["valid_until"] = "2026-09-18"
        self.assertTrue(validate(self.doc))

    def test_invalid_number_and_duplicate_capacity_day(self):
        self.doc["owners"][0]["availability"][0]["working_minutes"] = True
        self.assertTrue(validate(self.doc))
        self.setUp()
        self.doc["owners"][0]["availability"].append(copy.deepcopy(self.doc["owners"][0]["availability"][0]))
        self.assertTrue(validate(self.doc))

    def test_empty_population_rejected(self):
        self.doc["households"] = []
        self.assertTrue(validate(self.doc))

    def test_priority_tamper_rejected(self):
        out = build(self.doc)
        out["result"]["action_plan"][0]["priority_rank"] = 99
        self.assertTrue(validate_output(out))

    def test_capacity_tamper_rejected(self):
        out = build(self.doc)
        out["result"]["owner_workloads"][0]["available_before_queue_minutes"] = 99999
        self.assertTrue(validate_output(out))

    def test_narrative_and_context_tamper_rejected(self):
        out = build(self.doc)
        out["result"]["draft_markdown"] += "\nAll clients contacted."
        self.assertTrue(validate_output(out))
        out = build(self.doc)
        out["result"]["handoff_context"]["household_id"] = "HH-1"
        self.assertTrue(validate_output(out))

    def test_no_action_and_empty_output(self):
        self.assertTrue(validate_output({}))
        out = build(self.doc)
        out["action_taken"] = True
        self.assertTrue(validate_output(out))

    def test_hash_binds_policy_and_all_evidence(self):
        old = build(self.doc)["artifact_id"]
        self.doc["policy"]["version"] = "synthetic-new-version"
        self.assertNotEqual(old, build(self.doc)["artifact_id"])

    def test_full_reconstruction(self):
        self.assertEqual(validate_output(build(self.doc)), [])


if __name__ == "__main__":
    unittest.main()
