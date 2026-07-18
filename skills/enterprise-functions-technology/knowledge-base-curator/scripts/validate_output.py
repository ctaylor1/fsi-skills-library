#!/usr/bin/env python3
"""Deterministic output validation for knowledge-base-curator.

Enforces the Draft & package guardrails before a curation worklist is handed to a human:
  1. Draft-only: status is 'draft'; no finding is in a done-state; no send/publish/delete
     language.
  2. Template fidelity: required sections present (cover/summary/findings non-empty;
     retirements/gaps present); the source register is present.
  3. No unsupported claims: unsupported_claims is empty and every finding carries at least
     one citation.
  4. Required approvals recorded: every recommended change (action != none) appears in the
     approvals register with an approver_role and status; an 'obtained' approval names a human.
  5. The standing DRAFT note is present.

Usage: python validate_output.py curation_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_NONEMPTY = ("cover", "summary", "findings")
REQUIRED_PRESENT = ("retirements", "gaps")
NO_ACTION = "none"
DONE_STATES = {"published", "merged", "retired", "deleted", "applied", "approved"}
STANDING_NOTE = ("DRAFT knowledge-base curation worklist for human review; nothing has been "
                 "published, updated, merged, retired, or deleted, and no change has been "
                 "approved by this skill.")
# language that would mean content was changed/delivered rather than drafted
SEND_PATTERNS = [
    r"\bpublished to (the )?(kb|knowledge base|cms)\b", r"\bdeleted the\b",
    r"\bmerged and removed\b", r"\bretired the article\b", r"\bpushed to production\b",
    r"\bapplied the (change|update|edit)\b", r"\bsent to\b", r"\bsubmitted to\b",
    r"\bwent live\b", r"\bhas been published\b", r"\bhas been deleted\b",
]


def _iter_findings(doc):
    sections = doc.get("sections") or {}
    yield from sections.get("findings") or []
    yield from sections.get("gaps") or []


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    # 1a. draft-only status
    if doc.get("status") != "draft":
        errors.append(f"status must be 'draft' (draft-only), got {doc.get('status')!r}")

    # 2. template fidelity
    sections = doc.get("sections") or {}
    for k in REQUIRED_NONEMPTY:
        if not sections.get(k):
            errors.append(f"template fidelity: required section {k!r} missing or empty")
    for k in REQUIRED_PRESENT:
        if k not in sections:
            errors.append(f"template fidelity: required section {k!r} missing")
    if not doc.get("sources"):
        errors.append("template fidelity: source register ('sources') missing or empty")
    if "approvals" not in doc:
        errors.append("template fidelity: approvals register ('approvals') missing")

    # 3. no unsupported claims + every finding cited
    unsupported = doc.get("unsupported_claims")
    if unsupported is None:
        errors.append("unsupported_claims list missing (cannot certify sourcing)")
    elif unsupported:
        errors.append(f"{len(unsupported)} unsupported claim(s) present (every finding must cite the KB record and/or an approved source)")
    for f in _iter_findings(doc):
        ref = f.get("article_id") or f.get("topic_id") or "?"
        if not f.get("citations"):
            errors.append(f"finding {ref!r} has no citation (unsupported assertion)")
        # 1b. no done-state on a finding
        if str(f.get("finding", "")).lower() in DONE_STATES:
            errors.append(f"finding {ref!r} is in a done-state {f.get('finding')!r} (skill only proposes)")
        if str(f.get("recommended_action", "")).lower() in {"publish", "delete"}:
            errors.append(f"finding {ref!r} recommends a prohibited direct action {f.get('recommended_action')!r}")

    # 4. approvals recorded for every recommended change
    approvals = doc.get("approvals") or []
    ap_by_ref = {a.get("ref_id"): a for a in approvals}
    for f in _iter_findings(doc):
        ref = f.get("article_id") or f.get("topic_id")
        if f.get("recommended_action") and f.get("recommended_action") != NO_ACTION:
            a = ap_by_ref.get(ref)
            if not a:
                errors.append(f"change {ref!r} ({f.get('recommended_action')}) not recorded in approvals register")
            else:
                if not a.get("approver_role"):
                    errors.append(f"change {ref!r} approval has no approver_role recorded")
                if not a.get("status"):
                    errors.append(f"change {ref!r} approval has no status recorded")
                if str(a.get("status", "")).lower() == "obtained" and not a.get("approver"):
                    errors.append(f"change {ref!r} marked 'obtained' without a named human approver (unapproved claim)")
    for a in approvals:
        if str(a.get("status", "")).lower() not in {"pending", "obtained"}:
            errors.append(f"approval {a.get('ref_id')!r} has invalid status {a.get('status')!r} (pending|obtained)")

    # 1c. no send/publish/delete language (exclude the standing note, which negates these
    # words by design, e.g. "nothing has been published"; it is checked verbatim below)
    scanned = {k: v for k, v in doc.items() if k != "standing_note"}
    scan = json.dumps(scanned)
    for pat in SEND_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"draft-only violation: delivery/change language detected: {m.group(0)!r}")

    # 5. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing DRAFT note")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "curation_pack_example.json"
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
