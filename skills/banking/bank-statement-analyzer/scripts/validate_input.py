#!/usr/bin/env python3
"""Deterministic input validation for bank-statement-analyzer.

Validates a statement file before extraction/calculation. Fails closed on structural
problems; warns on data-quality gaps that limit which figures/anomalies are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  account_id, statement_period{start,end} (YYYY-MM-DD), currency, config_version,
  opening_balance?, closing_balance?, config{...thresholds...},
  transactions[{txn_id,date,amount,direction,category?,counterparty?,balance?,source_ref}]

Usage:
  python validate_input.py statement.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("account_id", "statement_period", "config_version", "transactions")
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

    period = doc.get("statement_period") or {}
    for k in ("start", "end"):
        if not DATE_RE.match(str(period.get(k, ""))):
            errors.append(f"statement_period.{k} must be YYYY-MM-DD, got {period.get(k)!r}")
    if not errors and str(period["end"]) < str(period["start"]):
        errors.append("statement_period.end is before statement_period.start")

    txns = doc.get("transactions") or []
    if not isinstance(txns, list) or not txns:
        errors.append("transactions must be a non-empty list")
        return errors, warnings

    ids = set()
    have_balance = 0
    have_category = 0
    out_of_period = 0
    p_start, p_end = str(period.get("start", "")), str(period.get("end", ""))
    for i, t in enumerate(txns):
        tag = f"transactions[{i}] ({t.get('txn_id','?')})"
        for k in REQUIRED_TXN:
            if k not in t or t[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(t.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        elif _num(t.get("amount")) < 0:
            errors.append(f"{tag}: amount must be non-negative (direction encodes sign)")
        if t.get("direction") not in ("debit", "credit"):
            errors.append(f"{tag}: direction must be 'debit' or 'credit'")
        tid = t.get("txn_id")
        if tid in ids:
            errors.append(f"{tag}: duplicate txn_id")
        ids.add(tid)
        if _num(t.get("balance")) is not None:
            have_balance += 1
        if t.get("category"):
            have_category += 1
        d = str(t.get("date", ""))[:10]
        if p_start and p_end and d and not (p_start <= d <= p_end):
            out_of_period += 1

    n = len(txns)
    if have_balance and have_balance < n:
        warnings.append(f"only {have_balance}/{n} rows carry a balance — negative_balance_day is partial")
    if have_balance == 0:
        warnings.append("no rows carry a balance — negative_balance_day not evaluable")
    if have_category < n:
        warnings.append(f"{n - have_category}/{n} rows lack a category — classification uses keyword heuristics")
    if out_of_period:
        warnings.append(f"{out_of_period} transaction(s) fall outside the stated statement_period")
    if "opening_balance" not in doc or "closing_balance" not in doc:
        warnings.append("opening_balance/closing_balance missing — cash-flow tie-out to closing balance not evaluable")
    debits = [t for t in txns if t.get("direction") == "debit"]
    if len(debits) < 10:
        warnings.append(f"thin baseline ({len(debits)} debits) — large_one_off_debit is low-confidence")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "statement_example.json"
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
