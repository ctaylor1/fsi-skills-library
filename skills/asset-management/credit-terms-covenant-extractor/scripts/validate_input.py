#!/usr/bin/env python3
"""Deterministic input validation for credit-terms-covenant-extractor.

Validates a document-intelligence extraction request before term normalization. Fails
closed on structural problems and on the tier's hard requirement that every extracted term
carry a page-level citation; warns on data-quality gaps that limit coverage.

Input schema (JSON): see references/source-map.md. Key fields:
  doc_id, doc_type, issuer, instrument, effective_date (YYYY-MM-DD), doc_version,
  governing_law, source_system, expected_fields[], candidates[{field, raw_value, page,
  locator, confidence, note}]

Usage:
  python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("doc_id", "doc_type", "issuer", "effective_date", "expected_fields", "candidates")
ALLOWED_FIELDS = {"maturity", "coupon", "seniority", "collateral", "call_provision", "covenant", "basket"}
REQUIRED_CAND = ("field", "raw_value", "page", "locator")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["effective_date"])):
        errors.append(f"effective_date must be YYYY-MM-DD, got {doc['effective_date']!r}")

    expected = doc.get("expected_fields") or []
    if not isinstance(expected, list) or not expected:
        errors.append("expected_fields must be a non-empty list")
    for f in expected:
        if f not in ALLOWED_FIELDS:
            errors.append(f"expected_fields contains unknown field {f!r} (allowed: {sorted(ALLOWED_FIELDS)})")

    cands = doc.get("candidates") or []
    if not isinstance(cands, list) or not cands:
        errors.append("candidates must be a non-empty list")
        return errors, warnings

    seen_fields = set()
    for i, c in enumerate(cands):
        tag = f"candidates[{i}] (field={c.get('field','?')})"
        for k in REQUIRED_CAND:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if c.get("field") not in ALLOWED_FIELDS:
            errors.append(f"{tag}: field must be one of {sorted(ALLOWED_FIELDS)}")
        # page-level citation is a hard requirement for this tier — fail closed if absent.
        page = c.get("page")
        if page is None or not isinstance(page, int) or isinstance(page, bool) or page < 1:
            errors.append(f"{tag}: 'page' must be a positive integer (page-level citation is required)")
        if not str(c.get("locator", "")).strip():
            warnings.append(f"{tag}: no locator (section/clause) — citation will be page-only")
        seen_fields.add(c.get("field"))

    for f in expected:
        if f in ALLOWED_FIELDS and f not in seen_fields:
            warnings.append(f"expected field {f!r} has no candidate — it will be reported not_found")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "extraction_request.json"
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
