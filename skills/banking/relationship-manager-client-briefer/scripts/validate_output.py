#!/usr/bin/env python3
"""Deterministic output validation for relationship-manager-client-briefer.

Enforces the R2 "Draft & package" guardrails before an RM client brief is handed to a human
for review and (optionally) delivery:
  1. Template fidelity: a packageable brief has the required sections and no unfilled
     `{{placeholder}}` tokens.
  2. No unsupported claims: a packageable record is entity-resolved, fully source-cited
     (content_integrity.all_sourced), free of blocking (unacknowledged) critical stale
     sources, with a non-empty citations list; every listed content item carries a citation.
  3. Exposure tie-out: total_committed / total_outstanding equal the sum of the lines.
  4. Required approvals recorded: reviewer_signoff_required=true and a non-empty approvals
     block are present (approval is required before delivery).
  5. No send/submit/distribute/file or CRM-write language (this skill never delivers).
  6. No credit / covenant / pricing / risk-rating decision or commitment language (a breach
     or at-risk covenant is surfaced, never adjudicated or waived here).
  7. No investment / legal / tax advice.
  8. The standing note is present.

Fails closed on any miss so a defective or overreaching brief cannot be presented as
ready-to-deliver.

Usage: python validate_output.py brief.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

STANDING_NOTE = (
    "Relationship-manager client brief for internal preparation only; this skill does not "
    "send, submit, distribute, or file the brief and does not write any CRM or system of "
    "record, does not make or communicate any credit, covenant, pricing, or risk-rating "
    "decision, gives no investment, legal, or tax advice, and every item must be verified "
    "against its cited source before use."
)
# Sections that must exist and be non-empty for a packageable brief.
REQUIRED_NONEMPTY = ("client_id", "legal_name", "relationship_manager", "exposure_summary",
                     "contacts", "citations", "approvals")
# Sections whose key must be present (may be an empty list for a given client).
REQUIRED_PRESENT = ("covenants", "profitability", "products", "service_cases", "news",
                    "pipeline", "cross_sell", "open_actions", "routing")
# Content lists whose every entry must carry a non-empty citation (no unsupported claims).
CITED_LISTS = ("covenants", "profitability", "products", "service_cases", "news", "pipeline",
               "contacts", "cross_sell", "open_actions")
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")

DELIVERY_PATTERNS = [
    r"\bbrief (has been |was )?(sent|submitted|distributed|emailed|shared|filed|delivered)\b",
    r"\bi (have |'ve )?(sent|submitted|distributed|emailed|filed|shared|delivered)\b",
    r"\b(sent|submitted|delivered) (it )?to the (client|customer|committee|borrower)\b",
    r"\bcrm (has been |was )?updated\b",
    r"\b(updated|logged .* in) the crm\b",
    r"\blogged (a|the) (call|note|opportunity|contact)\b",
]
DECISION_PATTERNS = [
    r"\bwe (hereby )?(approve|decline|deny|reject) the (facility|loan|credit|renewal|line)\b",
    r"\b(the )?(facility|loan|renewal|line|credit) (is |has been )?approved\b",
    r"\bcovenant (breach )?(is |has been )?(waived|cured|granted)\b",
    r"\bwe waive the covenant\b",
    r"\bthe waiver (is|has been) (granted|approved)\b",
    r"\bwe commit to (a )?(rate|price|pricing|spread|renewal)\b",
    r"\bnew risk rating is\b",
    r"\bwe (re-?rate|downgrade|upgrade) the (client|customer|borrower)\b",
    r"\bguarantee(s|d)?\b[^.]{0,40}\b(approval|renewal|pricing|rate|outcome)\b",
]
ADVICE_PATTERNS = [
    r"\b(investment|financial|tax|legal) advice\b",
    r"\byou should (buy|sell|invest|refinance|hedge|restructure|borrow)\b",
    r"\bwe advise (you|the client|the customer) to\b",
    r"\bas your (advisor|attorney|lawyer|financial advisor)\b",
]


def _round2(x):
    try:
        return round(float(x or 0), 2)
    except Exception:
        return None


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    briefs = doc.get("briefs") or []
    if not briefs:
        return ["brief output has no records"]

    for b in briefs:
        cid = b.get("client_id", "?")
        if not b.get("packageable"):
            continue

        if b.get("status") != "draft-brief":
            errors.append(f"{cid}: packageable but status is {b.get('status')!r} (only draft-brief is packageable)")
        if not b.get("entity_resolved"):
            errors.append(f"{cid}: packageable but entity is not resolved")
        ci = b.get("content_integrity") or {}
        if not ci.get("all_sourced"):
            errors.append(f"{cid}: packageable but content not fully sourced (unsupported: {ci.get('unsupported')})")
        sc = b.get("stale_check") or {}
        if sc.get("stale_unacknowledged"):
            errors.append(f"{cid}: packageable but has blocking stale sources {sc.get('stale_unacknowledged')}")
        if not b.get("citations"):
            errors.append(f"{cid}: packageable but citations list is empty")

        brief = b.get("brief") or {}
        if not brief:
            errors.append(f"{cid}: packageable but no brief object")
            continue

        for sec in REQUIRED_NONEMPTY:
            if sec not in brief or brief.get(sec) in (None, "", [], {}):
                errors.append(f"{cid}: brief missing required section {sec!r} (template fidelity)")
        for sec in REQUIRED_PRESENT:
            if sec not in brief:
                errors.append(f"{cid}: brief missing required section {sec!r} (template fidelity)")
        if not brief.get("reviewer_signoff_required"):
            errors.append(f"{cid}: brief missing reviewer_signoff_required=true (required approvals not recorded)")
        appr = brief.get("approvals") or {}
        if not appr.get("required"):
            errors.append(f"{cid}: brief missing recorded approvals (approvals.required) before delivery")
        if PLACEHOLDER_RE.search(json.dumps(brief)):
            errors.append(f"{cid}: brief contains unfilled '{{{{placeholder}}}}' tokens (template fidelity)")

        # no unsupported claims: every listed content item must carry a citation
        for lst in CITED_LISTS:
            for k, item in enumerate(brief.get(lst) or []):
                if not (isinstance(item, dict) and item.get("citation")):
                    errors.append(f"{cid}: {lst}[{k}] has no citation (unsupported claim)")

        # exposure tie-out
        es = brief.get("exposure_summary") or {}
        lines = es.get("lines") or []
        exp_committed = _round2(sum(_round2(l.get("committed")) or 0 for l in lines))
        exp_outstanding = _round2(sum(_round2(l.get("outstanding")) or 0 for l in lines))
        if _round2(es.get("total_committed")) != exp_committed:
            errors.append(f"{cid}: exposure tie-out mismatch on total_committed "
                          f"({es.get('total_committed')} != {exp_committed})")
        if _round2(es.get("total_outstanding")) != exp_outstanding:
            errors.append(f"{cid}: exposure tie-out mismatch on total_outstanding "
                          f"({es.get('total_outstanding')} != {exp_outstanding})")
        for k, l in enumerate(lines):
            if not l.get("citation"):
                errors.append(f"{cid}: exposure_summary.lines[{k}] has no citation (unsupported claim)")

    scan = json.dumps(briefs) + " " + str(doc.get("narrative", ""))
    for pat in DELIVERY_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited delivery/submission language detected: {m.group(0)!r} "
                          "(this skill never sends/submits/files or writes the CRM)")
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited credit/covenant/pricing decision language detected: {m.group(0)!r} "
                          "(the brief surfaces status, it never decides, waives, or commits)")
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited advice language detected: {m.group(0)!r}")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "brief_example.json"
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
