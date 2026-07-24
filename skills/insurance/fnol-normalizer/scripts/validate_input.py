#!/usr/bin/env python3
"""Deterministic input validation for fnol-normalizer.

Input schema (JSON): raw_fnol{fnol_id,policy_number,loss_date,reported_date,claimant_name,
loss_type_raw,cause_raw,loss_location_raw,description}; config{loss_type_map{},cause_map{},
required_fields[],config_version}.

Usage: python validate_input.py fnol.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("raw_fnol", "config"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    if not doc["raw_fnol"].get("fnol_id"):
        errors.append("raw_fnol missing 'fnol_id'")
    cfg = doc["config"]
    for m in ("loss_type_map", "cause_map"):
        if not isinstance(cfg.get(m), dict):
            errors.append(f"config.{m} must be an object")
    if not isinstance(cfg.get("required_fields"), list):
        errors.append("config.required_fields must be a list")
    if not cfg.get("config_version"):
        warnings.append("config.config_version missing — record the versioned vocabulary used")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "fnol_example.json"
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
