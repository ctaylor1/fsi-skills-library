#!/usr/bin/env python3
"""Deterministic output validation for model-risk-documenter.

Enforces the R3 "Draft & package" guardrails before a model documentation / validation-evidence
pack is handed to a human for review and adjudication:
  1. Template fidelity: all ten required documentation sections are present.
  2. Source-to-document traceability: every `documented` section carries a versioned citation;
     each section's declared status equals the deterministic re-derivation from its evidence.
  3. Methodology & limitation coverage: those two sections must carry all required coverage
     elements to be `documented` (recomputed here).
  4. Finding discipline: every finding is `open`, carries a source ref and a recommended
     remediation; every `gap`/`needs-data` section has a corresponding open documentation
     finding.
  5. No false attestation / finding-approval consistency: every recorded approval carries a
     citation; the attestation block is `pending` with adjudication required; an unconditional
     `approved` decision may not coexist with an open High-severity finding.
  6. No autonomous-decision / validation / approval / attestation / certification / clearance /
     finding-closure language.
  7. The standing disclaimer is present.

Fails closed on any miss so a defective or overreaching pack cannot be presented as a
completed, validated, or approved model documentation set.

Usage: python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = {
    "purpose", "methodology", "data", "performance", "limitations",
    "controls", "monitoring", "changes", "approvals", "traceability",
}
REQUIRED_COVERAGE = {
    "methodology": ["conceptual_soundness", "assumptions"],
    "limitations": ["known_limitations", "use_constraints"],
}
ORDER = {"Low": 0, "Medium": 1, "High": 2}
GAP_SEVERITY = {"gap": "Medium", "needs-data": "High"}
STANDING_NOTE = (
    "Draft model documentation pack for human review only; this skill assembles and traces "
    "evidence but does not validate, approve, attest, or certify any model or AI system, makes "
    "no fitness-for-use determination, closes no findings, and every section, finding, and "
    "approval requires review and adjudication by the model owner, independent validation, and "
    "the approver before any decision."
)
DECISION_PATTERNS = [
    r"\bmodel is (fully )?validated\b",
    r"\bvalidation (is )?complete\b",
    r"\bapproved for (use|production|deployment|release)\b",
    r"\bfit for (use|purpose|production|deployment)\b",
    r"\b(we|i) (hereby )?(certify|attest)\b",
    r"\battest(s|ed)? that\b",
    r"\bcertified\b",
    r"\bcleared (to|for) (deploy|deployment|production|use|release)\b",
    r"\bsign-?off (is )?complete\b",
    r"\bno (further|additional) (human )?review (is )?(required|needed)\b",
    r"\bfinding(s)? (closed|resolved|remediated|waived)\b",
    r"\bready for (production|deployment)\b",
    r"\brisk (is )?accepted\b",
    r"\bfinal (approval|determination|sign-?off)\b",
    r"\bauto-?approved\b",
    r"\bno action (required|needed)\b",
]


def _citations(artifacts):
    out = []
    for a in artifacts or []:
        if a.get("artifact_id") and a.get("version"):
            out.append(f"{a.get('artifact_type', 'artifact')}:{a['artifact_id']}@{a['version']}")
    return out


def _expected_status(sec: dict) -> str:
    name = sec.get("section")
    has_content = bool(sec.get("content_ref"))
    cited = len(_citations(sec.get("source_artifacts"))) > 0
    req_cov = REQUIRED_COVERAGE.get(name, [])
    cov = set(sec.get("coverage") or [])
    missing_cov = [c for c in req_cov if c not in cov]
    if not has_content:
        return "needs-data"
    if not cited:
        return "gap"
    if missing_cov:
        return "gap"
    return "documented"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections") or []
    if not sections:
        return ["documentation pack has no sections"]

    present = {s.get("section") for s in sections}
    for s in sorted(REQUIRED_SECTIONS - present):
        errors.append(f"missing required section '{s}' (template fidelity)")

    gap_sections = set()
    for sec in sections:
        name = sec.get("section", "?")
        declared = sec.get("status")
        expected = _expected_status(sec)
        if declared != expected:
            errors.append(f"{name}: status {declared!r} != expected {expected!r} (traceability tie-out)")
        status = declared if declared in ("documented", "gap", "needs-data") else expected
        if status == "documented" and not sec.get("citations"):
            errors.append(f"{name}: marked documented but has no versioned citation (untraceable assertion)")
        if status in ("gap", "needs-data"):
            gap_sections.add(name)

    findings = doc.get("findings") or []
    finding_sections = {f.get("section") for f in findings}
    for f in findings:
        fid = f.get("finding_id", "?")
        if f.get("status") != "open":
            errors.append(f"{fid} ({f.get('section')}): finding status must be 'open' (this skill does not close findings)")
        if not f.get("recommended_remediation"):
            errors.append(f"{fid} ({f.get('section')}): finding missing recommended_remediation")
        if not f.get("source_refs"):
            errors.append(f"{fid} ({f.get('section')}): finding missing source reference (unsupported assertion)")
    for name in sorted(gap_sections):
        if name not in finding_sections:
            errors.append(f"{name}: section is a gap/needs-data but no open documentation finding was raised")

    # No false attestation: recorded approvals must be cited; consistency with open findings.
    open_high = any(f.get("severity") == "High" and f.get("status") == "open" for f in findings)
    for a in doc.get("approvals") or []:
        aid = a.get("approval_id", "?")
        if not a.get("reference"):
            errors.append(f"approval {aid}: recorded without a citation (no false attestation - approvals must be evidenced)")
        if a.get("decision") == "approved" and open_high:
            errors.append(f"approval {aid}: unconditional 'approved' recorded while a High-severity finding is open (finding/approval inconsistency)")

    attest = doc.get("attestation") or {}
    if attest.get("status") != "pending":
        errors.append(f"attestation status must be 'pending' (this skill never validates/approves/attests a model), got {attest.get('status')!r}")
    if not attest.get("adjudication_required"):
        errors.append("attestation.adjudication_required must be true (R3 mandatory human adjudication)")
    if not (attest.get("required_approvers") or []):
        errors.append("attestation.required_approvers is empty (no routing)")

    scan = json.dumps(sections) + " " + json.dumps(findings) + " " + \
        json.dumps(doc.get("approvals") or []) + " " + str(doc.get("narrative", ""))
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited attestation/decision language detected: {m.group(0)!r} (this skill never validates/approves/attests/certifies a model or closes findings)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
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
