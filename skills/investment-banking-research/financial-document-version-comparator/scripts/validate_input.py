#!/usr/bin/env python3
"""Deterministic input validation for financial-document-version-comparator.

Input schema (JSON): doc_a{doc_id,version,sections[{id,heading,text,values?}]}, doc_b{...}.
The two versions must share the same doc_id.

Usage: python validate_input.py docs.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path


def _check_doc(d, tag, errors):
    if not isinstance(d, dict):
        errors.append(f"{tag} missing/not an object")
        return
    for k in ("doc_id", "version", "sections"):
        if d.get(k) in (None, ""):
            errors.append(f"{tag}: missing '{k}'")
    for i, s in enumerate(d.get("sections") or []):
        if not s.get("id"):
            errors.append(f"{tag}.sections[{i}]: missing 'id'")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    a, b = doc.get("doc_a"), doc.get("doc_b")
    _check_doc(a, "doc_a", errors)
    _check_doc(b, "doc_b", errors)
    if errors:
        return errors, warnings
    if a.get("doc_id") != b.get("doc_id"):
        errors.append(f"doc_id mismatch: {a.get('doc_id')!r} != {b.get('doc_id')!r} — versions are not comparable")
    ids_a = [s.get("id") for s in a["sections"]]
    ids_b = [s.get("id") for s in b["sections"]]
    if len(set(ids_a)) != len(ids_a) or len(set(ids_b)) != len(ids_b):
        warnings.append("duplicate section ids present — diff keys on id; resolve duplicates for a clean mapping")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "docs_example.json"
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
