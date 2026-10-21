#!/usr/bin/env python3
"""Validate exact native reconstruction against a separately retained original input.

No embedded source snapshot, extra narrative, source authentication or action authority.
Write audience-specific narrative as a separate reviewed artifact.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from native_integrity import validate_reconstruction

def validate(output, original_input=None):
    import importlib.util
    source=Path(__file__).with_name("calculate_or_transform.py")
    spec=importlib.util.spec_from_file_location("_native_compute_"+Path(__file__).parents[1].name.replace("-","_"),source)
    producer=importlib.util.module_from_spec(spec); spec.loader.exec_module(producer)
    errors=[]
    validate_reconstruction(output,producer.compute,errors,original_input=original_input)
    return errors

def main(argv):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",nargs="?"); parser.add_argument("--input"); parser.add_argument("--selftest",action="store_true")
    args=parser.parse_args(argv)
    try:
        base=Path(__file__).resolve().parents[1]/"evals/files"
        if args.selftest:
            output=json.loads((base/"changelog_example.json").read_text()); original=json.loads((base/"docs_example.json").read_text())
        else:
            output=json.loads(Path(args.output).read_text() if args.output else sys.stdin.read())
            original=json.loads(Path(args.input).read_text()) if args.input else None
        errors=validate(output,original)
    except (ValueError,TypeError,OSError) as exc: errors=["invalid validation input: "+str(exc)]
    for e in errors: print("ERROR",e)
    print(f"output validation: {len(errors)} error(s)")
    return int(bool(errors))
if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
