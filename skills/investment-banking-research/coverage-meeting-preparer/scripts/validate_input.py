#!/usr/bin/env python3
"""Deterministic input validation for coverage-meeting-preparer.

Validates a coverage-brief intake file before a brief is drafted. Fails closed on structural
problems (so a brief is never assembled from an ill-formed record); warns on data gaps that
force a `needs-data`, `unsupported-claims`, `stale-source`, or `barrier-hold` status
downstream.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  config_version, as_of_date, freshness_days?, approved_sources?, briefs[
    {engagement_id, client_name, meeting_type(client|prospect), meeting_date, objective?,
     preparer?, intended_distribution?, objective_source_id?,
     sources[{source_id, system, ref, date, classification?, stale_ack?}],
     relationship{coverage_since?, last_meeting?, mandates?, open_items?, mnpi?, source_id?}?,
     developments[{id, date, headline, material?, mnpi?, source_id}],
     strategic_issues[{id, issue, material?, mnpi?, source_id}]?,
     client_objectives[{id, objective, source_id}]?,
     discussion_questions[{id, question, source_id}]?,
     follow_ups[{id, action, owner?, source_id}]?,
     approvals{supervisory_review?, control_room_clearance?, external_delivery_approval?}?}]

Usage: python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("as_of_date", "briefs")
REQUIRED_BRIEF = ("engagement_id", "client_name", "meeting_type", "meeting_date")  # structural
MEETING_TYPES = {"client", "prospect"}
# (list_key, item_text_field)
CONTENT_LISTS = [
    ("developments", "headline"),
    ("strategic_issues", "issue"),
    ("client_objectives", "objective"),
    ("discussion_questions", "question"),
    ("follow_ups", "action"),
]


def _is_iso_date(v) -> bool:
    try:
        date.fromisoformat(str(v))
        return True
    except Exception:
        return False


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not _is_iso_date(doc.get("as_of_date")):
        errors.append("as_of_date is not an ISO date (YYYY-MM-DD)")

    briefs = doc.get("briefs") or []
    if not isinstance(briefs, list) or not briefs:
        errors.append("briefs must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, b in enumerate(briefs):
        tag = f"briefs[{i}] ({b.get('engagement_id','?')})"
        for k in REQUIRED_BRIEF:
            if k not in b or b[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        eid = b.get("engagement_id")
        if eid in ids:
            errors.append(f"{tag}: duplicate engagement_id")
        ids.add(eid)
        if b.get("meeting_type") and b.get("meeting_type") not in MEETING_TYPES:
            errors.append(f"{tag}: meeting_type {b.get('meeting_type')!r} not in {sorted(MEETING_TYPES)}")
        if b.get("meeting_date") and not _is_iso_date(b.get("meeting_date")):
            errors.append(f"{tag}: meeting_date is not an ISO date")

        # source inventory must be well formed
        sources = b.get("sources") or []
        if not isinstance(sources, list):
            errors.append(f"{tag}: sources must be a list")
            sources = []
        source_ids = set()
        for j, s in enumerate(sources):
            if not s.get("source_id") or not s.get("system") or not s.get("ref"):
                errors.append(f"{tag}: sources[{j}] needs source_id, system, and ref")
            if s.get("date") and not _is_iso_date(s.get("date")):
                errors.append(f"{tag}: sources[{j}] date is not an ISO date")
            source_ids.add(s.get("source_id"))

        # content-required gaps are WARNINGS -> drive needs-data downstream, not input errors
        if not b.get("objective"):
            warnings.append(f"{tag}: missing 'objective' -> needs-data")
        if not b.get("developments"):
            warnings.append(f"{tag}: no developments -> needs-data")
        if not b.get("client_objectives"):
            warnings.append(f"{tag}: no client_objectives -> needs-data")
        if not b.get("discussion_questions"):
            warnings.append(f"{tag}: no discussion_questions -> needs-data")

        # every content item should cite a source in the inventory
        for lst, text_field in CONTENT_LISTS:
            for k, item in enumerate(b.get(lst) or []):
                sid = item.get("source_id")
                if not sid:
                    warnings.append(f"{tag}: {lst}[{k}] has no source_id -> unsupported-claims")
                elif sid not in source_ids:
                    warnings.append(f"{tag}: {lst}[{k}] cites source {sid!r} not in inventory -> unsupported-claims")
                if item.get("date") and not _is_iso_date(item.get("date")):
                    errors.append(f"{tag}: {lst}[{k}] date is not an ISO date")

        # MNPI hint: flag when MNPI items are present but control-room clearance is not approved
        has_mnpi = False
        for lst, _tf in CONTENT_LISTS:
            for it in b.get(lst) or []:
                if it.get("mnpi"):
                    has_mnpi = True
        for s in sources:
            if s.get("classification") == "mnpi":
                has_mnpi = True
        if (b.get("relationship") or {}).get("mnpi"):
            has_mnpi = True
        if has_mnpi:
            clr = ((b.get("approvals") or {}).get("control_room_clearance") or {}).get("status")
            if clr != "approved":
                warnings.append(f"{tag}: MNPI present without approved control-room clearance -> barrier-hold")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "intake_example.json"
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
