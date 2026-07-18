#!/usr/bin/env python3
"""Deterministic output validation for company-profile-builder.

Enforces the Draft & package guardrails before the assembled profile is presented:
  1. All required template sections are present (matches assets/output-template.md).
  2. No unsupported assertions: every section entry carries an asserted status
     (included | stale | unresolved) AND a citation; no unsourced fact is asserted.
  3. No MNPI on any section entry when intended_distribution is 'external'.
  4. Required human approvals are recorded (role + date + citation); delivery approval flagged
     required; required-but-missing approvals surface as outstanding open items.
  5. No investment-advice / rating / recommendation / price-target language, and no
     distribution / delivery language.
  6. assembly_status is 'draft-assembled' (never reviewed/approved/final/distributed).
  7. The standing note is present.

Usage: python validate_output.py profile.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

# Canonical profile sections; the human-facing render in assets/output-template.md mirrors
# these (versioned contract).
REQUIRED_SECTIONS = [
    "profile_summary", "business_overview", "key_financials", "ownership", "management",
    "trading_data", "transactions", "sources",
]
CONTENT_SECTIONS = ["business_overview", "key_financials", "ownership", "management",
                    "trading_data", "transactions"]
ASSERTED_STATUSES = {"included", "stale", "unresolved"}

STANDING_NOTE = ("Draft company profile for human review only. This profile is not investment "
                 "advice or a recommendation, every stated fact is source-cited, and the profile "
                 "has not been distributed or delivered.")

# Claims a factual profile must NEVER make: advice / ratings / recommendations / targets.
ADVICE_PATTERNS = [
    r"\bwe recommend\b", r"\bour recommendation\b", r"\binvestment recommendation\b",
    r"\bbuy rating\b", r"\bsell rating\b", r"\bstrong buy\b", r"\bstrong sell\b",
    r"\brated (a )?(buy|sell|hold)\b", r"\bshould (buy|sell|invest)\b",
    r"\bprice target\b", r"\bwe rate\b", r"\boutperform\b", r"\bunderperform\b",
]
# A profile is a draft, never distributed by this skill.
DELIVERY_PATTERNS = [
    r"\bsent to\b", r"\bsubmitted to\b", r"\bdelivered to\b", r"\bdistributed to\b",
    r"\breleased to\b", r"\bemailed to\b", r"\bshared with the client\b", r"\bwe have sent\b",
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


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections")
    if not isinstance(sections, dict):
        return ["profile output has no 'sections' object"]

    # 1. required sections present
    for sec in REQUIRED_SECTIONS:
        if sec not in sections:
            errors.append(f"missing required profile section '{sec}'")

    external = doc.get("intended_distribution") == "external"

    # 2 + 3. no unsupported assertions; no MNPI in an external profile
    for sec, e in _content_entries(sections):
        fid = e.get("fact_id") or e.get("label") or "?"
        status = e.get("status")
        if status not in ASSERTED_STATUSES:
            errors.append(f"unsupported claim: {sec} entry {fid!r} has non-asserted status "
                          f"{status!r} in a profile section (only included/stale/unresolved may be asserted)")
        if not e.get("citation"):
            errors.append(f"unsupported claim: {sec} entry {fid!r} asserts status {status!r} "
                          f"without a citation")
        if external and e.get("mnpi"):
            errors.append(f"MNPI in external profile: {sec} entry {fid!r} is MNPI-flagged and "
                          f"must be excluded from an external-distribution profile")

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
    for label, patterns in (("investment-advice", ADVICE_PATTERNS),
                            ("distribution/delivery", DELIVERY_PATTERNS)):
        for pat in patterns:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"prohibited {label} language detected: {m.group(0)!r} "
                              f"(profile-builder only assembles a factual draft)")

    # 6. assembly status must be draft
    if doc.get("assembly_status") != "draft-assembled":
        errors.append(f"assembly_status must be 'draft-assembled', got {doc.get('assembly_status')!r}")

    # 7. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "profile_example.json"
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
