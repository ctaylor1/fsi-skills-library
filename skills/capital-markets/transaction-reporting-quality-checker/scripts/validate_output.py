#!/usr/bin/env python3
"""Deterministic output validation for transaction-reporting-quality-checker.

Validates the final quality-control pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Fails closed. Checks:
  1. Every exception carries >= 1 cited evidence row.
  2. Every exception code is recognized (unknown codes cannot silently change priority).
  3. suggested_priority equals the deterministic mapping derived from the exception codes.
  4. No compliance-determination or report-action language (narrative + notes + reasons).
  5. The standing disclaimer is present.
  6. false_positive_checks are included whenever any exception is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Quality-control findings only; not a compliance determination. No regulatory "
              "report has been submitted, amended, cancelled, or suppressed.")

# Canonical severity per exception code — must match calculate_or_transform.py.
SEVERITY_BY_CODE = {
    "missing_report": "blocking",
    "over_report": "blocking",
    "economic_field_mismatch": "blocking",
    "invalid_identifier": "high",
    "missing_required_field": "high",
    "late_report": "high",
    "rejected_report_unresolved": "high",
    "noncritical_field_mismatch": "low",
}

# Compliance determinations / report actions an R2 read-only QC checker must never make.
# Targeted at directive/assertive phrasing; the standing disclaimer (excluded from the
# scan) may legitimately use the passive nouns "amended, cancelled, or suppressed".
DETERMINATION_PATTERNS = [
    r"\bin breach\b",
    r"\bis non-?compliant\b",
    r"\bnon-?compliance (is )?confirmed\b",
    r"\bconfirmed (a )?breach\b",
    r"\bregulatory (breach|violation)\b",
    r"\bviolat(es|ed|ion)\b",
    r"\bwe (should|will|must) (submit|amend|cancel|correct|resubmit|suppress)\b",
    r"\bsubmit(ting)? (the |a )?(correction|amendment|cancellation|report) to (the )?(regulator|arm|nca|esma|fca|sec|finra)\b",
    r"\b(cancel|amend|resubmit|correct) (the )?report\b",
    r"\bcertif(y|ies|ied) (that )?remediation\b",
    r"\battest(s|ed)? (that|to)\b",
    r"\bsign off (on|that)\b",
    r"\bno report (is )?required\b",
    r"\bsuppress (the )?(exception|report|alert)\b",
    r"\bself-report to (the )?(regulator|nca|fca|esma|sec|finra)\b",
]


def _expected_priority(codes: list[str]) -> str:
    sev = {SEVERITY_BY_CODE.get(c) for c in codes}
    if "blocking" in sev:
        return "Blocking"
    if "high" in sev:
        return "High"
    if codes:
        return "Review"
    return "Clean"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    exceptions = pack.get("exceptions") or []
    codes = []

    for ex in exceptions:
        code = ex.get("code")
        codes.append(code)
        if code not in SEVERITY_BY_CODE:
            errors.append(f"unknown exception code {code!r} (cannot map to a severity/priority)")
        ev = ex.get("evidence") or []
        if not ev:
            errors.append(f"exception {code} has no evidence")
        for row in ev:
            has_cite = any(str(row.get(k, "")).strip() for k in ("citation", "citation_report", "citation_source"))
            if not has_cite:
                errors.append(f"exception {code} evidence row missing citation")

    exp = _expected_priority(codes)
    if pack.get("suggested_priority") != exp:
        errors.append(f"suggested_priority {pack.get('suggested_priority')!r} != deterministic {exp!r} for codes={sorted(set(codes))}")

    # scan free text (narrative + notes + reasons), but NOT the disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(ex.get("reason", "")) for ex in exceptions])
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/action language detected: {m.group(0)!r} (R2 evidences, does not decide/act)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if exceptions and not pack.get("false_positive_checks"):
        errors.append("exceptions present but no false_positive_checks included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "quality_report_example.json"
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
