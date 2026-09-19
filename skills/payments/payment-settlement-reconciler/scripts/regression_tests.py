#!/usr/bin/env python3
"""Settlement and payout regression cases with independently stated expectations."""
import copy
import json
import unittest
from pathlib import Path
from calculate_or_transform import compute, validate_input
from validate_output import validate
from payment_contract import validate_evidence, validate_handoff

FILES = Path(__file__).resolve().parents[1] / "evals/files"


def base():
    doc = json.loads((FILES / "recon_example.json").read_text())
    doc["sources"] = {s: [r for r in rows if r["match_key"] == "B-0701-VISA"] for s, rows in doc["sources"].items()}
    return doc


def payout():
    return json.loads((FILES / "payout_mismatch_example.json").read_text())


class Regression(unittest.TestCase):
    def test_golden_and_evidence_handoffs(self):
        doc = json.loads((FILES / "recon_example.json").read_text())
        out = compute(doc)
        self.assertEqual(validate(out, doc), [])
        for group in out["groups"]:
            for ev in group["evidence"]:
                self.assertEqual(validate_evidence(ev), [])
        for h in out["investigation_handoffs"]:
            self.assertEqual(validate_handoff(h), [])
        types = {i["type"] for g in out["groups"] for i in g["issues"]}
        self.assertTrue({"FEE_VARIANCE", "GROSS_MISMATCH", "MISSING_IN_LEDGER", "NET_CASH_MISMATCH", "MISSING_IN_SETTLEMENT"} <= types)
        self.assertNotIn("total_break_impact", out["summary"])

    def test_fully_covered_clean_group(self):
        self.assertTrue(compute(base())["summary"]["fully_evaluated_and_matched"])

    def test_all_four_partition_dimensions(self):
        for field, alternate in (("currency", "EUR"), ("legal_entity_id", "other-entity"),
                                 ("account_id", "other-account"), ("settlement_cycle", "other-cycle")):
            with self.subTest(field=field):
                doc = base()
                for source, rows in doc["sources"].items():
                    extra = copy.deepcopy(rows)
                    for r in extra:
                        r[field] = alternate
                        r["record_id"] += "-independent"
                        r["source_ref"] += ";row=independent"
                    rows.extend(extra)
                out = compute(doc)
                self.assertEqual(len(out["groups"]), 2)
                self.assertEqual(len(out["partition_totals"]), 2)

    def test_cross_currency_does_not_net(self):
        doc = base()
        doc["sources"]["bank_cash"][0]["currency"] = "EUR"
        out = compute(doc)
        self.assertEqual(len(out["groups"]), 2)
        self.assertFalse(out["summary"]["fully_evaluated_and_matched"])
        self.assertTrue(all(g["source_values"]["bank_cash"]["amount"] is None or g["source_values"]["processor"]["net"] is None for g in out["groups"]))

    def test_ambiguous_duplicate_quarantines_every_check(self):
        doc = base()
        dup = copy.deepcopy(doc["sources"]["processor"][0])
        dup["record_id"] += "-duplicate"
        dup["net"] = "999.99"
        doc["sources"]["processor"].append(dup)
        out = compute(doc)
        group = out["groups"][0]
        self.assertEqual(group["status"], "quarantined")
        self.assertEqual(group["checks"], [])
        self.assertEqual(len(group["evidence"]), 5)
        self.assertTrue(all(v is None for fields in group["source_values"].values() for v in fields.values()))
        self.assertTrue(all(v["total"] is None for v in out["partition_totals"][0]["source_totals"].values()))

    def test_missing_amount_is_not_zero(self):
        doc = base()
        doc["sources"]["bank_cash"][0].pop("amount")
        out = compute(doc)
        cash = next(c for c in out["groups"][0]["checks"] if c["type"] == "NET_CASH_MISMATCH")
        self.assertIsNone(cash["observed_minus_expected"])
        self.assertEqual(cash["status"], "not_evaluable")
        self.assertIsNone(out["partition_totals"][0]["source_totals"]["bank_cash.amount"]["total"])

    def test_reused_source_identity_across_equal_batches_quarantines_both(self):
        doc = base()
        for rows in doc["sources"].values():
            extra = copy.deepcopy(rows)
            for r in extra: r["match_key"] = "BATCH-COPY"
            rows.extend(extra)
        out = compute(doc)
        self.assertEqual(len(out["groups"]), 2)
        self.assertTrue(all(g["status"] == "quarantined" for g in out["groups"]))
        self.assertTrue(all(v["known_subtotal"] is None for v in out["partition_totals"][0]["source_totals"].values()))
        self.assertEqual(validate(out, doc), [])

    def test_either_record_id_or_source_reference_reuse_quarantines_batches(self):
        for preserved in ("record_id", "source_ref"):
            doc = base()
            for rows in doc["sources"].values():
                extra = copy.deepcopy(rows)
                for r in extra:
                    r["match_key"] = "BATCH-COPY"
                    if preserved != "record_id": r["record_id"] += "-new"
                    if preserved != "source_ref": r["source_ref"] += ";row=new"
                rows.extend(extra)
            self.assertTrue(all(g["status"] == "quarantined" for g in compute(doc)["groups"]))

    def test_changed_scope_cannot_launder_reused_settlement_row(self):
        for field, value in (("currency", "EUR"), ("settlement_cycle", "other"),
                             ("legal_entity_id", "other"), ("account_id", "other")):
            doc = base()
            for rows in doc["sources"].values():
                extra = copy.deepcopy(rows)
                for r in extra:
                    r[field] = value
                    r["record_id"] += "-alias"
                rows.extend(extra)
            out = compute(doc)
            self.assertTrue(all(g["status"] == "quarantined" for g in out["groups"]))
            self.assertTrue(all(v["total"] is None for p in out["partition_totals"] for v in p["source_totals"].values()))

    def test_independent_source_namespaces_can_share_record_id(self):
        doc = base()
        for rows in doc["sources"].values():
            for r in rows: r["record_id"] = "source-local-1"
        self.assertTrue(compute(doc)["summary"]["fully_evaluated_and_matched"])

    def test_empty_bank_source_is_not_zero(self):
        doc = base()
        doc["sources"]["bank_cash"] = []
        out = compute(doc)
        self.assertIsNone(out["partition_totals"][0]["source_totals"]["bank_cash.amount"]["total"])
        self.assertTrue(any(i["type"] == "MISSING_IN_BANK" for i in out["groups"][0]["issues"]))

    def test_absent_component_does_not_default_zero(self):
        doc = base()
        del doc["sources"]["processor"][0]["refunds"]
        group = compute(doc)["groups"][0]
        check = next(c for c in group["checks"] if c["type"] == "NET_CALC_MISMATCH")
        self.assertEqual(check["status"], "not_evaluable")
        self.assertFalse(compute(doc)["summary"]["fully_evaluated_and_matched"])

    def test_asof_not_period_end_controls_explicit_funding_due_date(self):
        doc = base()
        doc["sources"]["bank_cash"] = []
        p = doc["sources"]["processor"][0]
        p.update(expected_funding_date="2026-07-16", funding_due_source_ref="contract:due-date")
        group = compute(doc)["groups"][0]
        self.assertEqual(group["pending_items"][0]["type"], "PENDING_FUNDING")
        self.assertFalse(any(i["type"] == "MISSING_IN_BANK" for i in group["issues"]))
        doc["as_of"] = "2026-07-17"
        group = compute(doc)["groups"][0]
        self.assertEqual(group["pending_items"], [])
        self.assertTrue(any(i["type"] == "MISSING_IN_BANK" for i in group["issues"]))

    def test_uncited_or_conflicting_funding_dates(self):
        doc = base()
        doc["sources"]["processor"][0]["expected_funding_date"] = "2026-07-16"
        self.assertTrue(validate_input(doc)[0])
        doc["sources"]["processor"][0]["funding_due_source_ref"] = "contract:processor"
        doc["sources"]["network"][0].update(expected_funding_date="2026-07-17", funding_due_source_ref="network:due")
        doc["sources"]["bank_cash"] = []
        group = compute(doc)["groups"][0]
        self.assertEqual(group["pending_items"], [])
        self.assertIn("conflicting", next(i["reason"] for i in group["issues"] if i["type"] == "MISSING_IN_BANK"))

    def test_upstream_error_survives_cash_and_ledger_agreement(self):
        doc = base()
        doc["sources"]["network"][0]["gross"] = "100500.00"
        group = compute(doc)["groups"][0]
        self.assertTrue(any(i["type"] == "GROSS_MISMATCH" for i in group["issues"]))
        self.assertEqual(next(c["status"] for c in group["checks"] if c["type"] == "LEDGER_CASH_MISMATCH"), "within_tolerance")

    def test_missing_ambiguous_wrong_scope_and_expired_schedule(self):
        for change in ("missing", "duplicate", "scope", "expired", "no-rate"):
            with self.subTest(change=change):
                doc = base()
                if change == "missing": doc.pop("fee_schedule")
                if change == "duplicate": doc["fee_schedule"].append(copy.deepcopy(doc["fee_schedule"][0]))
                if change == "scope": doc["fee_schedule"][0]["account_id"] = "wrong-account"
                if change == "expired": doc["fee_schedule"][0]["effective_to"] = "2026-06-30"; doc["fee_schedule"][0]["effective_from"] = "2026-06-01"
                if change == "no-rate": doc["fee_schedule"][0].pop("rate_bps")
                check = next(c for c in compute(doc)["groups"][0]["checks"] if c["type"] == "FEE_VARIANCE")
                self.assertEqual(check["status"], "not_evaluable")

    def test_currency_precision_and_decimal_half_up(self):
        doc = base()
        for source, rows in doc["sources"].items():
            for r in rows: r["currency"] = "KWD"
        doc["config"]["currency_minor_units"] = {"KWD": 3}
        for schedule in doc["fee_schedule"]: schedule["currency"] = "KWD"
        p = doc["sources"]["processor"][0]
        p["gross"] = "1.2345"
        doc["fee_schedule"][0]["rate_bps"] = "100"
        check = next(c for c in compute(doc)["groups"][0]["checks"] if c["type"] == "FEE_VARIANCE")
        self.assertEqual(check["expected"], "0.012")
        doc["fee_schedule"][0]["rate_bps"] = "1000"
        p["gross"] = "1.235"
        check = next(c for c in compute(doc)["groups"][0]["checks"] if c["type"] == "FEE_VARIANCE")
        self.assertEqual(check["expected"], "0.124")

    def test_invalid_boolean_nonfinite_and_tolerance(self):
        for value in (True, False, "NaN", "Infinity", {}, []):
            doc = base()
            doc["sources"]["processor"][0]["net"] = value
            self.assertTrue(validate_input(doc)[0])
            with self.assertRaises(ValueError): compute(doc)
        doc = base()
        doc["config"]["cash_tolerance_abs"] = "-1"
        self.assertTrue(validate_input(doc)[0])

    def test_no_journals_or_fake_closure(self):
        out = compute(base())
        out["corrections"] = [{"type": "journal", "debit_account": "Cash", "credit_account": "Suspense"}]
        self.assertTrue(validate(out))
        out = compute(base())
        out["summary"]["posted"] = True
        self.assertTrue(validate(out))

    def test_source_binding_and_tamper_detection(self):
        doc = base()
        out = compute(doc)
        out["groups"][0]["checks"][0]["observed_minus_expected"] = "123"
        self.assertTrue(validate(out, doc))
        alternative = copy.deepcopy(doc)
        alternative["sources"]["processor"][0]["net"] = "998"
        self.assertIn("authoritative", validate(compute(alternative), doc)[0])

    def test_payout_report_only_accepts_and_surfaces_mismatch(self):
        doc = payout()
        self.assertNotIn("sources", doc)
        out = compute(doc)
        self.assertEqual(validate(out, doc), [])
        p = out["partitions"][0]
        self.assertEqual(p["calculated_net"], "90500.0")
        self.assertEqual(p["effective_fee_rate_pct"], "2.850000")
        check = next(c for c in p["checks"] if c["type"] == "calculated_vs_funding")
        self.assertEqual(check["right_minus_left"], "-500.00")
        self.assertEqual(check["status"], "mismatch")
        self.assertEqual(p["status"], "discrepancy")
        self.assertFalse(out["summary"]["bank_cash_confirmed"])
        self.assertFalse(out["summary"]["ledger_reconciled"])

    def test_unvalued_payout_keeps_known_subtotal_and_unknown_net(self):
        doc = json.loads((FILES / "settlement_example.json").read_text())
        p = compute(doc)["partitions"][0]
        self.assertEqual(p["known_line_subtotal"], "90500.0")
        self.assertIsNone(p["calculated_net"])
        self.assertTrue(p["data_gaps"])
        self.assertEqual(p["status"], "incomplete")

    def test_no_funding_or_fee_line_is_not_zero(self):
        doc = payout()
        doc.pop("funding")
        doc["lines"] = [r for r in doc["lines"] if r["category"] == "gross_sales"]
        p = compute(doc)["partitions"][0]
        self.assertIsNone(p["funding_expected_net"])
        self.assertIsNone(p["total_fees"])
        self.assertIsNone(p["effective_fee_rate_pct"])
        self.assertEqual(validate(compute(doc), doc), [])

    def test_net_control_not_double_counted(self):
        doc = payout()
        net = copy.deepcopy(doc["lines"][0])
        net.update(line_id="NET-CONTROL",category="net_settlement",net_amount="90500")
        net["source"]["ref"] += ";section=net-control"
        doc["lines"].append(net)
        p = compute(doc)["partitions"][0]
        self.assertEqual(p["calculated_net"], "90500.0")
        self.assertEqual(p["reported_net"], "90500")
        self.assertEqual(len(p["reported_net_lines"]), 1)

    def test_report_duplicate_is_quarantined(self):
        doc = payout()
        doc["lines"].append(copy.deepcopy(doc["lines"][0]))
        p = compute(doc)["partitions"][0]
        self.assertIsNone(p["calculated_net"])
        self.assertTrue(any(g["type"] == "AMBIGUOUS_DUPLICATE" for g in p["data_gaps"]))
        self.assertEqual(validate(compute(doc), doc), [])

    def test_payout_partitions_currencies_and_scopes(self):
        for field, value in (("currency", "EUR"), ("legal_entity_id", "other"), ("account_id", "other"), ("settlement_cycle", "other")):
            doc = payout()
            doc["lines"][0][field] = value
            out = compute(doc)
            self.assertEqual(len(out["partitions"]), 2)
            self.assertEqual(sum(p["funding_expected_net"] is not None for p in out["partitions"]), 1)

    def test_payout_sign_and_conflicting_fee_evidence_preserved(self):
        doc = payout()
        fee = next(r for r in doc["lines"] if r["category"] == "processor_fees")
        fee["net_amount"] = "900"
        p = compute(doc)["partitions"][0]
        self.assertTrue({"SIGN_CONVENTION_CONFLICT", "FEE_LINE_CONFLICT"} <= {i["type"] for i in p["issues"]})

    def test_payout_advice_addition_rejected(self):
        out = compute(payout())
        out["narrative"] = "You should switch processors; settlement is verified."
        self.assertTrue(validate(out))

    def test_payout_reused_citation_is_unknown_even_across_partitions(self):
        for field, value in (("currency", "EUR"), ("settlement_cycle", "other")):
            doc = payout()
            extra = copy.deepcopy(doc["lines"][0])
            extra["line_id"] = "renamed-copy"
            extra[field] = value
            doc["lines"].append(extra)
            out = compute(doc)
            self.assertEqual(len(out["partitions"]), 2)
            self.assertTrue(all(p["calculated_net"] is None for p in out["partitions"]))
            self.assertTrue(all(any(g["type"] == "AMBIGUOUS_DUPLICATE" for g in p["data_gaps"]) for p in out["partitions"]))
            self.assertEqual(validate(out, doc), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
