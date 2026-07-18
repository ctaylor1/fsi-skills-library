#!/usr/bin/env python3
"""Deterministic input validation for policy-document-explainer.

Validates a normalized policy document against the documented schema BEFORE explaining.
Fails closed on structural problems; warns (does not fail) on data-quality gaps the
explanation must surface (unresolved cross-references, unknown section types, coverage
sections without a stated limit, empty declarations).

Input schema (JSON):
{
  "policy_id": "str (masked, e.g. ****7788)",
  "form_edition": "str (e.g. 'HO-3 (07/2021)')",
  "effective_date": "YYYY-MM-DD",
  "expiration_date": "YYYY-MM-DD",
  "insured_name": "str (masked/redacted)",
  "sections": [
    {"section_id","section_type","heading","text",
     "source":{"system","ref"},
     "limit"(opt),"deductible"(opt),"refers_to"(opt list of section_ids)}
  ]
}

section_type is one of: coverage, exclusion, condition, definition, endorsement,
declaration, premium, other.

Usage:
  python validate_input.py policy.json
  python validate_input.py --selftest        # validate the bundled fixture
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("policy_id", "form_edition", "effective_date", "expiration_date", "sections")
REQUIRED_SEC = ("section_id", "section_type", "heading", "text", "source")
KNOWN_TYPES = {
    "coverage", "exclusion", "condition", "definition", "endorsement",
    "declaration", "premium", "other",
}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    eff, exp = str(doc["effective_date"]), str(doc["expiration_date"])
    if not DATE_RE.match(eff):
        errors.append(f"effective_date must be YYYY-MM-DD, got {doc['effective_date']!r}")
    if not DATE_RE.match(exp):
        errors.append(f"expiration_date must be YYYY-MM-DD, got {doc['expiration_date']!r}")
    if DATE_RE.match(eff) and DATE_RE.match(exp) and exp < eff:
        errors.append(f"expiration_date {exp} precedes effective_date {eff}")

    sections = doc.get("sections") or []
    if not isinstance(sections, list) or not sections:
        errors.append("sections must be a non-empty list")
        return errors, warnings

    seen_ids: set[str] = set()
    for i, s in enumerate(sections):
        tag = f"sections[{i}] ({s.get('section_id', '?')})"
        for k in REQUIRED_SEC:
            if k not in s or s[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        src = s.get("source") or {}
        if not (src.get("system") and src.get("ref")):
            errors.append(f"{tag}: source must include 'system' and 'ref' (citation)")

        sid = s.get("section_id")
        if sid in seen_ids:
            errors.append(f"{tag}: duplicate section_id {sid!r}")
        elif sid:
            seen_ids.add(sid)

        stype = s.get("section_type")
        if stype and stype not in KNOWN_TYPES:
            warnings.append(f"{tag}: unknown section_type {stype!r} — classify as one of {sorted(KNOWN_TYPES)}")
        if stype == "coverage" and s.get("limit") in (None, ""):
            warnings.append(f"{tag}: coverage section has no stated limit — cite the declarations or flag as a data gap")

    # cross-reference resolution (second pass, now that ids are known)
    for i, s in enumerate(sections):
        tag = f"sections[{i}] ({s.get('section_id', '?')})"
        for ref in (s.get("refers_to") or []):
            if ref not in seen_ids:
                warnings.append(f"{tag}: unresolved cross-reference to {ref!r} — endorsement/section not in document; report as a data gap")

    return errors, warnings


def _report(errors, warnings) -> int:
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "policy_example.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
    elif len(argv) >= 1:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    return _report(*validate(doc))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
