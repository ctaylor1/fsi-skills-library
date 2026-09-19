#!/usr/bin/env python3
"""Calculate or transform a household reconciliation JSON artifact."""
import json
import sys
from pathlib import Path
from reconcile import reconcile


def main():
    path = Path(__file__).resolve().parents[1] / "evals/files/household_example.json" if sys.argv[1:] == ["--selftest"] else Path(sys.argv[1]) if len(sys.argv) == 2 else None
    if path is None:
        print("usage: python scripts/calculate_or_transform.py INPUT.json | --selftest")
        return 2
    try:
        doc = json.loads(path.read_text())
        print(json.dumps(reconcile(doc), indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
