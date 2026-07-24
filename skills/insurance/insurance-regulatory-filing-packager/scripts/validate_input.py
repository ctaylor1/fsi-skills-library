#!/usr/bin/env python3
"""Deterministic input validation for insurance-regulatory-filing-packager.

Input schema (JSON): filing{filing_id,filing_type,state,company,effective_date,as_of,
proposed_rate_change_pct}; checklist{required_components[],required_exhibits[],rate_tolerance_pct,
min_notice_days,indicated_rate_change_pct,config_version}; components[{type,present,source_ref}];
exhibits[{exhibit_id,present,source_ref}].

Usage: python validate_input.py filing.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQ_TOP = ("filing", "checklist", "components", "exhibits")
REQ_FILING = ("filing_id", "filing_type", "as_of", "effective_date")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQ_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    f = doc["filing"]
    for k in REQ_FILING:
        if f.get(k) in (None, ""):
            errors.append(f"filing missing '{k}'")
    if f.get("filing_type") not in ("rate", "form", "rule"):
        errors.append("filing.filing_type must be one of rate|form|rule")
    ck = doc["checklist"]
    if not isinstance(ck.get("required_components"), list):
        errors.append("checklist.required_components must be a list")
    for name, key in (("components", "type"), ("exhibits", "exhibit_id")):
        items = doc.get(name)
        if not isinstance(items, list):
            errors.append(f"{name} must be a list")
            continue
        for i, it in enumerate(items):
            if it.get(key) in (None, ""):
                errors.append(f"{name}[{i}]: missing '{key}'")
            if not (it.get("source_ref") or "").strip():
                warnings.append(f"{name}[{i}] ({it.get(key,'?')}): missing source_ref")
    if f.get("filing_type") == "rate" and ck.get("indicated_rate_change_pct") is None:
        warnings.append("rate filing without checklist.indicated_rate_change_pct — rate_support not evaluable")
    if not ck.get("config_version"):
        warnings.append("checklist.config_version missing — record the versioned checklist used")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "filing_example.json"
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
