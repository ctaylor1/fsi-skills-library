#!/usr/bin/env python3
"""Deterministic pitch-book assembly engine for investment-banking-pitch-builder.

Takes a pitch build request (approved analyses/models/profiles, a versioned template, page
takeaways, sources, and recorded approvals) and assembles a DRAFT pitch-book package:
orders pages by the template's required sections, computes a per-page readiness status,
maps every claim to its cited source, checks section completeness and recorded approvals,
and sets a delivery status. It NEVER sends, submits, distributes, or files materials, never
fabricates a figure or source, and never marks a page ready when a claim lacks an approved
source. External delivery remains a human action gated on the recorded approvals.

Usage: python calculate_or_transform.py request.json | --selftest
Prints the assembled draft JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

STANDING_NOTE = (
    "Draft pitch materials only; no materials have been sent, delivered, distributed, or "
    "filed. External delivery requires the recorded banker, control-room/compliance, and "
    "legal/disclaimer approvals and is performed by a person, not this skill."
)
DRAFT_ONLY_NOTICE = (
    "DRAFT - for internal banker and compliance review only. Not for external distribution "
    "until the required approvals are recorded."
)


def _page_status(p: dict) -> tuple[str, list[str]]:
    """Return (status, issues) for a page. Status is the first blocking condition found."""
    issues: list[str] = []
    unsupported = [c for c in (p.get("claims") or [])
                   if not c.get("source_ref") or c.get("approved") is not True]
    for c in unsupported:
        issues.append(f"unsupported/unapproved claim: {c.get('text','')!r}")
    no_source = not p.get("sources")
    if no_source:
        issues.append("page has no source citation")
    no_takeaway = not p.get("takeaway")
    if no_takeaway:
        issues.append("page has no takeaway")
    appr = (p.get("approval") or {}).get("status")
    needs_approval = appr != "approved"
    if needs_approval:
        issues.append(f"content approval status is {appr!r}")

    if unsupported:
        return "unsupported-claim", issues
    if no_source or no_takeaway:
        return "needs-source", issues
    if needs_approval:
        return "needs-approval", issues
    return "ready", issues


def assemble(doc: dict) -> dict:
    tmpl = doc.get("template") or {}
    required_sections = list(tmpl.get("required_sections") or [])
    pages_in = doc.get("pages") or []

    # Order pages by the template's required-section order, then by original order.
    order = {s: i for i, s in enumerate(required_sections)}
    pages_sorted = sorted(
        enumerate(pages_in),
        key=lambda t: (order.get(t[1].get("section"), len(required_sections)), t[0]),
    )

    pages_out = []
    unsupported_claims = []
    for _, p in pages_sorted:
        status, issues = _page_status(p)
        if status == "unsupported-claim":
            for c in (p.get("claims") or []):
                if not c.get("source_ref") or c.get("approved") is not True:
                    unsupported_claims.append({"page_id": p.get("page_id"), "claim": c.get("text")})
        pages_out.append({
            "page_id": p.get("page_id"),
            "section": p.get("section"),
            "title": p.get("title"),
            "source_component": p.get("source_component"),
            "takeaway": p.get("takeaway"),
            "claims": p.get("claims") or [],
            "sources": p.get("sources") or [],
            "approval": p.get("approval") or {},
            "status": status,
            "issues": issues,
        })

    present = {p["section"] for p in pages_out}
    sections_present = [s for s in required_sections if s in present]
    sections_missing = [s for s in required_sections if s not in present]

    required_approvals = list(doc.get("required_approvals") or [])
    approvals = doc.get("approvals") or []
    appr_map = {a.get("role"): a.get("status") for a in approvals}
    approvals_status = {r: appr_map.get(r, "missing") for r in required_approvals}
    approvals_met = all(v == "approved" for v in approvals_status.values()) and bool(required_approvals)

    all_pages_ready = all(p["status"] == "ready" for p in pages_out)
    complete = not sections_missing and all_pages_ready and not unsupported_claims

    if complete and approvals_met:
        delivery_status = "approved-for-delivery"
    else:
        delivery_status = "hold-for-approval"

    summary = {
        "pages_total": len(pages_out),
        "pages_ready": sum(1 for p in pages_out if p["status"] == "ready"),
        "pages_blocked": sum(1 for p in pages_out if p["status"] != "ready"),
        "sections_present": len(sections_present),
        "sections_missing": len(sections_missing),
        "unsupported_claims": len(unsupported_claims),
        "approvals_met": approvals_met,
    }

    return {
        "engagement_id": doc.get("engagement_id"),
        "template_id": tmpl.get("template_id"),
        "template_version": tmpl.get("version"),
        "template_required_sections": required_sections,
        "deal_context": doc.get("deal_context") or {},
        "delivery_status": delivery_status,
        "sections_present": sections_present,
        "sections_missing": sections_missing,
        "pages": pages_out,
        "required_approvals": required_approvals,
        "approvals": approvals,
        "approvals_status": approvals_status,
        "unsupported_claims": unsupported_claims,
        "summary": summary,
        "draft_only_notice": DRAFT_ONLY_NOTICE,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pitch_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
