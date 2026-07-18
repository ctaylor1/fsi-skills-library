#!/usr/bin/env python3
"""Deterministic output validation for enterprise-meeting-preparer.

Enforces the R1 "Draft & package" guardrails before a meeting brief is handed to a human for
review and (optionally) distribution:
  1. Template fidelity: a packageable brief has the required sections and no unfilled
     `{{placeholder}}` tokens.
  2. A packageable record is attendee-resolved, fully source-cited (no unsupported content),
     and free of blocking (unacknowledged) stale sources, with a non-empty citations list and
     reviewer_signoff_required.
  3. No scheduling/sending/distributing language (this skill never sends or schedules).
  4. No decision/commitment or outcome-guarantee language (the brief never decides).
  5. No investment/legal/tax advice.
  6. The standing disclaimer is present.

Fails closed on any miss so a defective or overreaching brief cannot be presented as
ready-to-distribute.

Usage: python validate_output.py brief.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

STANDING_NOTE = (
    "Internal meeting brief for preparation only; this skill does not schedule, send, "
    "distribute, or update any meeting, invite, calendar, or system of record, does not make "
    "or authorize any decision or commitment, and every item must be verified against its "
    "cited source before the meeting."
)
REQUIRED_BRIEF_SECTIONS = ("meeting_id", "purpose", "attendees", "agenda", "citations",
                           "reviewer_signoff_required")
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")

SCHEDULING_PATTERNS = [
    r"\binvite (has been )?(sent|created)\b",
    r"\bcalendar (has been )?(updated|created)\b",
    r"\bmeeting (has been |was )?(scheduled|booked|sent)\b",
    r"\bbrief (has been )?(distributed|sent|emailed|shared)\b",
    r"\bi (have |'ve )?(scheduled|sent|booked|invited|distributed|emailed)\b",
    r"\bemail(ed)? (the )?(brief|invite|attendees)\b",
]
DECISION_PATTERNS = [
    r"\bthis brief (approves|authorizes|commits)\b",
    r"\bhereby (approve|authorize|commit)\b",
    r"\byou are authorized to proceed\b",
    r"\bwe commit to\b",
    r"\bthe decision is final\b",
    r"\bguarantee(s|d)?\b[^.]{0,40}\b(approval|outcome|success|sign-?off)\b",
]
ADVICE_PATTERNS = [
    r"\b(investment|legal|tax) advice\b",
    r"\byou should (buy|sell|invest|sign|settle)\b",
    r"\bas your (attorney|lawyer|financial advisor|advisor)\b",
    r"\bwe advise you to\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    briefs = doc.get("briefs") or []
    if not briefs:
        return ["brief output has no records"]

    for b in briefs:
        mid = b.get("meeting_id", "?")
        packageable = bool(b.get("packageable"))
        if not packageable:
            continue

        if b.get("status") != "draft-brief":
            errors.append(f"{mid}: packageable but status is {b.get('status')!r} (only draft-brief is packageable)")
        if not b.get("attendees_resolved"):
            errors.append(f"{mid}: packageable but attendees are not resolved")
        ci = b.get("content_integrity") or {}
        if not ci.get("all_sourced"):
            errors.append(f"{mid}: packageable but content not fully sourced (unsupported: {ci.get('unsupported')})")
        sc = b.get("stale_check") or {}
        if sc.get("stale_unacknowledged"):
            errors.append(f"{mid}: packageable but has blocking stale sources {sc.get('stale_unacknowledged')}")
        if not b.get("citations"):
            errors.append(f"{mid}: packageable but citations list is empty")

        brief = b.get("brief") or {}
        if not brief:
            errors.append(f"{mid}: packageable but no brief object")
        else:
            for sec in REQUIRED_BRIEF_SECTIONS:
                if sec not in brief or brief.get(sec) in (None, "", [], {}):
                    errors.append(f"{mid}: brief missing required section {sec!r} (template fidelity)")
            if not brief.get("reviewer_signoff_required"):
                errors.append(f"{mid}: brief missing reviewer_signoff_required=true")
            if PLACEHOLDER_RE.search(json.dumps(brief)):
                errors.append(f"{mid}: brief contains unfilled '{{{{placeholder}}}}' tokens (template fidelity)")

    scan = json.dumps(briefs) + " " + str(doc.get("narrative", ""))
    for pat in SCHEDULING_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited scheduling/delivery language detected: {m.group(0)!r} "
                          "(this skill never schedules/sends/distributes)")
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited decision/commitment language detected: {m.group(0)!r} "
                          "(the brief reports decisions, it never makes them)")
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
