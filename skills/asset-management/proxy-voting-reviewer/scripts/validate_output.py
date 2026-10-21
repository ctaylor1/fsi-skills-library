#!/usr/bin/env python3
"""Validate native subresult and strict outer reconstruction against detached input."""
import argparse,json,sys
from pathlib import Path
from native_integrity import validate_reconstruction
from mode_dispatch import components,validate_request
from calculate_or_transform import compute

def validate(output,original_input=None):
    errors=[]
    if isinstance(original_input,dict):
        input_errors,_=validate_request(original_input);errors.extend(input_errors)
        if not input_errors:
            _,_,native_output=components(original_input['mode'])
            if not isinstance(output,dict) or output.get('mode')!=original_input['mode']:errors.append('result mode differs from original request')
            elif not isinstance(output.get('result'),dict):errors.append('native result must be an object')
            else:errors.extend('native: '+e for e in native_output.validate(output['result'],original_input=original_input['input']))
    validate_reconstruction(output,compute,errors,original_input=original_input)
    return errors

def main(argv):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',nargs='?');p.add_argument('--input',dest='original_input');args=p.parse_args(argv)
    original=json.loads(Path(args.original_input).read_text()) if args.original_input else None
    output=json.loads(Path(args.output).read_text() if args.output else sys.stdin.read());errors=validate(output,original)
    for e in errors:print('ERROR',e)
    print(f'output validation: {len(errors)} error(s)');return bool(errors)
if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
