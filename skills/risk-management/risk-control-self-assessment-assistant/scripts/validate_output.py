#!/usr/bin/env python3
"""Deterministic output validation for risk-control-self-assessment-assistant.

Enforces the R3 decision-support + Draft & package guardrails before an RCSA package is
presented to a human:
  1. All required template sections are present (template fidelity).
  2. No UNSUPPORTED assertions: any credited control conclusion (Effective / Partially
     Effective) must carry evidence; an unevidenced credited claim is rejected.
  2b. Any control rated Ineffective must have remediation_required set (checked
     independently of the transform so a masked/order-dependent Ineffective fails closed).
  3. Residual risk ties out to the deterministic mapping (inherent_level - reduction).
  4. Required human approvals are RECORDED (control owner, first-line sign-off, second-line
     challenge) and the assistant has not marked any as obtained without a named approver+date.
  5. No autonomous decision / closure / attestation / filing language.
  6. The standing note is present.
Fails closed (exit 1) on any miss.

Usage: python validate_output.py rcsa_package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "assessment_scope", "risk_and_control_assessment", "residual_risk_summary",
    "evidence_map", "challenges_and_gaps", "remediation_plan", "approvals",
]
REQUIRED_APPROVAL_ROLES = [
    "Control / process owner (accuracy attestation)",
    "First-line business management (assessment sign-off)",
    "Second-line operational risk (independent challenge / validation)",
]
ALLOWED_APPROVAL_STATUS = {"pending", "obtained"}
CREDITED = {"Effective", "Partially Effective"}
LEVEL_BAND = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}
STANDING_NOTE_KEY = "draft rcsa"  # sentinel that must appear in the standing note

# Autonomous decision / closure / attestation / filing language the DRAFT must never assert.
# Patterns target the AFFIRMATIVE adjacent phrasing; passive/negated phrasing is safe.
PROHIBITED_PATTERNS = [
    r"\brisk accepted\b", r"\baccept(?:ing|ed)? the risk\b", r"\bwe accept the risk\b",
    r"\bassessment approved\b", r"\bassessment is approved\b", r"\bapproved and closed\b",
    r"\bsigned off by\b", r"\bsign-?off (?:is|has been) complete\b",
    r"\bself-certif", r"\battestation (?:is )?complete\b", r"\battested by\b",
    r"\bassessment closed\b", r"\bmarked (?:as )?closed\b", r"\bassessment finali[sz]ed\b",
    r"\bfiled to (?:the )?grc\b", r"\bposted to the system of record\b",
    r"\bwritten to the (?:grc )?system of record\b", r"\bno further review (?:is )?required\b",
    r"\bno remediation (?:is )?(?:needed|required)\b", r"\bcontrol is effective, no evidence\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections") or {}
    if not sections:
        return ["package has no 'sections' block"]

    # 1. required template sections
    for s in REQUIRED_SECTIONS:
        if s not in sections:
            errors.append(f"missing required template section '{s}'")

    assessments = sections.get("risk_and_control_assessment") or []
    if not assessments:
        errors.append("risk_and_control_assessment has no records")

    for r in assessments:
        rid = r.get("risk_id", "?")
        controls = r.get("controls") or []
        # 2. no unsupported assertions
        for c in controls:
            eff = c.get("overall_effectiveness")
            if eff in CREDITED and not c.get("evidence"):
                errors.append(f"{rid}/{c.get('control_id')}: credited effectiveness "
                              f"{eff!r} asserted without evidence (unsupported claim)")
        # 2b. an Ineffective control must flag remediation (derived independently of the
        # transform's flag so a masked/order-dependent Ineffective cannot slip through).
        if any(c.get("overall_effectiveness") == "Ineffective" for c in controls) \
                and r.get("remediation_required") is not True:
            errors.append(f"{rid}: control rated Ineffective but remediation_required "
                          f"{r.get('remediation_required')!r} (ineffective control not "
                          f"flagged for remediation)")
        # 3. residual tie-out
        inh = r.get("inherent_level")
        red = r.get("control_effect_reduction")
        if isinstance(inh, int) and isinstance(red, int):
            exp_level = max(1, inh - red)
            if r.get("residual_level") != exp_level:
                errors.append(f"{rid}: residual_level {r.get('residual_level')!r} != expected "
                              f"{exp_level} (inherent {inh} - reduction {red})")
            if r.get("residual_band") != LEVEL_BAND.get(exp_level):
                errors.append(f"{rid}: residual_band {r.get('residual_band')!r} != "
                              f"{LEVEL_BAND.get(exp_level)!r} for level {exp_level}")
        else:
            errors.append(f"{rid}: missing inherent_level/control_effect_reduction for tie-out")

    # 4. required approvals recorded (and not fabricated)
    approvals = sections.get("approvals") or []
    roles_present = {a.get("role") for a in approvals}
    for role in REQUIRED_APPROVAL_ROLES:
        if role not in roles_present:
            errors.append(f"required approval not recorded: {role!r}")
    for a in approvals:
        st = a.get("status")
        if st not in ALLOWED_APPROVAL_STATUS:
            errors.append(f"approval {a.get('role')!r}: status {st!r} not in {sorted(ALLOWED_APPROVAL_STATUS)}")
        if st == "obtained" and not (a.get("approver") and a.get("date")):
            errors.append(f"approval {a.get('role')!r}: marked obtained without a named approver+date")

    # 5. prohibited autonomous-decision language (scan sections + narrative, NOT standing note)
    scan = json.dumps(sections) + " " + str(doc.get("narrative", ""))
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited autonomous-decision language: {m.group(0)!r} "
                          f"(this skill drafts only; humans decide)")

    # 6. standing note present
    if STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing or altered standing note")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "rcsa_package.json"
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
