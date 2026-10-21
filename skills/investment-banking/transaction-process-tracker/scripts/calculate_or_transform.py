#!/usr/bin/env python3
"""Deterministic transaction-process tracker assembler for transaction-process-tracker.

Turns a deal-process intake bundle into a source-linked status tracker draft. For each
counterparty it records the current stage and NDA / data-room-access / diligence / bid
status, applies deterministic control gates (an executed NDA before access; granted access
before diligence), computes deadline reminders (overdue and due-soon) against as_of_date,
diffs the current state against a prior snapshot to build an auditable change log, captures
recorded approvals plus outstanding required approvals, and compiles an open-items list.

It never selects a bid, recommends a counterparty, grants access, sends outreach or an NDA,
fabricates a status, or delivers the tracker. The output is a DRAFT manifest
(tracker_status: draft-tracker) for human deal-team review.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the tracker manifest JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import date, timedelta
from pathlib import Path

DEFAULT_STAGE_ORDER = ["outreach", "nda", "access", "diligence", "bid", "approval"]
DONE_MILESTONE = {"complete", "completed", "done", "received", "executed", "satisfied", "closed"}
DEFAULT_LOOKAHEAD = 7

STANDING_NOTE = (
    "Draft transaction process tracker for internal deal-team review only. It records "
    "status, reminders, and a change log; it is not a deal decision, bid selection, or "
    "recommendation, and no outreach, NDA, data-room access, or delivery has been executed."
)


def _parse_date(s):
    try:
        return date.fromisoformat(str(s))
    except Exception:
        return None


def _stage_index(stage, order):
    return order.index(stage) if stage in order else -1


def _bid_summary(bid):
    if not isinstance(bid, dict):
        return None
    return {
        "type": bid.get("type"),
        "amount": bid.get("amount"),
        "currency": bid.get("currency"),
        "received_date": bid.get("received_date"),
        "citation": bid.get("source_ref") or "?",
    }


def _control_exceptions(party, order):
    """Deterministic process-control gates. Returns a list of exception dicts."""
    exceptions = []
    if party.get("engagement", "active") != "active":
        return exceptions  # declined/withdrawn parties are tracked but not gated
    stage = party.get("stage")
    nda = party.get("nda_status", "none")
    access = party.get("access_status", "none")
    si = _stage_index(stage, order)
    access_i = _stage_index("access", order)
    diligence_i = _stage_index("diligence", order)

    nda_breach = (access == "granted") or (access_i >= 0 and si >= access_i)
    if nda_breach and nda != "executed":
        exceptions.append({
            "type": "nda-not-executed",
            "detail": f"stage {stage!r}/access {access!r} requires an executed NDA (nda_status={nda!r})",
        })
    if diligence_i >= 0 and si >= diligence_i and access != "granted":
        exceptions.append({
            "type": "access-not-granted",
            "detail": f"stage {stage!r} (>= diligence) requires granted data-room access (access_status={access!r})",
        })
    return exceptions


def _reminders_for_party(party, as_of, lookahead):
    """Overdue and due-soon milestone reminders for one party."""
    reminders = []
    horizon = as_of + timedelta(days=lookahead) if as_of else None
    for m in party.get("milestones") or []:
        status = str(m.get("status", "")).lower()
        if status in DONE_MILESTONE:
            continue
        due = _parse_date(m.get("due_date"))
        if due is None or as_of is None:
            continue
        rec = {
            "party_id": party.get("party_id"),
            "party_name": party.get("name"),
            "milestone_id": m.get("milestone_id"),
            "label": m.get("label"),
            "due_date": m.get("due_date"),
            "citation": m.get("source_ref") or "?",
        }
        if due < as_of:
            rec["urgency"] = "overdue"
            reminders.append(rec)
        elif horizon is not None and due <= horizon:
            rec["urgency"] = "due-soon"
            reminders.append(rec)
    return reminders


def _change_log(parties, prior_snapshot, as_of_str):
    prior_parties = (prior_snapshot or {}).get("parties") or {}
    tracked_fields = ("stage", "nda_status", "access_status")
    log = []
    for p in parties:
        pid = p.get("party_id")
        prev = prior_parties.get(pid)
        if prev is None:
            log.append({"party_id": pid, "field": "party", "from": None, "to": "added",
                        "as_of": as_of_str})
            continue
        for field in tracked_fields:
            old = prev.get(field)
            new = p.get(field)
            if old is not None and old != new:
                log.append({"party_id": pid, "field": field, "from": old, "to": new,
                            "as_of": as_of_str})
    return log


def assemble(doc: dict) -> dict:
    order = doc.get("stage_order") or DEFAULT_STAGE_ORDER
    as_of_str = doc.get("as_of_date")
    as_of = _parse_date(as_of_str)
    lookahead = int(doc.get("reminder_lookahead_days") or DEFAULT_LOOKAHEAD)
    parties = doc.get("parties") or []

    tracker_entries = []
    reminders = []
    open_items = []
    citations = []
    stage_counts = {s: 0 for s in order}
    engagement_counts = {}

    for p in parties:
        pid = p.get("party_id")
        engagement = p.get("engagement", "active")
        engagement_counts[engagement] = engagement_counts.get(engagement, 0) + 1
        stage = p.get("stage")
        if stage in stage_counts:
            stage_counts[stage] += 1

        exceptions = _control_exceptions(p, order)
        entry = {
            "party_id": pid,
            "name": p.get("name"),
            "type": p.get("type"),
            "engagement": engagement,
            "stage": stage,
            "nda_status": p.get("nda_status", "none"),
            "access_status": p.get("access_status", "none"),
            "bid": _bid_summary(p.get("bid")),
            "exceptions": exceptions,
            "status": "tracked",
            "citation": p.get("source_ref") or "?",
        }
        tracker_entries.append(entry)
        citations.append(entry["citation"])
        if entry["bid"] and entry["bid"].get("citation"):
            citations.append(entry["bid"]["citation"])

        # control-exception open items (surfaced, never auto-resolved)
        for ex in exceptions:
            open_items.append({
                "item": f"{pid} ({p.get('name')})",
                "type": "control-exception",
                "exception": ex["type"],
                "detail": ex["detail"],
                "citation": entry["citation"],
                "action": "escalate to the deal team; do not advance the party until resolved",
            })

        # reminders + overdue open items
        pr = _reminders_for_party(p, as_of, lookahead)
        for r in pr:
            reminders.append(r)
            citations.append(r["citation"])
            if r["urgency"] == "overdue":
                open_items.append({
                    "item": f"{pid} {r['milestone_id']} — {r['label']}",
                    "type": "overdue-milestone",
                    "due_date": r["due_date"],
                    "citation": r["citation"],
                    "action": "follow up on the overdue milestone",
                })

    # approvals: capture recorded, then mark required-but-missing as outstanding
    recorded, outstanding = [], []
    recorded_types = set()
    for a in doc.get("approvals") or []:
        if a.get("status") == "recorded":
            rec = {"type": a.get("type"), "approver_role": a.get("approver_role"),
                   "approver": a.get("approver"), "date": a.get("date"),
                   "citation": a.get("source_ref") or "?"}
            recorded.append(rec)
            recorded_types.add(a.get("type"))
            citations.append(rec["citation"])
        else:
            outstanding.append({"type": a.get("type"), "status": a.get("status") or "outstanding"})
    for req_ap in doc.get("required_approvals") or []:
        if req_ap not in recorded_types:
            if not any(o.get("type") == req_ap for o in outstanding):
                outstanding.append({"type": req_ap, "status": "outstanding"})
            open_items.append({
                "item": req_ap,
                "type": "outstanding-approval",
                "action": "obtain the required approval before any external delivery",
            })

    change_log = _change_log(parties, doc.get("prior_snapshot"), as_of_str)

    # dedup source index, preserving order
    seen = set()
    source_index = []
    for cit in citations:
        if cit and cit != "?" and cit not in seen:
            seen.add(cit)
            source_index.append(cit)

    overdue_n = sum(1 for r in reminders if r["urgency"] == "overdue")
    due_soon_n = sum(1 for r in reminders if r["urgency"] == "due-soon")

    sections = {
        "process_summary": {
            "process_id": doc.get("process_id"),
            "deal_name": doc.get("deal_name"),
            "as_of_date": as_of_str,
            "stage_order": order,
            "counts": {
                "parties_total": len(parties),
                "by_stage": stage_counts,
                "by_engagement": engagement_counts,
                "reminders_overdue": overdue_n,
                "reminders_due_soon": due_soon_n,
                "control_exceptions": sum(1 for o in open_items if o["type"] == "control-exception"),
                "open_items_total": len(open_items),
                "approvals_recorded": len(recorded),
                "approvals_outstanding": len(outstanding),
            },
        },
        "party_tracker": tracker_entries,
        "approvals": {"recorded": recorded, "outstanding": outstanding},
        "reminders": reminders,
        "change_log": change_log,
        "open_items": open_items,
        "source_index": source_index,
    }

    return {
        "config_version": doc.get("config_version"),
        "process_id": doc.get("process_id"),
        "deal_name": doc.get("deal_name"),
        "as_of_date": as_of_str,
        "template_version": doc.get("template_version", "transaction-process-tracker-template@0.1.0"),
        "tracker_status": "draft-tracker",
        "human_approval_required_before_delivery": True,
        "sections": sections,
        "open_items": open_items,
        "standing_note": STANDING_NOTE,
    }


REQUIRED_SECTIONS = ["process_summary", "party_tracker", "approvals", "reminders",
                     "change_log", "open_items", "source_index"]


def _selftest() -> int:
    """Assemble the bundled fixture and check internal invariants (deterministic)."""
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "tracker_intake_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = assemble(doc)
    print(json.dumps(out, indent=2))
    errs = []
    secs = out.get("sections", {})
    for s in REQUIRED_SECTIONS:
        if s not in secs:
            errs.append(f"missing section {s}")
    if out.get("tracker_status") != "draft-tracker":
        errs.append(f"tracker_status must be draft-tracker, got {out.get('tracker_status')!r}")
    if out.get("human_approval_required_before_delivery") is not True:
        errs.append("human_approval_required_before_delivery must be true")
    for e in secs.get("party_tracker", []):
        if not e.get("citation"):
            errs.append(f"party {e.get('party_id')} missing citation")
    counts = secs.get("process_summary", {}).get("counts", {})
    overdue = sum(1 for r in secs.get("reminders", []) if r.get("urgency") == "overdue")
    if counts.get("reminders_overdue") != overdue:
        errs.append(f"overdue count mismatch: summary={counts.get('reminders_overdue')} actual={overdue}")
    ce = sum(1 for o in secs.get("open_items", []) if o.get("type") == "control-exception")
    if counts.get("control_exceptions") != ce:
        errs.append(f"control-exception count mismatch: summary={counts.get('control_exceptions')} actual={ce}")
    if not secs.get("source_index"):
        errs.append("source_index is empty (no citations indexed)")
    for e in errs:
        print("ERROR", e)
    print(f"transform selftest: {len(errs)} error(s)")
    return 1 if errs else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
