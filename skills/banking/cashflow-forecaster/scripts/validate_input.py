#!/usr/bin/env python3
"""Deterministic input validation for cashflow-forecaster.

Validates a forecast-input file before projection. Fails closed on structural problems;
warns on data-quality gaps that reduce confidence (thin history, missing categories,
assumptions outside the horizon).

Input schema (JSON): see references/source-map.md. Key fields:
  entity_id, as_of (YYYY-MM-DD), period ('month'|'week'), horizon_periods (int > 0),
  opening_balance (number), config_version, config{...factors/tolerance...},
  assumptions[{id,description,offset,amount,direction,provenance}],
  transactions[{txn_id,date,amount,direction,category,counterparty,source_ref}]

Usage:
  python validate_input.py forecast_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("entity_id", "as_of", "period", "horizon_periods", "opening_balance",
                "config_version", "transactions")
REQUIRED_TXN = ("txn_id", "date", "amount", "direction", "source_ref")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _int(v):
    try:
        return int(v)
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
    if doc["period"] not in ("month", "week"):
        errors.append(f"period must be 'month' or 'week', got {doc['period']!r}")
    horizon = _int(doc["horizon_periods"])
    if horizon is None or horizon <= 0:
        errors.append(f"horizon_periods must be a positive integer, got {doc['horizon_periods']!r}")
    if _num(doc["opening_balance"]) is None:
        errors.append(f"opening_balance not numeric: {doc['opening_balance']!r}")

    txns = doc.get("transactions") or []
    if not isinstance(txns, list) or not txns:
        errors.append("transactions must be a non-empty list")
        return errors, warnings

    ids, missing_cat = set(), 0
    keys = set()
    for i, t in enumerate(txns):
        tag = f"transactions[{i}] ({t.get('txn_id','?')})"
        for k in REQUIRED_TXN:
            if k not in t or t[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(t.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        elif _num(t.get("amount")) < 0:
            errors.append(f"{tag}: amount must be non-negative (direction carries sign)")
        if t.get("direction") not in ("debit", "credit"):
            errors.append(f"{tag}: direction must be 'debit' or 'credit'")
        tid = t.get("txn_id")
        if tid in ids:
            errors.append(f"{tag}: duplicate txn_id")
        ids.add(tid)
        d = str(t.get("date", ""))
        if not t.get("category") and not t.get("counterparty"):
            missing_cat += 1
        if DATE_RE.match(d):
            keys.add(d[:7] if doc["period"] == "month" else d[:10])

    # assumptions (optional)
    for i, a in enumerate(doc.get("assumptions") or []):
        tag = f"assumptions[{i}] ({a.get('id','?')})"
        if not a.get("id"):
            errors.append(f"{tag}: missing 'id'")
        if _num(a.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        if a.get("direction") not in ("debit", "credit"):
            errors.append(f"{tag}: direction must be 'debit' or 'credit'")
        off = _int(a.get("offset"))
        if off is None or off < 1:
            errors.append(f"{tag}: offset must be a positive integer (period index into the horizon)")
        elif horizon is not None and off > horizon:
            warnings.append(f"{tag}: offset {off} is beyond horizon {horizon}; it will not affect the forecast")
        if not (a.get("provenance") or "").strip():
            warnings.append(f"{tag}: no provenance; will default to 'user-supplied'")

    min_hist = _int((doc.get("config") or {}).get("min_history_periods")) or 3
    n_hist = len(keys)
    if n_hist < min_hist:
        warnings.append(f"thin history ({n_hist} distinct {doc['period']} periods < {min_hist}) "
                        f"— averages and volatility are low-confidence")
    if missing_cat:
        warnings.append(f"{missing_cat} txn(s) have neither category nor counterparty — "
                        f"driver attribution will bucket them as 'Uncategorized'")
    if not doc.get("config"):
        warnings.append("no 'config' block — default scenario factors will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "forecast_input_example.json"
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
