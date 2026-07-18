#!/usr/bin/env python3
"""Deterministic output validation for call-quality-compliance-reviewer.

Validates the final quality-review pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Checks:
  1. Every fired finding has >= 1 cited evidence row.
  2. suggested_disposition equals the deterministic mapping from the fired findings'
     severities.
  3. No misconduct/regulatory-breach determination, disciplinary/action, or personalized
     advice language (narrative + notes + finding reasons).
  4. The standing disclaimer is present.
  5. considerations (review prompts) are included when any finding fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Quality-review evidence only; not a determination of misconduct, a "
              "regulatory breach, or a disciplinary decision. No action has been taken.")

# Positive determination / action / advice assertions that R2 must not make. The reviewer
# evidences findings and suggests a disposition band for a human; it never adjudicates
# misconduct, declares a breach, decides discipline, files, or gives personalized advice.
DETERMINATION_PATTERNS = [
    r"\bconfirmed misconduct\b", r"\bmisconduct is confirmed\b",
    r"\bcommitted (a )?(regulatory |compliance )?(breach|violation)\b",
    r"\bviolated (the )?regulation\b", r"\bregulatory breach confirmed\b",
    r"\bis a reportable breach\b", r"\breportable breach\b",
    r"\bmust be terminated\b", r"\bterminate the agent\b", r"\bfire the agent\b",
    r"\bdisciplinary action\b", r"\bissue (a )?(formal )?warning\b",
    r"\bfail the agent\b", r"\bagent failed the (call|review|interaction)\b",
    r"\breport (this|it|the breach) to the (regulator|cfpb|fca|finra|occ)\b",
    r"\bfile (a )?(complaint|sar|report) with\b",
    r"\b(recommend|advise) (you|the customer) (buy|sell|invest)\b",
]

CRITICAL = {"recording_consent_disclosure", "identity_authentication",
            "required_disclosures", "prohibited_language", "fair_treatment_vulnerability"}


def _expected_disposition(findings: list) -> str:
    fired = [f for f in findings if f.get("fired")]
    if any(f.get("severity") == "critical" or f.get("check") in CRITICAL for f in fired):
        return "Compliance review required"
    return "Coaching recommended" if fired else "Meets expectations"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []
    fired = [f for f in findings if f.get("fired")]

    for f in fired:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"fired finding {f.get('check')} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"fired finding {f.get('check')} evidence row missing citation")

    exp = _expected_disposition(findings)
    if pack.get("suggested_disposition") != exp:
        errors.append(f"suggested_disposition {pack.get('suggested_disposition')!r} != deterministic {exp!r}")

    # scan free text (narrative + notes + reasons), but NOT the disclaimer/disposition fields
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/action/advice language detected: {m.group(0)!r} (R2 evidences, does not adjudicate/act)")

    combined = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in combined:
        errors.append("missing standing disclaimer text")

    if fired and not pack.get("considerations"):
        errors.append("findings fired but no considerations (review prompts) included")

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
