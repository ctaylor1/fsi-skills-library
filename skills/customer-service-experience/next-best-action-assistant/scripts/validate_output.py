#!/usr/bin/env python3
"""Deterministic output validation for next-best-action-assistant.

Enforces the Draft & package guardrails before a next-best-action package is presented to
the agent:
  1. Template fidelity  -- every required section is present.
  2. Support/citation   -- every recommendation cites at least one approved source, and no
                           recommendation is a prohibited binding decision.
  3. No unsupported/unapproved claims -- guarantee/advice/approval language is rejected.
  4. Draft-only         -- no send/submit/executed/system-of-record language.
  5. Approvals recorded -- a required-approver list is present and external delivery is not
                           marked complete without an "approved" status.
  6. Standing note      -- the draft-only, no-binding-decision note is present.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "Customer Context Snapshot",
    "Recommended Next Best Actions",
    "Consent & Eligibility Checks",
    "Excluded or Routed to Specialist",
    "Required Disclosures",
    "Approvals & Handling",
    "Sources",
]
PROHIBITED_BINDING = {
    "credit_decision", "claim_decision", "investment_advice", "suitability_determination",
}
STANDING_NOTE_KEYS = [
    "draft recommendations only",
    "binding credit, claims, or investment decision",
]
CLAIM_PATTERNS = [
    r"\bguarantee(d|s)?\b",
    r"\bpre-?approved\b",
    r"\byou (are|will be) approved\b",
    r"\bbest investment\b",
    r"\brisk-?free\b",
    r"\bassured returns?\b",
    r"\bwe recommend you (buy|sell|invest|switch|move)\b",
    r"\byou should (buy|sell|invest)\b",
    r"\bclaim (will|is|would) (be )?(paid|approved|covered)\b",
    r"\bno risk\b",
]
SEND_PATTERNS = [
    r"\b(email|message|sms|text|letter|offer|notice) (was )?sent\b",
    r"\bsent to (the )?customer\b",
    r"\bsubmitted to (the )?customer\b",
    r"\bwe have (sent|emailed|notified|submitted)\b",
    r"\baccount (was|is|has been) updated\b",
    r"\bposted to (the )?account\b",
    r"\bexecuted the\b",
    r"\bfiled (the )?(claim|application)\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    sections = doc.get("sections") or {}
    if not isinstance(sections, dict):
        errors.append("sections must be an object keyed by section title")
        sections = {}
    for sec in REQUIRED_SECTIONS:
        if sec not in sections or not str(sections.get(sec, "")).strip():
            errors.append(f"missing required section: {sec}")

    recs = doc.get("recommendations")
    if not recs:
        errors.append("package has no recommendations")
        recs = []
    for r in recs:
        aid = r.get("action_id", "?")
        if not r.get("action_id"):
            errors.append("recommendation missing action_id (unapproved action)")
        if not r.get("citations"):
            errors.append(f"unsupported action {aid}: no citation to an approved source")
        if r.get("type") in PROHIBITED_BINDING or r.get("binding_category") in PROHIBITED_BINDING:
            errors.append(f"prohibited binding decision in recommendations: {aid} ({r.get('type')})")

    # Claim + send/submit language scan across the whole package.
    scan = " ".join([
        json.dumps(recs),
        json.dumps(sections),
        str(doc.get("standing_note", "")),
        str(doc.get("narrative", "")),
    ])
    for pat in CLAIM_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited claim/advice language: {m.group(0)!r}")
    for pat in SEND_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"send/submit language (draft-only violated): {m.group(0)!r}")

    approvals = doc.get("approvals")
    if not isinstance(approvals, dict) or not approvals.get("required"):
        errors.append("approvals not recorded: required-approver list is missing")
    else:
        status = approvals.get("status")
        if status not in ("pending", "approved"):
            errors.append(f"approvals.status must be 'pending' or 'approved', got {status!r}")
        if approvals.get("external_delivery") and status != "approved":
            errors.append("external_delivery marked true without an 'approved' status")

    note = str(doc.get("standing_note", "")).lower()
    for key in STANDING_NOTE_KEYS:
        if key not in note:
            errors.append(f"standing note missing required phrase: {key!r}")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "package_example.json"
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
