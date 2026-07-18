#!/usr/bin/env python3
"""Deterministic output validation for valuation-reviewer.

Validates the final review pack (the calculate_or_transform core + a narrative) before it is
presented or delivered. Checks:
  1. Every fired finding has >= 1 cited evidence row.
  2. suggested_disposition equals the deterministic mapping from the fired findings.
  3. No valuation sign-off / override-approval / fair-value-determination / posting language
     (narrative + finding reasons + notes).
  4. The standing disclaimer is present.
  5. review_considerations are included when any finding fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATE_FINDING_COUNT = 4  # matches DEFAULT_CONFIG in calculate_or_transform.py
DISCLAIMER = ("Valuation review evidence only; not a valuation sign-off, override approval, "
              "or fair-value determination. No value has been posted or approved.")
# Affirmative determination / approval / posting assertions that R2 must not make.
# (The disclaimer's "not a valuation sign-off ..." phrasing is intentionally NOT matched.)
DETERMINATION_PATTERNS = [
    r"\bvaluation is approved\b",
    r"\bapprove(s|d)? the (valuation|override|mark|adjustment)\b",
    r"\boverride is approved\b",
    r"\boverride approved\b",
    r"\bwe approve\b",
    r"\bsigned off\b",
    r"\bpost(ed|s)? (the|this) (mark|value|adjustment) to (the )?(gl|ledger|books|system of record)\b",
    r"\bbook(ed|s)? (the|this) (mark|value|adjustment)\b",
    r"\bthe (mark|value|valuation) is (correct|accurate|fair|right)\b",
    r"\bfair value is (confirmed|correct)\b",
    r"\bconfirmed (as )?fair value\b",
    r"\bno further review (is )?(required|needed)\b",
    r"\bfinal(ized)? and approved\b",
]


def _expected_disposition(findings: list[dict]) -> str:
    fired = [f for f in findings if f.get("fired")]
    if any((f.get("severity") == "high") for f in fired) or len(fired) >= ESCALATE_FINDING_COUNT:
        return "Escalate"
    return "Findings raised" if fired else "Pass with observations"


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

    exp = _expected_disposition(findings)
    if pack.get("suggested_disposition") != exp:
        errors.append(f"suggested_disposition {pack.get('suggested_disposition')!r} != deterministic {exp!r}")

    # scan free text (narrative + reasons + notes), NOT the standalone disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/approval language detected: {m.group(0)!r} "
                          f"(R2 evidences findings, it does not sign off, approve, or post)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if any(f.get("fired") for f in findings) and not (pack.get("review_considerations")):
        errors.append("findings raised but no review_considerations included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "review_example.json"
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
