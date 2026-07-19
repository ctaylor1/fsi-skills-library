#!/usr/bin/env python3
"""Deterministic follow-up package assembler for advisor-follow-up-assistant.

Lays a documented post-meeting record into the firm's required follow-up template sections
(meeting summary, action items, client communication, disclosures, CRM update, next-meeting
reminder, approvals), maps every material assertion to a source, checks disclosure completeness
for each recommendation discussed, records suitability/senior-protection handoffs, and scores
completeness. It produces a DRAFT ONLY: it never sends the communication, writes the CRM or any
system of record, places a trade, schedules a meeting, or makes a suitability determination.
Uncited material assertions, action items missing an owner/due date, and recommendations lacking a
required disclosure are surfaced as `needs-data`, never smoothed over.

Usage: python calculate_or_transform.py request.json | --selftest
Prints the draft follow-up package JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# The 7 required follow-up sections (key, title). Order and titles are the template contract.
REQUIRED_SECTIONS = [
    ("meeting-summary", "Meeting Summary"),
    ("action-items", "Action Items"),
    ("client-communication", "Client Communication (Draft)"),
    ("disclosures", "Disclosures"),
    ("crm-update", "CRM Update (Proposed)"),
    ("next-meeting", "Next-Meeting Reminder"),
    ("approvals-and-delivery", "Approvals and Delivery"),
]
# Sections whose content is a material assertion and MUST carry a citation.
MATERIAL_SECTIONS = {
    "meeting-summary", "action-items", "client-communication",
    "disclosures", "crm-update", "next-meeting",
}
APPROVAL_ROLES = ("Advisor", "Supervisory Principal")
SUITABILITY_SKILL = "suitability-reg-bi-reviewer"
SENIOR_SKILL = "senior-investor-protection-screener"
STANDING_NOTE = ("Draft follow-up package for human review only; nothing has been sent to the "
                 "client, no CRM or system of record has been updated, no trade has been placed, "
                 "and no suitability determination has been made.")


def _dp_citations(doc):
    return [dp.get("citation") for dp in (doc.get("discussion_points") or []) if dp.get("citation")]


def _section_citations(key, doc):
    """Map a section key to the citations available for it from the request."""
    meeting = doc.get("meeting") or {}
    meeting_cite = [meeting.get("citation")] if meeting.get("citation") else []
    disclosures = doc.get("disclosures") or []
    disc_cites = [d.get("citation") for d in disclosures if d.get("citation")]
    m = {
        "meeting-summary": meeting_cite + _dp_citations(doc),
        "action-items": [ai.get("citation") for ai in (doc.get("action_items") or []) if ai.get("citation")],
        "client-communication": ([doc["client_communication"]["citation"]]
                                 if (doc.get("client_communication") or {}).get("citation") else []),
        # If no product-specific disclosure applies, the meeting record cites the "none required" basis.
        "disclosures": disc_cites or meeting_cite,
        "crm-update": [f.get("citation") for f in (doc.get("crm_update") or {}).get("fields") or []
                       if f.get("citation")],
        "next-meeting": ([doc["next_meeting"]["citation"]]
                         if (doc.get("next_meeting") or {}).get("citation") else []),
        "approvals-and-delivery": [],  # approvals are a pending block, not a cited assertion
    }
    # de-duplicate while preserving order
    seen, out = set(), []
    for c in m.get(key, []):
        if c and c not in seen:
            seen.add(c); out.append(c)
    return out


def assemble(doc: dict) -> dict:
    needs, sections, source_map = [], [], {}

    for key, title in REQUIRED_SECTIONS:
        cites = _section_citations(key, doc)
        gaps = []
        if key in MATERIAL_SECTIONS and not cites:
            gaps.append(f"missing citation for {title.lower()} (material assertion)")
            needs.append(f"{title}: source citation")
        sections.append({"key": key, "title": title, "present": True,
                         "citations": cites, "gaps": gaps})
        source_map[key] = cites

    # --- action items: owner + due date + citation required ---
    action_items = []
    for ai in doc.get("action_items") or []:
        aid = ai.get("id")
        for f in ("owner", "due_date", "citation"):
            if not ai.get(f):
                needs.append(f"Action Items: {aid} missing {f}")
        action_items.append({"id": aid, "owner": ai.get("owner"), "description": ai.get("description"),
                             "due_date": ai.get("due_date"), "citation": ai.get("citation")})

    # --- disclosure completeness + suitability / senior routing ---
    recommendations = doc.get("recommendations") or []
    disclosures = doc.get("disclosures") or []
    covered = {d.get("covers_recommendation") for d in disclosures}
    routes = []
    for rec in recommendations:
        rid = rec.get("id")
        if rec.get("requires_disclosure") and rid not in covered:
            needs.append(f"Disclosures: add a disclosure covering recommendation {rid}")
        if rec.get("requires_suitability_review"):
            routes.append({"to": SUITABILITY_SKILL, "ref": rid,
                           "reason": "recommendation discussed requires suitability / Reg BI review"})
    if (doc.get("client") or {}).get("senior_or_vulnerable"):
        routes.append({"to": SENIOR_SKILL, "ref": (doc.get("client") or {}).get("household_id"),
                       "reason": "senior / vulnerable client indicator raised in the meeting"})

    # --- approvals: always recorded as pending; never granted by this skill ---
    existing = {a.get("role"): a for a in (doc.get("approvals") or [])}
    approvals = []
    for role in APPROVAL_ROLES:
        a = existing.get(role, {})
        approvals.append({"role": role, "name_masked": a.get("name_masked", "TBD"), "status": "pending"})

    cited_material = sum(1 for s in sections if s["key"] in MATERIAL_SECTIONS and s["citations"])
    disposition = "needs-data" if needs else "draft-ready"

    return {
        "followup_id": doc.get("followup_id"),
        "config_version": doc.get("config_version"),
        "template_version": doc.get("template_version"),
        "disclosures_version": doc.get("disclosures_version"),
        "author_id": doc.get("author_id"),
        "meeting": {"date": (doc.get("meeting") or {}).get("date"),
                    "channel": (doc.get("meeting") or {}).get("channel"),
                    "citation": (doc.get("meeting") or {}).get("citation")},
        "draft_status": "draft",
        "delivery_status": "not-delivered",
        "crm_write_status": "not-written",
        "sections": sections,
        "discussion_points": doc.get("discussion_points") or [],
        "recommendations": recommendations,
        "action_items": action_items,
        "client_communication": doc.get("client_communication") or {},
        "disclosures": disclosures,
        "crm_update": doc.get("crm_update") or {"fields": []},
        "next_meeting": doc.get("next_meeting") or {},
        "routes": routes,
        "source_map": source_map,
        "completeness": {
            "required_sections": len(REQUIRED_SECTIONS),
            "present_sections": sum(1 for s in sections if s["present"]),
            "material_required": len(MATERIAL_SECTIONS),
            "cited_material_sections": cited_material,
            "action_items": len(action_items),
            "disclosures": len(disclosures),
        },
        "approvals": approvals,
        "needs": needs,
        "disposition": disposition,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "followup_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
