#!/usr/bin/env python3
"""Deterministic input validation for model-roll-forward-auditor.

Input schema (JSON): model{model_id,prior_version,current_version}; roll_forward[{line_item,
prior_ending,current_opening,tolerance}].

Usage: python validate_input.py model.json | --selftest
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
    for k in ("model", "roll_forward"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    if not doc["model"].get("model_id"):
        errors.append("model missing 'model_id'")
    items = doc.get("roll_forward") or []
    if not isinstance(items, list) or not items:
        errors.append("roll_forward must be a non-empty list")
        return errors, warnings
    for i, it in enumerate(items):
        tag = f"roll_forward[{i}] ({it.get('line_item','?')})"
        if it.get("line_item") in (None, ""):
            errors.append(f"{tag}: missing 'line_item'")
        if _num(it.get("prior_ending")) is None:
            warnings.append(f"{tag}: prior_ending not numeric — item not tieable (structural break)")
        if _num(it.get("current_opening")) is None:
            warnings.append(f"{tag}: current_opening not numeric — item not tieable (structural break)")
        if it.get("tolerance") is not None and _num(it.get("tolerance")) is None:
            errors.append(f"{tag}: tolerance present but not numeric")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_example.json"
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
