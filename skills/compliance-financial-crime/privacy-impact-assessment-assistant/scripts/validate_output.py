#!/usr/bin/env python3
"""Deterministic output validation for privacy-impact-assessment-assistant.

Screens a draft PIA/DPIA package before it is presented to a human adjudicator (DPO / privacy
officer). It fails closed (exit 1) on any control breach. This is a Draft & package (R3)
guardrail: the assessment may recommend, never decide. Checks:
  1. packaging_status is an allowed DRAFT status (no decision/closure/sign-off states).
  2. All required template sections are present (template fidelity).
  3. No unsupported claims: every 'present' evidence section carries citations.
  4. Required human approvals are recorded (ledger covers every required role; any
     'obtained' entry names an approver + date).
  5. Privacy-risk assessment is a bounded indicator, not a decision on the processing.
  6. Hard-boundary consistency: an unlawful-processing indicator must yield status=blocked.
  7. No approval / sign-off / closure / filing language, and no send/submit language.
  8. The standing note is present.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_STATUS = {"ready-for-adjudication", "needs-information", "blocked"}
BANDS = {"Low", "Medium", "High", "Unlawful-processing-proximity"}
REVIEW_PATHS = {
    "standard-privacy-sign-off", "dpo-review", "dpo-and-senior-review",
    "return-for-information", "hold-pending-privacy-counsel",
}
APPROVAL_STATES = {"pending", "obtained"}

EVIDENCE_SECTIONS = (
    "processing_purpose", "data_inventory", "legal_basis", "data_sharing",
    "retention", "security", "data_subject_rights", "mitigations",
)
REQUIRED_SECTIONS = EVIDENCE_SECTIONS + (
    "assessment_scope", "privacy_risk_assessment", "recommendation", "approvals",
    "sources_citations", "standing_note_limitations",
)
STANDING_NOTE_KEY = "for human sign-off only"

# Completed regulated actions this draft-only skill must never assert. Written to catch
# assertive/completed statements, not the mere mention of a concept.
DECISION_PATTERNS = [
    r"\bprocessing (is |has been |was )?(approved|authorized|authorised|signed off|cleared to (go live|launch|proceed))\b",
    r"\bdpia (is |has been )?(approved|signed off|closed)\b",
    r"\bassessment (is |has been )?(approved|signed off)\b",
    r"\bwe (have |hereby )?(approved|authorized|authorised|signed off|cleared)\b",
    r"\b(cleared to (go live|launch|proceed))\b",
    r"\blawful basis (set|recorded|established|updated) (in|of) (the )?(system|record|ropa)\b",
    r"\brisk (accepted and closed|accepted on behalf of)\b",
    r"\bcase (is |has been )?closed\b", r"\bcase closed\b",
    r"\b(no further action|no-action)\b",
]
FILING_PATTERNS = [
    r"\b(dpia|pia|assessment|report) (has been |was )?filed\b",
    r"\bfiled (a |the |an )?(dpia|pia|report)\b",
    r"\bwe (have )?filed\b",
    r"\b(prior consultation) (has been |was )?(submitted|completed|filed)\b",
    r"\bsubmitted to (the )?(supervisory authority|regulator|ico|dpa|cnil)\b",
]
SEND_PATTERNS = [
    r"\bwe (have )?(sent|submitted|emailed|dispatched)\b",
    r"\b(assessment|dpia|pia|package|report) (was|has been) (sent|submitted|emailed|dispatched)\b",
    r"\bsent (the|this) (assessment|dpia|pia|package|report)\b",
    r"\bsubmitted (the|this) (assessment|dpia|pia|package|report)\b",
]


def _scan(text: str, patterns, label, errors):
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"{label}: {m.group(0)!r} (draft-only; decisions/filings/sends belong to the human adjudicator)")


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections") or {}

    status = doc.get("packaging_status")
    if status not in ALLOWED_STATUS:
        errors.append(f"disallowed packaging_status {status!r} (allowed: {sorted(ALLOWED_STATUS)}; no decision/sign-off state)")

    # Template fidelity: every required section present.
    for sec in REQUIRED_SECTIONS:
        if sec not in sections:
            errors.append(f"missing required template section: {sec}")

    # No unsupported claims: present evidence sections must cite sources.
    for sec in EVIDENCE_SECTIONS:
        s = sections.get(sec) or {}
        if s.get("status") == "present" and not s.get("citations"):
            errors.append(f"unsupported claim: section {sec} is 'present' but has no citations")
        if s.get("status") not in ("present", "gap", None) and sec in sections:
            errors.append(f"section {sec}: invalid status {s.get('status')!r}")

    # Privacy-risk indicator sanity.
    risk = sections.get("privacy_risk_assessment") or {}
    if risk:
        if risk.get("residual_risk_band") not in BANDS:
            errors.append(f"privacy_risk_assessment: invalid band {risk.get('residual_risk_band')!r}")
        if not isinstance(risk.get("score"), (int, float)):
            errors.append("privacy_risk_assessment: missing numeric score")

    # Hard-boundary consistency.
    hard = bool(doc.get("hard_boundary")) or bool(risk.get("hard_boundary"))
    if hard and status != "blocked":
        errors.append(f"hard boundary present but packaging_status={status!r} (must be 'blocked' and routed to privacy counsel)")
    if risk.get("residual_risk_band") == "Unlawful-processing-proximity" and status != "blocked":
        errors.append("Unlawful-processing-proximity band must yield packaging_status='blocked'")

    # Recommendation must be advisory (path enum).
    rec = sections.get("recommendation") or {}
    if rec and rec.get("recommended_review_path") not in REVIEW_PATHS:
        errors.append(f"recommendation: invalid recommended_review_path {rec.get('recommended_review_path')!r}")

    # Required approvals recorded.
    appr = sections.get("approvals") or {}
    required = appr.get("required") or []
    ledger = appr.get("ledger") or []
    if not required:
        errors.append("approvals.required is empty (required approvals must be recorded)")
    ledger_roles = {e.get("role") for e in ledger if isinstance(e, dict)}
    for role in required:
        if role not in ledger_roles:
            errors.append(f"approvals: required role {role!r} not recorded in ledger")
    for e in ledger:
        st = e.get("status")
        if st not in APPROVAL_STATES:
            errors.append(f"approvals: invalid status {st!r} for {e.get('role')!r}")
        if st == "obtained" and not (e.get("approver") and e.get("date")):
            errors.append(f"approvals: {e.get('role')!r} marked obtained without approver + date (no fabricated sign-off)")

    # Sources aggregate present.
    src = sections.get("sources_citations") or {}
    if "sources_citations" in sections and not src.get("citations"):
        errors.append("sources_citations: aggregate citation list is empty")

    # Language screens over the whole package.
    scan = json.dumps(doc) + " " + str(doc.get("narrative", ""))
    _scan(scan, DECISION_PATTERNS, "decision/sign-off language detected", errors)
    _scan(scan, FILING_PATTERNS, "filing language detected", errors)
    _scan(scan, SEND_PATTERNS, "send/submit language detected", errors)

    # Standing note.
    note = (sections.get("standing_note_limitations") or {}).get("text", "")
    if STANDING_NOTE_KEY not in note.lower() and STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note (draft-only / no-decision limitation)")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pia_package_example.json"
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
