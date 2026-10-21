#!/usr/bin/env python3
"""Validate immutable native output against separately retained original input.

Source binding is reproducibility, not source authentication. Authored narrative
is a separate draft requiring review, never an unchecked field in this object.
"""
import argparse,json,sys
from pathlib import Path
from native_integrity import validate_reconstruction
from calculate_or_transform import compute

def validate(output, original_input=None):
    errors=[]
    validate_reconstruction(output,compute,errors,original_input=original_input)
    return errors

def main(argv):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',nargs='?')
    parser.add_argument('--input',dest='original_input')
    parser.add_argument('--selftest',action='store_true')
    args=parser.parse_args(argv)
    if args.selftest:
        source=_read_json((Path(__file__).resolve().parents[1]/'evals/files/extraction_request.json').read_text())
        output=compute(source)
    else:
        source=_read_json(Path(args.original_input).read_text()) if args.original_input else None
        output=_read_json(Path(args.output).read_text() if args.output else sys.stdin.read())
    errors=validate(output,original_input=source)
    for error in errors:print('ERROR',error)
    print(f'output validation: {len(errors)} error(s)')
    return bool(errors)

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


if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
