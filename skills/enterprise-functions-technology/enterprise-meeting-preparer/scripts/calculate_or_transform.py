#!/usr/bin/env python3
"""Deterministic meeting-brief assembler for enterprise-meeting-preparer.

For each meeting: confirm required inputs are present, resolve attendees, check that every
content item cites a source in the meeting's inventory, screen source freshness against
`freshness_days`, flag overdue prior actions, and — only when all invariants hold — assemble
a draft brief with a citations index from an approved template.

It NEVER schedules/sends/distributes/updates anything, never makes or authorizes a decision
or commitment, never gives investment/legal/tax advice, and never states anything a cited
source does not support. When a required input is missing, an attendee is unresolved, content
cites an unknown source, or a cited source is stale (and unacknowledged), the meeting is
flagged (not packaged) with the reason.

Usage: python calculate_or_transform.py meetings.json | --selftest
Prints the brief-assembly JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

STANDING_NOTE = (
    "Internal meeting brief for preparation only; this skill does not schedule, send, "
    "distribute, or update any meeting, invite, calendar, or system of record, does not make "
    "or authorize any decision or commitment, and every item must be verified against its "
    "cited source before the meeting."
)
DEFAULT_FRESHNESS_DAYS = 30
# (list_key, label, text_field)
CONTENT_SPEC = [
    ("agenda_items", "agenda_item", "item"),
    ("decisions", "decision", "decision"),
    ("risks", "risk", "risk"),
    ("prior_actions", "prior_action", "action"),
    ("talking_points", "talking_point", "point"),
]


def _as_of(doc) -> date:
    return date.fromisoformat(str(doc.get("as_of_date")))


def _cite(s) -> str:
    return f"{s.get('system','?')}:{s.get('ref','?')}@{s.get('date','?')}"


def _age_days(s, as_of) -> int | None:
    d = s.get("date")
    try:
        return (as_of - date.fromisoformat(str(d))).days
    except Exception:
        return None


def _content_items(m):
    for list_key, label, text_field in CONTENT_SPEC:
        for item in m.get(list_key) or []:
            yield label, item.get(text_field), item.get("source_id")


def prep_meeting(m, doc, as_of, freshness):
    rec = {"meeting_id": m.get("meeting_id"), "title": m.get("title")}

    # 1. needs-data: required content inputs present
    needs = []
    if not m.get("purpose"):
        needs.append("purpose")
    if not m.get("attendees"):
        needs.append("attendees")
    if not m.get("agenda_items"):
        needs.append("agenda_items")
    if needs:
        rec.update(status="needs-data", packageable=False, needs=needs, citations=[])
        return rec

    sources = {s.get("source_id"): s for s in m.get("sources") or []}

    # 2. unresolved attendee
    unresolved = [a.get("name") for a in m.get("attendees") or [] if not a.get("resolved")]
    rec["attendees_resolved"] = not unresolved

    # 3. content-to-source integrity
    unsupported = []
    for label, text, sid in _content_items(m):
        if sid not in sources:
            unsupported.append({"type": label, "text": text, "source_id": sid})
    rec["content_integrity"] = {"all_sourced": not unsupported, "unsupported": unsupported}

    # 4. freshness of cited sources
    cited_ids = {sid for _, _, sid in _content_items(m) if sid in sources}
    stale_unack = []
    for sid in sorted(cited_ids):
        s = sources[sid]
        age = _age_days(s, as_of)
        if age is not None and age > freshness and not s.get("stale_ack"):
            stale_unack.append({"source_id": sid, "age_days": age, "citation": _cite(s)})
    rec["stale_check"] = {"freshness_days": freshness, "stale_unacknowledged": stale_unack}

    # status precedence
    if unresolved:
        rec.update(status="unresolved-attendee", packageable=False, unresolved_attendees=unresolved)
        return rec
    if unsupported:
        rec.update(status="unsupported-content", packageable=False)
        return rec
    if stale_unack:
        rec.update(status="stale-source", packageable=False)
        return rec

    # packageable -> assemble the brief
    citations = [_cite(sources[sid]) for sid in sorted(cited_ids)]
    rec["citations"] = citations

    def _overdue(pa):
        if pa.get("status") == "open" and pa.get("due_date"):
            try:
                return date.fromisoformat(str(pa["due_date"])) < as_of
            except Exception:
                return False
        return False

    rec.update(status="draft-brief", packageable=True)
    rec["brief"] = {
        "meeting_id": m.get("meeting_id"),
        "title": m.get("title"),
        "datetime": m.get("datetime"),
        "organizer": m.get("organizer"),
        "location": m.get("location"),
        "as_of_date": as_of.isoformat(),
        "purpose": m.get("purpose"),
        "attendees": [{"name": a.get("name"), "role": a.get("role"), "org": a.get("org")}
                      for a in m.get("attendees") or []],
        "agenda": [{"item": a.get("item"), "owner": a.get("owner"),
                    "citation": _cite(sources[a.get("source_id")])}
                   for a in m.get("agenda_items") or []],
        "decisions": [{"decision": d.get("decision"), "status": d.get("status"),
                       "citation": _cite(sources[d.get("source_id")])}
                      for d in m.get("decisions") or []],
        "risks": [{"risk": r.get("risk"), "severity": r.get("severity"),
                   "citation": _cite(sources[r.get("source_id")])}
                  for r in m.get("risks") or []],
        "open_actions": [{"action": p.get("action"), "owner": p.get("owner"),
                          "due_date": p.get("due_date"), "status": p.get("status"),
                          "overdue": _overdue(p), "citation": _cite(sources[p.get("source_id")])}
                         for p in m.get("prior_actions") or []],
        "talking_points": [{"point": t.get("point"),
                            "citation": _cite(sources[t.get("source_id")])}
                           for t in m.get("talking_points") or []],
        "citations": citations,
        "reviewer_signoff_required": True,
    }
    return rec


def build(doc: dict) -> dict:
    as_of = _as_of(doc)
    freshness = int(doc.get("freshness_days") or DEFAULT_FRESHNESS_DAYS)
    briefs = [prep_meeting(m, doc, as_of, freshness) for m in doc["meetings"]]

    def _count(s):
        return sum(1 for b in briefs if b.get("status") == s)

    summary = {
        "total": len(briefs),
        "draft_brief": _count("draft-brief"),
        "needs_data": _count("needs-data"),
        "unresolved_attendee": _count("unresolved-attendee"),
        "unsupported_content": _count("unsupported-content"),
        "stale_source": _count("stale-source"),
    }
    return {"as_of_date": as_of.isoformat(), "freshness_days": freshness,
            "briefs": briefs, "summary": summary, "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "meetings_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
