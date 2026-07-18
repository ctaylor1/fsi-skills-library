#!/usr/bin/env python3
"""Deterministic input validation for post-trade-settlement-monitor.

Validates a settlement-monitoring snapshot before alert computation. Fails closed on
structural problems; warns on data-quality gaps that limit which alert rules are evaluable
or that disable deduplication / freshness handling.

Input schema (JSON): see references/source-map.md. Key fields:
  run_id, as_of (YYYY-MM-DDThh:mm:ss), config_version, market, config{...thresholds...},
  open_alerts[{dedup_key,status}], instructions[{
    instruction_id, trade_id, security_id, isin, counterparty, direction,
    quantity, cash_amount, currency, trade_date, intended_settlement_date (YYYY-MM-DD),
    status (matched|unmatched|affirmed|pending|settled|failed), cutoff_time,
    penalty_accrued, source_ref, source_as_of}]

Usage:
  python validate_input.py snapshot.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
REQUIRED_TOP = ("run_id", "as_of", "config_version", "instructions")
REQUIRED_INSTR = ("instruction_id", "trade_id", "intended_settlement_date", "status", "source_ref")
STATUSES = {"matched", "unmatched", "affirmed", "pending", "settled", "failed"}


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

    if not DATETIME_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must be a YYYY-MM-DDThh:mm datetime, got {doc['as_of']!r}")

    instrs = doc.get("instructions") or []
    if not isinstance(instrs, list) or not instrs:
        errors.append("instructions must be a non-empty list")
        return errors, warnings

    ids = set()
    has_cutoff = 0
    has_freshness = 0
    for i, t in enumerate(instrs):
        tag = f"instructions[{i}] ({t.get('instruction_id','?')})"
        for k in REQUIRED_INSTR:
            if k not in t or t[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        st = t.get("status")
        if st is not None and st not in STATUSES:
            errors.append(f"{tag}: status {st!r} not in {sorted(STATUSES)}")
        if not DATE_RE.match(str(t.get("intended_settlement_date", ""))):
            errors.append(f"{tag}: intended_settlement_date must be YYYY-MM-DD")
        if "cash_amount" in t and _num(t.get("cash_amount")) is None:
            errors.append(f"{tag}: cash_amount not numeric")
        if "penalty_accrued" in t and _num(t.get("penalty_accrued")) is None:
            errors.append(f"{tag}: penalty_accrued not numeric")
        iid = t.get("instruction_id")
        if iid in ids:
            errors.append(f"{tag}: duplicate instruction_id")
        ids.add(iid)
        if t.get("cutoff_time"):
            has_cutoff += 1
        if t.get("source_as_of"):
            has_freshness += 1
        else:
            warnings.append(f"{tag}: no source_as_of — freshness/staleness not evaluable for this row")
        if not t.get("cash_amount"):
            warnings.append(f"{tag}: no cash_amount — material_cash_impact not evaluable for this row")

    # dedup wiring
    open_alerts = doc.get("open_alerts")
    if open_alerts is None:
        warnings.append("no 'open_alerts' — deduplication is disabled; every alert will be treated as new")
    elif isinstance(open_alerts, list):
        for j, a in enumerate(open_alerts):
            if not a.get("dedup_key"):
                errors.append(f"open_alerts[{j}]: missing 'dedup_key'")

    if has_cutoff == 0:
        warnings.append("no instruction has cutoff_time — unmatched_near_cutoff and cutoff_breach are not evaluable")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "settlement_snapshot.json"
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
