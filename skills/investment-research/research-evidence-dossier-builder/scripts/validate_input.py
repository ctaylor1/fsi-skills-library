#!/usr/bin/env python3
"""Validate the native input; semantic evidence gaps remain in the result."""
import argparse, json
from pathlib import Path
from domain import validate_document
ROOT = Path(__file__).resolve().parents[1]
def validate(doc):
    errors = []
    try: validate_document(doc)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc: errors.append(str(exc))
    return errors, []
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?"); parser.add_argument("--selftest", action="store_true")
    args=parser.parse_args()
    if not args.selftest and not args.path: parser.error("input path required")
    try:
        doc=json.loads((ROOT/"evals/files/input.json" if args.selftest else Path(args.path)).read_text())
        errors, _=validate(doc)
    except (OSError, ValueError) as exc: errors=[str(exc)]
    print(f"input validation: {len(errors)} error(s)")
    for error in errors: print("ERROR: "+error)
    return bool(errors)
if __name__=="__main__": raise SystemExit(main())
