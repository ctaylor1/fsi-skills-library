#!/usr/bin/env python3
import json, sys
from pathlib import Path
from calculate_or_transform import compute


def validate(doc):
    try:
        expected = compute(doc["source_snapshot"])
    except (ValueError, TypeError, KeyError) as exc:
        return ["missing/invalid source snapshot: " + str(exc)]
    return (
        []
        if doc == expected
        else ["output differs from supplied source calculation; savings/approval claims unsupported"]
    )


def main(argv):
    path = (
        Path(__file__).resolve().parents[1] / "evals/files/pack_example.json" if "--selftest" in argv else Path(argv[0])
    )
    errors = validate(json.loads(path.read_text()))
    for error in errors:
        print("ERROR", error)
    print(f"output validation: {len(errors)} error(s)")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
