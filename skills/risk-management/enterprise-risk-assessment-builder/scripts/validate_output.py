#!/usr/bin/env python3
"""Deterministic output validation for enterprise-risk-assessment-builder.

Enforces the Draft & package + R3 guardrails before a draft enterprise risk assessment is
presented to a human:
  1. Template fidelity - every required template section is present.
  2. Residual tie-out - each residual band equals the deterministic mapping
     (inherent band reduced by the recorded control credit) and over-appetite is consistent.
  3. No unsupported assertions - control credit (reduction > 0) is only taken when a credited
     control is tested AND carries evidence; credited controls must be `proven`.
  4. Treatment coverage - any residual above appetite records a treatment action.
  5. No autonomous decision/closure/filing language (fail closed on regulated-decision verbs).
  6. Required human approvals are RECORDED and left `pending` (the draft never self-approves).
  7. Only draft case states are used; the standing note is present.

Usage: python validate_output.py assessment.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

BAND_INDEX = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}
REQUIRED_SECTIONS = {
    "Scope & Basis", "Risk Inventory", "Inherent Risk Assessment", "Control Environment",
    "Residual Risk & Appetite", "Key Risk Indicators", "Treatment Actions",
    "Evidence Register", "Limitations & Assumptions", "Approvals & Attestations",
}
REQUIRED_APPROVALS = {
    "Risk & Control Owner (1st line)",
    "Enterprise Risk Management (2nd line)",
    "Risk Committee / CRO",
}
ALLOWED_STATUS = {"draft-for-review", "needs-evidence"}
GRANTED_STATES = {"approved", "granted", "signed", "signed-off", "complete", "accepted", "final"}
STANDING_NOTE = (
    "Draft enterprise risk assessment for human review only; no risk has been accepted, no "
    "residual rating approved, no assessment finalized, and nothing filed or written to the "
    "risk system of record."
)
# Regulated-decision / closure / filing language that a draft must never contain.
# Patterns target decision/closure VERBS, not descriptive nouns (e.g. a control named
# "Board-approved limits" or an "exit plan attestation" is legitimate and must not trip).
DECISION_PATTERNS = [
    r"\brisk (is |has been )?accepted\b", r"\baccept(ed|ing)? the residual\b",
    r"\bwe accept this risk\b", r"\bassessment (is |has been )?(approved|finalized|final)\b",
    r"\bapproved by\b", r"\bsigned off\b", r"\bsign-off complete\b",
    r"\bfinal determination\b", r"\brisk (is |has been )?closed\b", r"\bclose(d)? the risk\b",
    r"\bfiled with\b", r"\bsubmitted to (the )?regulator\b", r"\bwritten to the risk register\b",
    r"\battestation (is |has been )?complete\b", r"\bno further (action|review) (required|needed)\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    # 1. template fidelity
    sections = set(doc.get("sections") or [])
    missing = REQUIRED_SECTIONS - sections
    if missing:
        errors.append(f"missing required template section(s): {sorted(missing)}")

    # 7. assessment-level draft state
    if doc.get("status") not in ALLOWED_STATUS:
        errors.append(f"assessment status {doc.get('status')!r} is not a permitted draft state {sorted(ALLOWED_STATUS)}")

    risks = doc.get("risks") or []
    if not risks:
        errors.append("assessment has no risk records")

    for r in risks:
        rid = r.get("risk_id", "?")
        inh = r.get("inherent") or {}
        res = r.get("residual") or {}
        app = r.get("appetite") or {}
        ce = r.get("control_environment") or {}
        reduction = ce.get("reduction", 0)

        if r.get("status") not in ALLOWED_STATUS:
            errors.append(f"{rid}: risk status {r.get('status')!r} is not a permitted draft state")

        # 2. residual tie-out
        inh_idx = inh.get("band_index")
        if inh_idx != BAND_INDEX.get(inh.get("band")):
            errors.append(f"{rid}: inherent band/index mismatch")
        if isinstance(inh_idx, int):
            exp_idx = max(0, inh_idx - reduction)
            if res.get("band_index") != exp_idx or res.get("band") != {v: k for k, v in BAND_INDEX.items()}.get(exp_idx):
                errors.append(f"{rid}: residual {res.get('band')!r} != deterministic mapping "
                              f"(inherent {inh.get('band')} - reduction {reduction})")
            exp_over = res.get("band_index", 0) > app.get("band_index", 0)
            if bool(r.get("over_appetite")) != exp_over:
                errors.append(f"{rid}: over_appetite flag inconsistent with residual vs appetite")

        # 3. no unsupported assertions (control credit needs proven + evidenced controls)
        if reduction and reduction > 0:
            credited = [c for c in (r.get("controls") or []) if c.get("credited")]
            if not credited:
                errors.append(f"{rid}: control credit taken (reduction {reduction}) with no credited control")
            for c in credited:
                if not c.get("proven"):
                    errors.append(f"{rid}: control {c.get('control_id')} credited but not proven (untested)")
                if not c.get("evidence_ref"):
                    errors.append(f"{rid}: unsupported assertion - control {c.get('control_id')} credited without evidence_ref")

        # 4. treatment coverage for over-appetite residuals
        if r.get("over_appetite") and not (r.get("treatment_action_ids") or []):
            errors.append(f"{rid}: residual exceeds appetite but no treatment action recorded")

    # 6. approvals recorded and left pending
    approvals = {a.get("role"): a for a in (doc.get("approvals") or [])}
    miss_app = REQUIRED_APPROVALS - set(approvals)
    if miss_app:
        errors.append(f"missing required approval role(s): {sorted(miss_app)}")
    for role, a in approvals.items():
        if str(a.get("status", "")).lower() in GRANTED_STATES:
            errors.append(f"approval '{role}' is pre-granted ({a.get('status')!r}); a draft must leave approvals pending")

    # 5. no autonomous decision/closure/filing language.
    #    The standing note deliberately states these things were NOT done, so exclude it.
    scan_doc = {k: v for k, v in doc.items() if k != "standing_note"}
    scan = json.dumps(scan_doc) + " " + str(doc.get("narrative", ""))
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited decision/closure/filing language detected: {m.group(0)!r}")

    # 7. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessment_example.json"
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
