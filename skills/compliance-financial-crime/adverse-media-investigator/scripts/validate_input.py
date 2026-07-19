#!/usr/bin/env python3
"""Deterministic input validation for adverse-media-investigator.

Validates a screening batch before investigation. Fails closed on structural problems; warns
on data gaps that force a `needs-data` disposition or weaken entity resolution / chronology.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, as_of_date, case_batch_id, subjects[
    {subject_id, name, type(person|entity), dob, nationality, country, known_identifiers[],
     hits[{hit_id, source, source_ref, published_date, headline, category, assertion_type,
           source_tier(1|2|3), list_type, entity_match{name,dob,nationality,location,identifier},
           named_parties[], amounts[], excerpt}]}]

Usage: python validate_input.py screening_batch.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "as_of_date", "subjects")
REQUIRED_SUBJECT = ("subject_id", "name", "type")
REQUIRED_HIT = ("hit_id", "source", "source_ref", "published_date", "category", "assertion_type", "entity_match")
SUBJECT_TYPES = {"person", "entity"}
ASSERTIONS = {"finding", "allegation", "resolved-dismissed"}
NAME_MATCH = {"exact", "partial", "none"}
FIELD_MATCH = {"match", "mismatch", "unknown"}
KNOWN_CATEGORIES = {
    "money_laundering", "terrorist_financing", "sanctions_evasion", "sanctions_designation",
    "pep_exposure", "fraud", "corruption", "bribery", "tax_evasion", "market_abuse",
    "financial_crime_other", "regulatory_breach", "litigation_civil", "adverse_other",
}


def validate(doc: dict):
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    subjects = doc.get("subjects") or []
    if not isinstance(subjects, list) or not subjects:
        errors.append("subjects must be a non-empty list")
        return errors, warnings

    seen = set()
    for i, s in enumerate(subjects):
        tag = f"subjects[{i}] ({s.get('subject_id','?')})"
        for k in REQUIRED_SUBJECT:
            if not s.get(k):
                errors.append(f"{tag}: missing '{k}'")
        if s.get("type") and s.get("type") not in SUBJECT_TYPES:
            errors.append(f"{tag}: type must be one of {sorted(SUBJECT_TYPES)}")
        sid = s.get("subject_id")
        if sid in seen:
            errors.append(f"{tag}: duplicate subject_id")
        seen.add(sid)

        if not (s.get("dob") or s.get("nationality") or s.get("known_identifiers")):
            warnings.append(f"{tag}: no dob/nationality/identifier -> common-name hits cannot be "
                            f"resolved (needs-data)")

        hits = s.get("hits") or []
        if not hits:
            warnings.append(f"{tag}: no hits -> case will resolve to no-material-adverse-media")
        hids = set()
        for j, h in enumerate(hits):
            htag = f"{tag} hit[{j}] ({h.get('hit_id','?')})"
            for k in REQUIRED_HIT:
                if k not in h or h[k] in (None, ""):
                    errors.append(f"{htag}: missing '{k}'")
            if h.get("hit_id") in hids:
                errors.append(f"{htag}: duplicate hit_id")
            hids.add(h.get("hit_id"))
            if h.get("assertion_type") and h.get("assertion_type") not in ASSERTIONS:
                errors.append(f"{htag}: assertion_type {h.get('assertion_type')!r} not in {sorted(ASSERTIONS)}")
            em = h.get("entity_match") or {}
            if em.get("name") not in NAME_MATCH:
                errors.append(f"{htag}: entity_match.name must be one of {sorted(NAME_MATCH)}")
            for f in ("dob", "nationality", "location", "identifier"):
                if f in em and em[f] not in FIELD_MATCH:
                    errors.append(f"{htag}: entity_match.{f} {em[f]!r} not in {sorted(FIELD_MATCH)}")
            if h.get("category") and h.get("category") not in KNOWN_CATEGORIES:
                warnings.append(f"{htag}: unknown category {h.get('category')!r} -> defaults to lowest weight")
            if h.get("source_tier") not in (1, 2, 3):
                warnings.append(f"{htag}: source_tier missing/invalid -> defaults to tier 3 (lowest reliability)")
            if not h.get("published_date"):
                warnings.append(f"{htag}: no published_date -> chronology gap; recency scored 0")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "screening_batch_example.json"
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
