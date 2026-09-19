#!/usr/bin/env python3
"""Validate actual discovery content, missingness, lineage, and the common no-action envelope."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from wealth_contract import validate_output_envelope
from calculate_or_transform import build, SKILL

def validate(doc):
    errors = validate_output_envelope(doc, SKILL)
    if not isinstance(doc, dict) or not isinstance(doc.get("result"), dict):
        return errors
    try:
        expected = build(doc["result"].get("input_snapshot"))
        if doc != expected:
            errors.append("output content, member/goal identities, counts, findings, or input hash differs from the source snapshot")
    except (ValueError, KeyError, TypeError) as exc:
        errors.append(f"invalid discovery source snapshot: {exc}")
    return errors

def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/discovery_output.json" if "--selftest" in argv else None
    doc = json.loads(path.read_text() if path else Path(argv[0]).read_text() if argv else sys.stdin.read())
    errors = validate(doc)
    for error in errors:
        print("ERROR", error)
    print(f"output validation: {len(errors)} error(s)")
    return bool(errors)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
