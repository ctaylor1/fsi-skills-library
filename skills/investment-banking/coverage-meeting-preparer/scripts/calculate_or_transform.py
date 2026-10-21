#!/usr/bin/env python3
"""Deterministic coverage-meeting brief assembler for coverage-meeting-preparer.

For each requested brief: confirm required inputs are present, deduplicate and date-sort
company/market developments, bind every content item to an approved, in-inventory source,
screen source freshness against `freshness_days`, tag any material non-public information
(MNPI) as private-side / internal-only, and — only when all invariants hold and any MNPI is
cleared — assemble a DRAFT brief from an approved template with a citations index and a
recorded-approvals block.

It NEVER sends, distributes, files, or executes anything; never makes an investment
recommendation, price target, or valuation opinion; never gives investment/legal/tax advice;
and never states anything a cited approved source does not support. When a required input is
missing, a claim cites an unknown/unapproved source, a cited source is stale (and
unacknowledged), or MNPI is present without recorded control-room clearance, the brief is
flagged (not packaged) with the reason.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the brief-assembly JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

STANDING_NOTE = (
    "Draft coverage-meeting brief for internal preparation only; this skill does not send, "
    "distribute, file, or execute anything, makes no investment recommendation, price target, "
    "or valuation opinion, and states nothing not backed by a cited approved source. Any "
    "material non-public information is tagged private-side and internal-only; external "
    "delivery requires the recorded control-room and delivery approvals."
)
DEFAULT_FRESHNESS_DAYS = 45
DEFAULT_APPROVED_SOURCES = ("crm", "filings", "transcript", "research", "marketdata",
                            "news", "dataroom", "comps")
MEETING_TYPES = ("client", "prospect")

# (list_key, section_label, text_field, material_default)
CONTENT_SPEC = [
    ("developments", "development", "headline", True),
    ("strategic_issues", "strategic_issue", "issue", True),
    ("client_objectives", "client_objective", "objective", False),
    ("discussion_questions", "discussion_question", "question", False),
    ("follow_ups", "follow_up", "action", False),
]


def _as_of(doc) -> date:
    return date.fromisoformat(str(doc.get("as_of_date")))


def _cite(s) -> str:
    return f"{s.get('system','?')}:{s.get('ref','?')}@{s.get('date','?')}"


def _age_days(s, as_of) -> int | None:
    try:
        return (as_of - date.fromisoformat(str(s.get("date")))).days
    except Exception:
        return None


def _content_items(b):
    """Yield (section_label, text, source_id, material, mnpi, item_id) for every content item,
    including the meeting objective and the relationship summary."""
    obj = b.get("objective")
    if obj:
        rel = b.get("relationship") or {}
        yield ("objective", obj, b.get("objective_source_id") or rel.get("source_id"),
               True, False, "OBJ")
    rel = b.get("relationship") or {}
    if rel:
        summary = (f"Coverage since {rel.get('coverage_since','?')}; last meeting "
                   f"{rel.get('last_meeting','n/a')}; open items: {len(rel.get('open_items') or [])}")
        yield ("relationship", summary, rel.get("source_id"), True, bool(rel.get("mnpi")), "REL")
    for list_key, label, text_field, material_default in CONTENT_SPEC:
        for item in b.get(list_key) or []:
            yield (label, item.get(text_field), item.get("source_id"),
                   bool(item.get("material", material_default)), bool(item.get("mnpi")),
                   item.get("id"))


def _dedup_sorted_developments(b):
    """Deduplicate developments on (date, normalized headline); keep first; sort date desc."""
    seen, kept, removed = set(), [], 0
    for d in b.get("developments") or []:
        key = (str(d.get("date")), str(d.get("headline", "")).strip().lower())
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        kept.append(d)
    kept.sort(key=lambda d: (str(d.get("date")), str(d.get("id"))), reverse=True)
    return kept, removed


def prep_brief(b, doc, as_of, freshness, approved_systems):
    rec = {"engagement_id": b.get("engagement_id"), "client_name": b.get("client_name"),
           "meeting_type": b.get("meeting_type"), "meeting_date": b.get("meeting_date")}

    # 1. needs-data: required content inputs present (do not invent a brief)
    needs = []
    if not b.get("objective"):
        needs.append("objective")
    if not b.get("developments"):
        needs.append("developments")
    if not b.get("client_objectives"):
        needs.append("client_objectives")
    if not b.get("discussion_questions"):
        needs.append("discussion_questions")
    if needs:
        rec.update(status="needs-data", packageable=False, needs=needs, citations=[])
        return rec

    sources = {s.get("source_id"): s for s in b.get("sources") or []}

    # 2. deduplicate + sort developments (in place on a working copy)
    deduped, removed = _dedup_sorted_developments(b)
    work = dict(b)
    work["developments"] = deduped

    # 3. content-to-source integrity (unknown id OR unapproved system => unsupported)
    unsupported, claims = [], []
    mnpi_present = False
    for label, text, sid, material, mnpi, item_id in _content_items(work):
        s = sources.get(sid)
        approved = bool(s) and s.get("system") in approved_systems
        if not approved:
            unsupported.append({"section": label, "text": text, "source_id": sid,
                                "reason": "unknown source_id" if not s else "unapproved source system"})
        internal_only = bool(mnpi) or (bool(s) and s.get("classification") == "mnpi")
        if internal_only:
            mnpi_present = True
        claims.append({"id": item_id, "section": label, "text": text, "material": material,
                       "mnpi": bool(mnpi) or internal_only, "internal_only": internal_only,
                       "citation": _cite(s) if s else None})
    rec["content_integrity"] = {"all_supported": not unsupported, "unsupported": unsupported}
    rec["mnpi_present"] = mnpi_present

    # 4. freshness of cited sources
    cited_ids = {sid for _, _, sid, _, _, _ in _content_items(work) if sid in sources}
    stale_unack = []
    for sid in sorted(cited_ids):
        s = sources[sid]
        age = _age_days(s, as_of)
        if age is not None and age > freshness and not s.get("stale_ack"):
            stale_unack.append({"source_id": sid, "age_days": age, "citation": _cite(s)})
    rec["stale_check"] = {"freshness_days": freshness, "stale_unacknowledged": stale_unack}

    # required approvals (recorded before the draft is relied on / delivered)
    required_approvals = ["supervisory_review", "external_delivery_approval"]
    if mnpi_present:
        required_approvals.insert(1, "control_room_clearance")
    approvals = b.get("approvals") or {}
    rec["required_approvals"] = required_approvals

    # status precedence: needs-data > unsupported > stale > barrier-hold > draft
    if unsupported:
        rec.update(status="unsupported-claims", packageable=False)
        return rec
    if stale_unack:
        rec.update(status="stale-source", packageable=False)
        return rec
    if mnpi_present and (approvals.get("control_room_clearance") or {}).get("status") != "approved":
        rec.update(status="barrier-hold", packageable=False,
                   barrier_reason="MNPI present without recorded control-room clearance")
        return rec

    # packageable -> assemble the DRAFT brief
    citations = sorted({c["citation"] for c in claims if c["citation"]})
    rec["citations"] = citations
    dev_claim = {c["id"]: c for c in claims if c["section"] == "development"}

    handling = ("PRIVATE-SIDE / MNPI - internal coverage preparation only; do not distribute "
                "externally without recorded control-room and delivery approvals." if mnpi_present
                else "Confidential - internal coverage preparation; external delivery requires "
                     "recorded supervisory and delivery approvals.")

    def _sect(list_key, text_field):
        out = []
        for it in work.get(list_key) or []:
            s = sources.get(it.get("source_id"))
            mnpi = bool(it.get("mnpi")) or (bool(s) and s.get("classification") == "mnpi")
            out.append({"id": it.get("id"), "text": it.get(text_field),
                        "internal_only": mnpi, "mnpi": mnpi,
                        "citation": _cite(s) if s else None})
        return out

    rel = work.get("relationship") or {}
    rel_src = sources.get(rel.get("source_id"))
    rec.update(status="draft-brief", packageable=True)
    rec["brief"] = {
        "engagement_id": b.get("engagement_id"),
        "client_name": b.get("client_name"),
        "meeting_type": b.get("meeting_type"),
        "meeting_date": b.get("meeting_date"),
        "preparer": b.get("preparer"),
        "as_of_date": as_of.isoformat(),
        "handling": handling,
        "meeting_snapshot": {
            "objective": b.get("objective"),
            "objective_citation": next((c["citation"] for c in claims if c["section"] == "objective"), None),
            "attendees_client": b.get("attendees_client") or [],
            "attendees_internal": b.get("attendees_internal") or [],
        },
        "relationship_history": {
            "coverage_since": rel.get("coverage_since"),
            "last_meeting": rel.get("last_meeting"),
            "mandates": rel.get("mandates") or [],
            "open_items": rel.get("open_items") or [],
            "citation": _cite(rel_src) if rel_src else None,
        },
        "developments": [{"id": d.get("id"), "date": d.get("date"), "headline": d.get("headline"),
                          "internal_only": dev_claim.get(d.get("id"), {}).get("internal_only", False),
                          "mnpi": dev_claim.get(d.get("id"), {}).get("mnpi", False),
                          "citation": _cite(sources[d.get("source_id")])}
                         for d in deduped],
        "strategic_issues": _sect("strategic_issues", "issue"),
        "client_objectives": _sect("client_objectives", "objective"),
        "discussion_questions": _sect("discussion_questions", "question"),
        "follow_ups": _sect("follow_ups", "action"),
        "claims": claims,
        "citations": citations,
        "developments_deduped": removed,
        "mnpi_present": mnpi_present,
        "required_approvals": required_approvals,
        "approvals": {
            "supervisory_review": approvals.get("supervisory_review") or {"approver": None, "status": "pending"},
            "control_room_clearance": approvals.get("control_room_clearance")
            or {"approver": None, "status": ("approved" if not mnpi_present else "pending"),
                "note": "not required (no MNPI)" if not mnpi_present else "required"},
            "external_delivery_approval": approvals.get("external_delivery_approval") or {"approver": None, "status": "pending"},
        },
        "reviewer_signoff_required": True,
    }
    return rec


def build(doc: dict) -> dict:
    as_of = _as_of(doc)
    freshness = int(doc.get("freshness_days") or DEFAULT_FRESHNESS_DAYS)
    approved_systems = set(doc.get("approved_sources") or DEFAULT_APPROVED_SOURCES)
    briefs = [prep_brief(b, doc, as_of, freshness, approved_systems) for b in doc["briefs"]]

    def _count(s):
        return sum(1 for b in briefs if b.get("status") == s)

    summary = {
        "total": len(briefs),
        "draft_brief": _count("draft-brief"),
        "needs_data": _count("needs-data"),
        "unsupported_claims": _count("unsupported-claims"),
        "stale_source": _count("stale-source"),
        "barrier_hold": _count("barrier-hold"),
    }
    return {"config_version": doc.get("config_version"), "as_of_date": as_of.isoformat(),
            "freshness_days": freshness, "approved_sources": sorted(approved_systems),
            "briefs": briefs, "summary": summary, "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
