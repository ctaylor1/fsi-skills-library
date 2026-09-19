#!/usr/bin/env python3
"""Regression scenarios for transaction evidence, partitions, and output binding."""
import copy
import json
import unittest
from pathlib import Path
from calculate_or_transform import compute, validate_input
from validate_output import validate
from payment_contract import validate_evidence, validate_handoff

FILES = Path(__file__).resolve().parents[1] / "evals/files"


def base():
    doc = json.loads((FILES / "ledger_example.json").read_text())
    doc["records"] = [r for r in doc["records"] if r["txn_ref"] == "TXN-1001"]
    return doc


class Regression(unittest.TestCase):
    def test_golden_fixture_and_contracts(self):
        doc = json.loads((FILES / "ledger_example.json").read_text())
        out = compute(doc)
        self.assertEqual(validate(out, doc), [])
        self.assertEqual(out["summary"]["routed_count"], 1)
        for g in out["groups"]:
            for evidence in g["evidence"]:
                self.assertEqual(validate_evidence(evidence), [])
        for h in out["investigation_handoffs"] + [g["handoff"] for g in out["routed_groups"]]:
            self.assertEqual(validate_handoff(h), [])

    def test_clean_covered_group(self):
        out = compute(base())
        self.assertTrue(out["summary"]["fully_evaluated_and_matched"])
        self.assertEqual(out["groups"][0]["cash_ledger_check"]["ledger_minus_bank"], "0.0")

    def test_decimal_large_amount_and_exact_tolerance(self):
        doc = base()
        for r in doc["records"]:
            r["amount"] = "9007199254740993.01"
        doc["records"][-1]["amount"] = "9007199254740993.02"
        out = compute(doc)
        self.assertEqual(out["groups"][0]["cash_ledger_check"]["ledger_minus_bank"], "0.01")
        self.assertTrue(out["summary"]["fully_evaluated_and_matched"])
        doc["records"][-1]["amount"] = "9007199254740993.0201"
        self.assertFalse(compute(doc)["summary"]["fully_evaluated_and_matched"])

    def test_each_partition_dimension_isolates_same_reference(self):
        for dimension, alternate in (("currency", "EUR"), ("legal_entity_id", "merchant99"),
                                     ("account_id", "other-account"), ("settlement_cycle", "next-cycle")):
            with self.subTest(dimension=dimension):
                doc = base()
                extra = copy.deepcopy(doc["records"])
                for r in extra:
                    r[dimension] = alternate
                    r["amount"] = "800.01"
                    r["record_id"] += "-independent"
                    r["source_ref"] += ";row=independent"
                doc["records"] += extra
                out = compute(doc)
                self.assertEqual(len(out["groups"]), 2)
                self.assertEqual(len(out["partition_totals"]), 2)
                self.assertTrue(out["summary"]["fully_evaluated_and_matched"])

    def test_cross_currency_records_never_match(self):
        doc = base()
        doc["records"][-1]["currency"] = "EUR"
        out = compute(doc)
        self.assertEqual(len(out["groups"]), 2)
        self.assertFalse(out["summary"]["fully_evaluated_and_matched"])
        self.assertTrue(all(g["cash_ledger_check"]["status"] == "not_evaluable" for g in out["groups"]))

    def test_duplicate_quarantines_all_arithmetic_and_retains_evidence(self):
        doc = base()
        duplicate = copy.deepcopy(doc["records"][0])
        duplicate["record_id"] = "OTHER-GATEWAY-ID"
        duplicate["amount"] = "999"
        doc["records"].append(duplicate)
        out = compute(doc)
        group = out["groups"][0]
        self.assertEqual(group["status"], "quarantined")
        self.assertEqual(len(group["evidence"]), 5)
        self.assertTrue(all(v is None for v in group["source_amounts"].values()))
        self.assertEqual(group["comparisons"], [])
        self.assertTrue(all(v["total"] is None for v in out["partition_totals"][0]["source_totals"].values()))

    def test_missing_is_not_zero(self):
        for missing in (None, "absent"):
            doc = base()
            if missing == "absent":
                del doc["records"][-1]["amount"]
            else:
                doc["records"][-1]["amount"] = missing
            out = compute(doc)
            self.assertIsNone(out["groups"][0]["source_amounts"]["ledger"])
            self.assertIsNone(out["groups"][0]["cash_ledger_check"]["ledger_minus_bank"])
            self.assertIsNone(out["partition_totals"][0]["source_totals"]["ledger"]["total"])

    def test_reused_identity_across_equal_transaction_references_quarantines_both(self):
        doc = base()
        extra = copy.deepcopy(doc["records"])
        for r in extra:
            r["txn_ref"] = "TXN-COPY"
        doc["records"] += extra
        out = compute(doc)
        self.assertEqual(len(out["groups"]), 2)
        self.assertTrue(all(g["status"] == "quarantined" for g in out["groups"]))
        self.assertTrue(all(v["known_subtotal"] is None for v in out["partition_totals"][0]["source_totals"].values()))
        self.assertFalse(out["summary"]["fully_evaluated_and_matched"])
        self.assertEqual(validate(out, doc), [])

    def test_either_record_id_or_source_reference_reuse_is_sufficient(self):
        for preserved in ("record_id", "source_ref"):
            doc = base()
            extra = copy.deepcopy(doc["records"])
            for r in extra:
                r["txn_ref"] = "TXN-COPY"
                if preserved != "record_id": r["record_id"] += "-new"
                if preserved != "source_ref": r["source_ref"] += ";row=new"
            doc["records"] += extra
            self.assertTrue(all(g["status"] == "quarantined" for g in compute(doc)["groups"]))

    def test_changed_scope_cannot_launder_reused_source_row(self):
        for field, value in (("currency", "EUR"), ("settlement_cycle", "other"),
                             ("legal_entity_id", "other"), ("account_id", "other")):
            doc = base()
            extra = copy.deepcopy(doc["records"])
            for r in extra:
                r[field] = value
                r["record_id"] += "-alias"
            doc["records"] += extra
            out = compute(doc)
            self.assertEqual(len(out["groups"]), 2)
            self.assertTrue(all(g["status"] == "quarantined" for g in out["groups"]))
            self.assertTrue(all(v["total"] is None for p in out["partition_totals"] for v in p["source_totals"].values()))

    def test_transaction_settlement_identity_reuse_is_quarantined_and_handed_off(self):
        doc = base()
        extra = copy.deepcopy(doc["records"][0])
        extra.update(level="settlement", txn_ref="BATCH-COPY")
        doc["records"].append(extra)
        out = compute(doc)
        self.assertEqual(out["groups"][0]["status"], "quarantined")
        self.assertEqual(out["routed_groups"][0]["status"], "quarantined")
        self.assertTrue(out["routed_groups"][0]["source_identity_conflicts"])

    def test_independent_source_namespaces_can_use_same_local_record_id(self):
        doc = base()
        for r in doc["records"]: r["record_id"] = "source-local-1"
        self.assertTrue(compute(doc)["summary"]["fully_evaluated_and_matched"])

    def test_explicit_zero_is_evaluable(self):
        doc = base()
        for r in doc["records"]:
            r["amount"] = "0"
        out = compute(doc)
        self.assertTrue(out["summary"]["fully_evaluated_and_matched"])
        self.assertEqual(out["groups"][0]["source_amounts"]["bank"], "0")

    def test_gateway_processor_are_not_cash(self):
        doc = base()
        doc["records"] = [r for r in doc["records"] if r["source"] != "bank"]
        out = compute(doc)
        self.assertEqual(out["groups"][0]["cash_ledger_check"]["status"], "not_evaluable")
        self.assertIsNone(out["partition_totals"][0]["source_totals"]["bank"]["total"])
        self.assertNotIn("proposed_entries", out)

    def test_upstream_mismatch_survives_bank_ledger_agreement(self):
        doc = base()
        doc["records"][0]["amount"] = "125.00"
        out = compute(doc)
        self.assertEqual(out["groups"][0]["cash_ledger_check"]["status"], "within_tolerance")
        self.assertEqual(out["groups"][0]["status"], "needs_review")
        self.assertTrue(any(i["type"] == "AMOUNT_MISMATCH" for i in out["groups"][0]["issues"]))

    def test_equal_settlement_records_still_route(self):
        doc = base()
        for r in doc["records"]:
            r["level"] = "settlement"
        out = compute(doc)
        self.assertEqual(out["groups"], [])
        self.assertEqual(len(out["routed_groups"]), 1)
        self.assertFalse(out["summary"]["fully_evaluated_and_matched"])

    def test_states_only_compared_when_explicitly_normalized(self):
        doc = base()
        self.assertEqual(compute(doc)["groups"][0]["issues"], [])
        doc["records"][0]["normalized_state"] = "captured"
        doc["records"][1]["normalized_state"] = "reversed"
        self.assertTrue(any(i["type"] == "STATE_MISMATCH" for i in compute(doc)["groups"][0]["issues"]))

    def test_reject_nonfinite_boolean_and_invalid_schema(self):
        for value in (True, False, "NaN", "Infinity", "-Infinity", {}, []):
            with self.subTest(value=value):
                doc = base()
                doc["records"][0]["amount"] = value
                self.assertTrue(validate_input(doc)[0])
                with self.assertRaises(ValueError):
                    compute(doc)
        for change in ({"currency": ""}, {"legal_entity_id": ""}, {"date": "2026-02-30"}):
            doc = base()
            doc["records"][0].update(change)
            self.assertTrue(validate_input(doc)[0])

    def test_negative_or_boolean_tolerance_rejected(self):
        for value in ("-0.01", True, "NaN"):
            doc = base()
            doc["config"]["amount_tolerance"] = value
            self.assertTrue(validate_input(doc)[0])

    def test_no_unsupported_journal_corrections(self):
        out = compute(base())
        out["proposed_entries"] = [{"debit": "cash", "credit": "suspense", "amount": "100"}]
        self.assertTrue(validate(out))

    def test_output_detects_tampered_arithmetic_evidence_and_input(self):
        doc = base()
        out = compute(doc)
        out["groups"][0]["source_amounts"]["bank"] = "900"
        self.assertTrue(validate(out, doc))
        out = compute(doc)
        out["groups"][0]["evidence"] = []
        self.assertTrue(validate(out, doc))
        alternative = copy.deepcopy(doc)
        alternative["records"][0]["amount"] = "999"
        self.assertIn("authoritative", validate(compute(alternative), doc)[0])

    def test_repeatable_identity(self):
        doc = base()
        self.assertEqual(compute(doc), compute(copy.deepcopy(doc)))
        before = compute(doc)["groups"][0]["group_id"]
        doc["records"].reverse()
        self.assertEqual(compute(doc)["groups"][0]["group_id"], before)
        self.assertEqual(compute(doc)["groups"], compute(base())["groups"])

    def test_offsetting_differences_are_not_hidden(self):
        doc = base()
        extra = copy.deepcopy(doc["records"])
        for r in extra:
            r["txn_ref"] = "TXN-OTHER"
            r["record_id"] += "-OTHER"
            r["source_ref"] += ";row=other"
        doc["records"][0]["amount"] = "120"
        extra[0]["amount"] = "80"
        doc["records"] += extra
        out = compute(doc)
        self.assertEqual(len(out["investigation_handoffs"]), 2)
        self.assertFalse(out["summary"]["fully_evaluated_and_matched"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
