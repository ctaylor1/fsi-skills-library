#!/usr/bin/env python3
"""Deterministic input validation for payment-exception-investigator.

Validates a payment-exception batch before investigation. Fails closed (exit 1) on
structural problems; warns on data gaps that force a `needs-data` disposition so the
investigator never guesses to clear an exception.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, reason_code_set_version, as_of, open_cases[], exceptions[
    {exception_id, case_ref, exception_type, scheme,
     identifiers{uetr, instruction_id, end_to_end_id, transaction_id},
     amount{currency, value}, parties{debtor, creditor, debtor_agent, creditor_agent},
     sanctions_hold, fraud_indicator,
     messages[{msg_type, direction, timestamp, status, reason_code, reason_source, msg_ref}]}]

Usage: python validate_input.py exceptions.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "exceptions")
REQUIRED_EX = ("exception_id", "exception_type", "scheme")
ID_KEYS = ("uetr", "instruction_id", "end_to_end_id", "transaction_id")
RECALL_TYPES = {"recall_requested"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    exceptions = doc.get("exceptions") or []
    if not isinstance(exceptions, list) or not exceptions:
        errors.append("exceptions must be a non-empty list")
        return errors, warnings

    if not doc.get("as_of"):
        warnings.append("no 'as_of' date -> aging contribution to priority will be skipped")
    if doc.get("open_cases") is None:
        warnings.append("no open_cases provided -> duplicate linkage limited")

    ids = set()
    for i, ex in enumerate(exceptions):
        tag = f"exceptions[{i}] ({ex.get('exception_id','?')})"
        for k in REQUIRED_EX:
            if not ex.get(k):
                errors.append(f"{tag}: missing '{k}'")
        xid = ex.get("exception_id")
        if xid in ids:
            errors.append(f"{tag}: duplicate exception_id")
        ids.add(xid)

        idents = ex.get("identifiers") or {}
        if not any(idents.get(k) for k in ID_KEYS):
            warnings.append(f"{tag}: no payment identifier -> needs-data")

        msgs = ex.get("messages")
        if msgs is None or not isinstance(msgs, list) or not msgs:
            warnings.append(f"{tag}: no messages -> chronology cannot be built (needs-data)")
        else:
            for j, m in enumerate(msgs):
                if not m.get("msg_type") or not m.get("timestamp"):
                    errors.append(f"{tag}: messages[{j}] requires 'msg_type' and 'timestamp'")
                if not m.get("msg_ref"):
                    warnings.append(f"{tag}: messages[{j}] missing 'msg_ref' -> evidence item will be uncited")

        amt = ex.get("amount") or {}
        if amt.get("value") is None or not amt.get("currency"):
            warnings.append(f"{tag}: amount missing currency/value -> priority/evidence incomplete")

        if ex.get("exception_type") in RECALL_TYPES and not any(
                (m or {}).get("msg_type") == "camt.056" for m in (msgs or [])):
            warnings.append(f"{tag}: recall_requested but no camt.056 present -> recall handling limited")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "exceptions_example.json"
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
