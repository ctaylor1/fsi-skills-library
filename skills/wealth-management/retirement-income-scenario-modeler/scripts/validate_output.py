#!/usr/bin/env python3
"""Reconstruct complete artifact from its full input snapshot; never trust summaries."""

import json
import sys
from pathlib import Path
from calculate_or_transform import SKILL, compute
from wealth_contract import validate_output_envelope


def validate(doc):
    errors = validate_output_envelope(doc, SKILL)
    if errors:
        return errors
    snapshot = doc.get("input_snapshot")
    if not isinstance(snapshot, dict):
        return ["input_snapshot is required"]
    try:
        expected = compute(snapshot)
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        return ["input_snapshot rejected: " + str(exc)]
    if doc != expected:
        return [
            "Artifact does not match full reconstruction: evidence, arithmetic, findings, narrative or posture altered"
        ]
    return []


def main(argv):
    path = (
        Path(__file__).resolve().parents[1] / "evals/files/output_example.json"
        if "--selftest" in argv
        else Path(argv[0])
        if argv
        else None
    )
    try:
        errors = validate(json.loads(path.read_text() if path else sys.stdin.read()))
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("ERROR", error)
    print(f"output validation: {len(errors)} error(s)")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
