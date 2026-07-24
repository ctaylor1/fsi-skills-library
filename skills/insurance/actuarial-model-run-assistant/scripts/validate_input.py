#!/usr/bin/env python3
"""Deterministic input validation for actuarial-model-run-assistant.

Input schema (JSON): triangle{triangle_id,claim_type,origin_periods[],dev_ages[],
cumulative_paid[[...]]}; assumptions{method,tail_factor,config_version}. cumulative_paid is a
row-per-origin matrix; unfilled lower-right cells are null.

Usage: python validate_input.py triangle.json | --selftest
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
    for k in ("triangle", "assumptions"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    t = doc["triangle"]
    origins = t.get("origin_periods")
    ages = t.get("dev_ages")
    mat = t.get("cumulative_paid")
    if not (isinstance(origins, list) and origins):
        errors.append("triangle.origin_periods must be a non-empty list")
    if not (isinstance(ages, list) and ages):
        errors.append("triangle.dev_ages must be a non-empty list")
    if not (isinstance(mat, list) and mat):
        errors.append("triangle.cumulative_paid must be a non-empty matrix")
    if errors:
        return errors, warnings
    if len(mat) != len(origins):
        errors.append(f"cumulative_paid has {len(mat)} rows, expected {len(origins)} origins")
    for i, row in enumerate(mat):
        if not isinstance(row, list) or len(row) != len(ages):
            errors.append(f"cumulative_paid[{i}] must have {len(ages)} columns")
            continue
        filled = [j for j, v in enumerate(row) if v is not None]
        if filled and filled != list(range(len(filled))):
            errors.append(f"cumulative_paid[{i}] filled cells must be leftmost/contiguous (found gaps)")
        for j in filled:
            if _num(row[j]) is None:
                errors.append(f"cumulative_paid[{i}][{j}] not numeric")
    if _num(doc["assumptions"].get("tail_factor")) is None:
        errors.append("assumptions.tail_factor not numeric")
    if not doc["assumptions"].get("config_version"):
        warnings.append("assumptions.config_version missing — record the versioned assumptions used")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "triangle_example.json"
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
