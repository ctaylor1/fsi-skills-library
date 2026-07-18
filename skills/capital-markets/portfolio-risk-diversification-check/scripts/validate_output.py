#!/usr/bin/env python3
"""Deterministic output validation for portfolio-risk-diversification-check.

Validates the final diversification profile (the calculate_or_transform core + a narrative)
before it is presented or delivered. This is the R2 tier guardrail: the skill analyzes and
educates, it does NOT advise. Checks:
  1. Every flagged check has >= 1 cited evidence row.
  2. diversification_band equals the deterministic mapping from flagged_checks.
  3. No personalized-investment-advice / recommendation / forecast language (narrative +
     notes + check reasons).
  4. The standing educational disclaimer is present.
  5. educational_prompts are included when any check flagged.

Usage:
  python validate_output.py profile.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATORS = {"single_name_concentration", "correlation_concentration"}
DISCLAIMER = ("Educational risk analysis only; not personalized investment advice or a "
             "recommendation to buy, sell, or hold any security.")
# Personalized-advice / recommendation / forecast assertions an R2 analytical skill must
# never make. Patterns require directive context so factual description of concentration
# (e.g. "concentrated in technology", "buy, sell, or hold" inside the disclaimer) passes.
ADVICE_PATTERNS = [
    r"\byou should\b", r"\byou ought to\b", r"\bwe recommend\b", r"\bi recommend\b",
    r"\bour recommendation\b", r"\bmy recommendation\b",
    r"\brecommend (buying|selling|allocating|rebalancing|reducing|increasing|trimming|adding|holding|moving|shifting)\b",
    r"\brebalanc(e|ing)\b", r"\btrim (your|the|this|these)\b",
    r"\b(buy|sell) (this|these|the|more|into|now)\b",
    r"\bgood investment\b", r"\bbad investment\b", r"\bbest investment\b",
    r"\bstrong (buy|sell)\b", r"\bprice target\b", r"\bguaranteed returns?\b",
    r"\bwill (outperform|beat|rise|fall|gain|drop|increase|decrease|double)\b",
    r"\bexpected to (rise|fall|outperform|beat|gain|drop|surge)\b", r"\btime the market\b",
    r"\bshould (overweight|underweight|allocate|reduce|increase|move|shift|diversify|sell|buy|hold)\b",
    r"\b(increase|reduce|cut) your (allocation|exposure|position|holding|stake)\b",
    r"\bshift (into|out of|toward|away from)\b",
    r"\bmove (into|out of) (bonds|equities|cash|stocks|gold)\b",
    r"\bsuitable for you\b", r"\bright for your portfolio\b",
]


def _expected_band(flagged: list[str]) -> str:
    if len(flagged) >= 3 or (ESCALATORS & set(flagged)):
        return "Highly concentrated"
    return "Moderately concentrated" if flagged else "Well-diversified"


def validate(profile: dict) -> list[str]:
    errors: list[str] = []
    checks = profile.get("checks") or []
    flagged = profile.get("flagged_checks")
    if flagged is None:
        flagged = [c["check"] for c in checks if c.get("flagged")]

    # 1. evidence + citation on every flagged check
    by_name = {c.get("check"): c for c in checks}
    for name in flagged:
        c = by_name.get(name)
        if c is None:
            errors.append(f"flagged check {name} not present in checks[]")
            continue
        ev = c.get("evidence") or []
        if not ev:
            errors.append(f"flagged check {name} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"flagged check {name} evidence row missing citation")

    # 2. deterministic band tie-out
    exp = _expected_band(flagged)
    if profile.get("diversification_band") != exp:
        errors.append(f"diversification_band {profile.get('diversification_band')!r} != "
                      f"deterministic {exp!r} for flagged={flagged}")

    # 3. no advice/recommendation/forecast language (scan free text, NOT the disclaimer field)
    text = " ".join([str(profile.get("narrative", "")), str(profile.get("notes", ""))]
                    + [str(c.get("reason", "")) for c in checks])
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"investment-advice language detected: {m.group(0)!r} "
                          f"(R2 analyzes and educates, it does not advise)")

    # 4. standing educational disclaimer present
    combined = (str(profile.get("narrative", "")) + " " + str(profile.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in combined:
        errors.append("missing educational disclaimer text")

    # 5. educational prompts when anything flagged
    if flagged and not profile.get("educational_prompts"):
        errors.append("checks flagged but no educational_prompts included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "profile_example.json"
        profile = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        profile = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        profile = json.loads(sys.stdin.read())
    errors = validate(profile)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
