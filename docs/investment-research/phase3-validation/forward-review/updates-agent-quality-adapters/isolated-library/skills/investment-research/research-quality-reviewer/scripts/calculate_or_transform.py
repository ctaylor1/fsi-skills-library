#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
from analysis_contract import load_json
from domain import compute
assemble=compute
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('path',nargs='?');p.add_argument('--selftest',action='store_true');a=p.parse_args()
    try:
        doc=load_json((ROOT/'evals/files/input.json').read_text() if a.selftest else Path(a.path).read_text() if a.path else sys.stdin.read())
        print(json.dumps(compute(doc),indent=2,allow_nan=False));return 0
    except (ValueError,OSError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError) as exc:print('ERROR:',exc);return 1
if __name__=='__main__':raise SystemExit(main())
