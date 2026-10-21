#!/usr/bin/env python3
"""Validate explicit mode and actual native input."""
import json,sys
from pathlib import Path
from mode_dispatch import validate_request
validate=validate_request

def main(argv):
    doc=json.loads(Path(argv[0]).read_text() if argv else sys.stdin.read())
    errors,warnings=validate(doc)
    for x in warnings:print('WARN',x)
    for x in errors:print('ERROR',x)
    print(f'input validation: {len(errors)} error(s), {len(warnings)} warning(s)')
    return bool(errors)
if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
