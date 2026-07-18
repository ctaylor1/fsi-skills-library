#!/usr/bin/env python3
"""Deterministic input validation for account-anomaly-screener.

Validates an activity file before signal computation. Fails closed on structural problems;
warns on data-quality gaps that limit which signals are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  account_id, as_of (YYYY-MM-DD), config_version, lookback_days, focal_txn_ids[],
  transactions[{txn_id,date,amount,direction,channel,counterparty,country,source_ref}],
  crm{travel_notice_countries[],known_payees[]}, config{...thresholds...}

Usage:
  python validate_input.py activity.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from datetime import datetime
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("account_id", "as_of", "config_version", "focal_txn_ids", "transactions")
REQUIRED_TXN = ("txn_id", "date", "amount", "direction", "source_ref")


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

    txns = doc.get("transactions") or []
    if not isinstance(txns, list) or not txns:
        errors.append("transactions must be a non-empty list")
        return errors, warnings

    ids = set()
    has_time = 0
    for i, t in enumerate(txns):
        tag = f"transactions[{i}] ({t.get('txn_id','?')})"
        for k in REQUIRED_TXN:
            if k not in t or t[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(t.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        if t.get("direction") not in ("debit", "credit"):
            errors.append(f"{tag}: direction must be 'debit' or 'credit'")
        tid = t.get("txn_id")
        if tid in ids:
            errors.append(f"{tag}: duplicate txn_id")
        ids.add(tid)
        if "T" in str(t.get("date", "")):
            has_time += 1
        if not t.get("country"):
            warnings.append(f"{tag}: no country — geo_novelty not evaluable for this row")
        if not t.get("counterparty"):
            warnings.append(f"{tag}: no counterparty — new_counterparty signal not evaluable for this row")

    for fid in doc["focal_txn_ids"]:
        if fid not in ids:
            errors.append(f"focal_txn_ids references unknown txn_id {fid!r}")

    if has_time == 0:
        warnings.append("no transaction has a time component — velocity and rapid_in_out are not evaluable")
    baseline_n = len(txns) - len(doc["focal_txn_ids"])
    if baseline_n < 10:
        warnings.append(f"thin baseline ({baseline_n} non-focal txns) — amount_vs_history is low-confidence")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "activity_example.json"
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
