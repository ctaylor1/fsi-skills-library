#!/usr/bin/env python3
"""Deterministic input validation for knowledge-answer-composer.

Validates an answer-request bundle (the question plus the candidate approved-knowledge
sources retrieved for it) against the documented schema BEFORE an answer is composed. Fails
closed on structural problems; warns (does not fail) on governance/freshness gaps the
composer must act on — stale/expired sources, not-yet-effective or draft/unapproved content,
jurisdiction mismatches, missing source text, and the case where no usable source remains.

Input schema (JSON):
{
  "request_id": "str",
  "question": "str",
  "channel": "agent-desktop|chat|email|phone" (opt),
  "jurisdiction": "US" (opt),
  "as_of_date": "YYYY-MM-DD",
  "sources": [
    {"source_id","type","title","ref","effective_date","status",
     "excerpt"(opt),"expiry_date"(opt),"jurisdiction"(opt),"owner"(opt)}
  ]
}

Usage:
  python validate_input.py request.json
  python validate_input.py --selftest        # validate the bundled fixture
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("request_id", "question", "as_of_date", "sources")
REQUIRED_SRC = ("source_id", "type", "title", "ref", "effective_date", "status")
ALLOWED_TYPE = {"policy", "product-terms", "procedure", "service-status", "kb-article", "regulatory"}
ALLOWED_STATUS = {"approved", "draft", "expired", "pending", "retired"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    as_of = str(doc["as_of_date"])
    if not DATE_RE.match(as_of):
        errors.append(f"as_of_date must be YYYY-MM-DD, got {doc['as_of_date']!r}")
    if not str(doc.get("question", "")).strip():
        errors.append("question must be a non-empty string")

    sources = doc.get("sources") or []
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list of candidate knowledge items")
        return errors, warnings

    req_juris = doc.get("jurisdiction")
    usable = 0
    for i, s in enumerate(sources):
        tag = f"sources[{i}] ({s.get('source_id', '?')})"
        for k in REQUIRED_SRC:
            if k not in s or s[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        st = s.get("type")
        if st is not None and st not in ALLOWED_TYPE:
            errors.append(f"{tag}: type {st!r} not in {sorted(ALLOWED_TYPE)}")
        stat = s.get("status")
        if stat is not None and stat not in ALLOWED_STATUS:
            errors.append(f"{tag}: status {stat!r} not in {sorted(ALLOWED_STATUS)}")
        eff = str(s.get("effective_date", ""))
        if eff and not DATE_RE.match(eff):
            errors.append(f"{tag}: effective_date must be YYYY-MM-DD, got {eff!r}")
        exp = s.get("expiry_date")
        if exp and not DATE_RE.match(str(exp)):
            errors.append(f"{tag}: expiry_date must be YYYY-MM-DD, got {exp!r}")

        # Governance / freshness gates — the composer must EXCLUDE anything not usable.
        is_usable = True
        if stat and stat != "approved":
            warnings.append(f"{tag}: status {stat!r} is not 'approved' — do not use as answer basis")
            is_usable = False
        if eff and DATE_RE.match(eff) and DATE_RE.match(as_of) and eff > as_of:
            warnings.append(f"{tag}: effective_date {eff} is after as_of {as_of} — not yet effective; exclude")
            is_usable = False
        if exp and DATE_RE.match(str(exp)) and DATE_RE.match(as_of) and str(exp) < as_of:
            warnings.append(f"{tag}: expired on {exp} (before as_of {as_of}) — do not use as answer basis")
            is_usable = False
        sj = s.get("jurisdiction")
        if sj and req_juris and sj != req_juris:
            warnings.append(f"{tag}: jurisdiction {sj} != request {req_juris} — exclude unless the question is cross-jurisdiction")
            is_usable = False
        if not str(s.get("excerpt", "")).strip():
            warnings.append(f"{tag}: no excerpt text — cannot ground a citation; retrieve the source text before citing")
            is_usable = False
        if is_usable:
            usable += 1

    if usable == 0:
        warnings.append("no approved, in-effect, jurisdiction-matched source with text — compose no answer; "
                        "fail closed and route to a human/specialist")

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
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "request_example.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
    elif len(argv) >= 1:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    return _report(*validate(doc))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
