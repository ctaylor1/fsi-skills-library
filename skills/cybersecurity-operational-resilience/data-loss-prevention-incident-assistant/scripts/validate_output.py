#!/usr/bin/env python3
"""Deterministic output validation for data-loss-prevention-incident-assistant.

Screens a DRAFT DLP incident-assessment package before it is presented to a human
privacy/incident-response reviewer. It fails closed (exit 1) on any control breach. This is a
Draft & package (R3) guardrail: the package enriches, classifies, estimates exposure,
preserves evidence references, and recommends — it NEVER determines a breach, dispositions or
closes an incident, decides a notification obligation, contains/blocks/revokes/deletes, files,
or sends. Checks:
  1. package_status is an allowed DRAFT status (no decision/closure/containment state).
  2. All required template sections are present (template fidelity).
  3. No unsupported claims: every 'present' evidence section carries citations.
  4. Per-event assessment records use only allowed dispositions; approved-suppressed records
     use an APPROVED rule id + evidence; escalated records carry cited assessment context.
  5. severity_band is consistent with severity_score (+ active-exfiltration override).
  6. Required human approvals recorded (ledger covers every required role; any 'obtained'
     entry names an approver + date).
  7. Hard-boundary consistency: an active-exfiltration hard boundary forces package_status=blocked.
  8. No breach-determination / closure / containment / filing / send-submit language.
  9. The standing note is present.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_STATUS = {"ready-for-review", "needs-data", "blocked"}
ALLOWED_DISPOSITIONS = {"prepared-for-review", "approved-suppressed", "needs-data", "correlated-duplicate"}
APPROVED_SUPPRESSIONS = {"SUP-DUP-01", "SUP-SANCTIONED-01", "SUP-FP-PATTERN-01"}

REQUIRED_SECTIONS = (
    "incident_batch_overview", "event_enrichment", "data_classification", "exposure_assessment",
    "correlation_deduplication", "severity_prioritization", "suppression_log",
    "evidence_preservation", "escalation_routing", "approvals", "sources_citations",
    "standing_note_limitations",
)
# Sections that assert facts about the environment and therefore must cite sources when present.
EVIDENCE_SECTIONS = ("event_enrichment", "data_classification", "exposure_assessment", "evidence_preservation")
APPROVAL_STATES = {"pending", "obtained"}
STANDING_NOTE_KEY = "for privacy/ir review and human adjudication only"

S1_MIN, S2_MIN = 9, 5

# Completed regulated actions this draft-only skill must never assert. Written to catch
# assertive/completed statements, not the mere mention of a concept.
DECISION_PATTERNS = [
    r"\bconfirmed (a |the )?(data )?breach\b",
    r"\bdeclared (a |the )?(data )?breach\b",
    r"\bbreach (is |was |has been )?confirmed\b",
    r"\bclose(d)? (the )?(incident|case|event)\b",
    r"\b(incident|case|event) (is |was |has been )?closed\b",
    r"\bclosed as (a )?(false positive|benign|no[- ]loss)\b",
    r"\bno further action (is )?(required|needed)\b", r"\bno-action\b",
    r"\b(cleared|exonerat)\b",
    r"\bdispositioned as (benign|confirmed|malicious)\b",
    r"\bnotification (is )?(required|not required)\b",
    r"\bis (a )?reportable breach\b",
]
CONTAINMENT_PATTERNS = [
    r"\b(blocked|quarantined|revoked) (the )?(transfer|upload|email|file|user|account)\b",
    r"\b(disabled|locked|suspended|deprovisioned) (the )?(account|identity|user)\b",
    r"\b(revoked|rotated) (the )?(access|credential|token|key)s?\b",
    r"\b(deleted|wiped|purged|recalled) (the )?(data|file|message|email)\b",
    r"\b(blocked|blacklisted) (the )?(destination|domain|url|recipient)\b",
    r"\bwe (have )?(blocked|quarantined|revoked|disabled|deleted|contained|recalled)\b",
    r"\bcontainment (is )?complete\b", r"\bplaced (a )?(dlp )?block\b",
]
FILING_PATTERNS = [
    r"\b(created|opened|updated|logged) (the |a |an )?(ticket|case|incident) in (servicenow|jira|the dlp console|the case system)\b",
    r"\bwrote (to )?(the )?(dlp console|case management|siem)\b",
    r"\bupdated the (case|incident) (status )?in (servicenow|the dlp console)\b",
    r"\bfiled (the |a )?(breach|incident) (report|notification)\b",
]
SEND_PATTERNS = [
    r"\bwe (have )?(sent|submitted|emailed|dispatched|notified)\b",
    r"\b(package|report|assessment|notification) (was|has been) (sent|submitted|emailed|dispatched|filed)\b",
    r"\bsent (the|this) (package|report|assessment|notification)\b",
    r"\bsubmitted (the|this) (package|report|notification)\b",
    r"\bnotified (the )?(regulator|customer|data subject|supervisory authority)\b",
    r"\bissued (a )?breach notification\b",
]


def _expected_band(score, active_exfiltration) -> str:
    if score >= S1_MIN or active_exfiltration:
        return "S1 (Critical)"
    return "S2 (High)" if score >= S2_MIN else "S3 (Moderate)"


def _scan(text: str, patterns, label, errors):
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"{label}: {m.group(0)!r} (draft-only; breach determinations/containment/filings/sends belong to the human privacy/IR owner)")


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections") or {}

    status = doc.get("package_status")
    if status not in ALLOWED_STATUS:
        errors.append(f"disallowed package_status {status!r} (allowed: {sorted(ALLOWED_STATUS)}; no decision/closure/containment state)")

    # Template fidelity.
    for sec in REQUIRED_SECTIONS:
        if sec not in sections:
            errors.append(f"missing required template section: {sec}")

    # No unsupported claims: present evidence sections must cite sources.
    for sec in EVIDENCE_SECTIONS:
        s = sections.get(sec) or {}
        st = s.get("status")
        if st == "present" and not s.get("citations"):
            errors.append(f"unsupported claim: section {sec} is 'present' but has no citations")
        if sec in sections and st not in ("present", "empty", None):
            errors.append(f"section {sec}: invalid status {st!r}")

    # Per-event assessment records.
    records = doc.get("assessments") or []
    if not records:
        errors.append("assessment output has no per-event records")
    for r in records:
        eid = r.get("event_id", "?")
        disp = r.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{eid}: disallowed disposition {disp!r} (breach determination/closure/containment not permitted in assessment)")
        sup = r.get("suppression")
        if disp == "approved-suppressed":
            if not sup or sup.get("rule_id") not in APPROVED_SUPPRESSIONS:
                errors.append(f"{eid}: suppression must use an approved rule id, got {sup and sup.get('rule_id')!r}")
            elif not sup.get("evidence"):
                errors.append(f"{eid}: suppression {sup.get('rule_id')} missing evidence")
        if sup and sup.get("rule_id") not in APPROVED_SUPPRESSIONS:
            errors.append(f"{eid}: unapproved suppression rule {sup.get('rule_id')!r}")
        if disp == "prepared-for-review":
            ctx = r.get("assessment_context") or {}
            if not ctx:
                errors.append(f"{eid}: escalated but no assessment_context bundle")
            elif not ctx.get("citations"):
                errors.append(f"{eid}: assessment_context missing citations")
        exp = _expected_band(r.get("severity_score", 0), bool(r.get("active_exfiltration")))
        if r.get("severity_band") != exp:
            errors.append(f"{eid}: severity_band {r.get('severity_band')!r} != expected {exp!r} for score {r.get('severity_score')}")

    # Hard-boundary consistency.
    hard = bool(doc.get("hard_boundary")) or any(r.get("hard_boundary_event") for r in records)
    if hard and status != "blocked":
        errors.append(f"hard boundary present but package_status={status!r} (must be 'blocked' and routed to incident response)")

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
    _scan(scan, DECISION_PATTERNS, "breach-determination/closure language detected", errors)
    _scan(scan, CONTAINMENT_PATTERNS, "containment/response language detected", errors)
    _scan(scan, FILING_PATTERNS, "filing / system-of-record-write language detected", errors)
    _scan(scan, SEND_PATTERNS, "send/submit language detected", errors)

    # Standing note.
    note = (sections.get("standing_note_limitations") or {}).get("text", "")
    if STANDING_NOTE_KEY not in note.lower() and STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note (draft-only / no-breach-determination limitation)")

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
