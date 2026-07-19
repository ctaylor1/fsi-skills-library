#!/usr/bin/env python3
"""Deterministic output validation for kyc-customer-due-diligence-screener.

Validates the final CDD screening pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. This is the R3 fail-closed gate. Checks:
  1. Every fired signal has >= 1 cited evidence row.
  2. recommended_track equals the deterministic mapping from fired_signals.
  3. adjudication_required is present and true (R3 retains mandatory human adjudication).
  4. No regulated decision / closure / filing / disposition language anywhere in the
     free text (narrative + notes + signal reasons).
  5. The standing disclaimer is present.
  6. recommended_next_steps present when any elevated-risk or sanctions signal fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

# Kept identical to calculate_or_transform.recommended_track (documented in domain-rules.md).
SANCTIONS = {"sanctions_potential_match"}
ELEVATED_RISK = {"high_risk_jurisdiction", "high_risk_industry", "pep_flag",
                 "adverse_media_flag", "ubo_below_coverage", "ubo_unverified"}
COMPLETENESS_GAPS = {"missing_required_field", "missing_required_document", "expired_document",
                     "unverified_identity", "identity_mismatch", "ownership_over_100"}

DISCLAIMER = (
    "CDD screening evidence and a recommended review track only; not a KYC/AML decision. "
    "No customer has been onboarded, exited, or risk-rated, no case disposition or closure "
    "has been recorded, and no regulatory filing has been made. A qualified analyst must "
    "adjudicate every finding."
)

# Regulated decision / closure / filing / disposition assertions an R3 skill must NOT make.
PROHIBITED_PATTERNS = [
    r"\bapprove(d|s)? (the )?(customer|onboarding|account|relationship|application)\b",
    r"\bonboarding (is )?approved\b",
    r"\breject(ed|s)? (the )?(customer|application|onboarding)\b",
    r"\bdecline(d|s)? (the )?(customer|application)\b",
    r"\bdeny (the )?onboarding\b",
    r"\bexit the relationship\b", r"\boffboard(ed|ing)?\b",
    r"\bclose (the )?case\b", r"\bcase (is )?closed\b",
    r"\bclear(ed)? (the )?(sanctions|watchlist)?\s?(hit|alert|match)\b",
    r"\bconfirmed (true |false )?(positive|match)\b", r"\bcleared as (a )?false positive\b",
    r"\bfile (a |the )?sar\b", r"\bfile (a |the )?suspicious activity report\b",
    r"\bconfirmed money laundering\b", r"\bis (a )?money launderer\b",
    r"\bthe customer is (a )?(criminal|sanctioned|terrorist)\b",
    r"\bconfirmed pep\b",
    r"\b(set|update) (the )?(customer )?risk rating\b",
    r"\bwrite to the system of record\b",
]


def _expected_track(fired):
    fs = set(fired)
    if fs & SANCTIONS:
        return "Escalate-For-Adjudication"
    if fs & ELEVATED_RISK:
        return "EDD-Recommended"
    if fs & COMPLETENESS_GAPS:
        return "Remediate-First"
    return "Standard-CDD"


def validate(pack: dict):
    errors = []
    signals = pack.get("signals") or []
    fired = [s["signal"] for s in signals if s.get("fired")]

    for s in signals:
        if s.get("fired"):
            ev = s.get("evidence") or []
            if not ev:
                errors.append(f"fired signal {s['signal']} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired signal {s['signal']} evidence row missing citation")

    exp = _expected_track(fired)
    if pack.get("recommended_track") != exp:
        errors.append(f"recommended_track {pack.get('recommended_track')!r} != deterministic {exp!r} for fired={fired}")

    if pack.get("adjudication_required") is not True:
        errors.append("adjudication_required must be true (R3 retains mandatory human adjudication)")

    # scan free text (narrative + notes + reasons); the disclaimer field is intentionally excluded
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(s.get("reason", "")) for s in signals])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/closure/filing language detected: {m.group(0)!r} "
                          f"(R3 recommends + evidences; a human adjudicates, decides, and files)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if (set(fired) & (SANCTIONS | ELEVATED_RISK)) and not pack.get("recommended_next_steps"):
        errors.append("elevated-risk/sanctions signal fired but no recommended_next_steps (routing) included")

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
