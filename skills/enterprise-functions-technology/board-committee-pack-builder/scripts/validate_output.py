#!/usr/bin/env python3
"""Deterministic output validation for board-committee-pack-builder.

Enforces the Draft & package guardrails before an assembled pack is handed to a human:
  1. Template fidelity: every required section is present and non-empty.
  2. No unsupported claims: unsupported_claims is empty and every decision/metric/risk/issue
     carries at least one resolvable citation.
  3. No unapproved claims: a decision is treated as "not yet taken" only while its status is a
     recognized non-decided state (proposed/pending/...); ANY other status -- including
     paraphrased or multi-word decided language ('agreed', 'passed', 'carried by the
     committee') -- is a decided claim that MUST have a named human approver recorded in the
     approvals register. This is an allowlist: unrecognized statuses fail closed as decided.
  4. Required human approvals are recorded: every requires_approval decision appears in the
     approvals register with an approver_role and a status.
  5. Draft-only: status is 'draft' and no send / submit / distribute / finalize language.
  6. The standing DRAFT note is present.

Usage: python validate_output.py pack_draft.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = ("cover", "agenda", "decisions", "metrics", "risks", "issues", "takeaways")
SOURCED_KINDS = ("decisions", "metrics", "risks", "issues")
# Allowlist of statuses that mean a decision is NOT yet taken and may stand WITHOUT a recorded
# human approver. This is the safety backstop: any status that is non-empty and not one of
# these recognized non-decided states -- however it is phrased -- is treated as a decided
# claim that must name a human approver (fail closed on unknown/paraphrased decided language).
UNDECIDED_STATES = frozenset({
    "proposed", "pending", "draft", "tabled", "deferred", "withdrawn", "open",
    "for discussion", "for noting", "noting", "for information", "information",
    "for decision", "for approval", "under review", "in review", "not decided",
    "undecided", "to be approved", "awaiting approval", "awaiting ratification",
    "pending approval", "pending ratification", "recommended",
})
STANDING_NOTE = ("DRAFT board/committee pack assembled for human review; nothing has been "
                 "sent, submitted, distributed, or finalized, and no decision has been "
                 "approved by this skill.")
# language that would mean the pack was delivered/finalized rather than drafted
SEND_PATTERNS = [
    r"\bsent to the board\b", r"\bsubmitted to (the )?(board|regulator|committee|sec|fca)\b",
    r"\bdistributed to (the )?(board|committee|members|directors)\b",
    r"\bfiled with\b", r"\bissued to\b", r"\bfinal and issued\b",
    r"\bboard[- ]?approved\b", r"\bpack finalized\b", r"\bpack finalised\b",
]


def _norm_status(status) -> str:
    """Normalize a status for allowlist comparison: lowercase, punctuation->space, collapse ws."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(status or "").lower()).split())


def presents_as_decided(status) -> bool:
    """True if a decision's status asserts the decision has been TAKEN.

    Allowlist model (fail closed): a status counts as *not yet decided* only when it is empty
    or exactly matches a recognized non-decided state in UNDECIDED_STATES. Any other non-empty
    status -- 'agreed', 'passed', 'carried by the committee', 'board-approved', or any other
    decided-state wording -- is a decided claim that must name a recorded human approver.
    """
    norm = _norm_status(status)
    if not norm:
        return False
    return norm not in UNDECIDED_STATES


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    # 5a. draft-only status
    if doc.get("status") != "draft":
        errors.append(f"status must be 'draft' (draft-only), got {doc.get('status')!r}")

    # 1. template fidelity
    sections = doc.get("sections") or {}
    for k in REQUIRED_SECTIONS:
        if not sections.get(k):
            errors.append(f"template fidelity: required section {k!r} missing or empty")
    if not doc.get("sources"):
        errors.append("template fidelity: source register ('sources') missing or empty")
    if "approvals" not in doc:
        errors.append("template fidelity: approvals register ('approvals') missing")

    # 2. no unsupported claims
    unsupported = doc.get("unsupported_claims")
    if unsupported is None:
        errors.append("unsupported_claims list missing (cannot certify sourcing)")
    elif unsupported:
        errors.append(f"{len(unsupported)} unsupported claim(s) present (every claim must cite an approved source)")
    for kind in SOURCED_KINDS:
        for item in sections.get(kind) or []:
            if not item.get("citations"):
                errors.append(f"{kind} item {item.get('id')!r} has no citation (unsupported assertion)")

    # 3 + 4. approvals recorded; no unapproved claims
    approvals = doc.get("approvals") or []
    ap_by_decision = {a.get("decision_id"): a for a in approvals}
    for d in sections.get("decisions") or []:
        did = d.get("id")
        if d.get("requires_approval"):
            a = ap_by_decision.get(did)
            if not a:
                errors.append(f"decision {did!r} requires approval but is not in the approvals register")
            else:
                if not a.get("approver_role"):
                    errors.append(f"decision {did!r} approval has no approver_role recorded")
                if not a.get("status"):
                    errors.append(f"decision {did!r} approval has no status recorded")
        # unapproved-claim check: a decision presented as decided must name a human approver.
        # Allowlist screen: any status that is not a recognized non-decided state is decided.
        if presents_as_decided(d.get("status")):
            a = ap_by_decision.get(did) or {}
            if not a.get("approver"):
                errors.append(f"decision {did!r} presented as {d.get('status')!r} without a recorded human approver (unapproved claim)")

    # 5b. no send/submit/distribute/finalize language
    scan = json.dumps(doc)
    for pat in SEND_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"draft-only violation: delivery/finalization language detected: {m.group(0)!r}")

    # 6. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing DRAFT note")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_draft_example.json"
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
