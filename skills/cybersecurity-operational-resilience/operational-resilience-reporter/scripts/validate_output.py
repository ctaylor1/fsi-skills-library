#!/usr/bin/env python3
"""Deterministic output validation for operational-resilience-reporter.

Enforces the Draft & package (R3) guardrails on an assembled report package before it is
handed to a human:
  1. Template fidelity - every required section for the report_type/jurisdiction is present.
  2. No unsupported/unapproved claims - `unsupported_claims` is empty; every `drafted`
     section carries >=1 citation and >=1 fact; every `gap` section carries NO content.
  3. Impact-tolerance assessments tie out (breached == observed vs threshold, direction).
  4. Required human approvals recorded (accountable-executive + second-line-review, each
     approved with a name and date).
  5. Fail closed on any regulatory decision / attestation / filing / submission / closure
     language (this skill drafts only; humans adjudicate and file).
  6. Draft watermark and standing note present.

Usage: python validate_output.py report_package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

BASE_TEMPLATES = {
    "incident": ["executive-summary", "incident-chronology", "impacted-important-business-services",
                 "impact-tolerance-assessment", "root-cause-and-remediation", "customer-and-market-impact",
                 "regulatory-notification-status", "approvals"],
    "impact-tolerance": ["executive-summary", "important-business-services", "impact-tolerance-statements",
                         "mapping-and-third-parties", "vulnerabilities-and-remediation", "remediation-plan",
                         "approvals"],
    "dependency": ["executive-summary", "service-dependency-map", "critical-third-parties",
                   "concentration-and-substitutability", "exit-and-contingency", "approvals"],
    "testing": ["executive-summary", "scenario-testing-summary", "tolerance-outcomes",
                "vulnerabilities-and-remediation", "lessons-learned", "approvals"],
    "self-assessment": ["executive-summary", "important-business-services", "impact-tolerance-statements",
                        "mapping-and-third-parties", "scenario-testing-summary", "incident-experience",
                        "vulnerabilities-and-remediation", "lessons-learned", "board-attestation-status",
                        "approvals"],
}
JURISDICTION_SECTIONS = {
    "EU-DORA": ["ict-third-party-register", "major-incident-classification"],
    "UK-PRA-SS1-21": ["self-assessment-document-reference"],
    "US-INTERAGENCY": ["interconnection-and-concentration"],
}
REQUIRED_APPROVERS = ["accountable-executive", "second-line-review"]
DRAFT_WATERMARK = "not filed or submitted to any regulator"
STANDING_NOTE = "makes no regulatory determination, files"

# Regulatory decision / attestation / filing / submission / closure language (fail closed).
# NOTE: factual observations such as "impact tolerance breached" are allowed by design.
FORBIDDEN_PATTERNS = [
    r"\bsubmitted to (the )?(regulator|pra|fca|ecb|occ|federal reserve|supervisor)\b",
    r"\bfiled with (the )?(regulator|pra|fca|ecb|occ)\b",
    r"\bwe (hereby )?attest\b", r"\bhereby certif(y|ies|ied)\b", r"\bboard has attested\b",
    r"\bdetermination:\s*(fully )?compliant\b",
    r"\bwe determine (that )?(we are|the firm is)\b",
    r"\bno notification (is )?required\b", r"\bnotification not required\b",
    r"\bno further action\b", r"\bcase closed\b", r"\bmatter closed\b",
    r"\bself-assessment (is )?(complete and )?filed\b",
    r"\bapproved for submission to the regulator\b", r"\bsubmission complete\b",
]


def _expected_breach(a):
    obs, thr, direction = a.get("observed"), a.get("threshold"), a.get("direction", "max")
    if obs is None or thr is None:
        return None
    return obs > thr if direction == "max" else obs < thr


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    pkg = doc.get("report_package")
    if not isinstance(pkg, dict):
        return ["missing 'report_package' object"]

    rtype = pkg.get("report_type")
    juris = pkg.get("jurisdiction")
    if rtype not in BASE_TEMPLATES:
        errors.append(f"unknown report_type {rtype!r}")

    # 1. template fidelity
    base = BASE_TEMPLATES.get(rtype, [])
    js = JURISDICTION_SECTIONS.get(juris, [])
    required = set([k for k in base if k != "approvals"]) | set(js) | {"approvals"}
    present = {s.get("key") for s in (pkg.get("sections") or [])}
    for k in sorted(required - present):
        errors.append(f"missing required section for {rtype}/{juris}: {k}")

    # 2. no unsupported/unapproved claims
    uc = pkg.get("unsupported_claims")
    if uc:
        errors.append(f"unsupported_claims must be empty, found {len(uc)}")
    for s in (pkg.get("sections") or []):
        key, st = s.get("key"), s.get("status")
        if st == "drafted":
            if not s.get("citations"):
                errors.append(f"drafted section {key!r} has no citations (unsupported claim)")
            if not s.get("content_facts"):
                errors.append(f"drafted section {key!r} has no content_facts")
        elif st == "gap":
            if s.get("content_facts") or s.get("citations"):
                errors.append(f"gap section {key!r} carries content/citations (fabricated evidence)")
        else:
            errors.append(f"section {key!r} has invalid status {st!r}")

    # 3. impact-tolerance tie-out
    for a in (pkg.get("impact_tolerance_assessments") or []):
        exp = _expected_breach(a)
        if exp is not None and bool(a.get("breached")) != bool(exp):
            errors.append(f"assessment {a.get('incident_id')}: breached={a.get('breached')} "
                          f"!= expected {exp} (observed {a.get('observed')} vs {a.get('threshold')})")

    # 4. required approvals recorded
    by_role = {}
    for ap in (pkg.get("approvals_recorded") or []):
        by_role[ap.get("role")] = ap
    for role in REQUIRED_APPROVERS:
        ap = by_role.get(role)
        if not ap:
            errors.append(f"missing required approval: {role}")
        elif ap.get("decision") != "approved" or not ap.get("name") or not ap.get("date"):
            errors.append(f"approval {role} incomplete (needs decision=approved, name, date)")

    # 5. forbidden decision/filing/attestation language
    scan = json.dumps(pkg)
    for pat in FORBIDDEN_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited decision/filing/attestation language: {m.group(0)!r} "
                          f"(skill drafts only; humans adjudicate and file)")

    # 6. watermark + standing note
    if DRAFT_WATERMARK.lower() not in str(pkg.get("draft_watermark", "")).lower():
        errors.append("missing/incorrect draft watermark")
    if STANDING_NOTE.lower() not in str(pkg.get("standing_note", "")).lower():
        errors.append("missing/incorrect standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "report_package.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
