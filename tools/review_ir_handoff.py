#!/usr/bin/env python3
"""Compute a reviewed native handoff, including explicit macro-vintage evidence, offline."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'shared/investment-research'),str(ROOT/'shared/investment-data')]
from reviewed_handoffs import review
from analysis_contract import load_json
from native_integrity import validate_reconstruction
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',type=Path);p.add_argument('--library-root',type=Path,default=ROOT);p.add_argument('--input',type=Path,help='Validate the saved handoff against its retained original request');a=p.parse_args()
    try:
        document=load_json(a.path.read_text())
        if a.input:
            errors=[];validate_reconstruction(document,lambda d:review(d,a.library_root),errors,original_input=load_json(a.input.read_text()))
            for error in errors:print('ERROR:',error)
            print(f'handoff validation: {len(errors)} error(s)');return bool(errors)
        print(json.dumps(review(document,a.library_root),indent=2,allow_nan=False));return 0
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:print('ERROR:',exc);return 1
if __name__=='__main__':raise SystemExit(main())
