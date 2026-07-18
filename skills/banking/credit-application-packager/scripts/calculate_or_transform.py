#!/usr/bin/env python3
"""Deterministic credit-application package assembler for credit-application-packager.

Maps each required package component to its supporting document, assigns an assembly status
(included | stale | unresolved | open-item), checks borrower/entity consistency across
documents, captures recorded approvals plus outstanding required approvals, lists outstanding
conditions, and builds a cited source index. It never certifies completeness, never makes a
credit decision, never fabricates a missing document, and never sends/submits the package.
The output is a DRAFT manifest (`assembly_status: draft-assembled`) for human review.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the package manifest JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Canonical component -> template section mapping (versioned contract; mirrors the template).
COMPONENT_SECTION = {
    "application": "application",
    "financial-statements": "financial_information",
    "tax-returns": "financial_information",
    "collateral": "collateral",
    "kyc-onboarding": "kyc_onboarding",
}
LIST_SECTIONS = {"financial_information"}  # sections that hold multiple component entries

STANDING_NOTE = ("Draft credit package for human review only. This package is not a "
                 "completeness certification, not a credit decision or adverse-action notice, "
                 "and has not been submitted or delivered.")


def _mask_id(s):
    if not s:
        return s
    s = str(s)
    return s if len(s) <= 3 else f"{s[:2]}…{s[-2:]}"


def _cite(d):
    return d.get("source_ref") or "?"


def _is_stale(d, as_of):
    exp = d.get("expires")
    return bool(exp and as_of and str(exp) < str(as_of))


def _identity_mismatch(d, borrower):
    did = d.get("borrower_id")
    dname = d.get("borrower_name")
    if did and borrower.get("borrower_id") and did != borrower.get("borrower_id"):
        return f"document borrower_id {did!r} != package borrower_id {borrower.get('borrower_id')!r}"
    if dname and borrower.get("legal_name") and dname != borrower.get("legal_name"):
        return f"document borrower_name {dname!r} != package legal_name {borrower.get('legal_name')!r}"
    return None


def _component_entry(comp, d, borrower, as_of):
    """Build one assembled-component entry with a status and citation."""
    entry = {"component": comp, "doc_id": d.get("doc_id"), "title": d.get("title"),
             "effective_date": d.get("effective_date"), "expires": d.get("expires"),
             "citation": _cite(d), "values": d.get("values") or {}}
    mismatch = _identity_mismatch(d, borrower)
    if mismatch:
        entry["status"] = "unresolved"
        entry["reason"] = f"borrower identity mismatch: {mismatch}"
    elif _is_stale(d, as_of):
        entry["status"] = "stale"
        entry["reason"] = f"document expired {d.get('expires')} before as_of {as_of}"
    else:
        entry["status"] = "included"
    return entry


def assemble(doc: dict) -> dict:
    borrower = doc.get("borrower") or {}
    as_of = doc.get("as_of_date")
    required = list(doc.get("required_components") or [])
    documents = doc.get("documents") or []

    # index provided documents by component
    by_component: dict = {}
    for d in documents:
        by_component.setdefault(d.get("component"), []).append(d)

    # canonical sections scaffold
    sections: dict = {
        "package_summary": {},
        "borrower_profile": {
            "borrower_id": _mask_id(borrower.get("borrower_id")),
            "legal_name": borrower.get("legal_name"),
            "entity_type": borrower.get("entity_type"),
        },
        "application": {"status": "not-required"},
        "financial_information": [],
        "collateral": {"status": "not-required"},
        "kyc_onboarding": {"status": "not-required"},
        "approvals": {"recorded": [], "outstanding": []},
        "open_items": [],
        "source_index": [],
    }

    open_items: list = []
    citations: list = []

    for comp in required:
        section = COMPONENT_SECTION.get(comp)
        docs = by_component.get(comp) or []
        if not docs:
            # required but not provided -> open item (never fabricated)
            open_items.append({"item": comp, "type": "missing-component",
                               "action": "obtain and attach the required document"})
            entry = {"component": comp, "status": "open-item",
                     "reason": "required component has no supporting document"}
            if section and section not in LIST_SECTIONS:
                sections[section] = entry
            elif section in LIST_SECTIONS:
                sections[section].append(entry)
            continue
        for d in docs:
            entry = _component_entry(comp, d, borrower, as_of)
            citations.append(entry["citation"])
            if section in LIST_SECTIONS:
                sections[section].append(entry)
            elif section:
                sections[section] = entry
            if entry["status"] == "stale":
                open_items.append({"item": f"{comp} ({d.get('doc_id')})", "type": "stale-document",
                                   "citation": entry["citation"], "action": "refresh with a current document"})
            elif entry["status"] == "unresolved":
                open_items.append({"item": f"{comp} ({d.get('doc_id')})", "type": "identity-unresolved",
                                   "citation": entry["citation"], "action": "reconcile borrower identity with a human"})

    # approvals: capture recorded, then mark required-but-missing as outstanding
    recorded_types = set()
    for a in doc.get("approvals") or []:
        if a.get("status") == "recorded":
            rec = {"type": a.get("type"), "approver_role": a.get("approver_role"),
                   "approver": _mask_id(a.get("approver")), "date": a.get("date"),
                   "citation": _cite(a)}
            sections["approvals"]["recorded"].append(rec)
            recorded_types.add(a.get("type"))
            citations.append(rec["citation"])
        else:
            sections["approvals"]["outstanding"].append({"type": a.get("type"),
                                                          "status": a.get("status") or "outstanding"})
    for req_ap in doc.get("required_approvals") or []:
        if req_ap not in recorded_types:
            if not any(o.get("type") == req_ap for o in sections["approvals"]["outstanding"]):
                sections["approvals"]["outstanding"].append({"type": req_ap, "status": "outstanding"})
            open_items.append({"item": req_ap, "type": "outstanding-approval",
                               "action": "obtain the required approval before delivery"})

    # conditions
    for c in doc.get("conditions") or []:
        if c.get("status") not in ("satisfied", "cleared"):
            open_items.append({"item": c.get("condition_id"), "type": "outstanding-condition",
                               "citation": _cite(c), "action": c.get("description") or "satisfy condition"})
            citations.append(_cite(c))

    # dedup source index, preserving order
    seen = set()
    for cit in citations:
        if cit and cit != "?" and cit not in seen:
            seen.add(cit)
            sections["source_index"].append(cit)

    sections["open_items"] = open_items

    # summary counts
    def _count(status):
        n = 0
        for key, val in sections.items():
            if key in ("package_summary", "borrower_profile", "approvals", "open_items", "source_index"):
                continue
            entries = val if isinstance(val, list) else [val]
            n += sum(1 for e in entries if isinstance(e, dict) and e.get("status") == status)
        return n

    sections["package_summary"] = {
        "package_id": doc.get("package_id"),
        "product": doc.get("product"),
        "jurisdiction": doc.get("jurisdiction"),
        "as_of_date": as_of,
        "borrower_id": _mask_id(borrower.get("borrower_id")),
        "required_components": required,
        "counts": {
            "included": _count("included"),
            "stale": _count("stale"),
            "unresolved": _count("unresolved"),
            "open_item": _count("open-item"),
            "open_items_total": len(open_items),
            "approvals_recorded": len(sections["approvals"]["recorded"]),
            "approvals_outstanding": len(sections["approvals"]["outstanding"]),
        },
    }

    return {
        "config_version": doc.get("config_version"),
        "package_id": doc.get("package_id"),
        "product": doc.get("product"),
        "jurisdiction": doc.get("jurisdiction"),
        "as_of_date": as_of,
        "template_version": doc.get("template_version", "credit-package-template@0.1.0"),
        "assembly_status": "draft-assembled",
        "human_approval_required_before_delivery": True,
        "sections": sections,
        "open_items": open_items,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "package_intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
