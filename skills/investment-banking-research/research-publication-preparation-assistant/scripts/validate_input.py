#!/usr/bin/env python3
"""Deterministic input validation for research-publication-preparation-assistant.

Input schema (JSON): note{note_id,ticker,analyst,rating,prior_rating,target_price,prior_target,
currency}; disclosures{required[],present[]}; restricted_list[]; rating_scale[]; checklist{
required_items[],present_items[],config_version}.

Usage: python validate_input.py note.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("note", "disclosures", "restricted_list", "rating_scale", "checklist"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    note = doc["note"]
    for k in ("note_id", "ticker", "rating"):
        if not note.get(k):
            errors.append(f"note missing '{k}'")
    if not isinstance(doc["rating_scale"], list) or not doc["rating_scale"]:
        errors.append("rating_scale must be a non-empty list")
    for key in ("required", "present"):
        if not isinstance(doc["disclosures"].get(key), list):
            errors.append(f"disclosures.{key} must be a list")
    if not isinstance(doc["restricted_list"], list):
        errors.append("restricted_list must be a list")
    if not isinstance(doc["checklist"].get("required_items"), list):
        errors.append("checklist.required_items must be a list")
    if note.get("target_price") is not None:
        try:
            float(note["target_price"])
        except (TypeError, ValueError):
            errors.append("note.target_price present but not numeric")
    if not doc["checklist"].get("config_version"):
        warnings.append("checklist.config_version missing — record the versioned configs used")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "note_example.json"
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
