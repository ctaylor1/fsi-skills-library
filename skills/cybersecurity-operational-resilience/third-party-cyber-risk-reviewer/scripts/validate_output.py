#!/usr/bin/env python3
"""Deterministic output validation for third-party-cyber-risk-reviewer.

Validates the final supplier cyber-risk review (the calculate_or_transform core + a
narrative) before it is presented or delivered. This is the R3 prohibited-decision screen:
it fails closed if the review reads as a decision instead of decision support. Checks:
  1. Every fired finding has >= 1 cited evidence row.
  2. suggested_residual_tier equals the deterministic mapping from findings + engagement.
  3. suggested_residual_tier is one of Low/Moderate/High/Critical.
  4. No supplier-decision / risk-acceptance / closure / filing / sign-off language
     (narrative + notes + finding reasons). R3 recommends; a human adjudicates.
  5. The standing disclaimer is present.
  6. Considerations (compensating-control / adjudication notes) present when findings fired.

Usage:
  python validate_output.py review.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ORDER = ["Low", "Moderate", "High", "Critical"]
SEV_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
BASE_BY_TOP = {0: "Low", 1: "Low", 2: "Moderate", 3: "High"}
DISCLAIMER = ("Findings and evidence only; not a supplier approval, risk acceptance, or "
              "onboarding decision. A human risk owner must adjudicate. No system of record "
              "has been updated.")

# Autonomous regulated decisions / closures / filings an R3 review must NOT make:
DECISION_PATTERNS = [
    r"\bapprove(d|s)? (the |this )?(supplier|vendor|onboarding|engagement|third[- ]party)\b",
    r"\b(supplier|vendor|third[- ]party) (is|are) (hereby )?approved\b",
    r"\bcleared for onboarding\b",
    r"\bclear(ed)? (the |this )?(supplier|vendor)\b",
    r"\breject(ed|s)? (the |this )?(supplier|vendor|engagement)\b",
    r"\bonboarding (is |has been )?approved\b",
    r"\brisk (is |has been )?accepted\b",
    r"\bwe accept the (residual )?risk\b",
    r"\b(grant|granted|granting) (an? )?exception\b",
    r"\bexception (is |has been )?(granted|approved)\b",
    r"\bsign(ed)?[ -]off\b",
    r"\bclose(d|s)? (the |this )?(assessment|case|review|finding)\b",
    r"\bassessment (is |has been )?(closed|complete)\b",
    r"\bfiled? (the |a )?(assessment|attestation|report|determination)\b",
    r"\battest(ed|s)? that\b",
    r"\bfinal (approval|determination|decision)\b",
    r"\bcontract (is |has been )?(executed|signed|terminated)\b",
    r"\bterminate the (contract|supplier|vendor|relationship)\b",
    r"\bwaive(d|s)? (the |this )?(finding|requirement|control|risk)\b",
    r"\bwe (should |will |can )?(onboard|approve|reject|terminate)\b",
]


def _amplified(eng: dict) -> bool:
    return (eng.get("criticality") == "critical"
            or bool(eng.get("hosts_regulated_data"))
            or eng.get("data_classification") in ("Highly Confidential", "Restricted"))


def _expected_tier(findings: list, eng: dict) -> str:
    """Mirror of calculate_or_transform.residual_tier — recomputed independently."""
    fired = [f for f in findings if f.get("fired")]
    if not fired:
        return "Low"
    top = max(SEV_RANK.get(f.get("severity", "low"), 0) for f in fired)
    idx = ORDER.index(BASE_BY_TOP[top])
    if len(fired) >= 4:
        idx = min(idx + 1, 3)
    if eng.get("amplified", _amplified(eng)):
        idx = min(idx + 1, 3)
    return ORDER[idx]


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []
    eng = pack.get("engagement") or {}
    fired = [f for f in findings if f.get("fired")]

    # 1. evidence + citation on every fired finding
    for f in fired:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"fired finding {f.get('finding_id')} has no evidence")
        for row in ev:
            if not str(row.get("citation", "")).strip():
                errors.append(f"fired finding {f.get('finding_id')} has an evidence row missing a citation")

    # 2 + 3. deterministic tier tie-out and allowed value
    tier = pack.get("suggested_residual_tier")
    if tier not in ORDER:
        errors.append(f"suggested_residual_tier {tier!r} not one of {ORDER}")
    exp = _expected_tier(findings, eng)
    if tier != exp:
        errors.append(f"suggested_residual_tier {tier!r} != deterministic {exp!r} "
                      f"for {len(fired)} fired finding(s)")

    # 4. prohibited-decision screen (scan free text, NOT the disclaimer field)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"decision/closure/filing language detected: {m.group(0)!r} "
                          f"(R3 recommends; a human adjudicates)")

    # 5. standing disclaimer present
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    # 6. considerations required when any finding fired
    if fired and not pack.get("considerations"):
        errors.append("findings fired but no considerations / compensating-control notes included")

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
