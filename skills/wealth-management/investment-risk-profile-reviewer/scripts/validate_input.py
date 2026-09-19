#!/usr/bin/env python3
"""Validate the documented investment-risk-profile-reviewer JSON contract; no external calls."""
from __future__ import annotations
import json
from pathlib import Path
import sys
from domain import validate_input as validate


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/request_example.json" if "--selftest" in argv else None
    try:
        doc = json.loads(path.read_text() if path else Path(argv[0]).read_text() if argv else sys.stdin.read())
        errors = validate(doc)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("ERROR", error)
    print(f"input validation: {len(errors)} error(s)")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
