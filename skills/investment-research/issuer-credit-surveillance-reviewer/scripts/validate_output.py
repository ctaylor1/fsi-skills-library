#!/usr/bin/env python3
"""Reconstruct the current surveillance output from its separately retained original.

Historical legacy outputs require the preserved producer/validator source snapshot.
No live compatibility switch or automatic evidence migration is provided.
"""
import sys
from phase2_domain import compute as _compute
from pathlib import Path
from native_integrity import validate_reconstruction
from surveillance_contract import require_live_contract, read_json, MIGRATION_REQUIRED


def validate(doc, original_input=None):
    if isinstance(doc, dict) and doc.get("schema_version") != "ir-analysis/2.0":
        return [MIGRATION_REQUIRED]
    if original_input is not None:
        try:
            require_live_contract(original_input)
        except ValueError as exc:
            return [str(exc)]
    errors = []
    validate_reconstruction(doc, _compute, errors, original_input)
    return errors


def main(argv):
    try:
        original_input = None
        argv = list(argv)
        for option in ("--input", "--source"):
            if option in argv:
                index = argv.index(option)
                original_input = read_json(Path(argv[index + 1]).read_text(encoding="utf-8"))
                del argv[index:index + 2]
        if "--selftest" in argv:
            folder = Path(__file__).resolve().parents[1] / "evals/files"
            original_input = read_json((folder / "phase2_input.json").read_text(encoding="utf-8"))
            doc = read_json((folder / "phase2_valid.json").read_text(encoding="utf-8"))
        elif argv:
            doc = read_json(Path(argv[0]).read_text(encoding="utf-8"))
        else:
            doc = read_json(sys.stdin.read())
        errors = validate(doc, original_input)
        for error in errors:
            print("ERROR", error)
        print(f"output validation: {len(errors)} error(s)")
        return int(bool(errors))
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        print("ERROR:", str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
