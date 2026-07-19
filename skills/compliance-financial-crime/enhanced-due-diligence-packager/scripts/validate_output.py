#!/usr/bin/env python3
"""Deterministic output validation for enhanced-due-diligence-packager.

Screens a draft EDD package before it is presented to a human adjudicator. It fails closed
(exit 1) on any control breach. This is a Draft & package (R3) guardrail: the package may
recommend, never decide. Checks:
  1. packaging_status is an allowed DRAFT status (no decision/closure/filing states).
  2. All required template sections are present (template fidelity).
  3. No unsupported claims: every 'present' evidence section carries citations.
  4. Required human approvals are recorded (ledger covers every required role; any
     'obtained' entry names an approver + date).
  5. Residual-risk assessment is a bounded indicator, not a rating of record.
  6. Hard-boundary consistency: a hard boundary must yield packaging_status=blocked.
  7. No decision / closure / filing language, and no send/submit language.
  8. The standing note is present.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_STATUS = {"ready-for-adjudication", "needs-evidence", "blocked"}
BANDS = {"Low", "Medium", "High", "Prohibited-proximity"}
REVIEW_PATHS = {
    "standard-adjudication", "edd-committee-adjudication", "senior-management-adjudication",
    "return-for-evidence", "hold-pending-specialist",
}
APPROVAL_STATES = {"pending", "obtained"}

EVIDENCE_SECTIONS = (
    "customer_overview", "source_of_funds", "source_of_wealth", "ownership_control",
    "geography_exposure", "adverse_media", "pep_sanctions_screening", "expected_activity",
    "ongoing_monitoring_controls",
)
REQUIRED_SECTIONS = EVIDENCE_SECTIONS + (
    "edd_trigger_scope", "residual_risk_assessment", "recommendation", "approvals",
    "sources_citations", "standing_note_limitations",
)
STANDING_NOTE_KEY = "for human adjudication only"

# Completed regulated actions this draft-only skill must never assert. Written to catch
# assertive/completed statements, not the mere mention of a concept.
DECISION_PATTERNS = [
    r"\bcustomer (is |has been )?(approved|onboarded|cleared for onboarding)\b",
    r"\brelationship (approved|established|terminated|exited|offboarded)\b",
    r"\baccount (has been |was )?opened\b",
    r"\bwe (have |hereby )?(approved|declined|onboarded|offboarded|exited|retained)\b",
    r"\b(declined|rejected) the (customer|relationship|application)\b",
    r"\bcase (is |has been )?closed\b", r"\bcase closed\b",
    r"\b(cleared|exonerat|no further action|no-action)\b",
    r"\brisk rating (updated|changed|set) (in|of) (the )?(system|record)\b",
    r"\brating of record (updated|changed)\b",
]
FILING_PATTERNS = [
    r"\b(sar|str|ctr|report) (has been |was )?filed\b",
    r"\bfiled (a |the |an )?(sar|str|ctr|report)\b",
    r"\bwe (have )?filed\b", r"\bsubmitted to (fincen|the regulator|ofac)\b",
]
SEND_PATTERNS = [
    r"\bwe (have )?(sent|submitted|emailed|dispatched)\b",
    r"\b(package|dossier|report) (was|has been) (sent|submitted|emailed|dispatched)\b",
    r"\bsent (the|this) (package|dossier|report)\b",
    r"\bsubmitted (the|this) (package|dossier|report)\b",
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
        errors.append(f"disallowed packaging_status {status!r} (allowed: {sorted(ALLOWED_STATUS)}; no decision/closure state)")

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

    # Residual-risk indicator sanity.
    risk = sections.get("residual_risk_assessment") or {}
    if risk:
        if risk.get("residual_risk_band") not in BANDS:
            errors.append(f"residual_risk_assessment: invalid band {risk.get('residual_risk_band')!r}")
        if not isinstance(risk.get("score"), (int, float)):
            errors.append("residual_risk_assessment: missing numeric score")

    # Hard-boundary consistency.
    hard = bool(doc.get("hard_boundary")) or bool(risk.get("hard_boundary"))
    if hard and status != "blocked":
        errors.append(f"hard boundary present but packaging_status={status!r} (must be 'blocked' and routed to a specialist)")
    if risk.get("residual_risk_band") == "Prohibited-proximity" and status != "blocked":
        errors.append("Prohibited-proximity band must yield packaging_status='blocked'")

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
    _scan(scan, DECISION_PATTERNS, "decision/closure language detected", errors)
    _scan(scan, FILING_PATTERNS, "filing language detected", errors)
    _scan(scan, SEND_PATTERNS, "send/submit language detected", errors)

    # Standing note.
    note = (sections.get("standing_note_limitations") or {}).get("text", "")
    if STANDING_NOTE_KEY not in note.lower() and STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note (draft-only / no-decision limitation)")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "edd_package_example.json"
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
