#!/usr/bin/env python3
"""Deterministic output validation for coverage-gap-analyzer.

Validates the final coverage-gap analysis (the calculate_or_transform core + a narrative)
before it is presented or delivered. Checks:
  1. Every fired gap has >= 1 evidence row with an exposure citation AND a policy citation.
  2. review_priority equals the deterministic mapping from fired_gaps.
  3. No coverage/eligibility/claim determination and no insurance/legal advice language
     (narrative + gap reasons + notes).
  4. The standing disclaimer is present.
  5. review_prompts are included when any gap fired.

This is the R2 tier guardrail: the skill evidences gaps and suggests a review priority; it
never determines coverage, decides eligibility, or advises the customer to transact.

Usage:
  python validate_output.py analysis.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATORS = {"missing_coverage", "exclusion_match"}
DISCLAIMER = ("Coverage-gap analysis only; not a coverage, eligibility, or claim "
              "determination and not insurance or legal advice. Consult a licensed "
              "insurance professional before acting.")
# Coverage/eligibility/claim determinations and personalized advice an R2 skill must not make.
DETERMINATION_PATTERNS = [
    r"\byou(?:'re| are)(?: fully| now)? covered\b",
    r"\bfully covered\b",
    r"\bthis (?:claim|loss|event|incident) (?:is|would be|will be|is not|won'?t be) covered\b",
    r"\b(?:claim|loss|event) (?:is|will be|would be) (?:denied|paid|approved|covered)\b",
    r"\bwill be denied\b",
    r"\bwe (?:deny|approve|cover|will cover|will pay)\b",
    r"\bguaranteed (?:to be )?covered\b",
    r"\byou (?:should|must|need to) (?:buy|purchase|drop|cancel|switch|replace)\b",
    r"\bi recommend (?:that )?you (?:buy|purchase|drop|cancel|increase|switch|replace)\b",
    r"\byou (?:have|don'?t have|do not have) (?:adequate|sufficient|enough) coverage\b",
    r"\bthis policy is (?:the best|sufficient|adequate|right for you|all you need)\b",
    r"\byou(?:'re| are) (?:eligible|not eligible) for\b",
    r"\bthis (?:is|constitutes) (?:legal|insurance) advice\b",
]


def _expected_priority(fired: list[str]) -> str:
    if len(fired) >= 3 or (ESCALATORS & set(fired)):
        return "Elevated"
    return "Review" if fired else "Informational"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    gaps = pack.get("gaps") or []
    fired = [g["gap_type"] for g in gaps if g.get("fired")]

    for g in gaps:
        if g.get("fired"):
            ev = g.get("evidence") or []
            if not ev:
                errors.append(f"fired gap {g['gap_type']} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired gap {g['gap_type']} evidence row missing exposure citation")
                if not (row.get("policy_citation") or "").strip():
                    errors.append(f"fired gap {g['gap_type']} evidence row missing policy citation")

    exp = _expected_priority(fired)
    if pack.get("review_priority") != exp:
        errors.append(f"review_priority {pack.get('review_priority')!r} != deterministic {exp!r} for fired={fired}")

    # scan free text (narrative + reasons + notes), but NOT the disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(g.get("reason", "")) for g in gaps])
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/advice language detected: {m.group(0)!r} "
                          "(R2 evidences gaps, does not determine coverage or advise)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if fired and not pack.get("review_prompts"):
        errors.append("gaps fired but no review_prompts included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
