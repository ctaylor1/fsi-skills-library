"""Separate currencies, legal entities and funding-time dependencies."""
import json
from copy import deepcopy
from pathlib import Path
import unittest
import corridor_domain
import domain
from payment_foundation import build, validate_output, validate_request

FILES = Path(__file__).resolve().parents[1] / "evals/files"


class FundingTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((FILES / "corridor-request.json").read_text())
        self.data = self.request["data"]

    def output(self):
        return build(self.request, corridor_domain)

    def base(self):
        return self.output()["result"]["base"]

    def position(self, aid, result=None):
        return next(p for p in (result or self.base())["positions"] if p["account_id"] == aid)

    def reasons(self):
        return [r for row in self.base()["excluded_funding_transfers"] for r in row["reasons"]]

    def test_firm_funding_chain(self):
        self.assertEqual(self.position("us-source")["ending_available"], "1000")
        self.assertEqual(self.position("br-nostro")["ending_available"], "1000")
        self.assertEqual(self.position("br-payout")["ending_available"], "300")
        self.assertEqual(len(self.base()["included_funding_transfer_ids"]), 2)

    def test_removed_fx_blocks_downstream(self):
        stress = self.output()["result"]["stress_scenarios"][0]
        self.assertEqual(stress["included_funding_transfer_ids"], [])
        self.assertEqual(self.position("br-payout", stress)["peak_shortfall"], "4700")

    def test_unknown_balance_never_zero(self):
        self.data["accounts"][0]["opening_balance"] = None
        self.assertIsNone(self.position("us-source")["ending_available"])
        self.assertIn("source-funds-unavailable-at-debit", self.reasons())

    def test_insufficient_source_excluded(self):
        self.data["accounts"][0]["opening_balance"] = "999"
        self.assertEqual(self.base()["included_funding_transfer_ids"], [])

    def test_held_funds_not_available(self):
        self.data["accounts"][0]["held"] = "1001"
        self.assertIn("source-funds-unavailable-at-debit", self.reasons())

    def test_crossentity_agreement_required(self):
        self.data["funding_transfers"][1].pop("interentity_agreement_ref")
        self.assertIn("interentity-obligation-unresolved", self.reasons())

    def test_window_closed(self):
        self.data["funding_transfers"][0]["credit_window"]["closes_at"] = "2026-09-18T13:59:59Z"
        self.assertIn("credit-access-window-unresolved", self.reasons())

    def test_forecast_funding_excluded(self):
        self.data["funding_transfers"][0]["certainty"] = "forecast"
        self.assertIn("funding-not-firm-or-reviewed", self.reasons())

    def test_expired_fx(self):
        self.data["funding_transfers"][0]["fx_quote"]["expires_at"] = "2026-09-18T12:59:59Z"
        self.assertIn("funding-fx-not-current-at-debit", self.reasons())

    def test_inverse_fx(self):
        self.data["funding_transfers"][0]["fx_quote"].update(base_currency="BRL", quote_currency="USD", rate="0.2")
        self.assertEqual(self.base()["included_funding_transfer_ids"], ["fx-funding", "local-funding"])

    def test_rate_does_not_reconcile(self):
        self.data["funding_transfers"][0]["destination_amount"] = "6000"
        self.assertIn("funding-fx-amount-or-orientation-mismatch", self.reasons())

    def test_samecurrency_fee_not_hidden(self):
        self.data["funding_transfers"][1]["destination_amount"] = "4999"
        self.assertIn("same-currency-funding-not-conserved", self.reasons())

    def test_future_credit_does_not_cure_early_deficit(self):
        self.data["obligations"][0]["due_at"] = "2026-09-18T14:30:00Z"
        result = self.position("br-payout")
        self.assertEqual(result["ending_available"], "300")
        self.assertEqual(result["peak_shortfall"], "4700")

    def test_equal_timestamp_obligation_before_credit(self):
        self.data["obligations"][0]["due_at"] = "2026-09-18T12:00:00-04:00"
        self.assertEqual(self.position("br-payout")["peak_shortfall"], "4700")

    def test_account_entity_binding(self):
        self.data["obligations"][0]["entity_id"] = "us-provider"
        self.assertTrue(validate_request(self.request, corridor_domain))

    def test_account_currency_binding(self):
        self.data["funding_transfers"][0]["source_currency"] = "EUR"
        self.assertTrue(validate_request(self.request, corridor_domain))

    def test_duplicate_economic_exposure(self):
        self.data["obligations"][0]["economic_id"] = self.data["funding_transfers"][0]["economic_id"]
        self.assertTrue(validate_request(self.request, corridor_domain))

    def test_credit_cannot_precede_debit(self):
        self.data["funding_transfers"][0]["credit_at"] = "2026-09-18T12:59:00Z"
        self.assertTrue(validate_request(self.request, corridor_domain))

    def test_snapshot_exact_instant(self):
        self.data["accounts"][0]["snapshot_at"] = "2026-09-18T08:00:00-04:00"
        self.assertFalse(validate_request(self.request, corridor_domain))

    def test_outside_window_rejected(self):
        self.data["obligations"][0]["due_at"] = "2026-09-19T00:00:00Z"
        self.assertTrue(validate_request(self.request, corridor_domain))

    def test_stress_reference_required(self):
        self.data["stress_scenarios"][0]["remove_transfer_ids"] = ["not-a-transfer"]
        self.assertTrue(validate_request(self.request, corridor_domain))

    def test_action_tamper(self):
        output = self.output()
        output["action_taken"] = True
        self.assertTrue(validate_output(output, corridor_domain, self.request))

    def test_external_input_binding(self):
        output = self.output()
        changed = deepcopy(self.request)
        changed["data"]["accounts"][0]["opening_balance"] = "9999"
        self.assertTrue(validate_output(output, corridor_domain, changed))

    def test_original_core_scope_unchanged(self):
        original = json.loads((FILES / "request.json").read_text())
        original["jurisdiction"] = "BR"
        self.assertEqual(build(original, domain)["status"], "unsupported")


if __name__ == "__main__":
    unittest.main()
