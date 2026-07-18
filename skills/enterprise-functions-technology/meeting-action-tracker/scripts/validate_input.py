#!/usr/bin/env python3
"""Deterministic input validation for meeting-action-tracker.

Validates a meeting-extraction intake file before an action package is drafted. Fails closed
on structural problems (so a register is never assembled from an ill-formed record); warns on
data gaps that force a `needs-confirmation`, `blocked`, or `unsupported` status.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  template_version, as_of_date, meeting{meeting_id, title, date, attendees[]},
  segments[{segment_id, speaker?, ts?, text?}] (optional but recommended),
  candidate_items[{item_id, type, text, owner?, owner_confirmed?, due_date?, due_confirmed?,
                   depends_on[]?, source_segments[]?, decided_by?, raised_by?}],
  existing_tasks[{task_id, text, status?}] (optional; read-only dedup)

Usage: python validate_input.py meeting.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("template_version", "meeting", "candidate_items")
REQUIRED_MEETING = ("meeting_id", "date")
REQUIRED_ITEM = ("item_id", "type", "text")
ITEM_TYPES = {"action", "decision", "dependency", "open_question", "risk"}


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

    if doc.get("as_of_date") and not _is_iso_date(doc.get("as_of_date")):
        errors.append("as_of_date is not an ISO date (YYYY-MM-DD)")
    if not doc.get("as_of_date"):
        warnings.append("no as_of_date -> due dates normalized against the system date")

    meeting = doc.get("meeting") or {}
    if not isinstance(meeting, dict):
        errors.append("meeting must be an object")
        return errors, warnings
    for k in REQUIRED_MEETING:
        if meeting.get(k) in (None, ""):
            errors.append(f"meeting: missing '{k}'")
    if meeting.get("date") and not _is_iso_date(meeting.get("date")):
        errors.append("meeting.date is not an ISO date")
    roster = {str(a).strip().lower() for a in (meeting.get("attendees") or [])}
    roster |= {str(a).strip().lower() for a in (doc.get("roster") or [])}
    if not roster:
        warnings.append("no attendee roster -> owners cannot be resolved (needs-confirmation)")

    segment_ids = {s.get("segment_id") for s in (doc.get("segments") or []) if s.get("segment_id")}
    if not segment_ids:
        warnings.append("no segments provided -> citations cannot be verified against the record")

    items = doc.get("candidate_items") or []
    if not isinstance(items, list) or not items:
        errors.append("candidate_items must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, it in enumerate(items):
        tag = f"candidate_items[{i}] ({it.get('item_id','?')})"
        for k in REQUIRED_ITEM:
            if it.get(k) in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        iid = it.get("item_id")
        if iid in ids:
            errors.append(f"{tag}: duplicate item_id")
        ids.add(iid)
        typ = it.get("type")
        if typ and typ not in ITEM_TYPES:
            errors.append(f"{tag}: invalid type {typ!r} (allowed: {sorted(ITEM_TYPES)})")

        srcs = it.get("source_segments") or []
        if not srcs:
            warnings.append(f"{tag}: no source_segments -> unsupported (kept out of the register)")
        elif segment_ids:
            for s in srcs:
                if s not in segment_ids:
                    warnings.append(f"{tag}: cites segment {s!r} not in the record -> unsupported")

        if typ == "action":
            owner = str(it.get("owner") or "").strip().lower()
            if not owner:
                warnings.append(f"{tag}: action has no owner -> needs-confirmation")
            elif roster and owner not in roster:
                warnings.append(f"{tag}: owner {it.get('owner')!r} not on roster -> needs-confirmation")
            due = it.get("due_date")
            if not due:
                warnings.append(f"{tag}: action has no due date -> needs-confirmation")
            elif not _is_iso_date(due):
                warnings.append(f"{tag}: due_date {due!r} is not ISO -> needs-confirmation")

        for dep in it.get("depends_on") or []:
            if dep not in [x.get("item_id") for x in items]:
                warnings.append(f"{tag}: depends_on {dep!r} references an unknown item -> blocked")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "meeting_example.json"
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
