#!/usr/bin/env python3
"""Compute only the explicitly selected mode after native input/output checks."""
import json,sys
from pathlib import Path
from native_integrity import attach_source
from mode_dispatch import components,validate_request

def compute(doc):
    errors,_=validate_request(doc)
    if errors:raise ValueError('; '.join(errors))
    _,calculate,native_output=components(doc['mode'])
    result=calculate(doc['input'])
    errors=native_output.validate(result,original_input=doc['input'])
    if errors:raise ValueError('native result validation failed: '+'; '.join(errors))
    return attach_source({'mode':doc['mode'],'result':result,'action_taken':False},doc)

def main(argv):
    try:
        doc=json.loads(Path(argv[0]).read_text() if argv else sys.stdin.read())
        print(json.dumps(compute(doc),indent=2));return 0
    except (ValueError,TypeError,KeyError,ArithmeticError) as exc:
        print('ERROR',exc,file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
