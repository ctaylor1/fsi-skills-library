#!/usr/bin/env python3
"""Deterministic output validation for fee-and-charge-reviewer.

Validates the final fee-review pack (the calculate_or_transform core + a narrative) before
it is presented or delivered. Checks:
  1. Every flagged finding (any non-`matches_disclosed` status) has >= 1 cited evidence row.
  2. review_outcome equals the deterministic mapping from the finding statuses.
  3. No legal/regulatory-violation assertion, binding refund/adjustment decision, fee
     reversal/credit action, or legal advice (R2 reviews and questions; it does not decide,
     act, or advise).
  4. The standing disclaimer is present.
  5. questions and a remediation_request_draft are included when any finding is flagged.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCREPANCY_STATUSES = {"exceeds_disclosed", "frequency_cap_exceeded", "not_in_schedule"}
QUESTION_STATUSES = {"waiver_condition_may_apply"}
CLEAN_STATUS = "matches_disclosed"
DISCLAIMER = ("Fee review and questions only; not a legal conclusion, refund decision, or "
              "legal advice, and not a reversal or credit of any charge.")

# Assertions an R2 fee review must never make (violation finding / refund decision /
# fee action / legal advice). Phrased to catch affirmative constructions; the negated
# disclaimer language above is intentionally not matched.
PROHIBITED_PATTERNS = [
    # legal / regulatory violation determination
    r"\bviolat(e|es|ed|ion|ing)\b",
    r"\bunlawful\b",
    r"\billegal\b",
    r"\bnon-?compliant\b",
    r"\bbreach(es|ed|ing)?\b",
    # binding refund / adjustment decision
    r"\bwe will refund\b",
    r"\bthe bank owes\b",
    r"\bmust (be )?refund(ed)?\b",
    r"\bentitled to (a )?refund\b",
    r"\brefund (is )?approved\b",
    r"\bapproved for (a )?refund\b",
    r"\bguaranteed refund\b",
    # fee reversal / credit action
    r"\breverse the (fee|charge)\b",
    r"\bissue (a )?credit\b",
    r"\bhas been (refunded|reversed|credited|waived)\b",
    r"\bwe (have )?(refunded|reversed|credited|waived)\b",
    # legal advice
    r"\byou should sue\b",
    r"\bgrounds for (a )?(lawsuit|legal claim)\b",
    r"\blegal claim\b",
    r"\bfile (a )?lawsuit\b",
]


def _expected_outcome(findings: list[dict]) -> str:
    statuses = {f.get("status") for f in findings}
    if statuses & DISCREPANCY_STATUSES:
        return "discrepancies_found"
    if statuses & QUESTION_STATUSES:
        return "questions_to_raise"
    return "no_discrepancies"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []
    flagged = [f for f in findings if f.get("status") != CLEAN_STATUS]

    for f in flagged:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"flagged finding {f.get('fee_id')} ({f.get('status')}) has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"flagged finding {f.get('fee_id')} evidence row missing citation")

    exp = _expected_outcome(findings)
    if pack.get("review_outcome") != exp:
        errors.append(f"review_outcome {pack.get('review_outcome')!r} != deterministic {exp!r}")

    # scan free text (narrative + notes + reasons + questions + remediation draft),
    # but NOT the disclaimer field.
    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", "")),
         str(pack.get("remediation_request_draft", ""))]
        + [str(q) for q in (pack.get("questions") or [])]
        + [str(f.get("reason", "")) for f in findings]
    )
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited assertion/action language detected: {m.group(0)!r} "
                          f"(R2 reviews and questions; it does not decide, act, or advise)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if flagged and not pack.get("questions"):
        errors.append("findings flagged but no questions included")
    if flagged and not str(pack.get("remediation_request_draft", "")).strip():
        errors.append("findings flagged but no remediation_request_draft included")

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
