#!/usr/bin/env python3
"""Fresh independent trust evidence and ledger scenarios; package CLIs only."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills/wealth-management/trust-administration-reviewer"
FIXTURE = ROOT / "tools/fixtures/wealth-p3-forward/trust-administration-reviewer.json"


class IndependentTrustCases(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text())

    def cli(self, script, value):
        with tempfile.TemporaryDirectory(prefix="wealth-p3-trust-forward-") as tmp:
            path = Path(tmp) / "input.json"
            path.write_text(json.dumps(value))
            run = subprocess.run(
                [sys.executable, "-B", str(PACKAGE / "scripts" / script), str(path)],
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        self.assertFalse(run.stderr, run.stderr)
        return run.returncode, json.loads(run.stdout)

    def out(self):
        code, out = self.cli("calculate_or_transform.py", self.doc)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.cli("validate_output.py", out), (0, {"errors": []}))
        return out

    def result(self):
        return self.out()["result"]

    def codes(self, out):
        return {f["code"] for f in out["findings"]}

    def test_complete_case_ready_but_no_legal_or_payment_decision(self):
        out = self.out()
        self.assertEqual(out["status"], "review-ready")
        self.assertFalse(out["action_taken"])
        self.assertTrue(out["human_review_required"])
        self.assertEqual(out["result"]["legal_profile_review"]["legal_applicability_decision"], "not-determined")
        self.assertTrue(all(r["payment_approval"] == "not-given" for r in out["result"]["distribution_requests"]))

    def test_cash_and_buckets_independent_arithmetic(self):
        a, b = self.result()["cash_reconciliation"]
        expected_a = {"total": "66300.00", "principal": "49300.00", "income": "17000.00"}
        expected_b = {"total": "18000.00", "principal": "14000.00", "income": "4000.00"}
        for row, expected in [(a, expected_a), (b, expected_b)]:
            for key, amount in expected.items():
                self.assertEqual(row["components"][key]["expected_closing"], amount)
                self.assertEqual(row["components"][key]["difference"], "0.00")
                self.assertTrue(row["components"][key]["reconciled"])

    def test_internal_transfer_nets_zero_at_trust_scope(self):
        r = self.result()
        # 100000 opening +3500 receipt -1200 expense -6000 distribution -12000 acquisition.
        self.assertEqual(r["asset_summary"]["known_cash_subtotal"], "84300.00")
        self.assertTrue(all(row["components"]["total"]["reconciled"] for row in r["cash_reconciliation"]))

    def test_reclassification_changes_buckets_not_total(self):
        self.doc["reclassifications"][0]["from_bucket"] = "principal"
        r = self.result()["cash_reconciliation"][0]["components"]
        self.assertEqual(r["total"]["expected_closing"], "66300.00")
        self.assertEqual(r["principal"]["expected_closing"], "46300.00")
        self.assertEqual(r["income"]["expected_closing"], "20000.00")
        self.assertEqual(r["principal"]["difference"], "3000.00")
        self.assertEqual(r["income"]["difference"], "-3000.00")

    def test_asset_total_counts_cash_once(self):
        r = self.result()["asset_summary"]
        self.assertEqual(r["known_cash_subtotal"], "84300.00")
        self.assertEqual(r["known_noncash_subtotal"], "250000.00")
        self.assertEqual(r["reported_trust_assets_total"], "334300.00")
        self.assertTrue(r["cash_counted_once"])

    def test_paid_history_and_pending_cash_not_double_counted(self):
        r = self.result()
        old, new = r["distribution_requests"]
        self.assertEqual(old["observed_current_period_paid"], "6000.00")
        self.assertEqual(old["observed_pending_payments"], "8000.00")
        self.assertEqual(old["outstanding_requested_amount"], "11000.00")
        self.assertEqual(new["outstanding_requested_amount"], "2500.00")
        self.assertEqual(
            [x["illustrative_cash_after_all_open_requests"] for x in r["distribution_cash_scenarios"]],
            ["50300.00", "13500.00"],
        )

    def test_actual_settlement_changes_cash_and_request_once(self):
        payment = next(m for m in self.doc["movements"] if m["movement_id"] == "PENDING-OLD")
        payment.update(lifecycle="settled", date="2026-09-16")
        self.doc["cash_accounts"][0]["closing"].update(total=58300, principal=43300, income=15000)
        self.doc["assets"][0]["reported_value"] = 58300
        r = self.result()
        self.assertEqual(r["distribution_requests"][0]["outstanding_requested_amount"], "3000.00")
        self.assertEqual(r["distribution_requests"][0]["observed_current_period_paid"], "14000.00")
        self.assertEqual(r["distribution_cash_scenarios"][0]["illustrative_cash_after_all_open_requests"], "50300.00")
        self.assertTrue(r["cash_reconciliation"][0]["components"]["total"]["reconciled"])

    def test_removing_pending_rows_changes_no_current_balance(self):
        before = self.result()
        self.doc["movements"] = [m for m in self.doc["movements"] if m["lifecycle"] != "pending"]
        after = self.result()
        self.assertEqual(before["cash_reconciliation"], after["cash_reconciliation"])
        self.assertEqual(before["distribution_cash_scenarios"], after["distribution_cash_scenarios"])

    def test_unknown_allocation_preserves_cash_total_only(self):
        self.doc["movements"][0]["allocation"]["income"] = None
        r = self.result()["cash_reconciliation"][0]["components"]
        self.assertEqual(r["total"]["expected_closing"], "66300.00")
        self.assertIsNone(r["income"]["expected_closing"])
        self.assertIsNone(r["principal"]["expected_closing"])

    def test_unknown_reclassification_not_zero(self):
        self.doc["reclassifications"][0]["amount"] = None
        out = self.out()
        r = out["result"]["cash_reconciliation"][0]["components"]
        self.assertEqual(r["total"]["expected_closing"], "66300.00")
        self.assertIsNone(r["principal"]["expected_closing"])
        self.assertIn("classification-unknown", self.codes(out))

    def test_unknown_prior_payment_blocks_remaining_and_scenario(self):
        self.doc["distribution_requests"][0]["paid_before_period"] = None
        r = self.result()
        self.assertIsNone(r["distribution_requests"][0]["outstanding_requested_amount"])
        self.assertIsNone(r["distribution_cash_scenarios"][0]["illustrative_cash_after_all_open_requests"])

    def test_unknown_requested_split_not_legal_classification(self):
        self.doc["distribution_requests"][0]["requested_principal"] = None
        r = self.result()["distribution_requests"][0]
        self.assertEqual(r["outstanding_requested_amount"], "11000.00")
        self.assertEqual(r["evidence_status"], "incomplete")

    def test_cash_difference_retained_as_unreconciled(self):
        self.doc["cash_accounts"][0]["closing"]["total"] += 1
        self.doc["cash_accounts"][0]["closing"]["principal"] += 1
        out = self.out()
        r = out["result"]["cash_reconciliation"][0]["components"]["total"]
        self.assertEqual(r["difference"], "1.00")
        self.assertFalse(r["reconciled"])
        self.assertIn("cash-reconciliation-difference", self.codes(out))
        self.assertIsNone(out["result"]["distribution_cash_scenarios"][0]["illustrative_cash_after_all_open_requests"])

    def test_one_cent_cash_comparison_tolerance_is_explicit(self):
        self.doc["cash_accounts"][0]["closing"].update(total="66300.01", principal="49300.01")
        self.doc["assets"][0]["reported_value"] = "66300.01"
        r = self.result()["cash_reconciliation"][0]["components"]["total"]
        self.assertTrue(r["reconciled"])
        self.assertEqual(r["difference"], "0.01")

    def test_cash_asset_duplicate_rejected(self):
        row = copy.deepcopy(self.doc["assets"][0])
        row["asset_id"] = "DUPLICATE-CASH"
        self.doc["assets"].append(row)
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_missing_cash_reference_blocks_full_inventory(self):
        self.doc["assets"].pop(1)
        out = self.out()
        self.assertIsNone(out["result"]["asset_summary"]["reported_trust_assets_total"])
        self.assertIn("cash-inventory-gap", self.codes(out))

    def test_stale_noncash_not_counted_as_supported_current_value(self):
        self.doc["assets"][2]["valuation_date"] = "2026-01-01"
        r = self.result()
        self.assertIsNone(r["asset_summary"]["reported_trust_assets_total"])
        self.assertFalse(r["assets"][2]["evidence_current"])

    def test_missing_amendment_precedence_review_blocks_authority(self):
        self.doc["legal_profile"]["document_ids"] = ["DOC-ORIGINAL"]
        r = self.result()
        self.assertEqual(r["legal_profile_review"]["evidence_status"], "incomplete")
        self.assertEqual(r["authority_reviews"][0]["evidence_status"], "incomplete")
        self.assertEqual(r["distribution_requests"][0]["evidence_status"], "incomplete")
        self.assertEqual(r["cash_reconciliation"][0]["components"]["total"]["expected_closing"], "66300.00")

    def test_trustee_title_not_appointment_evidence(self):
        self.doc["fiduciaries"][0]["appointment_review"]["status"] = "unknown"
        self.assertEqual(self.result()["authority_reviews"][0]["evidence_status"], "incomplete")

    def test_no_distribution_power_cannot_qualify_packet(self):
        self.doc["authority_reviews"][0]["powers"] = ["administration", "accounting-review"]
        out = self.out()
        self.assertEqual(out["result"]["distribution_requests"][0]["evidence_status"], "incomplete")
        self.assertIn("trust-authority-review-gap", self.codes(out))

    def test_required_packet_missing_not_inferred_from_approval_label(self):
        self.doc["distribution_requests"][0]["packet"].pop()
        self.assertEqual(self.result()["distribution_requests"][0]["evidence_status"], "incomplete")

    def test_conflict_review_must_follow_request(self):
        self.doc["distribution_requests"][1]["conflict_review"]["reviewed_on"] = "2026-09-14"
        self.assertEqual(self.result()["distribution_requests"][1]["evidence_status"], "incomplete")

    def test_open_conflict_not_resolved_by_packet_completeness(self):
        self.doc["distribution_requests"][0]["conflict_state"] = "open"
        out = self.out()
        self.assertIn("distribution-conflict", self.codes(out))
        self.assertEqual(out["result"]["distribution_requests"][0]["evidence_status"], "incomplete")

    def test_obligation_dates_and_unproven_completion(self):
        self.doc["obligations"][0]["due_on"] = "2026-09-16"
        self.doc["obligations"][1]["completion_reference"] = None
        r = self.result()["obligations"]
        self.assertEqual(r[0]["review_state"], "overdue")
        self.assertEqual(r[1]["review_state"], "unknown")
        self.assertFalse(r[1]["completion_authenticated"])

    def test_unknown_reserve_is_not_zero(self):
        self.doc["cash_accounts"][0]["protected_reserve"] = None
        self.assertIsNone(self.result()["distribution_cash_scenarios"][0]["illustrative_cash_after_all_open_requests"])

    def test_negative_request_scenario_not_approval(self):
        self.doc["cash_accounts"][0]["protected_reserve"] = 60000
        out = self.out()
        r = out["result"]["distribution_cash_scenarios"][0]
        self.assertEqual(r["illustrative_cash_after_all_open_requests"], "-4700.00")
        self.assertFalse(r["funding_authorized"])
        self.assertIn("distribution-cash-scenario-shortfall", self.codes(out))

    def test_uncited_coverage_withholds_complete_results(self):
        self.doc["coverage"]["source_ids"] = []
        r = self.result()
        self.assertIsNone(r["cash_reconciliation"][0]["components"]["total"]["expected_closing"])
        self.assertIsNone(r["asset_summary"]["reported_trust_assets_total"])
        self.assertEqual(r["distribution_requests"][0]["evidence_status"], "incomplete")

    def test_uncited_movement_withholds_supported_cash_bridge(self):
        self.doc["movements"][0]["source_ids"] = []
        self.assertIsNone(self.result()["cash_reconciliation"][0]["components"]["total"]["expected_closing"])

    def test_uncited_allocation_review_only_withholds_buckets(self):
        self.doc["movements"][0]["allocation"]["review"]["source_ids"] = []
        r = self.result()["cash_reconciliation"][0]["components"]
        self.assertEqual(r["total"]["expected_closing"], "66300.00")
        self.assertIsNone(r["principal"]["expected_closing"])

    def test_uncited_asset_never_in_complete_supported_total(self):
        self.doc["assets"][2]["source_ids"] = []
        self.assertIsNone(self.result()["asset_summary"]["reported_trust_assets_total"])

    def test_uncited_packet_and_legal_review_never_qualified(self):
        self.doc["distribution_requests"][0]["packet"][0]["source_ids"] = []
        self.assertEqual(self.result()["distribution_requests"][0]["evidence_status"], "incomplete")
        self.setUp()
        self.doc["legal_profile"]["source_ids"] = []
        self.assertEqual(self.result()["legal_profile_review"]["evidence_status"], "incomplete")

    def test_upstream_issue_origin_survives_and_blocks_authority(self):
        issue = dict(
            artifact_id="prior-trust-ownership",
            code="ownership-conflict",
            message="Named fiduciary appointment conflicts with current instrument.",
            status="unresolved",
            source_ids=["record"],
        )
        self.doc["upstream_issues"] = [issue]
        out = self.out()
        self.assertEqual(out["result"]["handoff_context"]["upstream_issues"], [issue])
        self.assertEqual(out["result"]["authority_reviews"][0]["evidence_status"], "incomplete")
        self.assertTrue(any(f.get("upstream_artifact_id") == issue["artifact_id"] for f in out["findings"]))

    def test_resolution_needs_cited_attributed_evidence(self):
        self.doc["upstream_issues"] = [
            dict(
                artifact_id="prior-trust-ownership",
                code="ownership-conflict",
                message="Original conflict retained.",
                status="resolved",
                source_ids=["record"],
                resolution=dict(
                    owner="Synthetic counsel", reference="Synthetic correction memo", as_of="2026-09-17", source_ids=[]
                ),
            )
        ]
        self.assertEqual(self.result()["authority_reviews"][0]["evidence_status"], "incomplete")
        self.doc["upstream_issues"][0]["resolution"]["source_ids"] = ["record"]
        self.assertEqual(self.out()["status"], "review-ready")

    def test_absent_and_unmapped_issue_inventory_reject(self):
        del self.doc["upstream_issues"]
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)
        self.setUp()
        self.doc["unresolved_issues"] = []
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_scoped_handoff_and_actual_beneficiary_household(self):
        r = self.result()
        self.assertEqual(r["handoff_context"]["scope_type"], "trust")
        self.assertEqual(r["handoff_context"]["trust_id"], "TRUST-FRESH")
        self.assertEqual(r["distribution_requests"][0]["beneficiary_household_id"], "HH-ACTUAL-BEN")

    def test_cross_trust_marker_and_household_misrouting_reject(self):
        self.doc["assets"][0]["trust_id"] = "OTHER"
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)
        self.setUp()
        self.doc["beneficiaries"][0]["household_id"] = "family:FAMILY"
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_internal_transfer_missing_leg_or_mismatched_allocation_reject(self):
        self.doc["movements"].pop(3)
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)
        self.setUp()
        self.doc["movements"][3]["allocation"].update(principal=7000, income=3000)
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_snapshot_and_movement_allocation_identities_reject(self):
        self.doc["cash_accounts"][0]["closing"]["total"] = 60000
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)
        self.setUp()
        self.doc["movements"][0]["allocation"]["income"] = 3501
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_illegal_payment_lifecycle_and_double_history_reject(self):
        self.doc["distribution_requests"][0]["lifecycle"] = "settled"
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)
        self.setUp()
        self.doc["distribution_requests"][1]["paid_before_period"] = 1
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_pending_exceeds_remaining_is_explicit_conflict(self):
        self.doc["movements"][6]["amount"] = 12000
        self.doc["movements"][6]["allocation"].update(principal=10000, income=2000)
        out = self.out()
        self.assertIn("distribution-pending-state-conflict", self.codes(out))
        self.assertEqual(out["result"]["distribution_requests"][0]["evidence_status"], "incomplete")

    def test_tamper_reconstruction_rejects_financial_and_authority_claims(self):
        base = self.out()
        mutations = [
            lambda o: o["result"]["cash_reconciliation"][0]["components"]["total"].__setitem__(
                "expected_closing", "99999.00"
            ),
            lambda o: o["result"]["asset_summary"].__setitem__("reported_trust_assets_total", "418600.00"),
            lambda o: o["result"]["distribution_requests"][0].__setitem__("payment_approval", "given"),
            lambda o: o["result"]["authority_reviews"][0].__setitem__("permission_authenticated", True),
            lambda o: o["result"]["handoff_context"].__setitem__("trust_id", "OTHER"),
            lambda o: o.__setitem__("action_taken", True),
        ]
        for mutation in mutations:
            out = copy.deepcopy(base)
            mutation(out)
            self.assertEqual(self.cli("validate_output.py", out)[0], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
