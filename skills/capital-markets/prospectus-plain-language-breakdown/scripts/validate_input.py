#!/usr/bin/env python3
"""Deterministic input validation for prospectus-plain-language-breakdown.

Validates a parsed prospectus source against the documented schema BEFORE producing the
breakdown. Fails closed on structural problems (missing page anchors, out-of-range pages,
missing section text). Warns (does not fail) on coverage gaps the breakdown must surface —
a required disclosure topic the document does not appear to cover, or a recommended topic
that is absent.

Input schema (JSON):
{
  "document_id": "str",
  "document_type": "prospectus" | "summary_prospectus" | "sai" | "kiid" |
                   "offering_memorandum" | "offering_circular",
  "issuer": "str",
  "instrument": "str",
  "effective_date": "YYYY-MM-DD",
  "jurisdiction": "US",
  "total_pages": int,
  "sections": [
    {"topic": "fees|strategy|liquidity|conflicts|risks|obligations|<optional>",
     "heading": "str", "page_start": int, "page_end": int, "text": "str",
     "share_class": "str"(opt), "incorporated_by_reference": bool(opt)}
  ]
}

Usage:
  python validate_input.py prospectus.json
  python validate_input.py --selftest        # validate the bundled fixture
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("document_id", "document_type", "issuer", "instrument",
                "effective_date", "total_pages", "sections")
REQUIRED_SECTION = ("topic", "heading", "page_start", "page_end", "text")
DOC_TYPES = {
    "prospectus", "summary_prospectus", "sai", "kiid",
    "offering_memorandum", "offering_circular",
}
REQUIRED_TOPICS = ("fees", "strategy", "liquidity", "conflicts", "risks", "obligations")
RECOMMENDED_TOPICS = ("tax", "distributions", "performance", "management", "governance")


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["effective_date"])):
        errors.append(f"effective_date must be YYYY-MM-DD, got {doc['effective_date']!r}")

    if doc["document_type"] not in DOC_TYPES:
        errors.append(f"document_type {doc['document_type']!r} not in {sorted(DOC_TYPES)}")

    total_pages = _int(doc.get("total_pages"))
    if total_pages is None or total_pages < 1:
        errors.append(f"total_pages must be a positive integer, got {doc.get('total_pages')!r}")

    sections = doc.get("sections") or []
    if not isinstance(sections, list) or not sections:
        errors.append("sections must be a non-empty list")
        return errors, warnings

    topics_seen: dict[str, int] = {}
    for i, s in enumerate(sections):
        tag = f"sections[{i}] ({s.get('topic', '?')})"
        for k in REQUIRED_SECTION:
            if k not in s or s[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")

        ps = _int(s.get("page_start"))
        pe = _int(s.get("page_end"))
        if ps is None or pe is None:
            errors.append(f"{tag}: page_start/page_end must be integers (page-level citation required)")
        else:
            if ps < 1:
                errors.append(f"{tag}: page_start {ps} < 1")
            if pe < ps:
                errors.append(f"{tag}: page_end {pe} < page_start {ps}")
            if total_pages is not None and pe > total_pages:
                errors.append(f"{tag}: page_end {pe} > total_pages {total_pages}")

        topic = s.get("topic")
        if topic:
            topics_seen[topic] = topics_seen.get(topic, 0) + 1

    # Coverage warnings (breakdown must surface these; they are not structural errors).
    for t in REQUIRED_TOPICS:
        if t not in topics_seen:
            warnings.append(
                f"required topic '{t}' not found in source sections — "
                f"breakdown must flag it as a disclosure gap")
    for t in RECOMMENDED_TOPICS:
        if t not in topics_seen:
            warnings.append(f"recommended topic '{t}' not present (optional)")
    for t, n in topics_seen.items():
        if n > 1 and t in REQUIRED_TOPICS:
            warnings.append(
                f"topic '{t}' appears in {n} sections — consolidate or cite each share class")

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
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "prospectus_example.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
    elif len(argv) >= 1:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    return _report(*validate(doc))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
