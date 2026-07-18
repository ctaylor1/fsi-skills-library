#!/usr/bin/env python3
"""Deterministic output validation for policy-renewal-reviewer.

Validates the final renewal-review pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Checks:
  1. Every fired finding has >= 1 cited evidence row.
  2. suggested_disposition equals the deterministic mapping from fired_findings.
  3. No renewal/pricing/coverage determination or action language, and no personalized
     advice (narrative + notes + finding reasons + renewal_questions).
  4. The standing disclaimer is present.
  5. context_prompts are included when any finding fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATORS = {"coverage_removed", "loss_ratio_flag"}
DISCLAIMER = ("Comparison and review evidence only; not a renewal, pricing, or coverage "
              "determination. No renewal decision or notice has been issued.")

# Determination / action / personalized-advice assertions that R2 must not make. These
# target decision and action verbs, NOT factual restatement of premium/limit/deductible data.
DETERMINATION_PATTERNS = [
    r"\b(we|i|the (carrier|insurer|company))\s+(will|shall|are going to|intend to)\s+non-?renew",
    r"\bdecline to renew\b",
    r"\bwill not (be )?renew(ed|ing)?\b",
    r"\bwe recommend non-?renewal\b",
    r"\brenewal (is|has been|will be)\s+(approved|declined|denied|bound)\b",
    r"\bapprove the renewal\b",
    r"\bbind (the )?(renewal|coverage|policy)\b",
    r"\bissue (a |the )?non-?renewal notice\b",
    r"\bset the (premium|rate|deductible)\s+(at|to)\b",
    r"\bthe (final|new) premium (is|will be)\b",
    r"\bcoverage is (denied|declined)\b",
    r"\bdeny coverage\b",
    r"\bthe claim is denied\b",
    r"\byou should (renew|switch|cancel|drop|buy|purchase|accept)\b",
    r"\bi recommend (that )?(you )?(renew|switch|cancel|drop|buy|purchase|accept)\b",
]


def _expected_disposition(fired: list) -> str:
    if len(fired) >= 3 or (ESCALATORS & set(fired)):
        return "Escalated"
    return "Review" if fired else "Routine"


def validate(pack: dict) -> list:
    errors: list = []
    findings = pack.get("findings") or []
    fired = [f["finding"] for f in findings if f.get("fired")]

    for f in findings:
        if f.get("fired"):
            ev = f.get("evidence") or []
            if not ev:
                errors.append(f"fired finding {f['finding']} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired finding {f['finding']} evidence row missing citation")

    exp = _expected_disposition(fired)
    if pack.get("suggested_disposition") != exp:
        errors.append(
            f"suggested_disposition {pack.get('suggested_disposition')!r} != deterministic "
            f"{exp!r} for fired={fired}")

    # scan free text: narrative + notes + finding reasons + renewal questions (NOT disclaimer)
    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
        + [str(f.get("reason", "")) for f in findings]
        + [str(q) for q in (pack.get("renewal_questions") or [])])
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(
                f"determination/action language detected: {m.group(0)!r} "
                f"(R2 compares and evidences; it does not decide/price/act)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " "
                                  + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if fired and not (pack.get("context_prompts")):
        errors.append("findings fired but no context_prompts included")

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
