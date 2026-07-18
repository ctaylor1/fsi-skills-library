#!/usr/bin/env python3
"""Deterministic output validation for agent-permission-scope-reviewer.

Enforces the R3 guardrails before the scope-review pack is presented or delivered. Checks:
  1. Every finding uses an APPROVED rule id and has >= 1 cited evidence row.
  2. recommended_disposition equals the deterministic mapping from the findings' severities.
  3. No autonomous decision/approval/provisioning/closure/filing language (narrative + notes
     + finding reasons).
  4. human_adjudication_required is present and true.
  5. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

APPROVED_RULES = {
    "LP-NEED-01", "LP-WRITE-NOGATE", "LP-CLASS-MODE", "LP-CLASS-UNDECLARED",
    "LP-LOG-OFF", "LP-SOD-COMBO", "LP-REVOKE-MISSING", "LP-ENV-PROD",
}
SEVERITY_RANK = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
DISCLAIMER = ("Least-privilege review evidence only; not an access approval or denial. No "
              "entitlement has been granted, revoked, or provisioned, and no review has been "
              "closed. Human adjudication is required.")
# Autonomous access-decision / entitlement-action / closure / filing assertions an R3
# decision-support skill must NOT make. Recommendation phrasing ("recommend the adjudicator
# require/narrow/revoke scope") lives in recommended_remediation, which is NOT scanned.
PROHIBITED_PATTERNS = [
    r"\b(scope|access|entitlement|request|agent)\s+(is\s+|was\s+|has been\s+)?approved\b",
    r"\bapproved for (production|prod|deployment)\b",
    r"\bwe(?:'ve| have)?\s+approved\b", r"\bi approve\b",
    r"\b(scope|access|entitlement|request)\s+(is\s+|was\s+|has been\s+)?denied\b",
    r"\bgrant(?:ed|ing|s)?\s+(the\s+)?(role|access|permission|entitlement|token|credential|scope)\b",
    r"\bprovision(?:ed|ing|s)?\s+(the\s+)?(role|access|entitlement|token|credential|scope)\b",
    r"\bde-?provision(?:ed|ing|s)?\b",
    r"\brevoke[ds]?\s+(the\s+)?(role|access|entitlement|token|credential)\b",
    r"\brotate[ds]?\s+(the\s+)?(token|credential|key)\b",
    r"\bcleared for (production|prod|deployment)\b",
    r"\bclose[ds]?\s+(the\s+)?review\b", r"\breview (is\s+)?closed\b",
    r"\brisk accepted\b",
    r"\bfile[ds]?\s+(a\s+|an\s+|the\s+)?(waiver|exception)\b",
    r"\bwaiver (filed|granted|approved)\b",
    r"\bno (further )?human (review|adjudication) (is )?(needed|required)\b",
    r"\bcertif(?:y|ied|ies)\b.{0,20}\bcompliant\b",
    r"\bsign-?off (complete|done)\b",
]


def _expected_disposition(findings: list) -> str:
    sevs = {f.get("severity") for f in findings}
    if "Critical" in sevs:
        return "Remediate-before-approval"
    if "High" in sevs:
        return "Conditional-adjudication-required"
    if sevs:
        return "Review-minor-findings"
    return "No-exceptions-adjudication-required"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings")
    if findings is None:
        return ["pack has no 'findings' array"]

    for f in findings:
        rid = f.get("rule_id")
        if rid not in APPROVED_RULES:
            errors.append(f"finding uses unapproved rule id {rid!r} (not in the versioned rule set)")
        if f.get("severity") not in SEVERITY_RANK:
            errors.append(f"finding {rid} has invalid severity {f.get('severity')!r}")
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {rid} ({f.get('op_id')}) has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {rid} ({f.get('op_id')}) evidence row missing citation")

    exp = _expected_disposition(findings)
    if pack.get("recommended_disposition") != exp:
        errors.append(f"recommended_disposition {pack.get('recommended_disposition')!r} != deterministic {exp!r}")

    # scan free text (narrative + notes + reasons), NOT recommended_remediation or disclaimer
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"autonomous decision/approval/provisioning/closure/filing language detected: {m.group(0)!r} (R3 recommends, does not decide/act)")

    if pack.get("human_adjudication_required") is not True:
        errors.append("human_adjudication_required must be present and true")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

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
