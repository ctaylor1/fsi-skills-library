#!/usr/bin/env python3
"""Deterministic input validation for enterprise-meeting-preparer.

Validates a meeting-intake file before a brief is drafted. Fails closed on structural
problems (so a brief is never assembled from an ill-formed record); warns on data gaps that
force a `needs-data`, `unresolved-attendee`, or `unsupported-content` status downstream.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  as_of_date, freshness_days?, meetings[
    {meeting_id, title, datetime, purpose, organizer?, location?,
     sources[{source_id, system, ref, date, classification?, stale_ack?}],
     attendees[{name, role, org, resolved, source_id?}],
     agenda_items[{item, owner?, source_id}],
     decisions[{decision, status, source_id}]?,
     risks[{risk, severity, source_id}]?,
     prior_actions[{action, owner?, due_date?, status, source_id}]?,
     talking_points[{point, source_id}]?}]

Usage: python validate_input.py meetings.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("as_of_date", "meetings")
REQUIRED_MEETING = ("meeting_id", "title", "datetime")  # structural; error if missing
CONTENT_LISTS = ("agenda_items", "decisions", "risks", "prior_actions", "talking_points")
ITEM_LABEL = {"agenda_items": "item", "decisions": "decision", "risks": "risk",
              "prior_actions": "action", "talking_points": "point"}


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

    meetings = doc.get("meetings") or []
    if not isinstance(meetings, list) or not meetings:
        errors.append("meetings must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, m in enumerate(meetings):
        tag = f"meetings[{i}] ({m.get('meeting_id','?')})"
        for k in REQUIRED_MEETING:
            if k not in m or m[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        mid = m.get("meeting_id")
        if mid in ids:
            errors.append(f"{tag}: duplicate meeting_id")
        ids.add(mid)

        # source inventory
        sources = m.get("sources") or []
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
        if not m.get("purpose"):
            warnings.append(f"{tag}: missing 'purpose' -> needs-data")
        if not m.get("attendees"):
            warnings.append(f"{tag}: no attendees -> needs-data")
        if not m.get("agenda_items"):
            warnings.append(f"{tag}: no agenda_items -> needs-data")

        for a in m.get("attendees") or []:
            if not a.get("resolved"):
                warnings.append(f"{tag}: attendee {a.get('name','?')!r} unresolved -> unresolved-attendee")

        # every content item should cite a source in the inventory
        for lst in CONTENT_LISTS:
            for k, item in enumerate(m.get(lst) or []):
                sid = item.get("source_id")
                if not sid:
                    warnings.append(f"{tag}: {ITEM_LABEL[lst]}[{k}] has no source_id -> unsupported-content")
                elif sid not in source_ids:
                    warnings.append(f"{tag}: {ITEM_LABEL[lst]}[{k}] cites source {sid!r} not in inventory -> unsupported-content")

        for k, pa in enumerate(m.get("prior_actions") or []):
            if pa.get("due_date") and not _is_iso_date(pa.get("due_date")):
                errors.append(f"{tag}: prior_actions[{k}] due_date is not an ISO date")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "meetings_example.json"
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
