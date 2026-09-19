#!/usr/bin/env python3
"""Validate output a household reconciliation JSON artifact."""
import json
import sys
from pathlib import Path
from reconcile import validate_output


def main():
    path = Path(__file__).resolve().parents[1] / "evals/files/household_example.json" if sys.argv[1:] == ["--selftest"] else Path(sys.argv[1]) if len(sys.argv) == 2 else None
    if path is None:
        print("usage: python scripts/validate_output.py INPUT.json | --selftest")
        return 2
    try:
        doc = json.loads(path.read_text())
        if sys.argv[1:] == ["--selftest"]:
            from reconcile import reconcile
            doc = reconcile(doc)
        errors = validate_output(doc)
        print(json.dumps({"errors": errors}))
        return int(bool(errors))
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
