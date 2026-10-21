#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
from analysis_contract import load_json
from domain import validate_document
ROOT=Path(__file__).resolve().parents[1]
def validate(doc):
    try:validate_document(doc);return [],[]
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError) as exc:return [str(exc)],[]
def main():
    p=argparse.ArgumentParser();p.add_argument('path',nargs='?');p.add_argument('--selftest',action='store_true');a=p.parse_args()
    try:
        doc=load_json((ROOT/'evals/files/input.json').read_text() if a.selftest else Path(a.path).read_text() if a.path else sys.stdin.read())
        errors,_=validate(doc)
    except (ValueError,OSError,TypeError) as exc:errors=[str(exc)]
    for e in errors:print('ERROR:',e)
    print(f'input validation: {len(errors)} error(s)');return bool(errors)
if __name__=='__main__':raise SystemExit(main())
