#!/usr/bin/env python3
"""Deterministic output validation for credit-application-packager.

Enforces the Draft & package guardrails before the assembled package is presented:
  1. All required template sections are present (matches assets/output-template.md).
  2. No unsupported/unapproved claims: every asserted (included/stale/unresolved) component
     entry carries a citation.
  3. Required human approvals are recorded (role + date + citation) and delivery approval is
     flagged as required; missing required approvals appear as outstanding open items.
  4. No credit-decision, completeness-certification, or send/submit/deliver language.
  5. assembly_status is 'draft-assembled' (never certified/complete).
  6. The standing note is present.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

# Canonical package sections; the human-facing render in assets/output-template.md mirrors
# these (versioned contract). All must appear in the manifest's `sections`.
REQUIRED_SECTIONS = [
    "package_summary", "borrower_profile", "application", "financial_information",
    "collateral", "kyc_onboarding", "approvals", "open_items", "source_index",
]
ASSERTED_STATUSES = {"included", "stale", "unresolved"}
STANDING_NOTE = ("Draft credit package for human review only. This package is not a "
                 "completeness certification, not a credit decision or adverse-action notice, "
                 "and has not been submitted or delivered.")

# Claims a packager must NEVER make: credit decisions, completeness certification, delivery.
DECISION_PATTERNS = [
    r"\bcredit approved\b", r"\bapproved for (the )?(loan|credit|facility)\b",
    r"\bloan approved\b", r"\bdenied\b", r"\bdeclined\b", r"\badverse action\b",
    r"\bborrower qualifies\b", r"\bcleared to (close|fund)\b", r"\bready to fund\b",
]
CERTIFICATION_PATTERNS = [
    r"\b(package|file) is complete\b", r"\bcertified complete\b", r"\bcompleteness certified\b",
    r"\bunderwriting complete\b", r"\bmeets all (requirements|conditions)\b",
    r"\bfully documented\b", r"\bno (outstanding )?exceptions\b", r"\bno open items\b",
]
DELIVERY_PATTERNS = [
    r"\bsubmitted to\b", r"\bsent to underwriting\b", r"\bfiled with\b", r"\btransmitted to\b",
    r"\bdelivered to\b", r"\bwe have submitted\b",
]


def _entries_with_status(sections):
    """Yield every dict in `sections` that carries a 'status' field."""
    for key, val in sections.items():
        items = val if isinstance(val, list) else [val]
        for e in items:
            if isinstance(e, dict) and "status" in e:
                yield key, e


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections")
    if not isinstance(sections, dict):
        return ["package output has no 'sections' object"]

    # 1. required sections present
    for sec in REQUIRED_SECTIONS:
        if sec not in sections:
            errors.append(f"missing required package section '{sec}'")

    # 2. no unsupported claims: asserted component entries must be cited
    for sec, e in _entries_with_status(sections):
        if e.get("status") in ASSERTED_STATUSES and not e.get("citation"):
            errors.append(f"unsupported claim: {sec} entry {e.get('doc_id') or e.get('component')!r} "
                          f"asserts status {e.get('status')!r} without a citation")

    # 3. approvals recorded well-formed; delivery approval flagged
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

    # 4. forbidden language
    scan = json.dumps(doc)
    for label, patterns in (("credit-decision", DECISION_PATTERNS),
                            ("completeness-certification", CERTIFICATION_PATTERNS),
                            ("delivery/submission", DELIVERY_PATTERNS)):
        for pat in patterns:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"prohibited {label} language detected: {m.group(0)!r} "
                              f"(packager only assembles a draft)")

    # 5. assembly status must be draft
    if doc.get("assembly_status") != "draft-assembled":
        errors.append(f"assembly_status must be 'draft-assembled', got {doc.get('assembly_status')!r}")

    # 6. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
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
