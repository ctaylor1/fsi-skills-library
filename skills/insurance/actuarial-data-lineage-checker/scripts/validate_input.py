#!/usr/bin/env python3
"""Deterministic input validation for actuarial-data-lineage-checker.

Input schema (JSON): as_of, config_version, current[{key,metric,period,value,
definition_version,documented_reason?,source_ref}], prior[{key,metric,period,value,source_ref}],
expected_periods[], config{movement_pct,definition_baseline_version}.

Usage: python validate_input.py data.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQ_TOP = ("as_of", "current")
REQ_REC = ("key", "metric", "period", "value", "source_ref")


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
    cur = doc.get("current") or []
    if not isinstance(cur, list) or not cur:
        errors.append("current must be a non-empty list")
        return errors, warnings
    for i, r in enumerate(cur):
        tag = f"current[{i}]"
        for k in REQ_REC:
            if r.get(k) in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(r.get("value")) is None:
            errors.append(f"{tag}: value not numeric")
        if not r.get("definition_version"):
            warnings.append(f"{tag}: no definition_version — definition_shift not evaluable")
    if not doc.get("prior"):
        warnings.append("no prior dataset — movement checks limited (records treated as new_series)")
    if not doc.get("expected_periods"):
        warnings.append("no expected_periods — missing_period check disabled")
    if not doc.get("config_version"):
        warnings.append("no config_version — record the versioned reconciliation config")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "data_example.json"
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
