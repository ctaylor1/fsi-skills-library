#!/usr/bin/env python3
"""Deterministic output validation for policy-document-assistant.

Enforces the Draft & package guardrails before a policy draft is handed to a human for
review / external delivery:
  1. All required controlled-policy template sections are present (template fidelity).
  2. No unsupported / unapproved claims: every normative clause maps to an approved source,
     `unsupported_clauses` is empty, and no normative text uses unsupported-claim language.
  3. Required human approvals are recorded (each required role approved, with approver+date).
  4. Version and next-review date tie out to the deterministic rules.
  5. No publication / activation / filing language (draft-only; never send/submit).
  6. The standing note is present.

Usage: python validate_output.py draft.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import calendar, json, re, sys
from datetime import date
from pathlib import Path

REQUIRED_SECTIONS = ["document-control", "purpose", "scope", "policy-statements",
                     "roles-responsibilities", "related-documents",
                     "review-version-history", "approvals"]
TIER_REVIEW_MONTHS = {"tier-1": 12, "tier-2": 24, "tier-3": 36}
DEFAULT_REVIEW_MONTHS = 12
STANDING_NOTE_KEY = "draft policy for human review only"

# Language that would assert a policy is live/binding — forbidden in a draft.
PUBLICATION_PATTERNS = [
    r"\bnow in effect\b", r"\beffective immediately\b", r"\bmade effective\b",
    r"\bhas been published\b", r"\bis hereby published\b", r"\bpublished to (all )?(staff|employees)\b",
    r"\bactivated in the (policy|document|content) (management )?system\b",
    r"\bsubmitted to the regulator\b", r"\bfiled with the\b", r"\bgoes? live (today|immediately)\b",
    r"\bthis (policy|procedure) supersedes .*effective today\b",
]
# Hedge phrasing used to smuggle in an assertion with no approved requirement behind it.
UNSUPPORTED_CLAIM_PATTERNS = [
    r"\bindustry best practice\b", r"\bstudies show\b", r"\bit is well known\b",
    r"\bgenerally accepted that\b", r"\beveryone knows\b", r"\bbest-in-class practice requires\b",
]


def _bump(version, change_type):
    major, minor = (int(x) for x in str(version).split(".")[:2])
    if change_type == "major":
        return f"{major + 1}.0"
    if change_type == "minor":
        return f"{major}.{minor + 1}"
    return f"{major}.{minor}"


def _add_months(iso_date, months):
    y, m, d = (int(x) for x in iso_date.split("-"))
    total = y * 12 + (m - 1) + months
    ny, nm0 = divmod(total, 12)
    nm = nm0 + 1
    last = calendar.monthrange(ny, nm)[1]
    return date(ny, nm, min(d, last)).isoformat()


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections") or []
    if not sections:
        return ["policy draft has no sections"]
    present = {s.get("section_id") for s in sections}

    # 1. template fidelity
    for sid in REQUIRED_SECTIONS:
        if sid not in present:
            errors.append(f"missing required section: {sid}")

    # 2. no unsupported / unapproved claims
    ps = next((s for s in sections if s.get("section_id") == "policy-statements"), None)
    if ps is None:
        errors.append("policy-statements section absent; cannot verify clause sourcing")
    else:
        for c in ps.get("clauses") or []:
            if c.get("normative"):
                srcs = c.get("sources") or []
                approved = [s for s in srcs if s.get("status") == "approved" and s.get("source")]
                if c.get("unsupported") or not approved:
                    errors.append(f"unsupported normative clause {c.get('clause_id')}: no approved source mapped")
    for u in doc.get("unsupported_clauses") or []:
        errors.append(f"unsupported normative clause {u.get('clause_id')}: {u.get('reason')}")

    scan = json.dumps(sections)
    for pat in UNSUPPORTED_CLAIM_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"unsupported-claim language detected: {m.group(0)!r} (cite an approved requirement)")

    # 3. required approvals recorded
    required = doc.get("approvals_required") or []
    by_role = {a.get("role"): a for a in (doc.get("approvals") or [])}
    for role in required:
        a = by_role.get(role)
        if not a:
            errors.append(f"missing recorded approval for required role {role!r}")
        elif a.get("status") != "approved" or not a.get("approver") or not a.get("date"):
            errors.append(f"missing recorded approval for required role {role!r} "
                          f"(status={a.get('status')!r}, approver={a.get('approver')!r})")

    # 4. version + next-review tie-out
    exp_v = _bump(doc.get("prior_version", "0.0"), doc.get("change_type", "editorial"))
    if doc.get("new_version") != exp_v:
        errors.append(f"version mismatch: new_version {doc.get('new_version')!r} != expected {exp_v!r} "
                      f"for change_type {doc.get('change_type')!r}")
    eff = doc.get("proposed_effective_date")
    if eff:
        interval = TIER_REVIEW_MONTHS.get(doc.get("tier"), DEFAULT_REVIEW_MONTHS)
        exp_review = _add_months(eff, interval)
        if doc.get("next_review_date") != exp_review:
            errors.append(f"review-date mismatch: next_review_date {doc.get('next_review_date')!r} "
                          f"!= expected {exp_review!r} for tier {doc.get('tier')!r}")

    # 5. no publication / activation / filing language (draft-only).
    # Scan everything except the controlled standing note, which legitimately *negates*
    # this vocabulary ("not published, activated, or made effective").
    scanned = {k: v for k, v in doc.items() if k != "standing_note"}
    full = json.dumps(scanned)
    for pat in PUBLICATION_PATTERNS:
        m = re.search(pat, full, re.I)
        if m:
            errors.append(f"prohibited publication/activation language detected: {m.group(0)!r} "
                          f"(this skill is draft-only; never publish/activate/file)")

    # 6. standing note
    if STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note (draft-only disclaimer)")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "policy_draft_example.json"
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
