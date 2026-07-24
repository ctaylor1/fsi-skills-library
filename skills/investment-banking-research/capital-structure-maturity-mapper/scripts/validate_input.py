#!/usr/bin/env python3
"""Deterministic input validation for capital-structure-maturity-mapper.

Input schema (JSON): company{company_id,name,as_of}; instruments[{instrument_id,type,seniority,
principal,currency,coupon_pct,maturity_date,secured,source_ref}].

Usage: python validate_input.py debt.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQ_INSTR = ("instrument_id", "seniority", "principal")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("company", "instruments"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    if not doc["company"].get("as_of"):
        errors.append("company missing 'as_of' (weighted-average maturity is measured from it)")
    instrs = doc.get("instruments") or []
    if not isinstance(instrs, list) or not instrs:
        errors.append("instruments must be a non-empty list")
        return errors, warnings
    currencies = set()
    for i, it in enumerate(instrs):
        tag = f"instruments[{i}] ({it.get('instrument_id','?')})"
        for k in REQ_INSTR:
            if it.get(k) in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(it.get("principal")) is None:
            errors.append(f"{tag}: principal not numeric")
        if not it.get("maturity_date"):
            warnings.append(f"{tag}: no maturity_date — bucketed as undated")
        currencies.add(it.get("currency"))
    if len({c for c in currencies if c}) > 1:
        warnings.append(f"multiple currencies present {sorted(c for c in currencies if c)} — totals grouped, not summed across currency")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "debt_example.json"
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
