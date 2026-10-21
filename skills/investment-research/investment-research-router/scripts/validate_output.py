#!/usr/bin/env python3
"""Reconstruct the entire result against the separately retained original input."""
import argparse, json
from pathlib import Path
from domain import compute, validate_document
from native_integrity import validate_reconstruction
ROOT = Path(__file__).resolve().parents[1]
def validate(doc, original_input=None):
    errors=[]
    if original_input is not None:
        try: validate_document(original_input)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc: errors.append("invalid original input: "+str(exc))
    validate_reconstruction(doc, compute, errors, original_input=original_input)
    return errors, []
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?"); parser.add_argument("--input", dest="source"); parser.add_argument("--selftest", action="store_true")
    args=parser.parse_args()
    if not args.selftest and (not args.path or not args.source): parser.error("output path and --input original are required")
    try:
        source=json.loads((ROOT/"evals/files/input.json" if args.selftest else Path(args.source)).read_text())
        result=json.loads((ROOT/"evals/files/valid.json" if args.selftest else Path(args.path)).read_text())
        errors, _=validate(result, source)
    except (OSError, ValueError) as exc: errors=[str(exc)]
    print(f"output validation: {len(errors)} error(s)")
    for error in errors: print("ERROR: "+error)
    return bool(errors)
if __name__=="__main__": raise SystemExit(main())
