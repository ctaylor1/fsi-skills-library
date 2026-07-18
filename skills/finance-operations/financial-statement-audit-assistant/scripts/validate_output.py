#!/usr/bin/env python3
"""Deterministic output validation for financial-statement-audit-assistant.

Enforces the Draft & package guardrails before the working-paper draft is presented:
  1. Template fidelity  -- every required working-paper section is present and non-empty.
  2. No unsupported assertions -- every tie-out and every finding carries a citation.
  3. No unapproved / opinion claims -- no audit-opinion, fair-presentation, going-concern,
     assurance, or "final/filed/submitted" language (draft-only; never send/submit).
  4. Tie-out arithmetic -- difference == fs_amount - tb_sum and status matches the
     clearly-trivial threshold (ties output to the deterministic engine).
  5. Required human approvals recorded -- Preparer and Reviewer roles present with a name
     and a status.
  6. Standing limitation note present.

Usage: python validate_output.py workpaper.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "engagement_and_scope", "planning_and_materiality", "source_mapping_and_tieouts",
    "sampling_approach", "testing_results", "misstatement_summary",
    "open_items_and_requests", "approvals_and_signoff",
]
REQUIRED_APPROVAL_ROLES = ("Preparer", "Reviewer")
STANDING_NOTE = (
    "Draft audit working papers only. No audit opinion is expressed or implied; no "
    "conclusion on fair presentation, materiality, or going concern has been reached. "
    "Requires engagement-team review and partner approval before any reliance or external "
    "delivery."
)
# Opinion / unsupported-claim language that must never appear in a draft support paper.
OPINION_PATTERNS = [
    r"\bin our opinion\b", r"\bpresents?\s+fairly\b", r"\bpresent\s+fairly\b",
    r"\bfairly\s+stated\b", r"\btrue and fair\b",
    r"\b(unqualified|qualified|adverse|disclaimer of)\s+opinion\b", r"\baudit opinion\b",
    r"\breasonable assurance\b", r"\bfree from material misstatement\b",
    r"\bwe conclude(d)?\s+that the financial statements\b",
    r"\bgoing concern\s+(assumption\s+)?is appropriate\b",
    r"\bmaterially (correct|accurate)\b",
]
# Draft-only: never deliver / file / submit.
DELIVERY_PATTERNS = [
    r"\bfiled with the\b", r"\bsubmitted to the (sec|regulator|pcaob)\b",
    r"\bdelivered as final\b", r"\bissued to the client as final\b",
    r"\bthis (report|paper) is final\b",
]


def _expected_status(diff, threshold, unmapped):
    if unmapped:
        return "unmapped"
    return "difference" if abs(diff) > threshold else "tie"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    # 1. template fidelity
    sections = doc.get("sections") or {}
    for s in REQUIRED_SECTIONS:
        if not str(sections.get(s, "")).strip():
            errors.append(f"template fidelity: required section '{s}' missing or empty")

    # 2. + 4. tie-outs cited and arithmetic-consistent
    tieouts = doc.get("tieouts")
    if tieouts is None:
        errors.append("no tieouts array in output")
        tieouts = []
    for t in tieouts:
        cap = t.get("caption", "?")
        if not t.get("citations"):
            errors.append(f"unsupported assertion: tie-out '{cap}' has no citation")
        try:
            diff = round(float(t.get("fs_amount", 0)) - float(t.get("tb_sum", 0)), 2)
        except (TypeError, ValueError):
            errors.append(f"tie-out '{cap}': non-numeric fs_amount/tb_sum")
            continue
        if round(float(t.get("difference", 0)), 2) != diff:
            errors.append(f"tie-out '{cap}': difference {t.get('difference')} != fs_amount - tb_sum ({diff})")
        exp = _expected_status(diff, float(t.get("threshold", 0) or 0), t.get("status") == "unmapped")
        if t.get("status") != exp:
            errors.append(f"tie-out '{cap}': status {t.get('status')!r} != expected {exp!r}")

    # 2. findings cited
    for f in doc.get("findings") or []:
        if not f.get("citations"):
            errors.append(f"unsupported assertion: finding '{f.get('finding_id','?')}' has no citation")

    # 5. required approvals recorded
    approvals = doc.get("approvals") or []
    by_role = {a.get("role"): a for a in approvals}
    for role in REQUIRED_APPROVAL_ROLES:
        a = by_role.get(role)
        if not a:
            errors.append(f"required approval not recorded: '{role}' role missing from approvals")
        elif not a.get("name") or not a.get("status"):
            errors.append(f"required approval '{role}' incomplete: needs a name and a status")

    # 3. opinion / delivery language screen (exclude the standing note, which negates them)
    scan = " ".join([
        str(doc.get("narrative", "")),
        json.dumps(sections),
        json.dumps(doc.get("findings") or []),
        json.dumps(doc.get("tieouts") or []),
    ])
    for pat in OPINION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"unapproved claim: audit-opinion/assurance language {m.group(0)!r} (this skill forms no opinion)")
    for pat in DELIVERY_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"draft-only violation: delivery/filing language {m.group(0)!r} (never send/submit)")

    # 6. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing limitation note")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "workpaper_example.json"
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
