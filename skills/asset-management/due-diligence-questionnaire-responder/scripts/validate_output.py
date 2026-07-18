#!/usr/bin/env python3
"""Deterministic output validation for due-diligence-questionnaire-responder.

Enforces the Draft & package guardrails before the drafted DDQ/RFP response is presented:
  1. All required template sections are present (mirrors assets/output-template.md).
  2. No unsupported/unapproved claims: every asserted answer (status drafted|stale) carries a
     citation AND is drawn from an approved source; no answer text appears for a status that
     was routed to an owner (fabrication guard).
  3. Required disclosures: when any answer cites performance/data, the standard performance
     disclosure is present.
  4. Required human approvals are recorded (type + role + date + citation); missing required
     approvals appear as outstanding open items; delivery approval is flagged as required.
  5. No send/submit/deliver language, no performance/return guarantees, no completeness or
     "final/approved-for-submission" overclaims.
  6. draft_status is 'draft-assembled' (never final/submitted/approved).
  7. The standing note is present.

Usage: python validate_output.py response.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

# Canonical response sections; the human render in assets/output-template.md mirrors these.
REQUIRED_SECTIONS = [
    "response_summary", "respondent_profile", "responses", "data_appendix",
    "disclosures", "approvals", "open_items", "source_index",
]
ALLOWED_STATUS = {"drafted", "stale", "unapproved-source", "data-gap", "unsupported"}
ASSERTED = {"drafted", "stale"}          # carry answer text -> must be cited + approved
ROUTED = {"unapproved-source", "data-gap", "unsupported"}  # routed to owner -> no answer text

STANDARD_PERF_DISCLOSURE = ("Past performance is not indicative of future results. Figures are "
                            "as of the stated date, may be gross of fees, and are subject to "
                            "change and to verification by the content owner.")
STANDING_NOTE = ("Draft DDQ/RFP response for human review only. Every answer is drawn from "
                 "approved content and cited; no answer is fabricated. Content owners and "
                 "compliance must review and approve before any answer is sent or submitted to "
                 "a client, investor, or consultant.")

# Assertions a DDQ responder must NEVER make: completed delivery, guarantees, completeness.
DELIVERY_PATTERNS = [
    r"\bwe have (sent|submitted|delivered|filed|transmitted)\b",
    r"\bhas been (sent|submitted|delivered|filed|transmitted) to\b",
    r"\bsent to the (client|investor|consultant)\b",
    r"\bsubmitted to the (client|investor|consultant)\b",
    r"\bresponse (is|has been) submitted\b",
    r"\bready to (send|submit)\b",
    r"\bapproved for (release|submission)\b",
    r"\bfinal response\b",
]
GUARANTEE_PATTERNS = [
    r"\bguarantee[ds]? (returns?|profit|income|performance)\b",
    r"\bwill (out\s?perform|beat the (market|benchmark))\b",
    r"\bassured returns?\b", r"\brisk-?free\b", r"\bno risk of loss\b", r"\bcannot lose\b",
    r"\bguaranteed to (outperform|beat)\b",
]
OVERCLAIM_PATTERNS = [
    r"\ball (questions|answers) (are )?(complete|answered)\b",
    r"\bresponse is complete\b", r"\bno open items\b", r"\bfully compliant\b",
    r"\bcertified complete\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections")
    if not isinstance(sections, dict):
        return ["response output has no 'sections' object"]

    # 1. required sections present
    for sec in REQUIRED_SECTIONS:
        if sec not in sections:
            errors.append(f"missing required response section '{sec}'")

    # 2. per-response guardrails
    responses = sections.get("responses")
    if not isinstance(responses, list) or not responses:
        errors.append("responses section is missing or empty")
        responses = []
    data_cited_any = False
    for r in responses:
        qid = r.get("question_id", "?")
        status = r.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"disallowed response status {status!r} for {qid}")
        if r.get("data_cited"):
            data_cited_any = True
        if status in ASSERTED:
            if not r.get("citations"):
                errors.append(f"unsupported claim: response {qid} asserts status {status!r} without a citation")
            if r.get("source_approved") is not True:
                errors.append(f"unapproved claim: response {qid} status {status!r} not drawn from an approved source")
        if status in ROUTED and (r.get("text") not in (None, "")):
            errors.append(f"fabricated answer: response {qid} status {status!r} must not carry drafted answer text "
                          f"(route to the content owner instead)")

    # 3. required disclosures when data is cited
    disclosures = sections.get("disclosures")
    if data_cited_any:
        texts = " ".join(str(d.get("text", "")) for d in (disclosures or []))
        if STANDARD_PERF_DISCLOSURE not in texts:
            errors.append("required performance disclosure missing while performance/data is cited")

    # 4. approvals recorded well-formed; delivery approval flagged
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

    # 5. forbidden language
    scan = json.dumps(doc)
    for label, patterns in (("delivery/submission", DELIVERY_PATTERNS),
                            ("unsupported-performance-claim", GUARANTEE_PATTERNS),
                            ("completeness/overclaim", OVERCLAIM_PATTERNS)):
        for pat in patterns:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"prohibited {label} language detected: {m.group(0)!r} "
                              f"(the responder only drafts from approved content)")

    # 6. draft status
    if doc.get("draft_status") != "draft-assembled":
        errors.append(f"draft_status must be 'draft-assembled', got {doc.get('draft_status')!r}")

    # 7. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ddq_response_example.json"
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
