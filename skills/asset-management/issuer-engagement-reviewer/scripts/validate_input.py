#!/usr/bin/env python3
"""Deterministic input validation for issuer-engagement-reviewer.

Validates an issuer engagement-log file before the brief is assembled. Fails closed on
structural problems (an unusable log); warns on data-quality gaps that will surface in the
brief as uncited items, missing owners, or overdue commitments.

Input schema (JSON): see references/source-map.md. Key fields:
  brief_version, source_hierarchy_version, as_of_date,
  issuer{issuer_id, name, sector, ticker},
  engagements[ {engagement_id, date, type, channel, topics[],
     attendees_firm[{role,id}], attendees_issuer[{role,id}],
     commitments[{commitment_id, text, due}],
     disclosed_progress[{commitment_id, text, disclosed_date, source_ref}],
     follow_ups[{follow_up_id, text, status, owner_role}],
     source_docs[{doc_id, title, type, date, source_ref}], source_ref} ]

Usage: python validate_input.py engagements.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import math
from datetime import date
from native_integrity import canonical_hash

FIXTURE = Path(__file__).resolve().parents[1] / "evals" / "files" / "engagements_example.json"

REQUIRED_TOP = ("brief_version", "issuer", "as_of_date", "engagements")
REQUIRED_ENGAGEMENT = ("engagement_id", "date", "type", "source_ref")
KNOWN_TYPES = {"meeting", "call", "letter", "written-qa", "collaborative", "other"}


def _validate_native(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    issuer = doc.get("issuer") or {}
    for k in ("issuer_id", "name"):
        if not issuer.get(k):
            errors.append(f"issuer.{k} is required")

    as_of = doc.get("as_of_date")
    engagements = doc.get("engagements")
    if not isinstance(engagements, list) or not engagements:
        errors.append("engagements must be a non-empty list")
        return errors, warnings

    known_commitments: set[str] = set()
    for e in engagements:
        for c in e.get("commitments") or []:
            if c.get("commitment_id"):
                known_commitments.add(c["commitment_id"])

    ids: set[str] = set()
    for i, e in enumerate(engagements):
        tag = f"engagements[{i}] ({e.get('engagement_id', '?')})"
        for k in REQUIRED_ENGAGEMENT:
            if k in (None, "") or not e.get(k):
                errors.append(f"{tag}: missing '{k}'")
        eid = e.get("engagement_id")
        if eid in ids:
            errors.append(f"{tag}: duplicate engagement_id")
        ids.add(eid)

        if e.get("type") and e.get("type") not in KNOWN_TYPES:
            warnings.append(f"{tag}: unknown type {e.get('type')!r} -> treated as 'other'")
        if as_of and e.get("date") and str(e["date"]) > str(as_of):
            warnings.append(f"{tag}: engagement date is after as_of_date -> future-dated entry")
        if not (e.get("attendees_firm") or e.get("attendees_issuer")):
            warnings.append(f"{tag}: no attendees recorded -> attendee roll-up will be incomplete")
        if not e.get("source_docs"):
            warnings.append(f"{tag}: no source_docs -> supporting documents will be thin")

        for c in e.get("commitments") or []:
            if not c.get("commitment_id"):
                errors.append(f"{tag}: a commitment is missing 'commitment_id'")
            if not c.get("due"):
                warnings.append(f"{tag}: commitment {c.get('commitment_id')} has no due date")

        for p in e.get("disclosed_progress") or []:
            if not p.get("source_ref"):
                warnings.append(f"{tag}: disclosed_progress for {p.get('commitment_id')} lacks source_ref -> will be uncited")
            if p.get("commitment_id") and p["commitment_id"] not in known_commitments:
                warnings.append(f"{tag}: disclosed_progress references unknown commitment {p.get('commitment_id')!r}")

        for f in e.get("follow_ups") or []:
            if str(f.get("status", "open")).lower() != "closed" and not f.get("owner_role"):
                warnings.append(f"{tag}: open follow-up {f.get('follow_up_id')} has no owner_role")

    # overdue commitments with no disclosed progress anywhere (informational)
    progressed = set()
    for e in engagements:
        for p in e.get("disclosed_progress") or []:
            progressed.add(p.get("commitment_id"))
    for e in engagements:
        for c in e.get("commitments") or []:
            due = c.get("due")
            if due and as_of and str(due) < str(as_of) and c.get("commitment_id") not in progressed:
                warnings.append(f"commitment {c.get('commitment_id')} is overdue with no disclosed progress -> flagged in brief")

    return errors, warnings


def main(argv) -> int:
    if "--selftest" in argv:
        doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(warnings)} warning(s), {len(errors)} error(s)")
    return 1 if errors else 0




def validate(doc):
    try:
        canonical_hash(doc)
        errors, warnings = _validate_native(doc)
        date.fromisoformat(doc["as_of_date"])
        ids = [e.get("engagement_id") for e in doc.get("engagements", [])]
        if len(ids) != len(set(ids)):
            errors.append("duplicate engagement_id")
        return errors, warnings
    except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
        return ["invalid input: " + str(exc)], []

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
