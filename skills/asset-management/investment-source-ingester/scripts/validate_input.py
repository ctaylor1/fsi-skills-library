#!/usr/bin/env python3
"""Deterministic input validation for investment-source-ingester.

Validates a source-ingestion manifest before entitlement classification, dedup, and
indexing. Fails closed on structural problems; warns on business conditions that will cause
a source to be routed to the rejected-record queue (missing/blank entitlement, no grant,
duplicate content) so the associate can see them before the run.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  job_ref, as_of (YYYY-MM-DD), catalog_version, requested_by,
  sources[{source_ref, doc_type, content_hash, title, issuer,
           published_at, effective_date, language,
           entitlement{class, grant_ref, redistribution, expires}}]

doc_type is one of: filing, press_release, presentation, transcript, market_data,
internal_research.

Usage:
  python validate_input.py manifest.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("job_ref", "as_of", "sources")
REQUIRED_SOURCE = ("source_ref", "doc_type", "content_hash")
DOC_TYPES = ("filing", "press_release", "presentation", "transcript", "market_data", "internal_research")
ENTITLEMENT_CLASSES = ("public", "licensed", "internal", "restricted")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    sources = doc.get("sources") or []
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        return errors, warnings

    refs: set = set()
    hashes: dict = {}
    for i, s in enumerate(sources):
        tag = f"sources[{i}] ({s.get('source_ref', '?')})"
        for k in REQUIRED_SOURCE:
            if k not in s or s[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        dt = s.get("doc_type")
        if dt is not None and dt not in DOC_TYPES:
            errors.append(f"{tag}: doc_type {dt!r} not in {DOC_TYPES}")
        if not s.get("published_at") and not s.get("effective_date"):
            errors.append(f"{tag}: no timestamp — needs published_at or effective_date")

        ref = s.get("source_ref")
        if ref in refs:
            errors.append(f"{tag}: duplicate source_ref — each source needs a distinct identity")
        refs.add(ref)

        h = s.get("content_hash")
        if h:
            hashes.setdefault(h, []).append(ref)

        ent = s.get("entitlement") or {}
        cls = str(ent.get("class", "")).strip().lower()
        if not cls:
            warnings.append(f"{tag}: no declared entitlement class — will be REJECTED (no_entitlement_declared)")
        elif cls not in ENTITLEMENT_CLASSES:
            warnings.append(f"{tag}: unknown entitlement class {cls!r} — will be REJECTED (unknown_entitlement_class)")
        elif cls == "restricted":
            warnings.append(f"{tag}: restricted content — will be REJECTED (restricted_content), never ingested")
        elif cls in ("licensed", "internal") and not str(ent.get("grant_ref", "")).strip():
            warnings.append(f"{tag}: {cls} without grant_ref — will be REJECTED (missing_grant_ref)")

    for h, group in hashes.items():
        if len(group) > 1:
            warnings.append(f"content_hash {h} shared by {len(group)} sources — dedup will mark duplicates, not merge")

    if not doc.get("catalog_version"):
        warnings.append("no 'catalog_version' — record the entitlement-catalog version for reproducibility")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "source_manifest.json"
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
