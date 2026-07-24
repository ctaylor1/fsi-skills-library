#!/usr/bin/env python3
"""Deterministic input validation for desk-pnl-risk-attribution-pack.

Input schema (JSON): desk{desk_id,book,as_of}; reported_pnl (number); tolerance_abs (number);
config_version; components[{name,value,source_ref}].

Usage: python validate_input.py pnl.json | --selftest
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
    for k in ("desk", "reported_pnl", "components", "tolerance_abs"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    if not doc["desk"].get("desk_id"):
        errors.append("desk missing 'desk_id'")
    if _num(doc.get("reported_pnl")) is None:
        errors.append("reported_pnl not numeric")
    if _num(doc.get("tolerance_abs")) is None:
        errors.append("tolerance_abs not numeric (a tolerance is required; it is never invented)")
    comps = doc.get("components") or []
    if not isinstance(comps, list) or not comps:
        errors.append("components must be a non-empty list")
        return errors, warnings
    for i, c in enumerate(comps):
        if c.get("name") in (None, ""):
            errors.append(f"components[{i}]: missing 'name'")
        if _num(c.get("value")) is None:
            warnings.append(f"components[{i}] ({c.get('name','?')}): value not numeric — excluded, residual marked incomplete")
        if not (c.get("source_ref") or "").strip():
            warnings.append(f"components[{i}] ({c.get('name','?')}): missing source_ref")
    if not doc.get("config_version"):
        warnings.append("config_version missing — record the versioned attribution config used")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pnl_example.json"
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
