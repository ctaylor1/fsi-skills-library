#!/usr/bin/env python3
"""Deterministic meeting action-register builder for meeting-action-tracker.

For each candidate item extracted from a meeting: require a citation back to the meeting
record, resolve the proposed owner against the attendee roster, normalize the due date, resolve
`depends_on` (missing reference or cycle), detect possible duplicates against an existing task
list (read-only), and assign a status. Only a sourced, owner-resolved, date-confirmed,
dependency-clean item becomes `ready` and enters the committed register. From the `ready` set
it drafts a recap and per-owner reminders as text — marked draft, approval-required.

It NEVER creates/assigns/closes a task, sends a message, schedules an invite, writes any
tracker, invents an owner or due date, or asserts an item the record does not support.

Usage: python calculate_or_transform.py meeting.json | --selftest
Prints the action-register JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

STANDING_NOTE = (
    "Draft meeting outputs for human review only; this skill does not create tasks, send "
    "messages, or change any tracker, calendar, or system of record, and every action, owner, "
    "and due date must be confirmed before it is treated as committed."
)


def _as_of(doc) -> str:
    v = doc.get("as_of_date")
    return str(v) if v else date.today().isoformat()


def _is_iso_date(v) -> bool:
    try:
        date.fromisoformat(str(v))
        return True
    except Exception:
        return False


def _roster(doc) -> set:
    meeting = doc.get("meeting") or {}
    r = {str(a).strip().lower() for a in (meeting.get("attendees") or [])}
    r |= {str(a).strip().lower() for a in (doc.get("roster") or [])}
    return r


def _norm(text) -> str:
    return " ".join(str(text or "").split()).strip().lower()


def _has_cycle(item_id, edges, seen=None):
    """Depth-first cycle detection over depends_on edges reachable from item_id."""
    seen = seen or set()
    if item_id in seen:
        return True
    seen = seen | {item_id}
    for nxt in edges.get(item_id, []):
        if nxt in edges and _has_cycle(nxt, edges, seen):
            return True
    return False


def _dependency_status(it, ids, edges):
    for dep in it.get("depends_on") or []:
        if dep not in ids:
            return f"missing:{dep}"
    if _has_cycle(it.get("item_id"), edges):
        return "cycle"
    return "ok"


def _citations(it, meeting_id, valid_segments):
    cites = []
    for s in it.get("source_segments") or []:
        if not valid_segments or s in valid_segments:
            cites.append(f"meeting:{meeting_id};seg={s}")
    return cites


def _duplicate(it, existing_tasks):
    if it.get("type") != "action":
        return None
    t = _norm(it.get("text"))
    for task in existing_tasks:
        if _norm(task.get("text")) == t and str(task.get("status", "open")).lower() != "closed":
            return task.get("task_id")
    return None


def build_item(it, doc, ctx):
    meeting_id = (doc.get("meeting") or {}).get("meeting_id")
    typ = it.get("type")
    citations = _citations(it, meeting_id, ctx["segments"])

    owner_raw = it.get("owner")
    owner_norm = _norm(owner_raw)
    owner_required = typ == "action"
    if not owner_raw:
        owner_status = "none-required" if not owner_required else "unresolved"
    elif not ctx["roster"] or owner_norm in ctx["roster"]:
        owner_status = "resolved"
    else:
        owner_status = "unresolved"
    owner_confirmed = bool(it.get("owner_confirmed")) and owner_status == "resolved"

    due = it.get("due_date")
    due_confirmed = bool(it.get("due_confirmed")) and bool(due) and _is_iso_date(due)

    dep_status = _dependency_status(it, ctx["ids"], ctx["edges"])
    dup = _duplicate(it, ctx["existing_tasks"])

    rec = {
        "item_id": it.get("item_id"),
        "type": typ,
        "text": it.get("text"),
        "owner": owner_raw,
        "owner_status": owner_status,
        "owner_confirmed": owner_confirmed,
        "due_date": due if _is_iso_date(due) else None,
        "due_confirmed": due_confirmed,
        "depends_on": it.get("depends_on") or [],
        "dependency_status": dep_status,
        "decided_by": it.get("decided_by"),
        "raised_by": it.get("raised_by"),
        "citations": citations,
        "duplicate_task_id": dup,
        "needs": [],
    }

    # Status precedence: unsupported -> blocked -> needs-confirmation -> possible-duplicate -> ready
    if not citations:
        rec["needs"].append("a source segment in the meeting record")
        rec["status"] = "unsupported"
        return rec
    if dep_status != "ok":
        rec["needs"].append(f"resolve dependency ({dep_status})")
        rec["status"] = "blocked"
        return rec
    if owner_required and owner_status != "resolved":
        rec["needs"].append("a resolved owner from the roster")
        rec["status"] = "needs-confirmation"
        return rec
    if typ == "decision" and not it.get("decided_by"):
        rec["needs"].append("a named decision-maker")
        rec["status"] = "needs-confirmation"
        return rec
    if owner_required and not owner_confirmed:
        rec["needs"].append("owner confirmation")
        rec["status"] = "needs-confirmation"
        return rec
    if owner_required and not due_confirmed:
        rec["needs"].append("a confirmed ISO due date")
        rec["status"] = "needs-confirmation"
        return rec
    if dup:
        rec["needs"].append(f"human review vs existing task {dup}")
        rec["status"] = "possible-duplicate"
        return rec

    rec["status"] = "ready"
    return rec


def _draft_comms(ready_actions, ready_decisions, meeting):
    comms = []
    decision_lines = [f"- {d['text']} (decided by {d.get('decided_by')})" for d in ready_decisions]
    action_lines = [f"- {a['text']} — owner {a['owner']}, due {a['due_date']}" for a in ready_actions]
    recap_body = (
        f"Draft recap for {meeting.get('meeting_id')} ({meeting.get('title','')}). "
        f"Decisions:\n" + ("\n".join(decision_lines) or "- none") +
        "\nAction items:\n" + ("\n".join(action_lines) or "- none") +
        "\nConfirm owners and due dates before treating any item as committed."
    )
    comms.append({
        "type": "recap", "audience": "attendees",
        "delivery": "draft", "approval_required": True,
        "body": recap_body,
        "citations": sorted({c for a in ready_actions + ready_decisions for c in a["citations"]}),
    })
    for a in ready_actions:
        comms.append({
            "type": "reminder", "audience": a["owner"],
            "delivery": "draft", "approval_required": True,
            "body": (f"Draft reminder for {a['owner']}: \"{a['text']}\" (due {a['due_date']}). "
                     f"Confirm before this is treated as a committed action."),
            "citations": a["citations"],
        })
    return comms


def build(doc: dict) -> dict:
    meeting = doc.get("meeting") or {}
    items_in = doc.get("candidate_items") or []
    ctx = {
        "roster": _roster(doc),
        "segments": {s.get("segment_id") for s in (doc.get("segments") or []) if s.get("segment_id")},
        "ids": {it.get("item_id") for it in items_in},
        "edges": {it.get("item_id"): list(it.get("depends_on") or []) for it in items_in},
        "existing_tasks": doc.get("existing_tasks") or [],
    }
    items = [build_item(it, doc, ctx) for it in items_in]

    ready = [r for r in items if r["status"] == "ready"]
    ready_actions = [r for r in ready if r["type"] == "action"]
    ready_decisions = [r for r in ready if r["type"] == "decision"]
    ready_open = [r for r in ready if r["type"] in ("open_question", "risk", "dependency")]
    follow_ups = [r for r in items if r["status"] != "ready"]

    action_register = [
        {"item_id": r["item_id"], "text": r["text"], "owner": r["owner"],
         "due_date": r["due_date"], "depends_on": r["depends_on"], "citations": r["citations"]}
        for r in ready_actions
    ]
    decision_log = [
        {"item_id": r["item_id"], "text": r["text"], "decided_by": r["decided_by"],
         "citations": r["citations"]}
        for r in ready_decisions
    ]
    open_questions = [
        {"item_id": r["item_id"], "type": r["type"], "text": r["text"],
         "raised_by": r["raised_by"], "citations": r["citations"]}
        for r in ready_open
    ]

    def _count(s):
        return sum(1 for r in items if r["status"] == s)

    summary = {
        "total": len(items),
        "ready": len(ready),
        "needs_confirmation": _count("needs-confirmation"),
        "blocked": _count("blocked"),
        "unsupported": _count("unsupported"),
        "possible_duplicate": _count("possible-duplicate"),
    }

    return {
        "template_version": doc.get("template_version"),
        "meeting_id": meeting.get("meeting_id"),
        "as_of_date": _as_of(doc),
        "items": items,
        "decision_log": decision_log,
        "action_register": action_register,
        "open_questions": open_questions,
        "follow_ups": [
            {"item_id": r["item_id"], "type": r["type"], "text": r["text"],
             "status": r["status"], "needs": r["needs"],
             "citations": r["citations"], "duplicate_task_id": r["duplicate_task_id"]}
            for r in follow_ups
        ],
        "draft_comms": _draft_comms(ready_actions, ready_decisions, meeting),
        "summary": summary,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "meeting_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
