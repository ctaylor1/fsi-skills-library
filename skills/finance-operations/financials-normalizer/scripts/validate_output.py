#!/usr/bin/env python3
"""Deterministic output validation for financials-normalizer.

Validates the final normalization pack (the calculate_or_transform core + a narrative) before
it is presented or delivered. Checks:
  1. Every fired finding has >= 1 cited evidence row.
  2. suggested_readiness equals the deterministic mapping from the fired findings.
  3. No prohibited accounting/audit/investment decision or advice, and no restatement /
     posting-to-system-of-record language (narrative + finding reasons + notes).
  4. The standing disclaimer is present.
  5. review_considerations are included when any finding fired.

This enforces the R2 hard boundary: the skill maps, adjusts-with-rationale, and tie-out-checks
only. It never opines on GAAP/IFRS compliance or material correctness, issues an
accounting/audit/investment judgment or recommendation, or restates/posts figures to a system
of record. A bad fixture that contains such language must fail closed here.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATE_FINDING_COUNT = 4  # matches DEFAULT_CONFIG in calculate_or_transform.py
READY = "Model-ready"
NEEDS = "Needs mapping review"
HOLD = "Hold - tie-out break"
DISCLAIMER = ("Normalization output only; not an accounting, audit, or investment judgment, "
              "and not a system-of-record posting. Source figures are mapped and tied out, "
              "not restated or re-booked; a human reviewer must accept the normalized mapping "
              "before use.")
# Affirmative decision/advice/posting assertions that R2 must not make. The disclaimer's
# negated phrasing ("not an accounting, audit, or investment judgment ...") is intentionally
# NOT matched by any of these.
PROHIBITED_PATTERNS = [
    r"\b(us[- ]?)?(gaap|ifrs)[- ]?compliant\b",
    r"\bcompl(y|ies|iant) with (us[- ]?)?(gaap|ifrs)\b",
    r"\bmaterially (misstated|misstatement|correct|accurate|inaccurate|right)\b",
    r"\b(financials|statements) are (accurate|correct|fairly stated|reliable|right)\b",
    r"\bfairly stated in all material respects\b",
    r"\baudit opinion\b",
    r"\b(is|are) a (strong )?(buy|sell)\b",
    r"\b(buy|sell|hold|overweight|underweight) rating\b",
    r"\bwe recommend (buying|selling|investing|divesting|the investment|this investment)\b",
    r"\binvestment (advice|recommendation)\b",
    r"\b(good|bad|great|poor|strong|weak) investment\b",
    r"\bcreditworthy\b",
    r"\bpost(ed|s)?\b[\w ]*\bto (the )?(general ledger|gl|ledger|books|system of record)\b",
    r"\bre-?book (the|these|those)\b",
    r"\brestate (the|these|those)\b",
]


def _expected_readiness(findings: list[dict]) -> str:
    fired = [f for f in findings if f.get("fired")]
    if any((f.get("severity") == "high") for f in fired) or len(fired) >= ESCALATE_FINDING_COUNT:
        return HOLD
    return NEEDS if fired else READY


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []

    for f in findings:
        if f.get("fired"):
            ev = f.get("evidence") or []
            if not ev:
                errors.append(f"fired finding {f.get('check')} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired finding {f.get('check')} evidence row missing citation")

    exp = _expected_readiness(findings)
    if pack.get("suggested_readiness") != exp:
        errors.append(f"suggested_readiness {pack.get('suggested_readiness')!r} != deterministic {exp!r}")

    # scan free text (narrative + reasons + notes), NOT the standalone disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/advice language detected: {m.group(0)!r} "
                          f"(R2 normalizes and tie-out-checks; it does not judge, advise, restate, or post)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if any(f.get("fired") for f in findings) and not (pack.get("review_considerations")):
        errors.append("findings raised but no review_considerations included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "normalized_example.json"
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
