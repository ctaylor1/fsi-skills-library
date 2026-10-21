#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from native_integrity import validate_reconstruction
from calculate_or_transform import compute

def validate(doc, original_input=None):
    errors=[]
    validate_reconstruction(doc,compute,errors,original_input=original_input)
    return errors,[]

if __name__ == "__main__":
    parser=argparse.ArgumentParser();parser.add_argument("output");parser.add_argument("--input",required=True);args=parser.parse_args()
    try: errors,warnings=validate(json.loads(Path(args.output).read_text()),json.loads(Path(args.input).read_text()))
    except (ValueError,TypeError,OSError) as exc: errors=[str(exc)];warnings=[]
    print(json.dumps({"errors":errors,"warnings":warnings}));raise SystemExit(bool(errors))
