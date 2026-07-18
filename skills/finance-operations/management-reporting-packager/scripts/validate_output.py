#!/usr/bin/env python3
"""Deterministic output validation for management-reporting-packager.

Enforces the Draft & package guardrails before an assembled management report package is
presented for human review:
  1. All required approved-template sections are present.
  2. No unsupported / unapproved claims: every KPI figure carries a citation, and no KPI is
     flagged `unsupported` while the package claims `ready-for-review`.
  3. Required human approvals (preparer, reviewer) are recorded; delivery approval stays
     pending (this skill never obtains it).
  4. Draft-only: delivery_status is `draft` and no send/submit/distribute/post language
     appears.
  5. No forward-looking guarantees or investment advice.
  6. package_status is consistent with unsupported claims, breaks, and missing approvals.
  7. The standing note / distribution-control disclaimer is present.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "Cover & reporting scope",
    "Executive takeaways",
    "KPI scorecard & commentary",
    "Reconciliation & tie-out summary",
    "Source lineage & citations",
    "Exceptions & data gaps",
    "Approvals & sign-off log",
    "Standing note & distribution control",
]
REQUIRED_APPROVAL_ROLES = ("preparer", "reviewer")
RECORDED = {"recorded", "complete", "signed"}
STANDING_NOTE_MARKERS = (
    "draft management report package for human review only",
    "no figure has been approved as final",
)

# Language asserting the pack was delivered/submitted/posted (draft-only violation).
DELIVERY_PATTERNS = [
    r"\bhas been (distributed|delivered|submitted|sent|filed|posted)\b",
    r"\bdistributed to (the )?(board|committee|leadership|investors|regulator)\b",
    r"\bsent to (the )?(board|committee|leadership|investors|regulator)\b",
    r"\bsubmitted to (the )?(board|committee|regulator|sec)\b",
    r"\bfiled with (the )?(sec|regulator)\b",
    r"\bposted to the (gl|general ledger|ledger|system of record)\b",
]
# Language asserting a final/binding approval this skill cannot make.
APPROVAL_CLAIM_PATTERNS = [
    r"\bboard[- ]approved\b", r"\bapproved by the board\b",
    r"\bfinal and approved\b", r"\bcertified final\b",
]
# Unsupported forward-looking guarantees / investment advice.
CLAIM_PATTERNS = [
    r"\bguarantee(d|s)?\b", r"\bwill (exceed|beat|outperform)\b",
    r"\b(guaranteed|assured) (to )?(exceed|beat|hit)\b",
    r"\b(buy|sell|hold) recommendation\b", r"\binvest in\b",
]


def _scan(text, patterns, label, errors):
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"{label}: {m.group(0)!r}")


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    # 1. required sections
    sections = doc.get("sections") or []
    for s in REQUIRED_SECTIONS:
        if s not in sections:
            errors.append(f"missing required section: {s!r}")

    # draft-only control field
    if doc.get("delivery_status") != "draft":
        errors.append(f"delivery_status must be 'draft' (draft-only), got {doc.get('delivery_status')!r}")

    kpis = doc.get("kpis") or []
    if not kpis:
        errors.append("package has no KPIs")
    unsupported_ids = []
    for k in kpis:
        kid = k.get("id", "?")
        if not k.get("citations"):
            errors.append(f"KPI {kid}: missing citation (source lineage) -> unsupported claim")
        if k.get("support_status") == "unsupported":
            unsupported_ids.append(kid)

    # 2/6. package_status consistency
    status = doc.get("package_status")
    if status not in ("ready-for-review", "blocked"):
        errors.append(f"invalid package_status {status!r}")
    breaks = [r.get("name") for r in (doc.get("reconciliations") or []) if r.get("tie_out_status") == "break"]
    recorded_roles = {a.get("role") for a in (doc.get("approvals") or []) if a.get("status") in RECORDED}
    missing_appr = [r for r in REQUIRED_APPROVAL_ROLES if r not in recorded_roles]
    must_block = bool(unsupported_ids or breaks or missing_appr)
    if status == "ready-for-review" and must_block:
        reasons = []
        if unsupported_ids:
            reasons.append(f"unsupported KPIs {unsupported_ids}")
        if breaks:
            reasons.append(f"unreconciled breaks {breaks}")
        if missing_appr:
            reasons.append(f"missing approvals {missing_appr}")
        errors.append("package_status is 'ready-for-review' but must be 'blocked': " + "; ".join(reasons))

    # 3. required approvals recorded; delivery stays pending
    for role in REQUIRED_APPROVAL_ROLES:
        if role not in recorded_roles and status == "ready-for-review":
            errors.append(f"required approval not recorded: {role}")
    for a in (doc.get("approvals") or []):
        if a.get("role") == "delivery" and a.get("status") in RECORDED:
            errors.append("delivery approval is marked recorded; draft-only skill never obtains delivery sign-off")

    # 4/5. prohibited language scan (exclude the fixed standing note, which negates these
    # very phrases: "No pack has been delivered, submitted, distributed, or posted ...").
    scanned = {k: v for k, v in doc.items() if k != "standing_note"}
    scan = json.dumps(scanned)
    _scan(scan, DELIVERY_PATTERNS, "delivery/submission language (draft-only)", errors)
    _scan(scan, APPROVAL_CLAIM_PATTERNS, "unapproved final-approval claim", errors)
    _scan(scan, CLAIM_PATTERNS, "unsupported forward-looking/advice claim", errors)

    # 7. standing note
    note = str(doc.get("standing_note", "")).lower()
    for marker in STANDING_NOTE_MARKERS:
        if marker not in note:
            errors.append("missing/!incomplete standing note & distribution-control disclaimer")
            break

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "package_assembled.json"
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
