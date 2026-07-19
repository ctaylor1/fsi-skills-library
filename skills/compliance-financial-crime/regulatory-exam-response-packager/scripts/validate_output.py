#!/usr/bin/env python3
"""Deterministic output validation for regulatory-exam-response-packager.

Enforces the draft-and-package guardrails before the response package is handed to a human for
review and submission:
  1. All required template sections are present (template fidelity).
  2. Only allowed coverage / response_status values are used (no submission/closure states).
  3. No UNSUPPORTED assertion is carried inside an item marked ready.
  4. No UNAPPROVED item is marked ready (all required approver roles recorded as approved).
  5. A ready item is cited (no ready narrative without provenance).
  6. Package readiness is 'draft-not-submitted' (never submitted/filed/closed).
  7. No submission/closure/regulated-decision language anywhere in the items.
  8. The standing note is present.

Usage: python validate_output.py response_package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "Examination Identification", "Scope and Period", "Request-Response Index",
    "Response Narratives", "Evidence Register", "Issue and Remediation Status",
    "Approvals and Sign-offs", "Source Map and Provenance", "Outstanding Items and Gaps",
    "Draft Status and Limitations",
]
ALLOWED_COVERAGE = {"complete", "partial", "needs-evidence", "gap"}
ALLOWED_STATUS = {"draft-ready-for-review", "needs-approval", "unsupported-assertion",
                  "needs-evidence", "incomplete"}
REQUIRED_READINESS = "draft-not-submitted"
STANDING_NOTE = ("Draft response package only; not submitted to any regulator, no exam item "
                 "closed, and no system of record updated.")

SUBMISSION_PATTERNS = [
    r"\b(?:response|package|reply|submission)\s+(?:has been|have been|was|is|are)\s+"
    r"(?:submitted|sent|transmitted|filed)\b",
    r"\bsubmit(?:ted|ting)?\s+(?:this|the|our|the final)\s+(?:response|package|reply|submission)\b",
    r"\b(?:transmit(?:ted)?|sent)\s+to\s+the\s+(?:regulator|examiner|occ|fdic|sec|finra)\b",
]
CLOSURE_PATTERNS = [
    r"\bclose[ds]?\s+the\s+(?:exam|examination|inquiry|matter)\b",
    r"\b(?:exam|examination|inquiry|matter)\s+(?:is\s+)?(?:closed|resolved)\b",
    r"\bcase\s+closed\b",
    r"\bno\s+further\s+action\s+(?:is\s+)?(?:required|needed|necessary)\b",
]
DECISION_PATTERNS = [
    r"\bwe\s+hereby\s+(?:attest|certify|represent)\b",
    r"\bhereby\s+certif(?:y|ies|ied)\b",
    r"\bthe\s+(?:agent|assistant|skill)\s+(?:approves|certifies|attests|closes)\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    sections = doc.get("template_sections") or []
    for s in REQUIRED_SECTIONS:
        if s not in sections:
            errors.append(f"missing required template section {s!r}")

    required_roles = list(doc.get("required_approver_roles") or [])
    items = doc.get("items") or []
    if not items:
        errors.append("response package has no items")

    for it in items:
        rid = it.get("request_id", "?")
        cov = it.get("coverage")
        status = it.get("response_status")
        if cov not in ALLOWED_COVERAGE:
            errors.append(f"{rid}: disallowed coverage {cov!r}")
        if status not in ALLOWED_STATUS:
            errors.append(f"{rid}: disallowed response_status {status!r} "
                          f"(submission/closure states not permitted)")

        # recompute unsupported assertions from the item's own data (do not trust the flag)
        unsupported = [a.get("assertion_id") for a in (it.get("assertions") or [])
                       if not a.get("source_ref")]
        if unsupported and status == "draft-ready-for-review":
            errors.append(f"{rid}: marked ready but carries unsupported assertion(s) "
                          f"{unsupported} (no unsupported claim may be presented as ready)")

        if status == "draft-ready-for-review":
            approved = {a.get("role") for a in (it.get("approvals_recorded") or [])
                        if a.get("status") == "approved"}
            missing = [r for r in required_roles if r not in approved]
            if missing:
                errors.append(f"{rid}: marked ready but missing required approval(s) {missing}")
            if not it.get("citations"):
                errors.append(f"{rid}: marked ready but has no citations (provenance required)")

    if doc.get("readiness") != REQUIRED_READINESS:
        errors.append(f"readiness must be {REQUIRED_READINESS!r}, got {doc.get('readiness')!r} "
                      f"(this skill never submits)")

    scan = json.dumps(items)
    for label, pats in (("submission", SUBMISSION_PATTERNS), ("closure", CLOSURE_PATTERNS),
                        ("decision", DECISION_PATTERNS)):
        for pat in pats:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"prohibited submission/closure/decision language detected "
                              f"({label}): {m.group(0)!r}")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "response_package_example.json"
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
