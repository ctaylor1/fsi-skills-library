#!/usr/bin/env python3
"""Deterministic output validation for cloud-security-posture-reviewer.

Validates the final posture-review pack (the calculate_or_transform core + a narrative)
before it is presented or written to a case. This is the R3 fail-closed screen. Checks:
  1. Every finding has >= 1 cited evidence row (non-empty citation).
  2. posture_disposition equals the deterministic mapping from the findings' severities.
  3. No compliance-attestation, risk-acceptance, closure/suppression/waiver, exception-grant,
     or remediation-execution / config-write language (scanned across narrative + finding
     summaries + notes; the standing disclaimer text is stripped before scanning so its
     negations do not self-trigger).
  4. The standing disclaimer is present.
  5. reviewer_considerations are included whenever any finding is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Posture findings and remediation evidence only; not a compliance attestation "
              "or risk-acceptance decision. No finding closure, suppression, waiver, or risk "
              "acceptance has been made, no exception has been granted, and no cloud "
              "configuration change or remediation has been applied.")

# Prohibited R3 decision / action / filing / attestation assertions.
# The skill evidences and recommends; a human owner adjudicates and acts.
DETERMINATION_PATTERNS = [
    # compliance attestation / sign-off
    r"\b(environment|account|posture|configuration|resource) is (fully )?(secure|compliant)\b",
    r"\bis (now )?(fully )?compliant\b",
    r"\battest(s|ed|ing)?\b.{0,20}\b(compliance|controls|posture)\b",
    r"\bcertif(y|ies|ied|ying)\b.{0,20}\b(compliance|soc ?2|pci|the environment|the account)\b",
    r"\bsoc ?2 (is )?compliant\b", r"\bpci[- ]?dss (is )?compliant\b",
    r"\b(passes|passed) the audit\b",
    # closure / suppression / risk acceptance (decisive verb + object)
    r"\b(close|closed|closing|suppress|suppressed|dismiss|dismissed|waive|waived) (the )?finding(s)?\b",
    r"\bmark(ed|ing)? (the finding|it|them|findings)\b.{0,30}\b(resolved|accepted|closed|false[- ]positive)\b",
    r"\baccept(ed|ing)? the risk\b", r"\brisk (is|was) accepted\b",
    # exception / waiver granting / filing
    r"\bgrant(ed|ing)? (an? |the )?(exception|waiver|risk acceptance)\b",
    r"\b(exception|waiver) (is|was) (granted|approved)\b",
    r"\bapprove(d|s)? the (exception|waiver)\b",
    r"\bfile(d)? (an? |the )?(exception|waiver|poa\s?&\s?m|poam)\b",
    # remediation execution / configuration write
    r"\bwe (have )?(remediated|fixed|patched|applied|deployed|rotated|reconfigured|disabled|enabled)\b",
    r"\b(has|have) been (remediated|patched|fixed|reconfigured)\b",
    r"\bapply (the )?(fix|remediation|change) now\b",
    r"\b(modified|changed|updated) the (security group|iam policy|bucket policy|configuration)\b",
]


def _expected_disposition(findings: list[dict]) -> str:
    sev = {f.get("severity") for f in findings}
    if "critical" in sev:
        return "remediate_now"
    if "high" in sev:
        return "remediation_required"
    if sev & {"medium", "low"}:
        return "review_recommended"
    return "posture_acceptable"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []

    for f in findings:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {f.get('finding_id', '?')} ({f.get('rule', f.get('category', '?'))}) has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {f.get('finding_id', '?')} evidence row missing citation")

    exp = _expected_disposition(findings)
    if pack.get("posture_disposition") != exp:
        errors.append(f"posture_disposition {pack.get('posture_disposition')!r} != deterministic {exp!r} for finding severities")

    # scan free text: narrative + notes + finding summaries; strip the disclaimer so its
    # negations ("no finding closure ... has been made") do not self-trigger the screen.
    narrative = str(pack.get("narrative", "")).replace(DISCLAIMER, " ")
    text = " ".join([narrative, str(pack.get("notes", ""))]
                    + [str(f.get("summary", "")) for f in findings])
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/action language detected: {m.group(0)!r} (R3 evidences and recommends; a human adjudicates and acts)")

    disc_text = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in disc_text:
        errors.append("missing standing disclaimer text")

    if findings and not pack.get("reviewer_considerations"):
        errors.append("findings present but no reviewer_considerations included")

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
