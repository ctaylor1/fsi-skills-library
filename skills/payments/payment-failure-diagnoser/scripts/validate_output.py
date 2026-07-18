#!/usr/bin/env python3
"""Deterministic output validation for payment-failure-diagnoser.

Validates the final diagnosis pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. Checks:
  1. root_cause has a category and >= 1 cited evidence row.
  2. Every trace leg carrying a reason_code is interpreted (non-empty category).
  3. suggested_route equals the deterministic mapping from root_cause.category.
  4. retry_eligible equals the deterministic policy for root_cause.category.
  5. No payment-action or fraud/sanctions-determination language (narrative + notes + leg
     meanings + root-cause meaning). R2 diagnoses and routes; it does not act or decide.
  6. The standing disclaimer is present.
  7. Cautions are present when retry_eligible or a duplicate/screening-hold risk applies.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Diagnostic assessment only; not a payment instruction, repair, or "
              "fraud/sanctions determination. No payment has been modified, resubmitted, "
              "reversed, or released.")

# Kept in lockstep with calculate_or_transform.py (see references/domain-rules.md).
ROUTE_BY_CATEGORY = {
    "settled": "none",
    "insufficient_funds": "customer-remediation",
    "expired_or_restricted": "customer-remediation",
    "authorization_decline": "customer-remediation",
    "system_timeout": "payment-exception-investigator",
    "format_reference_error": "payment-repair-assistant",
    "account_invalid": "payment-exception-investigator",
    "duplicate": "payment-exception-investigator",
    "screening_hold": "payment-exception-investigator",
    "recall_return": "payment-exception-investigator",
    "unknown": "payment-exception-investigator",
    "message_unparseable": "iso-20022-message-interpreter",
    "suspected_fraud": "payment-fraud-case-investigator",
    "unauthorized_return": "dispute-operations-assistant",
}
RETRY_ELIGIBLE = {
    "insufficient_funds", "expired_or_restricted", "authorization_decline", "system_timeout",
}
CAUTION_REQUIRED = {"system_timeout", "duplicate", "screening_hold"}

# Payment-action / determination assertions an R2 diagnoser must not make:
PROHIBITED_PATTERNS = [
    r"\breverse the payment\b", r"\bresubmit the payment\b", r"\bre-?present the payment\b",
    r"\brelease the (payment|hold|funds)\b", r"\bcancel the payment\b",
    r"\brepair(ed|ing)? the (message|payment|instruction)\b",
    r"\brefund the (customer|payer|merchant)\b", r"\bprocess (a|the) refund\b",
    r"\breturn the funds\b", r"\bclear the (sanctions )?hold\b",
    r"\bapprove the (payment|refund|reversal)\b",
    r"confirmed sanctions", r"sanctions (match )?confirmed", r"\btrue (sanctions )?hit\b",
    r"\bthis is fraud\b", r"\bconfirmed fraud\b", r"\bfraudulent transaction\b",
]


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    rc = pack.get("root_cause") or {}
    category = rc.get("category")
    if not category:
        errors.append("root_cause.category missing")
    ev = rc.get("evidence") or []
    if not ev:
        errors.append("root_cause has no evidence")
    for row in ev:
        if not (row.get("citation") or "").strip():
            errors.append("root_cause evidence row missing citation")

    for r in pack.get("trace") or []:
        if r.get("reason_code") and not (r.get("category") or "").strip():
            errors.append(f"trace leg seq={r.get('seq')} has reason_code but no interpreted category")

    if category:
        exp_route = ROUTE_BY_CATEGORY.get(category)
        if pack.get("suggested_route") != exp_route:
            errors.append(f"suggested_route {pack.get('suggested_route')!r} != deterministic "
                          f"{exp_route!r} for category {category!r}")
        exp_retry = category in RETRY_ELIGIBLE
        if bool(pack.get("retry_eligible")) != exp_retry:
            errors.append(f"retry_eligible {pack.get('retry_eligible')!r} != deterministic "
                          f"{exp_retry} for category {category!r}")
        if (exp_retry or category in CAUTION_REQUIRED) and not (pack.get("cautions")):
            errors.append(f"category {category!r} requires a caution but none present")

    # scan free text (narrative + notes + leg meanings + root-cause meaning), NOT disclaimer
    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", "")), str(rc.get("meaning", ""))]
        + [str(r.get("meaning", "")) for r in (pack.get("trace") or [])]
    )
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/action language detected: {m.group(0)!r} "
                          f"(R2 diagnoses and routes, does not act/decide)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "diagnosis_example.json"
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
