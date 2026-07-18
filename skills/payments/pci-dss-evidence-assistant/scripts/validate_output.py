#!/usr/bin/env python3
"""Deterministic output validation for pci-dss-evidence-assistant.

Enforces the Draft & package guardrails on a PCI DSS evidence package before it is shown to
a human or handed to a QSA/ISA:

  1. Template fidelity — every required section is present in the rendered document.
  2. No unsupported/unapproved claims — every cited evidence_ref exists in the evidence
     index; evidence-complete / evidence-stale requirements actually cite evidence;
     evidence-gap requirements appear in the gap register.
  3. No attestation / compliance-determination language (the skill never attests, never
     marks a requirement "In Place", never claims compliance).
  4. Required human approvals are recorded (preparer, reviewer slot, QSA/ISA sign-off slot)
     and attestation_made is False.
  5. The standing (non-attestation) note is present.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise. Prints a final line ending "N error(s)".
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_STATUS = {"evidence-complete", "evidence-gap", "evidence-stale", "needs-data", "not-applicable"}

REQUIRED_SECTIONS = [
    "## 1. Assessment Scope and Metadata",
    "## 2. Cardholder Data Environment (CDE) Summary",
    "## 3. Requirement-to-Control-to-Evidence Mapping",
    "## 4. Evidence Readiness Summary",
    "## 5. Gap and Remediation Register",
    "## 6. Assumptions and Open Items",
    "## 7. Source and Citation Index",
    "## 8. Approvals and Attestation Boundary",
]

STANDING_FRAGMENT = "does not attest PCI DSS compliance"

# Attestation / compliance-determination language a DRAFT package must never contain.
ATTESTATION_PATTERNS = [
    r"\bwe are (fully )?(pci[- ]?dss )?compliant\b",
    r"\b(is|are) (fully )?compliant\b",
    r"\bfully compliant\b",
    r"\bcompliance (is|has been) (confirmed|achieved|validated|certified)\b",
    r"\bpci[- ]?dss[- ]?certified\b",
    r"\bcertified (as )?pci\b",
    r"\bpassed the assessment\b",
    r"\brequirement[s]? (is|are) (met|satisfied)\b",
    r"\bmarked (as )?in place\b",
    r"\bfinding:? in place\b",
    r"\bwe attest\b",
    r"\baoc (is |has been )?(signed|complete[d]?)\b",
    r"\broc (is |has been )?(signed|complete[d]?)\b",
    r"\bsaq (is |has been )?(signed|submitted)\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    records = doc.get("requirements") or []
    if not records:
        return ["package has no requirement records"]

    index_ids = {e.get("id") for e in (doc.get("evidence_index") or [])}
    gap_reqs = {g.get("req_id") for g in (doc.get("gap_register") or [])}

    for r in records:
        rid = r.get("req_id", "?")
        st = r.get("evidence_status")
        if st not in ALLOWED_STATUS:
            errors.append(f"{rid}: disallowed evidence_status {st!r} (compliance determination not permitted)")
        for ref in (r.get("evidence_refs") or []):
            if ref not in index_ids:
                errors.append(f"{rid}: unsupported claim - evidence_ref {ref!r} not in evidence_index")
        if st in ("evidence-complete", "evidence-stale") and not (r.get("evidence_refs")):
            errors.append(f"{rid}: unsupported claim - {st} but no evidence_refs cited")
        if st == "evidence-gap" and rid not in gap_reqs:
            errors.append(f"{rid}: evidence-gap not recorded in gap_register")

    # Template fidelity.
    document = str(doc.get("document", ""))
    for sec in REQUIRED_SECTIONS:
        if sec not in document:
            errors.append(f"missing required section: {sec}")

    # Attestation / determination language screen (scan document + records + narrative).
    scan = document + " " + json.dumps(records) + " " + str(doc.get("narrative", ""))
    for pat in ATTESTATION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"attestation/compliance-determination language detected: {m.group(0)!r} (draft never attests)")

    # Required human approvals recorded.
    ap = doc.get("approvals") or {}
    if not ap:
        errors.append("approvals block missing (required human approvals not recorded)")
    else:
        if not str(ap.get("prepared_by", "")).strip():
            errors.append("approvals.prepared_by not recorded")
        if "compliance_reviewer" not in ap or not str(ap.get("compliance_reviewer", "")).strip():
            errors.append("approvals.compliance_reviewer not recorded (use a name or 'pending')")
        if not str(ap.get("qsa_or_isa_signoff", "")).strip():
            errors.append("approvals.qsa_or_isa_signoff slot not recorded")
        if ap.get("attestation_made") is not False:
            errors.append("approvals.attestation_made must be False (draft-only; the skill never attests)")

    # Standing non-attestation note present.
    blob = (document + " " + str(doc.get("standing_note", ""))).lower()
    if STANDING_FRAGMENT.lower() not in blob:
        errors.append("missing standing non-attestation note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "package_example.json"
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
