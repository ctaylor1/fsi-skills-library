#!/usr/bin/env python3
"""Produce a source-bound review draft; never acts, approves or delivers."""
from __future__ import annotations
import json
from pathlib import Path
import sys
from domain import compute


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/request_example.json" if "--selftest" in argv else None
    try:
        doc = json.loads(path.read_text() if path else Path(argv[0]).read_text() if argv else sys.stdin.read())
        result = compute(doc)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print("ERROR", exc)
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
