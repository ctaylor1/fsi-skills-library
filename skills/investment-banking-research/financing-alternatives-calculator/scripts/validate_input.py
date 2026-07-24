#!/usr/bin/env python3
"""Deterministic input validation for financing-alternatives-calculator.

Input schema (JSON): request{request_id,amount_needed,currency,as_of}; alternatives[{alt_id,type,
rate_pct,fees_pct,term_years,share_price,current_shares,source_ref}]. Debt alts use rate/fees/term;
equity alts use share_price/current_shares.

Usage: python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("request", "alternatives"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    if _num(doc["request"].get("amount_needed")) is None:
        errors.append("request.amount_needed not numeric")
    alts = doc.get("alternatives") or []
    if not isinstance(alts, list) or not alts:
        errors.append("alternatives must be a non-empty list")
        return errors, warnings
    for i, a in enumerate(alts):
        tag = f"alternatives[{i}] ({a.get('alt_id','?')})"
        if a.get("alt_id") in (None, ""):
            errors.append(f"{tag}: missing 'alt_id'")
        t = a.get("type")
        if t in (None, ""):
            errors.append(f"{tag}: missing 'type'")
        if t == "equity":
            if _num(a.get("share_price")) in (None, 0):
                warnings.append(f"{tag}: share_price missing/zero — dilution not computable")
            if _num(a.get("current_shares")) is None:
                warnings.append(f"{tag}: current_shares missing — dilution not computable")
        else:
            if _num(a.get("rate_pct")) is None:
                warnings.append(f"{tag}: rate_pct missing — interest not computable")
            if _num(a.get("term_years")) in (None, 0):
                warnings.append(f"{tag}: term_years missing/zero — amortized/total cost not computable")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "request_example.json"
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
