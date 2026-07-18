#!/usr/bin/env python3
"""Deterministic input validation for commercial-cash-management-advisor.

Validates a de-identified commercial cash profile before service-fit analysis. Fails closed
on structural problems; warns on data-quality gaps that limit which services are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  customer_id, as_of (YYYY-MM-DD), config_version, currency, analysis_period_months,
  operating_buffer, accounts[{account_id,type,avg_collected_balance,avg_ledger_balance,source_ref}],
  activity{checks_issued,checks_deposited,mailed_check_receipts,ach_debits_received,
           card_acceptance_amount,cross_border_amount,overdraft_days,source_ref,...},
  crm{existing_services[],relationship_notes}, config{...thresholds...}

Usage:
  python validate_input.py profile.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("customer_id", "as_of", "config_version", "accounts", "activity")
REQUIRED_ACCOUNT = ("account_id", "type", "avg_collected_balance", "source_ref")
# activity metrics that must be numeric and non-negative when present
ACTIVITY_NUMERIC = (
    "checks_issued", "checks_deposited", "mailed_check_receipts", "ach_debits_received",
    "ach_credits_originated", "wires_out", "wires_in", "card_acceptance_amount",
    "cross_border_amount", "overdraft_days",
)


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

    accounts = doc.get("accounts") or []
    if not isinstance(accounts, list) or not accounts:
        errors.append("accounts must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, a in enumerate(accounts):
        tag = f"accounts[{i}] ({a.get('account_id','?')})"
        for k in REQUIRED_ACCOUNT:
            if k not in a or a[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        bal = _num(a.get("avg_collected_balance"))
        if bal is None:
            errors.append(f"{tag}: avg_collected_balance not numeric")
        elif bal < 0:
            warnings.append(f"{tag}: negative avg_collected_balance — verify overdraft vs. data error")
        aid = a.get("account_id")
        if aid in ids:
            errors.append(f"{tag}: duplicate account_id")
        ids.add(aid)

    act = doc.get("activity") or {}
    if not isinstance(act, dict) or not act:
        errors.append("activity must be a non-empty object")
        return errors, warnings
    if not act.get("source_ref"):
        errors.append("activity: missing 'source_ref' (evidence citations require it)")
    for k in ACTIVITY_NUMERIC:
        if k in act and act[k] not in (None, ""):
            v = _num(act[k])
            if v is None:
                errors.append(f"activity['{k}'] not numeric")
            elif v < 0:
                errors.append(f"activity['{k}'] must be >= 0")

    # data-quality gaps: not errors, but they limit evaluability
    if doc.get("operating_buffer") in (None, ""):
        warnings.append("no operating_buffer — idle balance assumes zero buffer (upper bound, low confidence)")
    if len(accounts) < 2:
        warnings.append("single account — liquidity_structure (pooling/ZBA) is not evaluable")
    if "card_acceptance_amount" not in act:
        warnings.append("no card_acceptance_amount — merchant_services not evaluable")
    if "cross_border_amount" not in act:
        warnings.append("no cross_border_amount — fx_international_services not evaluable")
    if "overdraft_days" not in act:
        warnings.append("no overdraft_days — overdraft_liquidity_referral not evaluable")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "profile_example.json"
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
