#!/usr/bin/env python3
"""Deterministic output validation for advisor-follow-up-assistant.

Enforces the draft-and-package guardrails before a follow-up package is presented:
  1. All 7 required template sections are present and titled (template fidelity).
  2. Every material section carries a citation (no unsupported / unapproved assertions).
  3. Disclosure completeness: every recommendation flagged `requires_disclosure` is covered by a
     disclosure entry; every recommendation flagged `requires_suitability_review` has a recorded
     route to suitability-reg-bi-reviewer (the draft never makes the determination itself).
  4. Every action item carries an owner, a due date, and a citation (completeness).
  5. Advisor and Supervisory Principal approvals are recorded and still `pending`.
  6. draft_status == "draft", delivery_status == "not-delivered", crm_write_status == "not-written".
  7. No prohibited language: execution-as-done, sent/delivered-as-done, CRM-write-as-done,
     guarantee/performance, or suitability/advice-as-done (regex families, case-insensitive).
  8. The standing note is present.
Any failure exits non-zero so the draft fails closed.

Usage: python validate_output.py draft.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    ("meeting-summary", "Meeting Summary"),
    ("action-items", "Action Items"),
    ("client-communication", "Client Communication (Draft)"),
    ("disclosures", "Disclosures"),
    ("crm-update", "CRM Update (Proposed)"),
    ("next-meeting", "Next-Meeting Reminder"),
    ("approvals-and-delivery", "Approvals and Delivery"),
]
MATERIAL_SECTIONS = {
    "meeting-summary", "action-items", "client-communication",
    "disclosures", "crm-update", "next-meeting",
}
APPROVAL_ROLES = ("Advisor", "Supervisory Principal")
SUITABILITY_SKILL = "suitability-reg-bi-reviewer"
STANDING_NOTE = ("Draft follow-up package for human review only; nothing has been sent to the "
                 "client, no CRM or system of record has been updated, no trade has been placed, "
                 "and no suitability determination has been made.")

PROHIBITED = {
    "execution-as-done": [
        r"\bexecute the trade\b", r"\btrades? executed\b", r"\border placed\b",
        r"\bplace the order\b", r"\bfunds transferred\b", r"\bhave rebalanced\b",
        r"\brebalance executed\b", r"\btrade has been placed\b",
    ],
    "sent-delivered-as-done": [
        r"\bemail sent\b", r"\bsent to the client\b", r"\bhave notified the client\b",
        r"\bdelivered to the client\b", r"\bmessage has been sent\b", r"\bsubmitted to compliance\b",
    ],
    "crm-write-as-done": [
        r"\bupdated the crm\b", r"\bcrm updated\b", r"\brecords? updated\b",
        r"\bwritten to the system of record\b", r"\bsaved to (salesforce|the crm)\b",
        r"\bposted to the account\b",
    ],
    "guarantee-performance": [
        r"\bguaranteed returns?\b", r"\bguarantees? to\b", r"\brisk-free\b",
        r"\bwill outperform\b", r"\bno downside\b",
    ],
    "suitability-advice-as-done": [
        r"\bsuitability approved\b", r"\bdeemed suitable\b", r"\bbest[- ]interest determination made\b",
        r"\bwe hereby approve\b", r"\bapproved as suitable\b", r"\bthis is suitable for you\b",
    ],
}


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    # 1 + 2: required sections present + material sections cited
    sections = {s.get("key"): s for s in (doc.get("sections") or [])}
    for key, title in REQUIRED_SECTIONS:
        s = sections.get(key)
        if not s:
            errors.append(f"missing required section '{key}' ({title})")
            continue
        if s.get("title") != title:
            errors.append(f"section '{key}': title {s.get('title')!r} != required {title!r}")
        if not s.get("present", False):
            errors.append(f"section '{key}': not present")
        if key in MATERIAL_SECTIONS and not s.get("citations"):
            errors.append(f"section '{key}': material assertion has no citation (unsupported)")

    # 3: disclosure completeness + suitability routing (recomputed, not trusted)
    recommendations = doc.get("recommendations") or []
    covered = {d.get("covers_recommendation") for d in (doc.get("disclosures") or [])}
    routed = {(r.get("to"), r.get("ref")) for r in (doc.get("routes") or [])}
    for rec in recommendations:
        rid = rec.get("id")
        if rec.get("requires_disclosure") and rid not in covered:
            errors.append(f"recommendation {rid!r}: requires a disclosure but none covers it "
                          f"(incomplete/unsupported)")
        if rec.get("requires_suitability_review") and (SUITABILITY_SKILL, rid) not in routed:
            errors.append(f"recommendation {rid!r}: requires suitability review but no route to "
                          f"{SUITABILITY_SKILL} recorded (this skill never makes the determination)")

    # 4: action-item completeness
    for ai in doc.get("action_items") or []:
        aid = ai.get("id", "?")
        for f in ("owner", "due_date", "citation"):
            if not ai.get(f):
                errors.append(f"action item {aid!r}: missing {f} (incomplete)")

    # 5: approvals recorded and pending
    appr = {a.get("role"): a for a in (doc.get("approvals") or [])}
    for role in APPROVAL_ROLES:
        a = appr.get(role)
        if not a:
            errors.append(f"approvals: missing '{role}' entry")
        elif str(a.get("status", "")).lower() != "pending":
            errors.append(f"approvals: '{role}' status {a.get('status')!r} must be 'pending' (draft-only)")

    # 6: draft-only status flags
    if doc.get("draft_status") != "draft":
        errors.append(f"draft_status {doc.get('draft_status')!r} must be 'draft' (never final/approved)")
    if doc.get("delivery_status") != "not-delivered":
        errors.append(f"delivery_status {doc.get('delivery_status')!r} must be 'not-delivered' (never sent)")
    if doc.get("crm_write_status") != "not-written":
        errors.append(f"crm_write_status {doc.get('crm_write_status')!r} must be 'not-written' "
                      f"(CRM updates are proposed, never written)")

    # 7: prohibited language (scan everything EXCEPT the standing_note field)
    scan_doc = {k: v for k, v in doc.items() if k != "standing_note"}
    scan = json.dumps(scan_doc) + " " + str(doc.get("narrative", ""))
    for family, pats in PROHIBITED.items():
        for pat in pats:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"prohibited {family} language detected: {m.group(0)!r} (draft never "
                              f"sends/writes/trades/guarantees/approves)")

    # 8: standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "followup_draft_example.json"
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
