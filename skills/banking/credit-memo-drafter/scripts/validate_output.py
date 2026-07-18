#!/usr/bin/env python3
"""Deterministic output validation for credit-memo-drafter.

Enforces the draft-and-package guardrails before a credit memorandum is handed to the
underwriter. Fails closed (exit 1) on any breach:

  1. disposition is the draft outcome only -- no decision/closure/booking outcome.
  2. Every required template section is present, non-empty, and carries a source citation
     (source-to-memo traceability).
  3. `unsupported_assertions` is empty -- no unsupported/unapproved claim survives.
  4. The spread tie-out status is `tie` (recomputed ratios reconcile to the approved spread).
  5. Required human approvals are RECORDED and still PENDING -- the draft never self-grants
     an approval.
  6. No decision / closure / filing / booking / covenant-waiver language anywhere (R3 screen).
  7. The standing "draft-only" note is present.

Usage: python validate_output.py memo_draft.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "borrower_overview", "facility_summary", "financial_analysis", "repayment_analysis",
    "collateral_analysis", "risk_rating", "covenants", "policy_exceptions", "recommendation",
]
ALLOWED_DISPOSITION = "draft-for-underwriter-review"
PENDING_STATES = {"pending", "required"}
STANDING_SNIPPET = "draft credit memorandum for human underwriting adjudication only"

# Affirmative decision / closure / filing / booking / waiver phrasing (tight adjacency so the
# negated "no facility has been approved..." standing note does NOT trip these).
DECISION_PATTERNS = [
    r"\bcredit (is |has been )?approved\b",
    r"\bloan (is |has been )?approved\b",
    r"\bfacility (is )?approved\b",
    r"\bapplication (is )?approved\b",
    r"\bwe (hereby )?approve\b",
    r"\bapproved and (booked|funded|disbursed)\b",
    r"\bcredit (is )?(declined|denied)\b",
    r"\b(is|are) (declined|denied)\b",
    r"\bfinal (credit )?decision\b",
    r"\badverse action\b",
    r"\bbooked to (the )?(core|los|system)\b",
    r"\bhas been funded\b",
    r"\bfunds (were |have been )?disbursed\b",
    r"\bfiled with (the )?(regulator|sec|occ|fdic)\b",
    r"\bposted to (the )?system of record\b",
    r"\bwe waive\b",
    r"\bcovenant (is )?waived\b",
    r"\bexception (is )?granted\b",
]
GRANTED_STATES = {"granted", "approved", "signed", "complete", "authorized"}


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    disp = doc.get("disposition")
    if disp != ALLOWED_DISPOSITION:
        errors.append(f"disallowed disposition {disp!r} "
                      f"(credit-memo-drafter may only produce {ALLOWED_DISPOSITION!r})")

    sections = doc.get("sections") or {}
    for name in REQUIRED_SECTIONS:
        s = sections.get(name)
        if not isinstance(s, dict) or not str(s.get("content", "")).strip():
            errors.append(f"missing required section: {name}")
            continue
        if not s.get("citations"):
            errors.append(f"unsupported assertion: section {name} has no source citation")

    unsupported = doc.get("unsupported_assertions")
    if unsupported is None:
        errors.append("missing unsupported_assertions field (traceability control)")
    elif unsupported:
        for u in unsupported:
            errors.append(f"unsupported assertion: {u}")

    tie = (doc.get("spread_tie_out") or {}).get("status")
    if tie != "tie":
        errors.append(f"spread tie-out not reconciled (status {tie!r}); financial section unsupported")

    approvals = doc.get("approvals")
    if not approvals or not isinstance(approvals, list):
        errors.append("required human approvals not recorded (approvals block missing/empty)")
    else:
        for a in approvals:
            st = str(a.get("status", "")).lower()
            if st in GRANTED_STATES:
                errors.append(f"self-granted approval for role {a.get('role')!r} "
                              f"(status {a.get('status')!r}); draft must leave approvals pending")
            elif st not in PENDING_STATES:
                errors.append(f"approval for role {a.get('role')!r} has invalid status {a.get('status')!r}")

    scan = json.dumps({k: v for k, v in doc.items() if k not in ("standing_note",)})
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"decision/closure language detected: {m.group(0)!r} "
                          f"(memo is draft decision-support, never a decision/booking/filing)")

    if STANDING_SNIPPET not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note (draft-only disclosure)")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "memo_draft_example.json"
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
