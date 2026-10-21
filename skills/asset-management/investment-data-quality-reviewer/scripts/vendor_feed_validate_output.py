#!/usr/bin/env python3
"""Validate immutable native output against separately retained original input.

Source binding is reproducibility, not source authentication. Authored narrative
is a separate draft requiring review, never an unchecked field in this object.
"""
import argparse,json,sys
from pathlib import Path
from native_integrity import validate_reconstruction
from vendor_feed_calculate_or_transform import compute

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
        source=json.loads((Path(__file__).resolve().parents[1]/'evals/files/feed_reconciliation_example.json').read_text())
        output=compute(source)
    else:
        source=json.loads(Path(args.original_input).read_text()) if args.original_input else None
        output=json.loads(Path(args.output).read_text() if args.output else sys.stdin.read())
    errors=validate(output,original_input=source)
    for error in errors:print('ERROR',error)
    print(f'output validation: {len(errors)} error(s)')
    return bool(errors)

if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
