#!/usr/bin/env python3
"""Deterministic input validation for payment-integration-readiness-pack.

Input schema (JSON): integration{integration_id,merchant,gateway,target_go_live}; checklist{
required_items[{item_id,category}],gate_items[],config_version}; attestations[{item_id,status,
justification,evidence_ref}].

Usage: python validate_input.py integration.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("integration", "checklist", "attestations"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    if not doc["integration"].get("integration_id"):
        errors.append("integration missing 'integration_id'")
    req = doc["checklist"].get("required_items")
    if not isinstance(req, list) or not req:
        errors.append("checklist.required_items must be a non-empty list")
    else:
        for i, it in enumerate(req):
            if it.get("item_id") in (None, ""):
                errors.append(f"checklist.required_items[{i}]: missing 'item_id'")
    att = doc.get("attestations")
    if not isinstance(att, list):
        errors.append("attestations must be a list")
        return errors, warnings
    for i, a in enumerate(att):
        if a.get("item_id") in (None, ""):
            errors.append(f"attestations[{i}]: missing 'item_id'")
        if a.get("status") not in ("attested", "not_attested", "na", None):
            errors.append(f"attestations[{i}]: status must be attested|not_attested|na")
    if not doc["checklist"].get("config_version"):
        warnings.append("checklist.config_version missing — record the versioned checklist used")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "integration_example.json"
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
