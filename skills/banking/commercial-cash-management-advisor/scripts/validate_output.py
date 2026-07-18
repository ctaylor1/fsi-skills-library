#!/usr/bin/env python3
"""Deterministic output validation for commercial-cash-management-advisor.

Validates the final advisory pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. Checks:
  1. Every recommended service has >= 1 cited evidence row.
  2. Every recommended service carries at least one implementation question.
  3. engagement_priority equals the deterministic mapping from the recommended set.
  4. No binding product/pricing/credit/investment DECISION or advice language (the R2 hard
     boundary) anywhere in the narrative, rationales, notes, or assumptions.
  5. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATORS = {"check_positive_pay", "ach_debit_block", "overdraft_liquidity_referral"}
DISCLAIMER = ("Advisory analysis only; not a binding product, pricing, credit, or investment "
              "decision. No account or service has been opened, changed, or priced.")
# Binding decisions / commitments / advice an R2 advisory skill must never make. It may
# RECOMMEND services and pose questions; it may not approve credit, commit pricing, guarantee
# outcomes, give investment advice, or open/enroll/price a service.
PROHIBITED_PATTERNS = [
    r"\byou are approved\b", r"\bapproved for (a |an )?(credit|line|loan|overdraft|facility)\b",
    r"\bcredit is approved\b", r"\bwe (will|can|hereby) approve\b", r"\bloan is approved\b",
    r"\bguaranteed (savings|returns?|yield|rate)\b", r"\bwe guarantee\b", r"\bguarantee(s|d)? you\b",
    r"\bfinal pricing\b", r"\block(ed|ing)?[- ]in (rate|pricing)\b", r"\bwe commit to\b",
    r"\bbinding (offer|quote|commitment|price)\b", r"\bthis (rate|price) is final\b",
    r"\bas your (financial|investment) advisor\b", r"\byou should invest\b",
    r"\bwe advise (you )?to invest\b", r"\bthis is investment advice\b", r"\bguaranteed return\b",
    r"\bwe have opened\b", r"\bopen(ed|ing)? the account for you\b", r"\benroll(ed|ing)? you in\b",
    r"\bwe have enrolled\b", r"\bwe('ve| have) priced\b",
]


def _expected_priority(recommended: list[str]) -> str:
    names = set(recommended)
    if len(names) >= 3 or (ESCALATORS & names):
        return "Priority-review"
    return "Recommended-review" if names else "Informational"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    recs = pack.get("recommendations") or []
    recommended = [r for r in recs if r.get("recommended")]
    rec_names = [r["service"] for r in recommended]

    for r in recommended:
        ev = r.get("evidence") or []
        if not ev:
            errors.append(f"recommended service {r.get('service')} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"recommended service {r.get('service')} evidence row missing citation")
        if not (r.get("implementation_questions") or []):
            errors.append(f"recommended service {r.get('service')} has no implementation questions")

    exp = _expected_priority(rec_names)
    if pack.get("engagement_priority") != exp:
        errors.append(f"engagement_priority {pack.get('engagement_priority')!r} != deterministic "
                      f"{exp!r} for recommended={rec_names}")

    # scan free text (narrative + notes + rationales + assumptions), NOT the disclaimer field
    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
        + [str(r.get("rationale", "")) for r in recs]
        + [str(a) for a in (pack.get("assumptions") or [])])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"binding-decision/advice language detected: {m.group(0)!r} "
                          "(R2 recommends and questions; it does not decide, commit, or advise)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer")

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
