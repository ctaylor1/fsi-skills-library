#!/usr/bin/env python3
"""Deterministic fund fact-sheet assembler for fund-fact-sheet-builder.

Maps each fact to its fact-sheet section, reconciles every numeric figure to its source
value, and assigns an assembly status:
  included | stale | unresolved  -> ASSERTED in the section (cited)
  unsupported (no citation)                       -> open item only, NEVER asserted
  restricted (MNPI/embargoed + external)          -> open item only, EXCLUDED from the sheet
  reconcile-break (figure does not tie to source) -> open item only, NEVER asserted

It also renders required regulatory disclosures (each must be cited), captures recorded
approvals plus outstanding required approvals, flags required sections with no asserted fact
as `section-incomplete`, builds a source-to-output reconciliation ledger, and builds a
deduplicated source index. It never states a return/fee figure that does not tie to its
system of record, never makes a performance promise, rating, or recommendation, never
fabricates a missing figure, and never sends/submits/publishes the fact sheet. The output is
a DRAFT manifest (`assembly_status: draft-assembled`) for human review.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the fact-sheet manifest JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

CONTENT_SECTIONS = ["performance", "holdings", "risk", "fees", "esg"]
ASSERTED = {"included", "stale", "unresolved"}
DEFAULT_TOLERANCE = 0.05

STANDING_NOTE = ("Draft fund fact sheet for human review only. Every figure is source-cited "
                 "and reconciled to its system of record, past performance is not indicative "
                 "of future results, and this fact sheet has not been reviewed, approved, or "
                 "distributed.")


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


def _identity_mismatch(f, fund):
    fid = f.get("fund_id")
    if fid and fund.get("fund_id") and fid != fund.get("fund_id"):
        return f"fact fund_id {fid!r} != fact-sheet fund_id {fund.get('fund_id')!r}"
    return None


def _reconcile(f):
    """Return (has_pair, delta, tolerance, ties_out) for a numeric figure."""
    v, sv = f.get("value_numeric"), f.get("source_value_numeric")
    if v is None or sv is None:
        return False, None, None, None
    tol = f.get("reconcile_tolerance")
    tol = DEFAULT_TOLERANCE if tol is None else float(tol)
    delta = round(abs(float(v) - float(sv)), 10)
    return True, delta, tol, delta <= tol


def _status(f, fund, as_of, external):
    """Assign a status in priority order. Returns (status, reason_or_None)."""
    if not _cite(f):
        return "unsupported", "no source_ref"
    if f.get("mnpi") and external:
        return "restricted", "MNPI/embargoed fact excluded from an external-distribution fact sheet"
    has_pair, delta, tol, ties = _reconcile(f)
    if has_pair and not ties:
        return "reconcile-break", (f"figure {f.get('value_numeric')} does not tie to source "
                                   f"{f.get('source_value_numeric')} (delta {delta} > tolerance {tol})")
    mismatch = _identity_mismatch(f, fund)
    if mismatch:
        return "unresolved", f"fund identity mismatch: {mismatch}"
    if _is_stale(f, as_of):
        return "stale", f"data expired {f.get('expires')} before as_of {as_of}"
    return "included", None


def _entry(f, status, reason):
    entry = {"section": f.get("section"), "fact_id": f.get("fact_id"),
             "label": f.get("label"), "value": f.get("value"),
             "value_numeric": f.get("value_numeric"),
             "basis": f.get("basis"),
             "effective_date": f.get("effective_date"), "expires": f.get("expires"),
             "mnpi": bool(f.get("mnpi")), "status": status, "citation": _cite(f)}
    if reason:
        entry["reason"] = reason
    return entry


def assemble(doc: dict) -> dict:
    fund = doc.get("fund") or {}
    as_of = doc.get("as_of_date")
    external = doc.get("intended_distribution") == "external"
    required = list(doc.get("required_sections") or [])
    facts = doc.get("facts") or []

    sections: dict = {
        "fund_summary": {},
        "performance": [], "holdings": [], "risk": [], "fees": [], "esg": [],
        "reconciliation": [],
        "disclosures": [],
        "approvals": {"recorded": [], "outstanding": []},
        "open_items": [],
        "sources": [],
    }
    open_items: list = []
    citations: list = []

    for f in facts:
        sec = f.get("section")
        status, reason = _status(f, fund, as_of, external)
        entry = _entry(f, status, reason)
        label = f.get("label") or f.get("fact_id")

        # source-to-output reconciliation ledger: record every figure that carries both a
        # rendered value and a source value, whatever its final assembly status.
        has_pair, delta, tol, ties = _reconcile(f)
        if has_pair:
            sections["reconciliation"].append({
                "fact_id": f.get("fact_id"), "section": sec, "label": label,
                "value_numeric": f.get("value_numeric"),
                "source_value_numeric": f.get("source_value_numeric"),
                "delta": delta, "tolerance": tol,
                "status": "reconciled" if ties else "reconcile-break",
                "citation": _cite(f)})

        if status == "unsupported":
            open_items.append({"item": f"{sec}: {label}", "type": "unsupported-claim",
                               "action": "attach an approved source or remove the figure"})
            continue
        if status == "restricted":
            open_items.append({"item": f"{sec}: {label}", "type": "mnpi-exclusion",
                               "status": "restricted", "citation": entry["citation"],
                               "action": "exclude from the external fact sheet or obtain wall-crossing / compliance clearance"})
            continue
        if status == "reconcile-break":
            open_items.append({"item": f"{sec}: {label}", "type": "reconcile-break",
                               "citation": entry["citation"], "reason": reason,
                               "action": "reconcile the figure to its system of record before it is asserted"})
            continue

        # asserted (included | stale | unresolved) -> placed in section, cited
        if sec in CONTENT_SECTIONS:
            sections[sec].append(entry)
        citations.append(entry["citation"])
        if status == "stale":
            open_items.append({"item": f"{sec}: {label}", "type": "stale-data",
                               "citation": entry["citation"],
                               "action": "refresh with data current as of the reporting date"})
        elif status == "unresolved":
            open_items.append({"item": f"{sec}: {label}", "type": "identity-unresolved",
                               "citation": entry["citation"],
                               "action": "reconcile fund/share-class identity with a human"})

    # required content sections with no asserted fact -> section-incomplete (never padded)
    for sec in required:
        if sec in CONTENT_SECTIONS and not sections.get(sec):
            open_items.append({"item": sec, "type": "section-incomplete",
                               "action": "add at least one source-cited figure for this required section"})

    # disclosures: render only cited disclosures; uncited -> unsupported open item.
    rendered_disclosures = set()
    for d in doc.get("disclosures") or []:
        did = d.get("disclosure_id")
        cit = d.get("source_ref") or None
        text = (d.get("text") or "").strip()
        if not cit or not text:
            open_items.append({"item": did, "type": "disclosure-unsupported",
                               "action": "attach the approved disclosure text and its controlled-content citation"})
            continue
        sections["disclosures"].append({"disclosure_id": did, "text": text,
                                        "status": "included", "citation": cit})
        rendered_disclosures.add(did)
        citations.append(cit)
    for did in doc.get("required_disclosures") or []:
        if did not in rendered_disclosures:
            open_items.append({"item": did, "type": "disclosure-outstanding",
                               "action": "add the required regulatory disclosure (approved text + citation) before delivery"})

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
                               "action": "obtain the required approval before external delivery"})

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

    sections["fund_summary"] = {
        "factsheet_id": doc.get("factsheet_id"),
        "fund_legal_name": fund.get("legal_name"),
        "share_class": fund.get("share_class"),
        "isin": fund.get("isin"),
        "ticker": fund.get("ticker"),
        "currency": fund.get("currency"),
        "inception_date": fund.get("inception_date"),
        "benchmark_name": fund.get("benchmark_name"),
        "objective": fund.get("objective"),
        "fund_id": _mask_id(fund.get("fund_id")),
        "as_of_date": as_of,
        "intended_distribution": doc.get("intended_distribution") or "internal",
        "required_sections": required,
        "counts": {
            "included": _count("included"),
            "stale": _count("stale"),
            "unresolved": _count("unresolved"),
            "excluded_mnpi": _open_count("mnpi-exclusion"),
            "unsupported": _open_count("unsupported-claim"),
            "reconcile_break": _open_count("reconcile-break"),
            "section_incomplete": _open_count("section-incomplete"),
            "disclosures_rendered": len(sections["disclosures"]),
            "disclosures_outstanding": _open_count("disclosure-outstanding") + _open_count("disclosure-unsupported"),
            "reconciled_figures": sum(1 for r in sections["reconciliation"] if r.get("status") == "reconciled"),
            "open_items_total": len(open_items),
            "approvals_recorded": len(sections["approvals"]["recorded"]),
            "approvals_outstanding": len(sections["approvals"]["outstanding"]),
        },
    }

    return {
        "config_version": doc.get("config_version"),
        "factsheet_id": doc.get("factsheet_id"),
        "fund_legal_name": fund.get("legal_name"),
        "ticker": fund.get("ticker"),
        "as_of_date": as_of,
        "intended_distribution": doc.get("intended_distribution") or "internal",
        "template_version": doc.get("template_version", "factsheet-template@0.1.0"),
        "assembly_status": "draft-assembled",
        "human_approval_required_before_delivery": True,
        "sections": sections,
        "open_items": open_items,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "factsheet_intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
