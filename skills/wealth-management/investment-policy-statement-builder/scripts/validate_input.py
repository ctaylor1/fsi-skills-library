#!/usr/bin/env python3
"""Check structural validity and report explicit incomplete domain evidence."""

import json
import sys
from pathlib import Path
from calculate_or_transform import inspect


def validate(doc):
    errors, findings, _ = inspect(doc)
    return errors, findings


def main(argv):
    path = (
        Path(__file__).resolve().parents[1] / "evals/files/request_example.json"
        if "--selftest" in argv
        else Path(argv[0])
        if argv
        else None
    )
    try:
        errors, findings = validate(json.loads(path.read_text() if path else sys.stdin.read()))
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        errors, findings = [str(exc)], []
    for row in findings:
        print("NEEDS-DATA", row["path"], row["message"])
    for error in errors:
        print("ERROR", error)
    print(f"input validation: {len(errors)} error(s), {len(findings)} finding(s)")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
