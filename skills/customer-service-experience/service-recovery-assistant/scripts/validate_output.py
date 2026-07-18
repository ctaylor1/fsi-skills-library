#!/usr/bin/env python3
"""Deterministic output validation for service-recovery-assistant (Draft & package).

Enforces the drafting guardrails before a service-recovery package is presented for
approval:
  1. Only draft dispositions are used (never sent/paid/resolved/closed).
  2. Draft-only: no entry may be marked delivered (delivery.sent must be false).
  3. Every `draft-for-approval` entry carries ALL required template sections, non-empty.
  4. Remediation ties out (redress + goodwill == total), goodwill stays within the matrix
     cap, and the figures quoted in the drafted communication are ONLY the computed ones
     (no unsupported monetary claims).
  5. Required human approvals are recorded (approval tier + approver role); an approval may
     not be marked recorded/approved without a named approver and decision.
  6. No unsupported/unapproved claims: no liability admission, guarantee, entitlement
     assertion, "already done" language, or investment/legal/tax advice.
  7. The standing note is present.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {"draft-for-approval", "needs-data", "refer-specialist"}
REQUIRED_SECTIONS = ("case_summary", "failure_assessment", "customer_impact",
                     "precedent_and_policy", "proposed_remediation", "communication_draft",
                     "required_approvals", "sources")
CITED_SECTIONS = ("failure_assessment", "proposed_remediation", "communication_draft")
APPROVAL_STATUSES = {"pending", "recorded"}
STANDING_NOTE = ("Draft for human review only; no communication has been sent and no "
                 "goodwill or redress has been paid.")
MONEY_RE = re.compile(r"\$\s?(\d+(?:\.\d{2})?)")

UNSUPPORTED_CLAIM_PATTERNS = [
    r"\bwe (are|'re) (legally )?liable\b", r"\blegally liable\b",
    r"\bwe admit (fault|negligence|liability|wrongdoing)\b",
    r"\bwe guarantee\b", r"\bguaranteed\b", r"\bwe promise\b",
    r"\b(this|it) (will|won'?t) never happen again\b",
    r"\bwill never happen again\b",
    r"\byou are (legally )?entitled to\b", r"\bcompensation you are (owed|entitled)\b",
]
ADVICE_PATTERNS = [
    r"\byou should invest\b", r"\bwe recommend (you )?(buy|sell|invest)\b",
    r"\binvestment advice\b", r"\btax advice\b", r"\blegal advice\b",
    r"\bfor tax purposes\b",
]
ALREADY_DONE_PATTERNS = [
    r"\bhas been (sent|delivered|paid|credited|refunded)\b",
    r"\bwe have (paid|credited|refunded|sent)\b",
    r"\bpayment (has been|was) (made|issued)\b",
]


def _nonempty(v) -> bool:
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (dict, list)):
        return len(v) > 0
    return v is not None


def _check_entry(r, errors):
    aid = r.get("case_id", "?")
    disp = r.get("disposition")
    if disp not in ALLOWED_DISPOSITIONS:
        errors.append(f"{aid}: disallowed disposition {disp!r} (draft only; never sent/paid/closed)")
    if (r.get("delivery") or {}).get("sent"):
        errors.append(f"{aid}: delivery.sent is true (draft-only skill must never send)")

    if disp != "draft-for-approval":
        return
    sec = r.get("sections") or {}
    for s in REQUIRED_SECTIONS:
        if s not in sec or not _nonempty(sec.get(s)):
            errors.append(f"{aid}: missing/empty required section '{s}'")
    for s in CITED_SECTIONS:
        block = sec.get(s) or {}
        if isinstance(block, dict) and not block.get("citations"):
            errors.append(f"{aid}: section '{s}' has no citations (unsupported)")

    rem = sec.get("proposed_remediation") or {}
    redress = round(float(rem.get("direct_redress") or 0), 2)
    goodwill = round(float(rem.get("goodwill_gesture") or 0), 2)
    total = round(float(rem.get("total") or 0), 2)
    cap = round(float(rem.get("goodwill_cap") or 0), 2)
    if round(redress + goodwill, 2) != total:
        errors.append(f"{aid}: remediation does not tie out ({redress}+{goodwill} != {total})")
    if cap and goodwill > cap:
        errors.append(f"{aid}: goodwill {goodwill} exceeds approved matrix cap {cap}")
    if not rem.get("matrix_version"):
        errors.append(f"{aid}: proposed_remediation missing matrix_version")

    # Every monetary figure quoted to the customer must be a computed value.
    allowed_amounts = {redress, goodwill, total}
    comm = sec.get("communication_draft") or {}
    comm_text = " ".join(str(comm.get(k, "")) for k in
                         ("apology", "explanation", "remediation_offer", "next_steps"))
    for m in MONEY_RE.findall(comm_text):
        if round(float(m), 2) not in allowed_amounts:
            errors.append(f"{aid}: communication quotes unsupported amount ${m} "
                          f"(allowed: {sorted(allowed_amounts)})")

    appr = sec.get("required_approvals") or {}
    if not appr.get("tier") or not appr.get("approver_role"):
        errors.append(f"{aid}: required_approvals missing tier/approver_role")
    status = appr.get("status")
    if status not in APPROVAL_STATUSES:
        errors.append(f"{aid}: required_approvals.status {status!r} not in {sorted(APPROVAL_STATUSES)}")
    if status == "recorded" and (not appr.get("approver") or not appr.get("decision")):
        errors.append(f"{aid}: approval marked recorded without a named approver and decision")


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    package = doc.get("package") or []
    if not package:
        return ["package has no entries"]
    for r in package:
        _check_entry(r, errors)

    # Scan the drafted package entries (not the controlled standing-note constant, which
    # legitimately says "no communication has been sent ... no goodwill ... has been paid").
    scan = json.dumps(package)
    for pat in UNSUPPORTED_CLAIM_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"unsupported/unapproved claim detected: {m.group(0)!r}")
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited advice detected: {m.group(0)!r}")
    for pat in ALREADY_DONE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"'already actioned' language detected: {m.group(0)!r} (draft only)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "svc_recovery_package.json"
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
