#!/usr/bin/env python3
"""Validate source evidence before read-only calculation."""
import json
import sys
from pathlib import Path
from calculate_or_transform import validate_input as validate


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/ledger_example.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    try:
        errors, warnings = validate(json.loads(path.read_text() if path else sys.stdin.read(), parse_float=str))
    except (ValueError, TypeError, OSError) as exc:
        errors, warnings = [str(exc)], []
    for warning in warnings:
        print("WARN", warning)
    for error in errors:
        print("ERROR", error)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
