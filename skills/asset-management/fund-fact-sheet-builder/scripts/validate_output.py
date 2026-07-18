#!/usr/bin/env python3
"""Deterministic output validation for fund-fact-sheet-builder.

Enforces the Draft & package guardrails before the assembled fact sheet is presented:
  1. All required template sections are present (matches assets/output-template.md).
  2. No unsupported assertions: every content-section entry carries an asserted status
     (included | stale | unresolved) AND a citation; no unsourced figure is asserted.
  3. Source-to-output reconciliation: any asserted numeric figure that carries a source value
     must tie out within tolerance (no unreconciled figure may be presented).
  4. No MNPI/restricted content on any section entry when intended_distribution is 'external'.
  5. Every rendered regulatory disclosure carries approved text AND a citation (no unsupported
     disclosure); required-but-missing disclosures are open items, not asserted.
  6. Required human approvals are recorded (role + date + citation); delivery approval flagged
     required; required-but-missing approvals surface as outstanding open items.
  7. No performance-promise / guarantee, no investment-advice / solicitation, and no
     distribution / delivery language.
  8. assembly_status is 'draft-assembled' (never reviewed/approved/final/distributed).
  9. The standing note is present.

Usage: python validate_output.py factsheet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

# Canonical fact-sheet sections; the human-facing render in assets/output-template.md mirrors
# these (versioned contract).
REQUIRED_SECTIONS = [
    "fund_summary", "performance", "holdings", "risk", "fees", "esg",
    "reconciliation", "disclosures", "sources",
]
CONTENT_SECTIONS = ["performance", "holdings", "risk", "fees", "esg"]
ASSERTED_STATUSES = {"included", "stale", "unresolved"}
DEFAULT_TOLERANCE = 0.05

STANDING_NOTE = ("Draft fund fact sheet for human review only. Every figure is source-cited "
                 "and reconciled to its system of record, past performance is not indicative "
                 "of future results, and this fact sheet has not been reviewed, approved, or "
                 "distributed.")

# A fact sheet is a factual, regulated marketing document: it must NEVER promise or guarantee
# returns, give advice / a recommendation, or claim to be delivered by this skill.
PROMISSORY_PATTERNS = [
    r"\bguarantee(s|d)?\b", r"\brisk[- ]?free\b", r"\bcan(?:no|')t lose\b",
    r"\bno risk of loss\b", r"\bwill (out)?perform\b", r"\bwill beat the (market|benchmark)\b",
    r"\bassured returns?\b", r"\bpromis(e|es|ed) (a )?return\b",
    r"\bprojected to (return|deliver)\b", r"\block(ed)?[- ]in returns?\b",
]
ADVICE_PATTERNS = [
    r"\bwe recommend\b", r"\byou should (buy|invest)\b", r"\bshould allocate\b",
    r"\brecommended for (your|investors)\b", r"\bthis fund is right for you\b",
    r"\bsuitable for you\b", r"\bbuy this fund\b",
]
DELIVERY_PATTERNS = [
    r"\bsent to\b", r"\bsubmitted to\b", r"\bdelivered to\b", r"\bdistributed to\b",
    r"\breleased to\b", r"\bemailed to\b", r"\bpublished to\b", r"\bposted to the website\b",
    r"\bshared with (the )?client\b", r"\bwe have sent\b",
]


def _content_entries(sections):
    for key in CONTENT_SECTIONS:
        val = sections.get(key)
        if val is None:
            continue
        items = val if isinstance(val, list) else [val]
        for e in items:
            if isinstance(e, dict):
                yield key, e


def _scan_text(doc: dict, sections: dict) -> str:
    """Build the prohibited-language scan surface: narrative, the fund objective, and the
    label/value of every content entry. Approved disclosures, the standing note, the source
    index, and the reconciliation ledger are controlled content and are NOT scanned."""
    parts = [str(doc.get("narrative", ""))]
    summary = sections.get("fund_summary")
    if isinstance(summary, dict):
        parts.append(str(summary.get("objective", "")))
    for _sec, e in _content_entries(sections):
        parts.append(str(e.get("label", "")))
        parts.append(str(e.get("value", "")))
    return " \n ".join(parts)


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections")
    if not isinstance(sections, dict):
        return ["fact-sheet output has no 'sections' object"]

    # 1. required sections present
    for sec in REQUIRED_SECTIONS:
        if sec not in sections:
            errors.append(f"missing required fact-sheet section '{sec}'")

    external = doc.get("intended_distribution") == "external"

    # 2 + 3 + 4. no unsupported assertions; every asserted figure reconciles; no MNPI external
    for sec, e in _content_entries(sections):
        fid = e.get("fact_id") or e.get("label") or "?"
        status = e.get("status")
        if status not in ASSERTED_STATUSES:
            errors.append(f"unsupported claim: {sec} entry {fid!r} has non-asserted status "
                          f"{status!r} in a fact-sheet section (only included/stale/unresolved may be asserted)")
        if not e.get("citation"):
            errors.append(f"unsupported claim: {sec} entry {fid!r} asserts status {status!r} "
                          f"without a citation")
        v, sv = e.get("value_numeric"), e.get("source_value_numeric")
        if v is not None and sv is not None:
            tol = e.get("reconcile_tolerance")
            tol = DEFAULT_TOLERANCE if tol is None else float(tol)
            if round(abs(float(v) - float(sv)), 10) > tol:
                errors.append(f"unreconciled figure: {sec} entry {fid!r} value {v} does not tie "
                              f"to source {sv} (tolerance {tol}) and must not be asserted")
        if external and e.get("mnpi"):
            errors.append(f"MNPI in external factsheet: {sec} entry {fid!r} is MNPI/restricted-flagged "
                          f"and must be excluded from an external-distribution fact sheet")

    # 5. rendered disclosures must carry approved text + a citation
    disclosures = sections.get("disclosures")
    if not isinstance(disclosures, list):
        errors.append("disclosures section missing or not a list")
    else:
        for d in disclosures:
            did = d.get("disclosure_id", "?")
            if not str(d.get("text", "")).strip():
                errors.append(f"unsupported disclosure: {did!r} rendered with empty text")
            if not d.get("citation"):
                errors.append(f"unsupported disclosure: {did!r} rendered without a citation")

    # 6. approvals recorded well-formed; delivery approval flagged
    approvals = sections.get("approvals")
    if not isinstance(approvals, dict) or "recorded" not in approvals:
        errors.append("approvals section missing or lacks a 'recorded' list")
    else:
        for rec in approvals.get("recorded") or []:
            for field in ("type", "approver_role", "date", "citation"):
                if not rec.get(field):
                    errors.append(f"recorded approval {rec.get('type','?')!r} missing '{field}'")
    if doc.get("human_approval_required_before_delivery") is not True:
        errors.append("human_approval_required_before_delivery must be true (external-delivery posture)")

    # 7. forbidden language (scan content + narrative only; approved disclosures excluded)
    scan = _scan_text(doc, sections)
    for label, patterns in (("performance-promise/guarantee", PROMISSORY_PATTERNS),
                            ("investment-advice/solicitation", ADVICE_PATTERNS),
                            ("distribution/delivery", DELIVERY_PATTERNS)):
        for pat in patterns:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"prohibited {label} language detected: {m.group(0)!r} "
                              f"(fact-sheet-builder assembles a factual, non-promissory draft)")

    # 8. assembly status must be draft
    if doc.get("assembly_status") != "draft-assembled":
        errors.append(f"assembly_status must be 'draft-assembled', got {doc.get('assembly_status')!r}")

    # 9. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "factsheet_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
