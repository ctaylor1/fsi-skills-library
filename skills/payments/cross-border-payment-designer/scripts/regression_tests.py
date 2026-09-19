"""Behavioral arithmetic, evidence and authority regressions for corridor design."""
import json
from copy import deepcopy
from pathlib import Path
import unittest
import domain
from payment_foundation import build, validate_output, validate_request


class CorridorTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((Path(__file__).resolve().parents[1] / "evals/files/request.json").read_text())
        self.option = self.request["data"]["options"][0]

    def run_case(self):
        return build(self.request, domain)

    def gaps(self):
        return [f["code"] for f in self.run_case()["findings"]]

    def test_separate_sender_receipt(self):
        result = self.run_case()["result"]["options"][0]
        self.assertEqual(result["payer_total_debit"], {"amount": "1010", "currency": "USD"})
        self.assertEqual(result["recipient_expected_receipt"], {"amount": "4995", "currency": "BRL"})
        self.assertTrue(result["comparison_ready"])

    def test_inverse_quote(self):
        self.option["fx_quote"].update(base_currency="BRL", quote_currency="USD", rate="0.2")
        self.assertEqual(self.run_case()["result"]["options"][0]["recipient_expected_receipt"]["amount"], "4995")

    def test_unknown_fee_not_zero(self):
        self.option["fees"][0]["amount"] = None
        output = self.run_case()["result"]["options"][0]
        self.assertIsNone(output["payer_total_debit"])
        self.assertIsNone(output["recipient_expected_receipt"])

    def test_incomplete_inventory(self):
        self.option["fees_complete"] = False
        self.assertIn("fee-inventory-incomplete", self.gaps())

    def test_fee_currency_not_netted(self):
        self.option["fees"][0]["currency"] = "EUR"
        self.assertIsNone(self.run_case()["result"]["options"][0]["payer_total_debit"])

    def test_our_allocation_conflict(self):
        self.option["charge_convention"] = "OUR"
        self.assertIn("charge-convention-fee-allocation-conflict", self.gaps())

    def test_ben_allocation_conflict(self):
        self.option["charge_convention"] = "BEN"
        self.assertIn("charge-convention-fee-allocation-conflict", self.gaps())

    def test_quote_expired(self):
        self.option["fx_quote"]["expires_at"] = "2026-09-18T13:59:59Z"
        self.assertIn("fx-not-current-firm-evidenced", self.gaps())

    def test_quote_offset_instants(self):
        self.option["fx_quote"]["expires_at"] = "2026-09-18T10:30:00-04:00"
        self.assertNotIn("fx-not-current-firm-evidenced", self.gaps())

    def test_indicative_quote_not_ready(self):
        self.option["fx_quote"]["kind"] = "indicative"
        self.assertFalse(self.run_case()["result"]["options"][0]["comparison_ready"])

    def test_missing_quote_unknown_receipt(self):
        self.option["fx_quote"] = None
        self.assertIsNone(self.run_case()["result"]["options"][0]["recipient_expected_receipt"])

    def test_quote_orientation_mismatch(self):
        self.option["fx_quote"]["base_currency"] = "EUR"
        self.assertIn("fx-orientation-mismatch", self.gaps())

    def test_payout_recipient_binding(self):
        self.option["legs"][-1]["to_entity"] = "substituted-payee"
        self.assertIn("final-beneficiary-payout-binding-unresolved", self.gaps())
        self.assertIn("screening-scope-unresolved", self.gaps())

    def test_payout_amount_reconciliation(self):
        self.option["legs"][-1]["amount"] = "5000"
        self.assertIn("final-payout-receipt-unreconciled", self.gaps())

    def test_customer_collection_reconciliation(self):
        self.option["legs"][0]["amount"] = "1000"
        self.assertIn("collection-debit-unreconciled", self.gaps())

    def test_nostro_separate(self):
        output = self.run_case()["result"]["options"][0]
        self.assertEqual(len(output["separate_nostro_funding_obligations"]), 1)
        self.assertEqual(output["payer_total_debit"]["amount"], "1010")

    def test_duplicate_economic_leg_rejected(self):
        self.option["legs"].append(deepcopy(self.option["legs"][0]))
        self.assertTrue(validate_request(self.request, domain))

    def test_stale_regulatory_review(self):
        self.option["regulatory_reviews"][1]["valid_until"] = "2026-09-18T13:00:00Z"
        self.assertIn("scoped-regulatory-review-unresolved:BR", self.gaps())

    def test_review_wrong_activity(self):
        self.option["regulatory_reviews"][1]["use_case"] = "commercial-payment"
        self.assertIn("scoped-regulatory-review-unresolved:BR", self.gaps())

    def test_missing_intermediary_screening(self):
        self.option["sanctions_review"]["entity_ids"].remove("br-provider")
        self.assertIn("screening-scope-unresolved", self.gaps())

    def test_expired_screening(self):
        self.option["sanctions_review"]["valid_until"] = "2026-09-18T13:00:00Z"
        self.assertIn("screening-review-not-current", self.gaps())

    def test_unsupported_currency_pair(self):
        self.request["data"]["payee"]["currency"] = "JPY"
        self.assertIn("unsupported-corridor-currency-pair", self.gaps())

    def test_unsupported_origin(self):
        self.request["jurisdiction"] = "JP"
        self.assertEqual(self.run_case()["status"], "unsupported")

    def test_missing_owner(self):
        self.request["data"]["accountable_reviewer"] = ""
        self.assertIn("accountable-corridor-owner-missing", self.gaps())

    def test_upstream_gap_preserved(self):
        self.request["upstream_issues"] = [{"code": "permission", "message": "unknown", "source_ids": ["case"]}]
        self.assertIn("upstream:permission", self.gaps())

    def test_action_and_source_tamper(self):
        output = self.run_case()
        self.assertFalse(output["authority_granted"])
        output["authority_granted"] = True
        self.assertTrue(validate_output(output, domain, self.request))

    def test_independent_input_binding(self):
        output = self.run_case()
        altered = deepcopy(self.request)
        altered["data"]["principal"] = "900"
        self.assertTrue(validate_output(output, domain, altered))

    def test_execution_rejected(self):
        self.request["requested_action"] = "execute"
        self.assertTrue(validate_request(self.request, domain))

    def test_infinite_rate_rejected(self):
        self.option["fx_quote"]["rate"] = "Infinity"
        self.assertTrue(validate_request(self.request, domain))

    def test_naive_timestamp_rejected(self):
        self.request["data"]["evaluate_at"] = "2026-09-18T14:00:00"
        self.assertTrue(validate_request(self.request, domain))

    def test_duplicate_leg_identity(self):
        self.option["legs"][1]["leg_id"] = self.option["legs"][0]["leg_id"]
        self.assertTrue(validate_request(self.request, domain))

    def test_regulatory_entity_scope(self):
        self.option["regulatory_reviews"][1]["entity_ids"] = ["br-beneficiary"]
        self.assertIn("scoped-regulatory-review-unresolved:BR", self.gaps())

    def test_fee_party_screening(self):
        self.option["fees"][0]["charging_entity"] = "new-intermediary"
        self.assertIn("screening-scope-unresolved", self.gaps())

    def test_local_profile_mismatch(self):
        self.option["legs"][-1]["method"] = "IN-UPI"
        self.assertIn("local-method-leg-scope-mismatch", self.gaps())

    def test_disconnected_delivery_chain(self):
        self.option["legs"][-1]["previous_leg_id"] = "collection"
        self.assertIn("delivery-entity-chain-unresolved", self.gaps())

    def test_account_transition_not_assumed(self):
        self.option["legs"][-1].pop("account_transition_review_ref")
        self.assertIn("intermediate-account-transition-unresolved", self.gaps())

    def test_intermediary_amount_reconciled(self):
        self.option["legs"][1]["amount"] = "1"
        output = self.run_case()["result"]["options"][0]
        self.assertFalse(output["comparison_ready"])
        self.assertIn("intermediary-funding-amount-unreconciled", output["gaps"])
        self.assertEqual(output["intermediary_reconciliation"][0]["difference"], "-999")


if __name__ == "__main__":
    unittest.main()
