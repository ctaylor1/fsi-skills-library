#!/usr/bin/env python3
"""Deterministic input validation for transaction-reconciliation-helper.

Validates a reconciliation input file before matching. Fails closed on structural problems;
warns on data-quality gaps that limit which breaks are evaluable or which tie-outs are
meaningful.

Input schema (JSON): see references/source-map.md. Key fields:
  recon_id, as_of (YYYY-MM-DD), config_version, currency,
  config{amount_tolerance, expected_sources[], cash_rank[], intransit_days},
  records[{record_id, txn_ref, source, level, date, amount, currency, status, source_ref}]

Usage:
  python validate_input.py input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from collections import defaultdict
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("as_of", "config_version", "records")
REQUIRED_REC = ("record_id", "txn_ref", "source", "date", "amount", "source_ref")
KNOWN_SOURCES = {
    "gateway", "processor", "acquirer", "bank", "ledger", "merchant",
    "settlement", "reserve", "fee_batch",
}
KNOWN_LEVELS = {"transaction", "settlement"}


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

    recs = doc.get("records") or []
    if not isinstance(recs, list) or not recs:
        errors.append("records must be a non-empty list")
        return errors, warnings

    ids = set()
    by_ref = defaultdict(set)          # txn_ref -> set(source)
    txn_level_srcs = set()             # transaction-level sources seen
    for i, r in enumerate(recs):
        tag = f"records[{i}] ({r.get('record_id', '?')})"
        for k in REQUIRED_REC:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(r.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        if not DATE_RE.match(str(r.get("date", ""))):
            errors.append(f"{tag}: date must start YYYY-MM-DD")
        rid = r.get("record_id")
        if rid in ids:
            errors.append(f"{tag}: duplicate record_id")
        ids.add(rid)
        src = r.get("source")
        if src and src not in KNOWN_SOURCES:
            warnings.append(f"{tag}: unrecognized source {src!r} — confirm the source taxonomy")
        lvl = r.get("level", "transaction")
        if lvl not in KNOWN_LEVELS:
            warnings.append(f"{tag}: unrecognized level {lvl!r} (expected transaction|settlement)")
        if not r.get("currency"):
            warnings.append(f"{tag}: no currency — currency_mismatch not evaluable for this row")
        ref = r.get("txn_ref")
        if ref and src:
            by_ref[ref].add(src)
            if lvl == "transaction":
                txn_level_srcs.add(src)

    for ref, srcs in by_ref.items():
        if len(srcs) == 1:
            warnings.append(f"txn_ref {ref!r} appears in only one source ({next(iter(srcs))}) — likely unmatched")

    if "ledger" not in txn_level_srcs:
        warnings.append("no transaction-level ledger records — ledger tie-out will be zero-based")
    cash = [s for s in ("bank", "processor", "gateway") if s in txn_level_srcs]
    if not cash:
        warnings.append("no bank/processor/gateway transaction-level records — no cash position of record to tie out")
    if not doc.get("config"):
        warnings.append("no 'config' block — default tolerance/ranking will be used; record the config_version")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ledger_example.json"
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
