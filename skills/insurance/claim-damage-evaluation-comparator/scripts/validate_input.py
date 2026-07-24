#!/usr/bin/env python3
"""Deterministic input validation for claim-damage-evaluation-comparator.

Input schema (JSON): claim{claim_id,claim_type}; config{categories_requiring_support[]};
documents[{doc_id,doc_type,source_ref}]; line_items[{item_id,doc_id,category,description,amount,
supported_by}].

Usage: python validate_input.py claim.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQ_TOP = ("claim", "documents", "line_items")
REQ_ITEM = ("item_id", "doc_id", "category", "description")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQ_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    if not doc["claim"].get("claim_id"):
        errors.append("claim missing 'claim_id'")
    docs = doc.get("documents") or []
    if not isinstance(docs, list) or not docs:
        errors.append("documents must be a non-empty list")
    doc_ids = {d.get("doc_id") for d in docs}
    items = doc.get("line_items") or []
    if not isinstance(items, list) or not items:
        errors.append("line_items must be a non-empty list")
        return errors, warnings
    for i, it in enumerate(items):
        tag = f"line_items[{i}] ({it.get('item_id','?')})"
        for k in REQ_ITEM:
            if it.get(k) in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(it.get("amount")) is None:
            warnings.append(f"{tag}: amount not numeric — item not evaluable for duplicate/difference")
        if it.get("doc_id") not in doc_ids:
            errors.append(f"{tag}: doc_id '{it.get('doc_id')}' not in documents")
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
