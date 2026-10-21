#!/usr/bin/env python3
"""Reconstruct the exact native result against separately retained original input.

All fields, including supplied evidence, are bound. Unknown fields and added narrative
are rejected. Keep human narrative and workflow approval envelopes separate. Hashing and
reconstruction establish repeatability, never source truth, professional approval or
permission to execute. Usage: validate_output.py OUTPUT.json --input INPUT.json.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path
from native_integrity import validate_reconstruction
_spec = importlib.util.spec_from_file_location(__name__ + "_calculator", Path(__file__).with_name("calculate_or_transform.py"))
_calc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_calc)

def validate(doc, original_input=None):
    errors = []
    validate_reconstruction(doc, _calc.compute, errors, original_input=original_input)
    return errors

def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?")
    parser.add_argument("--input")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    base = Path(__file__).resolve().parents[1]/"evals/files"
    if args.selftest:
        source_path, output_path = base/"change_example.json", base/"pack_example.json"
    elif not args.input or not args.output:
        parser.error("OUTPUT and --input INPUT are required; embedded source_input is forbidden")
    else:
        source_path, output_path = Path(args.input), Path(args.output)
    try:
        source = json.loads(source_path.read_text())
        output = json.loads(output_path.read_text())
        errors = validate(output, original_input=source)
    except (ValueError, TypeError, OSError) as exc:
        errors = [str(exc)]
    for error in errors: print("ERROR", error)
    print(f"output validation: {len(errors)} error(s)")
    return bool(errors)
if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
