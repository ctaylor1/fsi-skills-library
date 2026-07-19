#!/usr/bin/env python3
"""Deterministic output validation for beneficial-ownership-verifier.

Validates the final verification pack (the calculate_or_transform core + a narrative) before
it is presented to the analyst or attached to a case. This is the R3 fail-closed screen.
Checks:
  1. Every identified UBO (ownership + control prong) has >= 1 cited evidence row.
  2. readiness equals the deterministic mapping from the gap set.
  3. readiness is one of the allowed bands.
  4. No decision / closure / filing / approval language anywhere in the free text
     (narrative, notes, gap details, UBO reasons). R3 recommends and evidences; it never
     decides, approves, closes, or files.
  5. The standing disclaimer is present verbatim.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Verification evidence and recommendations only; not a beneficial-ownership "
              "determination or KYC/onboarding approval. No case has been approved, closed, "
              "or filed, and no system of record has been updated. Human adjudication is required.")

ALLOWED_READINESS = {"Complete-for-review", "Remediation-needed", "Escalate"}
BLOCKING = {"undeclared_owner", "undeclared_control", "control_prong_unsatisfied",
            "declared_not_supported", "circular_ownership"}
REMEDIABLE = {"missing_document", "expired_document", "pct_mismatch", "ownership_over_100"}

# Regulated decisions / actions that R3 must NOT assert (it recommends + evidences only):
DECISION_PATTERNS = [
    r"\bapprov(e|ed|ing) (the |this )?(customer|onboarding|entity|relationship|account|application)\b",
    r"\bapproved for (onboarding|the account|the relationship)\b",
    r"\bcleared for (onboarding|approval|the account|the relationship)\b",
    r"\breject(ed|ing)? (the |this )?(customer|onboarding|application|entity|relationship)\b",
    r"\bonboard (the |this )?(customer|entity|client|relationship)\b",
    r"\bclose (the |this )?(case|kyc|review|file)\b",
    r"\bfil(e|ed|ing) (a |the )?(boi|beneficial[- ]ownership|sar|report)\b",
    r"\bbeneficial owner(ship)? (is|are) (confirmed|verified|determined|established)\b",
    r"\bidentit(y|ies) (is|are) (confirmed|verified)\b",
    r"\bownership (is|has been) (verified|confirmed)\b",
    r"\bwe (should |will |can )?(approve|onboard|clear|reject|file|close)\b",
    r"\bkyc (is|has been) (complete|cleared|passed|approved)\b",
]


def _expected_readiness(gaps: list[dict]) -> str:
    types = {g.get("type") for g in gaps}
    if types & BLOCKING:
        return "Escalate"
    if types & REMEDIABLE:
        return "Remediation-needed"
    return "Complete-for-review"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    ubos = pack.get("ubos") or []
    for u in ubos:
        ev = u.get("evidence") or []
        cited = [r for r in ev if (r.get("citation") or "").strip()]
        if not cited:
            errors.append(f"identified UBO {u.get('person_id')} has no cited evidence")

    gaps = pack.get("gaps") or []
    readiness = pack.get("readiness")
    if readiness not in ALLOWED_READINESS:
        errors.append(f"readiness {readiness!r} not in {sorted(ALLOWED_READINESS)}")
    exp = _expected_readiness(gaps)
    if readiness != exp:
        errors.append(f"readiness {readiness!r} != deterministic {exp!r} for gap types {sorted({g.get('type') for g in gaps})}")

    # scan free text but exclude the standing disclaimer (which legitimately negates trigger words)
    parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    parts += [str(u.get("reason", "")) for u in ubos]
    parts += [str(g.get("detail", "")) for g in gaps]
    text = " ".join(parts)
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"decision/closure/filing language detected: {m.group(0)!r} "
                          "(R3 recommends and evidences; it does not decide, approve, close, or file)")

    combined = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in combined:
        errors.append("missing standing disclaimer text")

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
