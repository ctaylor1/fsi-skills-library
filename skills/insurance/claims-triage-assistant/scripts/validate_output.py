#!/usr/bin/env python3
"""Deterministic output validation for claims-triage-assistant.

Enforces the draft-and-package + R3 guardrails before a triage package is presented for
human review. It confirms the deliverable is a compliant DRAFT recommendation set, not a
regulated decision:
  1. Allowed dispositions only (no decision / closure / assignment / filing states).
  2. severity_band and urgency_band are consistent with their documented scores.
  3. Draft records carry every required template section, the DRAFT marker, and citations.
  4. Required human approvals are RECORDED (triage lead review + claims supervisor approval).
  5. No unsupported / unapproved claims: coverage determinations, claim approve/deny/pay/
     close, reserve setting, or fraud/liability conclusions.
  6. No send / submit / assign / file / pay / close (executed-action) language — draft-only.
  7. The standing note is present.

Usage: python validate_output.py triage.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {"draft-ready", "refer-specialist", "needs-data", "needs-review"}
REQUIRED_SECTIONS = [
    "Claim summary", "Severity and complexity", "Urgency and service level",
    "Coverage questions to resolve", "Recommended routing", "Human adjudication required",
]
REQUIRED_APPROVALS = ("triage_lead_review", "claims_supervisor_approval")
STANDING_NOTE = "Draft claims triage only"
DRAFT_MARKER = "DRAFT"

# Regulated conclusions this triage must never assert (R3: recommendations only).
UNSUPPORTED_PATTERNS = [
    r"\bcoverage is (confirmed|denied|declined|granted)\b",
    r"\bclaim is (covered|not covered|denied|approved|payable)\b",
    r"\bwe (deny|approve|confirm|decline|grant) coverage\b",
    r"\bnot covered under\b", r"\bcoverage (applies|does not apply)\b",
    r"\bclaim (approved|denied|closed|settled)\b",
    r"\b(approve|deny|pay|close|settle) the claim\b",
    r"\bset the reserve\b", r"\breserve set to\b", r"\breserve of \$",
    r"\bconfirmed fraud\b", r"\bthis is fraud\b", r"\bfraud (is )?(established|confirmed|proven)\b",
    r"\b(we are|insured is|claimant is) liable\b", r"\bliability is (established|admitted)\b",
    r"\bwe guarantee\b", r"\bguaranteed\b",
]
# Draft-only: none of these executed / delivery / closure states may appear.
SENT_PATTERNS = [
    r"\bhas been (sent|submitted|filed|assigned|paid|settled|closed)\b",
    r"\bwe have (sent|submitted|filed|assigned|paid|closed)\b",
    r"\bassigned to (the )?adjuster\b", r"\bpayment (has been )?issued\b",
    r"\bpayment made\b", r"\bclaim closed\b", r"\bcase closed\b",
    r"\bfiled (with|the)\b",
]


def _expected_severity(score):
    return "S1 (Complex)" if score >= 7 else "S2 (Moderate)" if score >= 3 else "S3 (Standard)"


def _expected_urgency(score):
    return "U1 (Immediate)" if score >= 5 else "U2 (Prompt)" if score >= 2 else "U3 (Routine)"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    records = doc.get("triage") or []
    if not records:
        return ["triage output has no records"]

    for r in records:
        cid = r.get("claim_id", "?")
        disp = r.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{cid}: disallowed disposition {disp!r} (decision/closure/assignment not permitted in triage)")

        ss = r.get("severity_score")
        if ss is not None and r.get("severity_band") != _expected_severity(ss):
            errors.append(f"{cid}: severity_band {r.get('severity_band')!r} != expected {_expected_severity(ss)!r} for score {ss}")
        us = r.get("urgency_score")
        if us is not None and r.get("urgency_band") != _expected_urgency(us):
            errors.append(f"{cid}: urgency_band {r.get('urgency_band')!r} != expected {_expected_urgency(us)!r} for score {us}")

        if disp in ("draft-ready", "refer-specialist"):
            ds = r.get("draft_summary") or {}
            body = ds.get("body", "")
            if not body:
                errors.append(f"{cid}: {disp} but no draft_summary.body")
            else:
                for s in REQUIRED_SECTIONS:
                    if s not in body:
                        errors.append(f"{cid}: draft summary missing required section {s!r}")
                if DRAFT_MARKER not in body:
                    errors.append(f"{cid}: draft summary missing DRAFT marker")
            ap = r.get("approvals") or {}
            for key in REQUIRED_APPROVALS:
                slot = ap.get(key)
                if not isinstance(slot, dict) or not slot.get("status"):
                    errors.append(f"{cid}: required approval {key!r} not recorded")
            if not r.get("citations"):
                errors.append(f"{cid}: draft with no citations")

    scan = json.dumps(records) + " " + str(doc.get("narrative", ""))
    for pat in UNSUPPORTED_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"unsupported/unapproved claim detected: {m.group(0)!r} (triage recommends, never decides)")
    for pat in SENT_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"draft-only violated (executed/send/assign/close language): {m.group(0)!r}")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "triage_example.json"
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
