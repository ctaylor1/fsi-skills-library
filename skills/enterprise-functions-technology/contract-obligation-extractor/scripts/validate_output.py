#!/usr/bin/env python3
"""Deterministic output validation for contract-obligation-extractor.

Enforces the Draft & package guardrails before the assembled obligation register is presented:
  1. All required template sections are present (matches assets/output-template.md).
  2. No unsupported/unapproved claims: every asserted (extracted/ambiguous/conflict) entry
     carries a clause citation.
  3. Required human reviews are recorded (type + reviewer_role + date + citation) and
     delivery approval is flagged as required; missing reviews appear as outstanding open items.
  4. No legal-advice/interpretation, completeness/exhaustiveness, or send/submit/execute/
     deliver language.
  5. assembly_status is 'draft-extracted' (never certified/complete/final).
  6. The standing note is present.

Usage: python validate_output.py register.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

# Canonical register sections; the human-facing render in assets/output-template.md mirrors
# these (versioned contract). All must appear in the manifest's `sections`.
REQUIRED_SECTIONS = [
    "register_summary", "contract_profile", "obligations", "key_dates", "service_levels",
    "rights_restrictions", "renewal_termination", "data_terms", "dependencies", "reviews",
    "open_items", "source_index",
]
ASSERTED_STATUSES = {"extracted", "ambiguous", "conflict"}
STANDING_NOTE = ("Draft obligation register for human review only. This register is an "
                 "extraction aid, not legal advice or a completeness certification, and it "
                 "has not been delivered, executed, or acted on. Every obligation must be "
                 "verified against the source contract.")

# Claims an extractor must NEVER make: legal advice/interpretation, breach or enforceability
# conclusions, or personalized recommendations.
LEGAL_ADVICE_PATTERNS = [
    r"\byou (may|can|must|should) (terminate|renew|withhold|refuse|sue)\b",
    r"\bis (legally )?enforceable\b", r"\b(un|not )enforceable\b",
    r"\bwe recommend\b", r"\bwe advise\b", r"\bour advice\b", r"\blegal opinion\b",
    r"\byou are (not )?liable\b", r"\bin breach of\b", r"\bhas breached\b",
    r"\bbreach determination\b", r"\bis (valid|void)\b",
]
# Claims that overstate coverage / assert the contract is silent or the register is done.
COMPLETENESS_PATTERNS = [
    r"\ball obligations (have been )?(captured|extracted|identified)\b",
    r"\bregister is complete\b", r"\bcomplete (list|register) of\b", r"\bfully extracted\b",
    r"\bexhaustive\b", r"\bno (other|further) (obligations|restrictions|dependencies|renewals)\b",
    r"\bthe contract (contains|has) no\b", r"\bnothing (further|else) to (review|extract)\b",
    r"\bno open items\b",
]
# Draft-only: never sent/submitted/executed/delivered.
DELIVERY_PATTERNS = [
    r"\bsubmitted to\b", r"\bsent to\b", r"\bfiled with\b", r"\btransmitted to\b",
    r"\bdelivered to\b", r"\bexecuted and returned\b", r"\bsigned and returned\b",
    r"\bcountersigned\b", r"\bwe have (sent|submitted|delivered)\b",
]


def _entries_with_status(sections):
    """Yield every dict in `sections` that carries a 'status' field (top level only)."""
    for key, val in sections.items():
        items = val if isinstance(val, list) else [val]
        for e in items:
            if isinstance(e, dict) and "status" in e:
                yield key, e


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections")
    if not isinstance(sections, dict):
        return ["register output has no 'sections' object"]

    # 1. required sections present
    for sec in REQUIRED_SECTIONS:
        if sec not in sections:
            errors.append(f"missing required register section '{sec}'")

    # 2. no unsupported claims: asserted entries must be cited
    for sec, e in _entries_with_status(sections):
        if e.get("status") in ASSERTED_STATUSES and not e.get("citation"):
            errors.append(f"unsupported claim: {sec} entry {e.get('extraction_id') or e.get('category')!r} "
                          f"asserts status {e.get('status')!r} without a clause citation")

    # 3. reviews recorded well-formed; delivery approval flagged
    reviews = sections.get("reviews")
    if not isinstance(reviews, dict) or "recorded" not in reviews:
        errors.append("reviews section missing or lacks a 'recorded' list")
    else:
        for rec in reviews.get("recorded") or []:
            for field in ("type", "reviewer_role", "date", "citation"):
                if not rec.get(field):
                    errors.append(f"recorded review {rec.get('type','?')!r} missing '{field}'")
    if doc.get("human_approval_required_before_delivery") is not True:
        errors.append("human_approval_required_before_delivery must be true (external-delivery posture)")

    # 4. forbidden language
    scan = json.dumps(doc)
    for label, patterns in (("legal-advice/interpretation", LEGAL_ADVICE_PATTERNS),
                            ("completeness/exhaustiveness", COMPLETENESS_PATTERNS),
                            ("delivery/submission", DELIVERY_PATTERNS)):
        for pat in patterns:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"prohibited {label} language detected: {m.group(0)!r} "
                              f"(the extractor only assembles a cited draft)")

    # 5. assembly status must be draft
    if doc.get("assembly_status") != "draft-extracted":
        errors.append(f"assembly_status must be 'draft-extracted', got {doc.get('assembly_status')!r}")

    # 6. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "register_example.json"
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
