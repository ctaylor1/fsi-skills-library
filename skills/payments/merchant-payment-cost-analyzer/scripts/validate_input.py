#!/usr/bin/env python3
import json, sys
from pathlib import Path
from calculate_or_transform import compute


def validate(doc):
    try:
        compute(doc)
        return [], []
    except (ValueError, TypeError, KeyError) as exc:
        return [str(exc)], []


def main(argv):
    path = (
        Path(__file__).resolve().parents[1] / "evals/files/statement_example.json"
        if "--selftest" in argv
        else Path(argv[0])
    )
    errors, _ = validate(json.loads(path.read_text()))
    for error in errors:
        print("ERROR", error)
    print(f"input validation: {len(errors)} error(s)")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
