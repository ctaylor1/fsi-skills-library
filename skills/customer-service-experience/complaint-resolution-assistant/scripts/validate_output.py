#!/usr/bin/env python3
"""Deterministic output validation for complaint-resolution-assistant.

Enforces the draft-and-package guardrails before a drafted complaint response is presented
for human review. It checks that the deliverable is a compliant DRAFT, not an executed or
sent action:
  1. Allowed dispositions and proposed outcomes only (no binding decision states).
  2. Draft letters carry every required template section and the DRAFT marker.
  3. Required human approvals are RECORDED (handler review + final approver).
  4. Remediation ties out (components sum to total) and goodwill is within the cap.
  5. No unsupported / unapproved claims (liability admissions, guarantees, promises,
     legal advice, or "we have paid you" style executed-action language).
  6. No send / submit / file / close language (draft-only; never delivered here).
  7. The standing note is present.

Usage: python validate_output.py response.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {"draft-ready", "refer-specialist", "needs-data", "needs-review"}
ALLOWED_OUTCOMES = {"uphold", "partial-uphold", "not-upheld", "needs-review", None}
REQUIRED_SECTIONS = [
    "Summary of your complaint", "What we looked into", "What we found",
    "Putting things right", "Our decision", "How to escalate",
]
REQUIRED_APPROVALS = ("complaints_handler_review", "final_response_approver")
STANDING_NOTE = "Draft complaint response only"
DRAFT_MARKER = "DRAFT"

# Claims a complaints response must never assert without support/approval.
UNSUPPORTED_PATTERNS = [
    r"\bwe admit (legal )?liability\b", r"\bwe are (legally )?liable\b",
    r"\bthis (is|constitutes|was) a breach of (the )?law\b",
    r"\bwe guarantee\b", r"\bguaranteed\b", r"\bwe promise\b",
    r"\byou will definitely\b", r"\bwithout a doubt\b", r"\b100% certain\b",
    r"\byou should sue\b", r"\bseek legal action\b", r"\bconsult your lawyer\b",
    r"\bwe have paid you\b", r"\bpayment has been made\b", r"\brefund has been issued\b",
    r"\bfunds have been credited\b",
]
# Draft-only: none of these delivery/execution/closure states may appear.
SENT_PATTERNS = [
    r"\bthis (response|letter|email) has been sent\b", r"\bemail sent\b",
    r"\bwe have (emailed|posted|sent) (you|this)\b", r"\bsubmitted to the regulator\b",
    r"\breported to the (regulator|ombudsman)\b", r"\bcase closed\b",
    r"\bwe have closed your (complaint|case)\b", r"\bcomplaint closed\b",
]


def _round(x):
    return round(float(x) + 1e-9, 2)


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    records = doc.get("complaints") or []
    if not records:
        return ["output has no complaint records"]

    for r in records:
        cid = r.get("complaint_id", "?")
        disp = r.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{cid}: disallowed disposition {disp!r} (binding/closure states not permitted)")
        if r.get("proposed_outcome") not in ALLOWED_OUTCOMES:
            errors.append(f"{cid}: disallowed proposed_outcome {r.get('proposed_outcome')!r}")

        rem = r.get("remediation")
        if rem:
            comp = _round(rem.get("financial_loss", 0) + rem.get("interest", 0)
                          + rem.get("distress_inconvenience", 0) + rem.get("goodwill", 0))
            if abs(comp - _round(rem.get("total", 0))) > 0.01:
                errors.append(f"{cid}: remediation total {rem.get('total')} != components {comp}")
            cap = (rem.get("basis") or {}).get("goodwill_cap")
            if cap is not None and rem.get("goodwill", 0) > float(cap) + 0.01:
                errors.append(f"{cid}: goodwill {rem.get('goodwill')} exceeds cap {cap}")

        if disp in ("draft-ready", "refer-specialist"):
            dr = r.get("draft_response") or {}
            body = dr.get("body", "")
            if not body:
                errors.append(f"{cid}: draft-ready but no draft_response.body")
            else:
                for s in REQUIRED_SECTIONS:
                    if s not in body:
                        errors.append(f"{cid}: draft letter missing required section {s!r}")
                if DRAFT_MARKER not in body:
                    errors.append(f"{cid}: draft letter missing DRAFT marker")
            ap = r.get("approvals") or {}
            for key in REQUIRED_APPROVALS:
                slot = ap.get(key)
                if not isinstance(slot, dict) or not slot.get("status"):
                    errors.append(f"{cid}: required approval {key!r} not recorded")
            if not r.get("citations"):
                errors.append(f"{cid}: draft-ready with no citations")

    scan = json.dumps(records) + " " + str(doc.get("narrative", ""))
    for pat in UNSUPPORTED_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"unsupported/unapproved claim detected: {m.group(0)!r}")
    for pat in SENT_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"draft-only violated (send/submit/close language): {m.group(0)!r}")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "response_example.json"
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
