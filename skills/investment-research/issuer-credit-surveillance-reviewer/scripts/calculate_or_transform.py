#!/usr/bin/env python3
"""Compute current surveillance evidence; legacy execution is retired."""
import json
import sys
from phase2_domain import compute as _compute
from pathlib import Path
from surveillance_contract import require_live_contract, read_json


def assemble(doc):
    require_live_contract(doc)
    return _compute(doc)


def main(argv):
    try:
        if "--selftest" in argv:
            path = Path(__file__).resolve().parents[1] / "evals/files/phase2_input.json"
            doc = read_json(path.read_text(encoding="utf-8"))
        elif argv:
            doc = read_json(Path(argv[0]).read_text(encoding="utf-8"))
        else:
            doc = read_json(sys.stdin.read())
        print(json.dumps(assemble(doc), indent=2, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        print("ERROR:", str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
