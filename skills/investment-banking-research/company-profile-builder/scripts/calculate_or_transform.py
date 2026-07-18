#!/usr/bin/env python3
"""Deterministic company-profile assembler for company-profile-builder.

Maps each fact to its profile section and assigns an assembly status:
  included | stale | unresolved  -> ASSERTED in the section (cited)
  unsupported (no citation)       -> open item only, NEVER asserted
  restricted-mnpi (MNPI + external distribution) -> open item only, EXCLUDED from the profile

It also captures recorded approvals plus outstanding required approvals, flags required
sections with no asserted fact as `section-incomplete`, and builds a deduplicated source
index. It never issues investment advice, a rating, a recommendation, or a price-target
opinion, never fabricates a missing fact, and never distributes/sends/submits the profile.
The output is a DRAFT manifest (`assembly_status: draft-assembled`) for human review.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the profile manifest JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

CONTENT_SECTIONS = ["business_overview", "key_financials", "ownership", "management",
                    "trading_data", "transactions"]
ASSERTED = {"included", "stale", "unresolved"}

STANDING_NOTE = ("Draft company profile for human review only. This profile is not investment "
                 "advice or a recommendation, every stated fact is source-cited, and the profile "
                 "has not been distributed or delivered.")


def _mask_id(s):
    if not s:
        return s
    s = str(s)
    return s if len(s) <= 3 else f"{s[:2]}…{s[-2:]}"


def _cite(f):
    return f.get("source_ref") or None


def _is_stale(f, as_of):
    exp = f.get("expires")
    return bool(exp and as_of and str(exp) < str(as_of))


def _identity_mismatch(f, company):
    fid = f.get("company_id")
    if fid and company.get("company_id") and fid != company.get("company_id"):
        return f"fact company_id {fid!r} != profile company_id {company.get('company_id')!r}"
    return None


def _status(f, company, as_of, external):
    """Assign a status in priority order. Returns (status, reason_or_None)."""
    if not _cite(f):
        return "unsupported", "no source_ref"
    if f.get("mnpi") and external:
        return "restricted-mnpi", "MNPI fact excluded from an external-distribution profile"
    mismatch = _identity_mismatch(f, company)
    if mismatch:
        return "unresolved", f"company identity mismatch: {mismatch}"
    if _is_stale(f, as_of):
        return "stale", f"data expired {f.get('expires')} before as_of {as_of}"
    return "included", None


def _entry(f, status, reason):
    entry = {"section": f.get("section"), "fact_id": f.get("fact_id"),
             "label": f.get("label"), "value": f.get("value"),
             "effective_date": f.get("effective_date"), "expires": f.get("expires"),
             "mnpi": bool(f.get("mnpi")), "status": status, "citation": _cite(f)}
    if reason:
        entry["reason"] = reason
    return entry


def assemble(doc: dict) -> dict:
    company = doc.get("company") or {}
    as_of = doc.get("as_of_date")
    external = doc.get("intended_distribution") == "external"
    required = list(doc.get("required_sections") or [])
    facts = doc.get("facts") or []

    sections: dict = {
        "profile_summary": {},
        "business_overview": [], "key_financials": [], "ownership": [],
        "management": [], "trading_data": [], "transactions": [],
        "approvals": {"recorded": [], "outstanding": []},
        "open_items": [],
        "sources": [],
    }
    open_items: list = []
    citations: list = []

    for f in facts:
        sec = f.get("section")
        status, reason = _status(f, company, as_of, external)
        entry = _entry(f, status, reason)
        label = f.get("label") or f.get("fact_id")

        if status == "unsupported":
            open_items.append({"item": f"{sec}: {label}", "type": "unsupported-claim",
                               "action": "attach an approved source or remove the claim"})
            continue
        if status == "restricted-mnpi":
            open_items.append({"item": f"{sec}: {label}", "type": "mnpi-exclusion",
                               "citation": entry["citation"],
                               "action": "exclude from the external profile or obtain wall-crossing / compliance clearance"})
            if entry["citation"]:
                citations.append(entry["citation"])
            continue

        # asserted (included | stale | unresolved) -> placed in section, cited
        if sec in CONTENT_SECTIONS:
            sections[sec].append(entry)
        citations.append(entry["citation"])
        if status == "stale":
            open_items.append({"item": f"{sec}: {label}", "type": "stale-data",
                               "citation": entry["citation"],
                               "action": "refresh with current data as of the profile date"})
        elif status == "unresolved":
            open_items.append({"item": f"{sec}: {label}", "type": "identity-unresolved",
                               "citation": entry["citation"],
                               "action": "reconcile company identity with a human"})

    # required content sections with no asserted fact -> section-incomplete (never padded)
    for sec in required:
        if sec in CONTENT_SECTIONS and not sections.get(sec):
            open_items.append({"item": sec, "type": "section-incomplete",
                               "action": "add at least one source-cited fact for this required section"})

    # approvals: capture recorded, then mark required-but-missing as outstanding
    recorded_types = set()
    for a in doc.get("approvals") or []:
        if a.get("status") == "recorded":
            rec = {"type": a.get("type"), "approver_role": a.get("approver_role"),
                   "approver": _mask_id(a.get("approver")), "date": a.get("date"),
                   "citation": a.get("source_ref")}
            sections["approvals"]["recorded"].append(rec)
            recorded_types.add(a.get("type"))
            if rec["citation"]:
                citations.append(rec["citation"])
        else:
            sections["approvals"]["outstanding"].append({"type": a.get("type"),
                                                          "status": a.get("status") or "outstanding"})
    for req_ap in doc.get("required_approvals") or []:
        if req_ap not in recorded_types:
            if not any(o.get("type") == req_ap for o in sections["approvals"]["outstanding"]):
                sections["approvals"]["outstanding"].append({"type": req_ap, "status": "outstanding"})
            open_items.append({"item": req_ap, "type": "outstanding-approval",
                               "action": "obtain the required approval before external distribution"})

    # dedup source index, preserving order
    seen = set()
    for cit in citations:
        if cit and cit not in seen:
            seen.add(cit)
            sections["sources"].append(cit)

    sections["open_items"] = open_items

    def _count(status):
        return sum(1 for sec in CONTENT_SECTIONS for e in sections[sec] if e.get("status") == status)

    def _open_count(t):
        return sum(1 for o in open_items if o.get("type") == t)

    sections["profile_summary"] = {
        "profile_id": doc.get("profile_id"),
        "company_legal_name": company.get("legal_name"),
        "ticker": company.get("ticker"),
        "entity_type": company.get("entity_type"),
        "company_id": _mask_id(company.get("company_id")),
        "as_of_date": as_of,
        "intended_distribution": doc.get("intended_distribution") or "internal",
        "required_sections": required,
        "counts": {
            "included": _count("included"),
            "stale": _count("stale"),
            "unresolved": _count("unresolved"),
            "excluded_mnpi": _open_count("mnpi-exclusion"),
            "unsupported": _open_count("unsupported-claim"),
            "section_incomplete": _open_count("section-incomplete"),
            "open_items_total": len(open_items),
            "approvals_recorded": len(sections["approvals"]["recorded"]),
            "approvals_outstanding": len(sections["approvals"]["outstanding"]),
        },
    }

    return {
        "config_version": doc.get("config_version"),
        "profile_id": doc.get("profile_id"),
        "company_legal_name": company.get("legal_name"),
        "ticker": company.get("ticker"),
        "as_of_date": as_of,
        "intended_distribution": doc.get("intended_distribution") or "internal",
        "template_version": doc.get("template_version", "profile-template@0.1.0"),
        "assembly_status": "draft-assembled",
        "human_approval_required_before_delivery": True,
        "sections": sections,
        "open_items": open_items,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "profile_intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
