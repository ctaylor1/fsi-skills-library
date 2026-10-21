#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from calculate_or_transform import validate

if __name__ == "__main__":
    parser=argparse.ArgumentParser();parser.add_argument("input");args=parser.parse_args()
    try: errors,warnings=validate(json.loads(Path(args.input).read_text()))
    except (ValueError,TypeError,OSError) as exc: errors=[str(exc)];warnings=[]
    print(json.dumps({"errors":errors,"warnings":warnings}));raise SystemExit(bool(errors))
