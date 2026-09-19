#!/usr/bin/env python3
"""Recompute all output; --input binds the supplied authoritative source file.

A hash provides lineage, never evidence authentication. Without --input this checks
internal consistency against the embedded snapshot only.
"""
import argparse
import json
from pathlib import Path
from calculate_or_transform import compute, stable_hash


def validate(doc, source=None):
    if not isinstance(doc, dict) or not isinstance(doc.get("source_snapshot"), dict):
        return ["missing source_snapshot; cannot independently recompute output"]
    try:
        if source is not None and stable_hash(source) != stable_hash(doc["source_snapshot"]):
            return ["source_snapshot differs from authoritative input"]
        expected = compute(source if source is not None else doc["source_snapshot"])
    except (ValueError, TypeError, ArithmeticError) as exc:
        return [f"invalid source_snapshot: {exc}"]
    return [f"output differs from recomputed contract: {key}" for key in sorted(set(expected) | set(doc))
            if key not in doc or key not in expected or stable_hash(doc[key]) != stable_hash(expected[key])]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?")
    parser.add_argument("--input")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    files = Path(__file__).resolve().parents[1] / "evals/files"
    try:
        path = files / "pack_example.json" if args.selftest else Path(args.output)
        source_path = files / "recon_example.json" if args.selftest else Path(args.input) if args.input else None
        errors = validate(json.loads(path.read_text(), parse_float=str), json.loads(source_path.read_text(), parse_float=str) if source_path else None)
    except (ValueError, TypeError, OSError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("ERROR", error)
    print(f"output validation: {len(errors)} error(s)")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
