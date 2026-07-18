#!/usr/bin/env python3
"""Deterministic output validation for portfolio-exposure-analyzer.

Validates the final exposure pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. This is the R2 prohibited-decision screen: it fails closed if the
pack drifts from evidenced exposure findings into a mandate-compliance determination, an
investment recommendation, or a trade/portfolio action.

Checks:
  1. Every finding has >= 1 cited evidence row.
  2. suggested_priority equals the deterministic mapping from findings.
  3. No mandate-determination / trade-action / investment-advice language
     (narrative + notes + finding reasons).
  4. The standing disclaimer is present.
  5. considerations are included when any finding fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Exposure analysis and evidence only; not a mandate-compliance determination or "
              "investment advice. No trade or portfolio action has been taken or recommended.")

# Positive determination / action / advice assertions that an R2 analyzer must not make:
DETERMINATION_PATTERNS = [
    r"\bmandate breach\b", r"\bin breach of\b", r"\bbreach(?:es|ed)? the (?:mandate|guideline|limit)\b",
    r"\bviolat(?:es|ed|ion of) (?:the )?(?:mandate|guideline|limit|restriction)\b",
    r"\bnon-?compliant\b", r"\bconfirmed (?:breach|violation)\b",
    r"\brebalanc(?:e|es|ing)\b", r"\bexecute (?:the |this )?(?:trade|order|rebalanc)",
    r"\bplace (?:the |a |this )?(?:order|trade)\b",
    r"\b(?:we )?recommend (?:selling|buying|trimming|reducing|increasing|divesting|hedging)\b",
    r"\byou should (?:buy|sell|trim|reduce|increase|divest|hedge|invest)\b",
    r"\bsell down\b", r"\btrim (?:the |this )?position\b", r"\bdivest\b",
    r"\bguaranteed (?:return|profit)\b",
]


def _expected_priority(findings: list[dict]) -> str:
    escalator = any(f.get("band") == "over_hard" for f in findings) or \
        any(f.get("dimension") == "liquidity" for f in findings)
    n = len(findings)
    if escalator or n >= 3:
        return "Elevated"
    return "Review" if n >= 1 else "Informational"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []

    for f in findings:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {f.get('dimension')}:{f.get('bucket')} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {f.get('dimension')}:{f.get('bucket')} evidence row missing citation")

    exp = _expected_priority(findings)
    if pack.get("suggested_priority") != exp:
        fired = [f"{f.get('dimension')}:{f.get('bucket')}" for f in findings]
        errors.append(f"suggested_priority {pack.get('suggested_priority')!r} != deterministic {exp!r} for findings={fired}")

    # scan free text (narrative + notes + finding reasons), but NOT the disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/action language detected: {m.group(0)!r} (R2 evidences, does not decide/act)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if findings and not pack.get("considerations"):
        errors.append("findings present but no considerations included")

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
