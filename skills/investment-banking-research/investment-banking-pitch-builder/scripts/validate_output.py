#!/usr/bin/env python3
"""Deterministic output validation for investment-banking-pitch-builder.

Enforces the Draft & package guardrails before an assembled pitch draft is handed to a
banker for review, in line with the primary validation focus (template fidelity,
completeness, source mapping, required approvals, no unsupported assertions):

  1. Template fidelity / completeness  - every required template section is present.
  2. Source mapping / no unsupported assertions - every page claim carries an approved
     source; no promissory/guarantee/personalized-advice language anywhere.
  3. Page completeness - every page has a takeaway and at least one source citation.
  4. Required approvals recorded - each required approval role has a record; an
     `approved-for-delivery` status is allowed only when all required approvals are approved.
  5. Draft-only - delivery_status is never a sent/delivered/submitted state; the draft-only
     notice and standing note are present.

Usage: python validate_output.py draft.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DELIVERY = {"draft", "hold-for-approval", "approved-for-delivery"}
FORBIDDEN_DELIVERY = {"sent", "delivered", "submitted", "distributed", "filed", "emailed", "released"}

STANDING_NOTE_KEY = "draft pitch materials only"
DRAFT_NOTICE_KEY = "draft"

# Promissory / guarantee / personalized-advice language that must never appear in an
# assembled pitch draft (unsupported assertions), regardless of any cited source.
PROHIBITED_PATTERNS = [
    r"\bguarante(e|ed|es)\b",
    r"\brisk[- ]free\b",
    r"\bno risk\b",
    r"\bcan'?t lose\b",
    r"\bwill (out ?perform|double|triple|beat the market)\b",
    r"\bassured returns?\b",
    r"\bpromis(e|ed|es) (of )?returns?\b",
    r"\bcertain to (rise|increase|outperform|deliver|double)\b",
    r"\byou should (buy|sell|invest)\b",
]


def _text_blob(doc: dict) -> str:
    parts = []
    for p in doc.get("pages") or []:
        parts.append(str(p.get("title", "")))
        parts.append(str(p.get("takeaway", "")))
        for c in p.get("claims") or []:
            parts.append(str(c.get("text", "")))
    parts.append(str(doc.get("narrative", "")))
    return " ".join(parts)


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    pages = doc.get("pages") or []
    if not pages:
        return ["assembled draft has no pages"]

    # 5. Draft-only delivery status
    status = doc.get("delivery_status")
    if status in FORBIDDEN_DELIVERY:
        errors.append(
            f"delivery_status {status!r} indicates the materials were sent/submitted/"
            f"distributed - this skill is draft-only and never delivers"
        )
    elif status not in ALLOWED_DELIVERY:
        errors.append(f"delivery_status {status!r} is not an allowed draft state {sorted(ALLOWED_DELIVERY)}")

    # 1. Template fidelity / completeness
    required_sections = doc.get("template_required_sections") or []
    present = {p.get("section") for p in pages}
    for sec in required_sections:
        if sec not in present:
            errors.append(f"missing required template section: {sec!r}")

    # 2/3. Source mapping, unsupported assertions, page completeness
    for p in pages:
        pid = p.get("page_id", "?")
        if not p.get("takeaway"):
            errors.append(f"{pid}: page has no takeaway (template fidelity)")
        if not p.get("sources"):
            errors.append(f"{pid}: page has no source citation")
        for c in p.get("claims") or []:
            if not c.get("source_ref") or c.get("approved") is not True:
                errors.append(f"{pid}: unsupported/unapproved assertion (no approved source): {c.get('text','')!r}")

    blob = _text_blob(doc)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, blob, re.I)
        if m:
            errors.append(f"prohibited unsupported/promissory language: {m.group(0)!r}")

    # 4. Required approvals recorded + delivery consistency
    required_approvals = doc.get("required_approvals") or []
    appr_map = {a.get("role"): a.get("status") for a in (doc.get("approvals") or [])}
    for role in required_approvals:
        if role not in appr_map:
            errors.append(f"required approval not recorded: {role!r}")
    if status == "approved-for-delivery":
        for role in required_approvals:
            if appr_map.get(role) != "approved":
                errors.append(
                    f"delivery_status 'approved-for-delivery' but required approval {role!r} "
                    f"is {appr_map.get(role)!r}"
                )

    # 5. Notices present
    if STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing draft-only standing note")
    if DRAFT_NOTICE_KEY not in str(doc.get("draft_only_notice", "")).lower():
        errors.append("missing draft-only notice")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pitch_draft_example.json"
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
