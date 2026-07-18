#!/usr/bin/env python3
"""Deterministic output validation for regulatory-reporting-data-validator.

Validates the final findings pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. Checks:
  1. Every fired finding (status fail/warn) has >= 1 cited evidence row.
  2. readiness_band equals the deterministic mapping from the fired-findings set.
  3. No filing-determination / certification / sign-off / submission language (narrative +
     notes + finding reasons + remediation) — the disclaimer field is excluded from the scan.
  4. The standing disclaimer is present.
  5. remediation_prompts are included when any finding fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

# Kept in sync with calculate_or_transform.py and references/domain-rules.md.
BLOCKING_CHECKS = {
    "completeness", "lineage_completeness", "edit_checks", "reconciliation_tie_out",
    "range_checks", "sign_off_completeness", "segregation_of_duties", "timeliness_overdue",
}
DISCLAIMER = ("Validation findings and cited evidence only; not a filing determination, "
              "certification, or submission. No regulatory report has been certified, "
              "signed off, filed, or submitted.")

# Affirmative determination / certification / filing-action assertions an R2 analyst-support
# skill must not make. Phrased affirmatively so the negated disclaimer does not match.
DETERMINATION_PATTERNS = [
    r"\bapproved for (filing|submission)\b",
    r"\bcleared for (filing|submission)\b",
    r"\bready to file\b",
    r"\bfit for filing\b",
    r"\bwe (certify|attest)\b",
    r"\bi (certify|attest)\b",
    r"\bcertified (as )?(accurate|correct|complete)\b",
    r"\battested to the accuracy\b",
    r"\bsigned off on (the|this) (filing|report|return)\b",
    r"\bwe (have )?(filed|submitted|transmitted) (the|this)\b",
    r"\bsubmit(ted)? (the|this) (report|filing|return) to the regulator\b",
    r"\bfinal and accurate\b",
    r"\bthe (report|filing|return) is (accurate|correct|compliant)\b",
]


def _expected_band(findings: list[dict]) -> str:
    fired = [f for f in findings if f.get("status") in ("fail", "warn")]
    if any(f.get("check") in BLOCKING_CHECKS for f in fired):
        return "Blocked"
    return "Review" if fired else "Clear"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []

    for f in findings:
        if f.get("status") in ("fail", "warn"):
            ev = f.get("evidence") or []
            if not ev:
                errors.append(f"fired finding {f.get('check')} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired finding {f.get('check')} evidence row missing citation")

    exp = _expected_band(findings)
    if pack.get("readiness_band") != exp:
        errors.append(f"readiness_band {pack.get('readiness_band')!r} != deterministic {exp!r}")

    # scan free text (narrative + notes + reasons + remediation) but NOT the disclaimer field
    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
        + [str(f.get("reason", "")) for f in findings]
        + [str(p) for p in (pack.get("remediation_prompts") or [])]
    )
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/action language detected: {m.group(0)!r} "
                          f"(R2 evidences exceptions, does not certify/approve/file)")

    if DISCLAIMER.lower() not in str(pack.get("disclaimer", "")).lower():
        errors.append("missing standing disclaimer text")

    if any(f.get("status") in ("fail", "warn") for f in findings) and not pack.get("remediation_prompts"):
        errors.append("findings fired but no remediation_prompts included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "findings_example.json"
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
