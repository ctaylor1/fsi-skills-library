#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
from analysis_contract import load_json
from domain import compute,validate_document
from native_integrity import validate_reconstruction
ROOT=Path(__file__).resolve().parents[1]
def validate(output,original_input=None):
    errors=[]
    if original_input is not None:
        try:validate_document(original_input)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError) as exc:errors.append(str(exc))
    validate_reconstruction(output,compute,errors,original_input=original_input)
    return errors,[]
def main():
    p=argparse.ArgumentParser();p.add_argument('path',nargs='?');p.add_argument('--input');p.add_argument('--selftest',action='store_true');a=p.parse_args()
    if not a.selftest and not a.input:p.error('--input original required')
    try:
        source=load_json((ROOT/'evals/files/input.json' if a.selftest else Path(a.input)).read_text())
        output=load_json((ROOT/'evals/files/valid.json').read_text() if a.selftest else Path(a.path).read_text() if a.path else sys.stdin.read())
        errors,_=validate(output,source)
    except (ValueError,OSError,TypeError) as exc:errors=[str(exc)]
    for e in errors:print('ERROR:',e)
    print(f'output validation: {len(errors)} error(s)');return bool(errors)
if __name__=='__main__':raise SystemExit(main())
