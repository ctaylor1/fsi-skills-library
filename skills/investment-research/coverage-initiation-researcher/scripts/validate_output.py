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
            output=_read_json((base/"coverage_pack_example.json").read_text()); original=_read_json((base/"coverage_dossier_example.json").read_text())
        else:
            output=_read_json(Path(args.output).read_text() if args.output else sys.stdin.read())
            original=_read_json(Path(args.input).read_text()) if args.input else None
        errors=validate(output,original)
    except (ValueError,TypeError,OSError) as exc: errors=["invalid validation input: "+str(exc)]
    for e in errors: print("ERROR",e)
    print(f"output validation: {len(errors)} error(s)")
    return int(bool(errors))
def _read_json(raw, **options):
    """Reject duplicate object keys and nonfinite constants before binding."""
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('duplicate JSON object key: '+key)
            result[key]=value
        return result
    def constant(value): raise ValueError('non-finite JSON constant: '+value)
    options.setdefault('object_pairs_hook',pairs)
    options.setdefault('parse_constant',constant)
    return json.loads(raw,**options)


_phase2_json_main = main

def main(*args, **kwargs):
    try: return _phase2_json_main(*args, **kwargs)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:
        print('ERROR:', str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
