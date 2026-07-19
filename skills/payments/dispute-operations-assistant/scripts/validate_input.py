#!/usr/bin/env python3
"""Deterministic input validation for dispute-operations-assistant.

Validates a dispute case file before the deterministic engine runs. Fails closed on
structural problems (missing role/identity/dates/source); warns on data gaps that will force
a `needs-data` or `evidence-insufficient` disposition rather than being guessed away.

Input schema (JSON): see references/source-map.md. Key fields:
  current_rule_version, processing_date, rule_registry{}, cases[
    {case_id, role(issuer|acquirer), network, reason_code, rule_version_cited,
     dispute_received_date, dispute_amount, currency,
     transaction{txn_id, auth_id, amount, currency, txn_date, card_last4, mcc},
     evidence[{type, ref}], source_ref,
     fraud_investigation_required?, merchant_representment_requested?, iso_exception?}]

Usage: python validate_input.py cases.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("current_rule_version", "cases")
REQUIRED_CASE = ("case_id", "role", "network", "reason_code", "rule_version_cited",
                 "dispute_received_date", "source_ref")
ROLES = {"issuer", "acquirer"}


def _is_iso_date(v) -> bool:
    try:
        date.fromisoformat(str(v))
        return True
    except (ValueError, TypeError):
        return False


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if doc.get("processing_date") and not _is_iso_date(doc["processing_date"]):
        errors.append(f"processing_date '{doc['processing_date']}' is not an ISO date")

    cases = doc.get("cases") or []
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, c in enumerate(cases):
        tag = f"cases[{i}] ({c.get('case_id', '?')})"
        for k in REQUIRED_CASE:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        cid = c.get("case_id")
        if cid in ids:
            errors.append(f"{tag}: duplicate case_id")
        ids.add(cid)
        if c.get("role") not in ROLES:
            errors.append(f"{tag}: role must be issuer|acquirer (got {c.get('role')!r})")
        txn = c.get("transaction") or {}
        if not txn.get("txn_id"):
            errors.append(f"{tag}: transaction.txn_id is required (transaction identity)")
        if c.get("dispute_received_date") and not _is_iso_date(c["dispute_received_date"]):
            errors.append(f"{tag}: dispute_received_date '{c.get('dispute_received_date')}' is not an ISO date")

        # data-quality warnings (drive needs-data / evidence-insufficient, not guessed away)
        if txn.get("currency") and c.get("currency") and str(txn["currency"]) != str(c["currency"]):
            warnings.append(f"{tag}: transaction/dispute currency mismatch -> identity issue (needs-data)")
        try:
            if float(c.get("dispute_amount") or 0) > float(txn.get("amount") or 0) and float(txn.get("amount") or 0) > 0:
                warnings.append(f"{tag}: dispute_amount exceeds transaction amount -> identity issue (needs-data)")
        except (TypeError, ValueError):
            warnings.append(f"{tag}: dispute_amount/transaction.amount not numeric")
        if not c.get("evidence"):
            warnings.append(f"{tag}: no evidence supplied -> response will be evidence-insufficient")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "cases_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
