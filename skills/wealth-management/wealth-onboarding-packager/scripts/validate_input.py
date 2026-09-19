#!/usr/bin/env python3
"""Reject malformed input; report incomplete evidence as needs-data findings."""

import json
import sys
from pathlib import Path
from calculate_or_transform import assess


def validate(doc):
    errors, findings = assess(doc)
    return errors, [f["message"] for f in findings]


def main(argv):
    path = (
        Path(__file__).resolve().parents[1] / "evals/files/onboarding_example.json"
        if "--selftest" in argv
        else Path(argv[0])
        if argv
        else None
    )
    try:
        errors, warnings = validate(json.loads(path.read_text() if path else sys.stdin.read()))
    except (ValueError, TypeError, KeyError) as exc:
        errors, warnings = [str(exc)], []
    for message in warnings:
        print("NEEDS-DATA", message)
    for message in errors:
        print("ERROR", message)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} data finding(s)")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
