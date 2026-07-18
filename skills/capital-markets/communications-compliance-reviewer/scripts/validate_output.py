#!/usr/bin/env python3
"""Deterministic output validation for communications-compliance-reviewer.

Validates the final communications-review pack (the calculate_or_transform core plus a
narrative) before it is presented or delivered. This is the R3 prohibited-decision screen:
the skill produces findings and a recommended disposition ONLY; a registered principal makes
the regulated decision, files, and closes the review. Checks:
  1. Every finding has >= 1 cited evidence row.
  2. recommended_disposition equals the deterministic mapping from finding severities.
  3. No approval / decision / closure / filing language (narrative + reasons + remediation).
  4. The standing disclaimer is present.
  5. remediation_prompts are included when any high/medium finding fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Advisory compliance review only; not a supervisory approval, regulated "
              "determination, or filing. A registered principal must independently review and "
              "adjudicate this communication before any use, distribution, regulatory filing, "
              "or review closure.")

# Regulated decisions/closures/filings an R3 decision-support skill must NEVER assert:
DECISION_PATTERNS = [
    r"\bapproved for (use|distribution|release|filing)\b",
    r"\bcleared for (use|distribution|release)\b",
    r"\bfit for (use|distribution)\b",
    r"\bprincipal approval (is |has been )?granted\b",
    r"\bthis communication is approved\b",
    r"\bi approve this\b",
    r"\bwe approve this\b",
    r"\bgreen-?lit\b",
    r"\bsign-?off (is )?complete\b",
    r"\breview (is )?(now )?closed\b",
    r"\bclosing (the|this) (review|case)\b",
    r"\bno further review (is )?(needed|required)\b",
    r"\bfiled with (finra|the sec)\b",
    r"\bwe (have )?filed\b",
    r"\bmeets all (regulatory )?requirements\b",
]


def _expected_disposition(findings: list[dict]) -> str:
    sevs = {str(f.get("severity")) for f in findings}
    if "high" in sevs:
        return "Escalate"
    if "medium" in sevs:
        return "Remediate"
    if "low" in sevs:
        return "Advisory"
    return "No-exceptions"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []

    for f in findings:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {f.get('finding_type')} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {f.get('finding_type')} evidence row missing citation")

    exp = _expected_disposition(findings)
    if pack.get("recommended_disposition") != exp:
        errors.append(f"recommended_disposition {pack.get('recommended_disposition')!r} != deterministic "
                      f"{exp!r} for finding severities")

    # scan free text (narrative + notes + reasons + remediation), but NOT the disclaimer field
    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
        + [str(f.get("reason", "")) for f in findings]
        + [str(f.get("remediation", "")) for f in findings]
        + [str(p) for p in (pack.get("remediation_prompts") or [])]
    )
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"decision/approval/closure/filing language detected: {m.group(0)!r} "
                          f"(R3 recommends and evidences; a registered principal decides/files/closes)")

    disc_text = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in disc_text:
        errors.append("missing standing disclaimer text")

    sevs = {str(f.get("severity")) for f in findings}
    if ("high" in sevs or "medium" in sevs) and not (pack.get("remediation_prompts")):
        errors.append("high/medium findings present but no remediation_prompts included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "review_pack_example.json"
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
