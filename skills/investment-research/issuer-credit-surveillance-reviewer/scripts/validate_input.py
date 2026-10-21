#!/usr/bin/env python3
"""Validate current supplied surveillance evidence; legacy requests require migration."""
import sys
from phase2_domain import validate_document
from pathlib import Path
from surveillance_contract import require_live_contract, read_json


def validate(doc):
    try:
        require_live_contract(doc)
        validate_document(doc)
        return [], []
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
        return [str(exc)], []


def main(argv):
    try:
        if "--selftest" in argv:
            path = Path(__file__).resolve().parents[1] / "evals/files/phase2_input.json"
            doc = read_json(path.read_text(encoding="utf-8"))
        elif argv:
            doc = read_json(Path(argv[0]).read_text(encoding="utf-8"))
        else:
            doc = read_json(sys.stdin.read())
        errors, warnings = validate(doc)
        for warning in warnings:
            print("WARN", warning)
        for error in errors:
            print("ERROR", error)
        print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
        return int(bool(errors))
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        print("ERROR:", str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
