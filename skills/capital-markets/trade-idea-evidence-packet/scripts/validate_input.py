#!/usr/bin/env python3
"""Deterministic input validation for trade-idea-evidence-packet.

Input schema (JSON): idea{idea_id,instrument,direction,thesis}; data_points[{point_id,claim,
value,source_ref}]; risk_factors[{factor,description}]; suitability_context{restricted_products[],
general_only}; checklist{required_sections[],config_version}.

Usage: python validate_input.py idea.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("idea", "data_points", "checklist"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    idea = doc["idea"]
    for k in ("idea_id", "instrument", "thesis"):
        if not idea.get(k):
            errors.append(f"idea missing '{k}'")
    dps = doc.get("data_points") or []
    if not isinstance(dps, list) or not dps:
        errors.append("data_points must be a non-empty list")
    else:
        for i, d in enumerate(dps):
            if d.get("point_id") in (None, ""):
                errors.append(f"data_points[{i}]: missing 'point_id'")
            if not (d.get("claim") or "").strip():
                warnings.append(f"data_points[{i}] ({d.get('point_id','?')}): empty claim")
            if not (d.get("source_ref") or "").strip():
                warnings.append(f"data_points[{i}] ({d.get('point_id','?')}): uncited — will be flagged")
    if not isinstance(doc["checklist"].get("required_sections"), list):
        errors.append("checklist.required_sections must be a list")
    if not doc.get("risk_factors"):
        warnings.append("no risk_factors — packet will be flagged as unbalanced")
    if not doc["checklist"].get("config_version"):
        warnings.append("checklist.config_version missing — record the versioned config used")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "idea_example.json"
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
