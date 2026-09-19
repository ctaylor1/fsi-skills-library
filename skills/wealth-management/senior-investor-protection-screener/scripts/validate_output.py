#!/usr/bin/env python3
"""Validate envelope and independently rebuild the structured domain artifact from its input.

This detects altered, incomplete, stale, unsupported or falsely ready drafts. It does not
verify source truth or make a professional approval. Narrative delivery is a separate task.
"""

import json
import sys
from pathlib import Path
from calculate_or_transform import SKILL, compute
from wealth_contract import validate_output_envelope


def validate(pack):
    errors = validate_output_envelope(pack, SKILL)
    if errors:
        return errors
    snapshot = pack.get("input_snapshot")
    if not isinstance(snapshot, dict):
        return ["input_snapshot is required to verify evidence and result integrity"]
    try:
        expected = compute(snapshot)
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        return [f"input_snapshot rejected: {exc}"]
    if pack != expected:
        errors.append("output does not match recomputed evidence, findings, readiness and input-bound artifact")
    return errors


def main(argv):
    path = (
        Path(__file__).resolve().parents[1] / "evals/files/pack_example.json"
        if "--selftest" in argv
        else Path(argv[0])
        if argv
        else None
    )
    try:
        errors = validate(json.loads(path.read_text() if path else sys.stdin.read()))
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        errors = [str(exc)]
    for message in errors:
        print("ERROR", message)
    print(f"output validation: {len(errors)} error(s)")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
