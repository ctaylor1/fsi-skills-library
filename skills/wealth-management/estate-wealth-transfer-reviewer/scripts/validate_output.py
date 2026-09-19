#!/usr/bin/env python3
"""Validate supplied JSON and emit a local draft; no external operations."""
import json
import sys
from pathlib import Path
from domain import build, validate, validate_output

MODE = "output"


def main():
    if len(sys.argv) != 2:
        print("usage: python scripts/" + Path(__file__).name + " INPUT.json | --selftest")
        return 2
    filename = Path(__file__).resolve().parents[1] / "evals/files/request.json" if sys.argv[1] == "--selftest" else Path(sys.argv[1])
    try:
        doc = json.loads(filename.read_text())
        if MODE == "output" and sys.argv[1] == "--selftest":
            doc = json.loads((filename.parent / "output.json").read_text())
        if MODE == "input":
            errors = validate(doc)
            print(json.dumps({"errors": errors}, indent=2))
            print(f"input validation: {len(errors)} error(s)")
        elif MODE == "output":
            errors = validate_output(doc)
            print(json.dumps({"errors": errors}, indent=2))
            print(f"output validation: {len(errors)} error(s)")
        else:
            errors = validate(doc)
            print(json.dumps({"errors": errors} if errors else build(doc), indent=2, allow_nan=False))
        return int(bool(errors))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({"errors": [str(exc)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
