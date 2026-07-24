#!/usr/bin/env python3
"""Deterministic input validation for order-allocation-validator.

Input schema (JSON): order{order_id,security,executed_qty,avg_price,order_ts,batch_cutoff,
trade_date}; policy{method,tolerance_pct,lot_size,config_version}; allocations[{account_id,
proposed_qty,participation_weight,eligible,allocation_ts,deviation_reason,source_ref}].

Usage: python validate_input.py alloc.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQ_TOP = ("order", "policy", "allocations")
REQ_ORDER = ("order_id", "executed_qty", "order_ts", "batch_cutoff")
REQ_LINE = ("account_id", "proposed_qty", "participation_weight", "allocation_ts", "source_ref")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQ_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    o = doc["order"]
    for k in REQ_ORDER:
        if o.get(k) in (None, ""):
            errors.append(f"order missing '{k}'")
    if _num(o.get("executed_qty")) is None:
        errors.append("order.executed_qty not numeric")
    lines = doc.get("allocations") or []
    if not isinstance(lines, list) or not lines:
        errors.append("allocations must be a non-empty list")
        return errors, warnings
    wsum = 0.0
    for i, a in enumerate(lines):
        tag = f"allocations[{i}] ({a.get('account_id','?')})"
        for k in REQ_LINE:
            if a.get(k) in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(a.get("proposed_qty")) is None:
            errors.append(f"{tag}: proposed_qty not numeric")
        w = _num(a.get("participation_weight"))
        if w is None:
            errors.append(f"{tag}: participation_weight not numeric")
        else:
            wsum += w
        if a.get("eligible") is None:
            warnings.append(f"{tag}: no 'eligible' flag — eligibility not evaluable")
    if abs(wsum - 1.0) > 0.01 and doc["policy"].get("method", "pro_rata") == "pro_rata":
        warnings.append(f"participation weights sum to {wsum:.4f}, expected ~1.0 (pro_rata targets may not reconcile)")
    if not doc["policy"].get("config_version"):
        warnings.append("policy.config_version missing — record the versioned policy used")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "allocation_example.json"
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
