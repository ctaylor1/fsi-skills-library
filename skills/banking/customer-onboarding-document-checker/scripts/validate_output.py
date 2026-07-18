#!/usr/bin/env python3
"""Deterministic output validation for customer-onboarding-document-checker.

Validates the final completeness pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Checks:
  1. Every fired check has >= 1 cited evidence row.
  2. readiness_status equals the deterministic mapping from the fired checks + severities.
  3. No onboarding-approval / identity-verification / KYC-CIP-sanctions determination or
     account-action language (narrative + notes + check reasons).
  4. The standing disclaimer is present.
  5. remediation prompts are included when any check fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Completeness check only; not an onboarding approval, identity verification, "
              "or KYC/CIP determination. No account has been opened.")
# Affirmative determination / approval / action assertions that an R2 check must not make.
# (Written so the negated wording inside the standing disclaimer does NOT match.)
PROHIBITED_PATTERNS = [
    r"\bapproved for onboarding\b", r"\bonboarding (is )?approved\b",
    r"\baccount (is )?approved\b", r"\bapprove the account\b",
    r"\bcleared to (open|onboard)\b", r"\bclear(ed)? to onboard\b",
    r"\beligible (to onboard|for onboarding)\b",
    r"\bidentity (is )?(verified|confirmed)\b", r"\bwe (have )?verified (the )?identity\b",
    r"\bcustomer (is )?verified\b", r"\bapplicant (is )?verified\b",
    r"\bkyc (passed|cleared|complete|satisfied)\b",
    r"\bcip (passed|cleared|complete|satisfied)\b",
    r"\bopen the account\b", r"\bonboard the customer\b",
    r"\bno sanctions (match|hit|concern|risk)\b", r"\bsanctions clear\b",
    r"\bnot a pep\b", r"\bwaive (the|this) (requirement|document|exception|finding)\b",
]


def _expected_readiness(checks: list) -> str:
    # missing severity fails closed to "blocking"
    blocking = any(c.get("fired") and c.get("severity", "blocking") == "blocking" for c in checks)
    advisory = any(c.get("fired") and c.get("severity") == "advisory" for c in checks)
    return "Not-ready" if blocking else ("Ready-with-advisories" if advisory else "Ready")


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    checks = pack.get("checks") or []

    for c in checks:
        if c.get("fired"):
            ev = c.get("evidence") or []
            if not ev:
                errors.append(f"fired check {c.get('check')} has no evidence")
            for row in ev:
                if not str(row.get("citation", "")).strip():
                    errors.append(f"fired check {c.get('check')} evidence row missing citation")

    exp = _expected_readiness(checks)
    if pack.get("readiness_status") != exp:
        errors.append(f"readiness_status {pack.get('readiness_status')!r} != deterministic {exp!r}")

    # scan free text (narrative + notes + check reasons); the disclaimer FIELD is excluded.
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(c.get("reason", "")) for c in checks])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/action language detected: {m.group(0)!r} "
                          "(R2 checks completeness; it does not approve, verify identity, or open accounts)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    fired = [c for c in checks if c.get("fired")]
    if fired and not (pack.get("remediation")):
        errors.append("checks fired but no remediation prompts included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "checks_example.json"
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
