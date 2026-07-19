#!/usr/bin/env python3
"""Deterministic output validation for security-alert-triage-assistant.

Screens a DRAFT security-alert triage package before it is presented to a human analyst. It
fails closed (exit 1) on any control breach. This is a Draft & package (R3) guardrail: the
package enriches, prioritizes, and recommends — it NEVER decides, closes, contains, files, or
sends. Checks:
  1. package_status is an allowed DRAFT status (no decision/closure/containment state).
  2. All eleven required template sections are present (template fidelity).
  3. No unsupported claims: every 'present' evidence section carries citations.
  4. Per-alert triage records use only allowed dispositions; approved-suppressed records use
     an APPROVED rule id + evidence; escalated records carry cited investigation context.
  5. priority_band is consistent with priority_score (+ known-malicious override).
  6. Required human approvals recorded (ledger covers every required role; any 'obtained'
     entry names an approver + date).
  7. Hard-boundary consistency: an active-compromise hard boundary forces package_status=blocked.
  8. No decision / closure / containment / filing / send-submit language.
  9. The standing note is present.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_STATUS = {"ready-for-analyst", "needs-data", "blocked"}
ALLOWED_DISPOSITIONS = {"prepared-for-investigation", "approved-suppressed", "needs-data", "correlated-duplicate"}
APPROVED_SUPPRESSIONS = {"SUP-DUP-01", "SUP-SCANNER-01", "SUP-MAINT-01"}

REQUIRED_SECTIONS = (
    "triage_batch_overview", "alert_enrichment", "asset_identity_map", "correlation_deduplication",
    "prioritization", "suppression_log", "investigation_context", "recommended_routing",
    "approvals", "sources_citations", "standing_note_limitations",
)
# Sections that assert facts about the environment and therefore must cite sources when present.
EVIDENCE_SECTIONS = ("alert_enrichment", "asset_identity_map", "investigation_context")
APPROVAL_STATES = {"pending", "obtained"}
STANDING_NOTE_KEY = "for analyst investigation only"

P1_MIN, P2_MIN = 9, 5

# Completed regulated actions this draft-only skill must never assert. Written to catch
# assertive/completed statements, not the mere mention of a concept.
DECISION_PATTERNS = [
    r"\bclose(d)? (the )?(alert|case|incident)\b",
    r"\b(alert|case|incident) (is |was |has been )?closed\b",
    r"\bincident (declared|resolved)\b", r"\bdeclared an? incident\b",
    r"\bclosed as (a )?(false positive|benign|no threat)\b",
    r"\bno further action (is )?(required|needed)\b", r"\bno-action\b",
    r"\b(cleared|exonerat)\b",
    r"\bconfirmed (a )?true positive\b", r"\bdispositioned as (benign|malicious)\b",
]
CONTAINMENT_PATTERNS = [
    r"\b(isolated|quarantined|contained) (the )?(host|endpoint|device|asset|account)\b",
    r"\b(disabled|locked|suspended) (the )?(account|identity|user)\b",
    r"\b(blocked|blacklisted) (the )?(ip|domain|url|hash|sender)\b",
    r"\b(reset|rotated) (the )?(credential|password)s?\b",
    r"\b(killed|terminated) (the )?(process|session)\b",
    r"\bwe (have )?(contained|remediated|isolated|blocked|disabled|quarantined)\b",
    r"\bremediation (is )?complete\b", r"\bpushed (a )?block\b",
]
FILING_PATTERNS = [
    r"\b(created|opened|updated|logged) (the |a |an )?(ticket|case|incident) in (servicenow|jira|soar|the siem)\b",
    r"\bwrote (to )?(the )?(siem|soar)\b",
    r"\bupdated the (case|alert) (status )?in (soar|the siem|servicenow)\b",
    r"\bfiled (the |a )?(report|incident)\b",
]
SEND_PATTERNS = [
    r"\bwe (have )?(sent|submitted|emailed|dispatched)\b",
    r"\b(package|report|summary) (was|has been) (sent|submitted|emailed|dispatched)\b",
    r"\bsent (the|this) (package|report|summary)\b",
    r"\bsubmitted (the|this) (package|report)\b",
    r"\bnotified (the )?(customer|regulator)\b",
]


def _expected_band(score, known_malicious) -> str:
    if score >= P1_MIN or known_malicious:
        return "P1 (Critical)"
    return "P2 (High)" if score >= P2_MIN else "P3 (Moderate)"


def _scan(text: str, patterns, label, errors):
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"{label}: {m.group(0)!r} (draft-only; decisions/containment/filings/sends belong to the human analyst / IR process)")


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

    # Per-alert triage records.
    records = doc.get("triage") or []
    if not records:
        errors.append("triage output has no per-alert records")
    for r in records:
        aid = r.get("alert_id", "?")
        disp = r.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{aid}: disallowed disposition {disp!r} (closure/containment/decision not permitted in triage)")
        sup = r.get("suppression")
        if disp == "approved-suppressed":
            if not sup or sup.get("rule_id") not in APPROVED_SUPPRESSIONS:
                errors.append(f"{aid}: suppression must use an approved rule id, got {sup and sup.get('rule_id')!r}")
            elif not sup.get("evidence"):
                errors.append(f"{aid}: suppression {sup.get('rule_id')} missing evidence")
        if sup and sup.get("rule_id") not in APPROVED_SUPPRESSIONS:
            errors.append(f"{aid}: unapproved suppression rule {sup.get('rule_id')!r}")
        if disp == "prepared-for-investigation":
            ctx = r.get("investigation_context") or {}
            if not ctx:
                errors.append(f"{aid}: escalated but no investigation_context bundle")
            elif not ctx.get("citations"):
                errors.append(f"{aid}: investigation_context missing citations")
        exp = _expected_band(r.get("priority_score", 0), bool(r.get("ti_known_malicious")))
        if r.get("priority_band") != exp:
            errors.append(f"{aid}: priority_band {r.get('priority_band')!r} != expected {exp!r} for score {r.get('priority_score')}")

    # Hard-boundary consistency.
    hard = bool(doc.get("hard_boundary")) or any(r.get("hard_boundary_alert") for r in records)
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
    _scan(scan, DECISION_PATTERNS, "decision/closure language detected", errors)
    _scan(scan, CONTAINMENT_PATTERNS, "containment/response language detected", errors)
    _scan(scan, FILING_PATTERNS, "filing / system-of-record-write language detected", errors)
    _scan(scan, SEND_PATTERNS, "send/submit language detected", errors)

    # Standing note.
    note = (sections.get("standing_note_limitations") or {}).get("text", "")
    if STANDING_NOTE_KEY not in note.lower() and STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note (draft-only / no-decision limitation)")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "triage_example.json"
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
