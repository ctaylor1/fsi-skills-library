#!/usr/bin/env python3
"""Independent fresh private-market scenarios through package CLIs; no package imports."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills/wealth-management/private-market-client-reviewer"
FIXTURE = ROOT / "tools/fixtures/wealth-p2-forward/private-market-client-reviewer.json"


class IndependentPrivateMarketCases(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text())

    def cli(self, script, obj):
        with tempfile.TemporaryDirectory(prefix="wealth-p2-private-forward-") as tmp:
            path = Path(tmp) / "input.json"
            path.write_text(json.dumps(obj))
            run = subprocess.run(
                [sys.executable, "-B", str(PACKAGE / "scripts" / script), str(path)],
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        self.assertFalse(run.stderr, run.stderr)
        return run.returncode, json.loads(run.stdout)

    def output(self):
        code, out = self.cli("calculate_or_transform.py", self.doc)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.cli("validate_output.py", out), (0, {"errors": []}))
        return out

    def ready_case(self):
        self.doc["accounts"][0]["available_cash"] = 50000

    def codes(self, out):
        return {f["code"] for f in out["findings"]}

    def test_partial_mixed_commitment_identity(self):
        row = self.output()["result"]["positions"][0]
        # 125,000 - (40,000 + 8,000) + 1,000 = 78,000.
        self.assertEqual(row["remaining_commitment_including_unpaid_calls"], "78000.00")
        self.assertEqual(row["reserved_commitment_in_unpaid_calls"], "16000.00")
        self.assertEqual(row["uncalled_commitment"], "62000.00")
        self.assertEqual(row["outstanding_calls"], "22000.00")
        self.assertEqual(row["uncalled_plus_outstanding_calls"], "84000.00")

    def test_notice_and_partial_receipt_ledger(self):
        rows = {r["record"]["notice_id"]: r for r in self.output()["result"]["notice_ledger"]}
        self.assertEqual(rows["CALL-MIXED"]["outstanding_commitment_effect"], "16000.00")
        self.assertEqual(rows["DIST-MIXED"]["settled_commitment_effect"], "1000.00")
        self.assertEqual(rows["DIST-MIXED"]["outstanding_amount"], "8000.00")
        self.assertEqual(rows["CANCELLED-CALL"]["outstanding_amount"], "0.00")

    def test_fund_aggregation_preserves_accounts(self):
        summary = self.output()["result"]["fund_summaries"][0]
        self.assertEqual(summary["remaining_commitment_including_unpaid_calls"], "123000.00")
        self.assertEqual(summary["uncalled_commitment"], "107000.00")
        self.assertEqual(summary["current_policy_nav"], "59000.00")

    def test_dated_cash_not_historical_cash_double_count(self):
        row = self.output()["result"]["account_liquidity"][0]
        self.assertEqual(row["opening_cash_after_reserve"], "15000.00")
        self.assertEqual(
            [r["committed_balance"] for r in row["schedule"]], ["12000.00", "-8000.00", "-10000.00", "-10000.00"]
        )
        self.assertEqual(row["horizon_forecast_balance"], "-17000.00")

    def test_household_cash_does_not_cure_account_shortfall(self):
        out = self.output()
        self.assertEqual(out["result"]["household_liquidity"]["horizon_committed_balance"], "60000.00")
        self.assertEqual(out["status"], "needs-data")
        self.assertIn("call-funding-shortfall", self.codes(out))
        self.assertIs(out["result"]["household_liquidity"]["transfer_authority_assumed"], False)

    def test_superseded_and_beyond_horizon_forecasts_not_added(self):
        row = self.output()["result"]["account_liquidity"][0]
        self.assertEqual([r["reference"] for r in row["schedule"]], ["RENT", "CALL-MIXED", "FEE-OUTSIDE", "FC-ACTIVE"])
        self.assertEqual([r["reference"] for r in row["excluded_beyond_horizon"]], ["FC-LATER"])

    def test_complete_high_cash_ready_still_no_actions_or_eligibility(self):
        self.ready_case()
        out = self.output()
        self.assertEqual(out["status"], "review-ready")
        self.assertEqual(out["result"]["account_liquidity"][0]["horizon_committed_balance"], "22000.00")
        self.assertEqual(out["result"]["account_liquidity"][0]["horizon_forecast_balance"], "15000.00")
        self.assertIs(out["action_taken"], False)
        self.assertEqual(out["result"]["eligibility_decision"], "not-determined")
        self.assertEqual(out["result"]["investment_recommendation"], "not-made")

    def test_unknown_effect_withholds_commitment_not_known_cash(self):
        self.doc["movements"][1]["commitment_effect_amount"] = None
        out = self.output()
        row = out["result"]["positions"][0]
        self.assertIsNone(row["remaining_commitment_including_unpaid_calls"])
        self.assertEqual(row["observed_settled_calls"], "50000.00")
        self.assertIn("unknown-commitment-effect", self.codes(out))

    def test_unknown_obligation_preserves_earlier_cash_only(self):
        self.doc["other_obligations"][0]["amount"] = None
        out = self.output()
        row = out["result"]["account_liquidity"][0]
        self.assertEqual(row["opening_cash_after_reserve"], "15000.00")
        self.assertTrue(all(r["committed_balance"] is None for r in row["schedule"]))
        self.assertIn("unknown-obligation", self.codes(out))

    def test_unknown_forecast_only_suppresses_scenario(self):
        self.doc["forecasts"][1]["amount"] = None
        row = self.output()["result"]["account_liquidity"][0]
        self.assertEqual(row["horizon_committed_balance"], "-10000.00")
        self.assertIsNone(row["horizon_forecast_balance"])

    def test_incomplete_inventory_suppresses_complete_ledger_and_cash(self):
        self.doc["coverage"]["movements_complete"] = None
        out = self.output()
        self.assertIsNone(out["result"]["positions"][0]["uncalled_commitment"])
        self.assertIsNone(out["result"]["account_liquidity"][0]["horizon_committed_balance"])
        self.assertIn("incomplete-inventory", self.codes(out))

    def test_incomplete_forecast_inventory_preserves_known_schedule(self):
        self.doc["coverage"]["forecasts_complete"] = False
        row = self.output()["result"]["account_liquidity"][0]
        self.assertEqual(row["horizon_committed_balance"], "-10000.00")
        self.assertIsNone(row["horizon_forecast_balance"])

    def test_stale_nav_not_updated_by_settlements(self):
        self.doc["positions"][0]["nav"]["valuation_date"] = "2026-03-01"
        out = self.output()
        self.assertIs(out["result"]["positions"][0]["nav_current_under_policy"], False)
        self.assertIsNone(out["result"]["fund_summaries"][0]["current_policy_nav"])
        self.assertEqual(out["result"]["positions"][0]["position"]["nav"]["amount"], 43000)

    def test_missing_required_document_cannot_be_eligible_by_label(self):
        self.ready_case()
        self.doc["positions"][0]["eligibility_evidence"][0]["document_refs"] = []
        out = self.output()
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(out["result"]["positions"][0]["eligibility_review"][0]["evidence_status"], "incomplete")

    def test_required_criterion_cannot_be_status_bypassed(self):
        self.ready_case()
        self.doc["positions"][0]["eligibility_evidence"][0]["status"] = "not-applicable"
        self.assertIn("eligibility-evidence-gap", self.codes(self.output()))

    def test_manager_open_and_stale_state_preserved(self):
        self.ready_case()
        self.doc["positions"][0]["manager_diligence"]["status"] = "needs-data"
        self.doc["positions"][1]["manager_diligence"]["review_by"] = "2026-09-16"
        out = self.output()
        self.assertEqual(sum(f["code"] == "manager-diligence-gap" for f in out["findings"]), 2)

    def test_upstream_origin_and_source_survive_ready_diligence_label(self):
        self.ready_case()
        issue = dict(
            artifact_id="origin-manager-77",
            code="valuation-conflict",
            message="Independent pricing evidence conflicts with manager mark.",
            status="unresolved",
            source_ids=["record"],
        )
        self.doc["upstream_issues"] = [issue]
        out = self.output()
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(out["result"]["handoff_context"]["upstream_issues"], [issue])
        self.assertTrue(any(f.get("upstream_artifact_id") == "origin-manager-77" for f in out["findings"]))

    def test_absent_upstream_inventory_rejects(self):
        del self.doc["upstream_issues"]
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_resolved_label_alone_rejects(self):
        self.doc["upstream_issues"] = [
            dict(
                artifact_id="origin-1",
                code="ownership",
                message="Owner conflict",
                status="resolved",
                source_ids=["record"],
            )
        ]
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_source_gap_blocks_global_readiness(self):
        self.ready_case()
        self.doc["notices"][1]["source_ids"] = ["MISSING"]
        out = self.output()
        self.assertEqual(out["status"], "needs-data")
        self.assertIn("evidence-gap", self.codes(out))

    def test_uncited_coverage_cannot_assert_complete_ledger(self):
        self.ready_case()
        self.doc["coverage"]["source_ids"] = []
        out = self.output()
        self.assertFalse(out["result"]["positions"][0]["ledger_complete"])
        self.assertIsNone(out["result"]["account_liquidity"][0]["horizon_committed_balance"])

    def test_uncited_nav_not_in_supported_current_nav_subtotal(self):
        self.ready_case()
        self.doc["positions"][0]["nav"]["source_ids"] = []
        out = self.output()
        self.assertFalse(out["result"]["positions"][0]["nav_current_under_policy"])
        self.assertIsNone(out["result"]["fund_summaries"][0]["current_policy_nav"])

    def test_uncited_account_cash_cannot_support_funding_conclusion(self):
        self.ready_case()
        self.doc["accounts"][0]["source_ids"] = []
        out = self.output()
        self.assertIsNone(out["result"]["account_liquidity"][0]["horizon_committed_balance"])

    def test_uncited_notice_cannot_support_complete_commitment(self):
        self.ready_case()
        self.doc["notices"][1]["source_ids"] = []
        out = self.output()
        self.assertFalse(out["result"]["positions"][0]["ledger_complete"])
        self.assertIsNone(out["result"]["positions"][0]["uncalled_commitment"])

    def test_uncited_settlement_cannot_support_complete_commitment(self):
        self.ready_case()
        self.doc["movements"][1]["source_ids"] = []
        out = self.output()
        self.assertFalse(out["result"]["positions"][0]["ledger_complete"])
        self.assertIsNone(out["result"]["positions"][0]["uncalled_commitment"])

    def test_uncited_legal_requirement_not_documented_for_review(self):
        self.ready_case()
        self.doc["positions"][0]["eligibility_requirements"][0]["source_ids"] = []
        out = self.output()
        self.assertEqual(out["result"]["positions"][0]["eligibility_review"][0]["evidence_status"], "incomplete")

    def test_settlement_cannot_exceed_notice(self):
        self.doc["movements"][1]["amount"] = 30001
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_effect_cannot_hide_noncommitment_overpayment(self):
        self.doc["movements"][1]["commitment_effect_amount"] = 1000
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_settled_label_requires_full_amount(self):
        self.doc["notices"][1]["lifecycle"] = "settled"
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_future_settlement_and_wrong_forecast_replacement_reject(self):
        self.doc["movements"][1]["settled_date"] = "2026-09-18"
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)
        self.setUp()
        self.doc["forecasts"][0]["superseded_by_notice_id"] = "DIST-MIXED"
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_precision_boolean_and_duplicate_scope_reject(self):
        self.doc["accounts"][0]["available_cash"] = True
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)
        self.setUp()
        self.doc["movements"][1]["amount"] = "10000.001"
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)
        self.setUp()
        row = copy.deepcopy(self.doc["positions"][0])
        row["position_id"] = "DUPLICATE"
        self.doc["positions"].append(row)
        self.assertEqual(self.cli("validate_input.py", self.doc)[0], 1)

    def test_empty_private_scope_never_ready(self):
        for key in ("positions", "accounts", "notices", "movements", "forecasts", "other_obligations"):
            self.doc[key] = []
        out = self.output()
        self.assertEqual(out["status"], "needs-data")
        self.assertIn("empty-scope", self.codes(out))

    def test_output_tamper_rejected(self):
        out = self.output()
        mutations = [
            lambda o: o["result"]["positions"][0].__setitem__("uncalled_commitment", "999999.00"),
            lambda o: o["result"]["household_liquidity"].__setitem__("transfer_authority_assumed", True),
            lambda o: o.__setitem__("status", "review-ready"),
            lambda o: o.__setitem__("action_taken", True),
            lambda o: o["result"].__setitem__("specialist_questions", []),
            lambda o: o["result"]["handoff_context"].__setitem__("household_id", "OTHER"),
        ]
        for change in mutations:
            altered = copy.deepcopy(out)
            change(altered)
            self.assertEqual(self.cli("validate_output.py", altered)[0], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
