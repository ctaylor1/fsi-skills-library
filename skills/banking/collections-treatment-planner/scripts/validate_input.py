#!/usr/bin/env python3
"""Deterministic input validation for collections-treatment-planner.

Validates a collections case file before the treatment engine runs. Fails closed on
structural problems (missing identity, bad delinquency figures, malformed contact history);
warns on data-quality gaps that limit which treatments/screens are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  account_id, as_of (YYYY-MM-DD), config_version, product_type, days_past_due, balance,
  minimum_due, past_due_amount, suppression{...flags...}, vulnerability_indicators[],
  preferences{preferred_channel,...}, affordability{disclosed_income_monthly,disclosed_expenses_monthly},
  contact_history[{date,channel,outcome,source_ref}], config{...thresholds...}

Usage:
  python validate_input.py case.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("account_id", "as_of", "config_version", "product_type", "days_past_due", "balance")
KNOWN_PRODUCTS = {"credit_card", "personal_loan", "auto_loan", "mortgage", "line_of_credit", "student_loan", "overdraft"}
KNOWN_CHANNELS = {"phone", "email", "letter", "sms", "secure_message", "in_person"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    dpd = _num(doc.get("days_past_due"))
    if dpd is None:
        errors.append("days_past_due not numeric")
    elif dpd < 0:
        errors.append(f"days_past_due must be >= 0, got {dpd}")

    if _num(doc.get("balance")) is None:
        errors.append("balance not numeric")

    if doc.get("product_type") not in KNOWN_PRODUCTS:
        warnings.append(f"product_type {doc.get('product_type')!r} not in known set — default treatment rules apply; confirm product policy")

    ch = doc.get("contact_history")
    if ch is None:
        warnings.append("no contact_history — the 7-in-7 call-frequency screen cannot be applied; treat phone caps as unknown")
    elif not isinstance(ch, list):
        errors.append("contact_history must be a list")
    else:
        for i, c in enumerate(ch):
            tag = f"contact_history[{i}]"
            if not DATE_RE.match(str(c.get("date", ""))):
                errors.append(f"{tag}: missing/invalid 'date'")
            if not c.get("channel"):
                errors.append(f"{tag}: missing 'channel'")
            elif c.get("channel") not in KNOWN_CHANNELS:
                warnings.append(f"{tag}: unrecognized channel {c.get('channel')!r}")

    sup = doc.get("suppression")
    if sup is None:
        warnings.append("no 'suppression' block — cease-communication/attorney/dispute/DNC flags assumed false; confirm before outreach")
    elif not isinstance(sup, dict):
        errors.append("suppression must be an object of boolean flags")

    aff = doc.get("affordability") or {}
    if not (isinstance(aff.get("disclosed_income_monthly"), (int, float)) and
            isinstance(aff.get("disclosed_expenses_monthly"), (int, float))):
        warnings.append("no disclosed income/expenses — payment_arrangement sizing is not evaluable (indicative only)")

    if not doc.get("vulnerability_indicators"):
        warnings.append("no vulnerability_indicators supplied — enhanced-care screen will not fire; confirm none apply")

    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "collections_case_example.json"
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
