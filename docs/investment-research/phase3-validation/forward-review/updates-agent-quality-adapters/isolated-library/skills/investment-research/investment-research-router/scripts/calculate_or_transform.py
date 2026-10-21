#!/usr/bin/env python3
"""Compute a bounded native draft from valid supplied JSON."""
import argparse, json
from pathlib import Path
from domain import compute
assemble = compute
ROOT = Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?"); parser.add_argument("--selftest", action="store_true")
    args=parser.parse_args()
    if not args.selftest and not args.path: parser.error("input path required")
    try:
        doc=json.loads((ROOT/"evals/files/input.json" if args.selftest else Path(args.path)).read_text())
        result=compute(doc)
        print(json.dumps(result, indent=2, allow_nan=False))
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
        print("ERROR: "+str(exc)); return 1
    return 0
if __name__=="__main__": raise SystemExit(main())
