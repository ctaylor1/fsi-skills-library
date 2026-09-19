#!/usr/bin/env python3
"""Deterministic input validation for liability-evidence-matrix-builder.

Input schema (JSON): claim{claim_id,claim_type}; facts[{fact_id,statement,party}];
evidence[{evidence_id,type,source_ref,supports[],contradicts[]}].

Usage: python validate_input.py claim.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("claim", "facts", "evidence"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    if not doc["claim"].get("claim_id"):
        errors.append("claim missing 'claim_id'")
    facts = doc.get("facts") or []
    if not isinstance(facts, list) or not facts:
        errors.append("facts must be a non-empty list")
    else:
        for i, f in enumerate(facts):
            if f.get("fact_id") in (None, ""):
                errors.append(f"facts[{i}]: missing 'fact_id'")
            if not (f.get("statement") or "").strip():
                warnings.append(f"facts[{i}] ({f.get('fact_id', '?')}): empty statement")
    ev = doc.get("evidence")
    if not isinstance(ev, list):
        errors.append("evidence must be a list")
        return errors, warnings
    for i, e in enumerate(ev):
        if e.get("evidence_id") in (None, ""):
            errors.append(f"evidence[{i}]: missing 'evidence_id'")
        if not (e.get("source_ref") or "").strip():
            warnings.append(f"evidence[{i}] ({e.get('evidence_id', '?')}): missing source_ref")
        for key in ("supports", "contradicts"):
            if key in e and not isinstance(e.get(key), list):
                errors.append(f"evidence[{i}]: '{key}' must be a list of fact_ids")
    return errors, warnings


def validate(doc: dict) -> tuple[list[str], list[str]]:
    if not isinstance(doc, dict):
        return ["input must be an object"], []
    try:
        errors, warnings = _validate(doc)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        return ["malformed input: " + str(exc)], []
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "claim_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
