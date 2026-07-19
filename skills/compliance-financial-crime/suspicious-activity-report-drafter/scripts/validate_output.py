#!/usr/bin/env python3
"""Deterministic output validation for suspicious-activity-report-drafter.

Screens a draft SAR package before it is presented for compliance quality review. It fails
closed (exit 1) on any control breach. This is a Draft & package (R3) guardrail: the package
drafts and recommends, it never decides, files, or sends. Checks:
  1. packaging_status is an allowed DRAFT status (no determination/closure/filed states).
  2. All required template sections are present (template fidelity).
  3. No unsupported claims: chronology events, the narrative, the evidence index, the
     investigation rationale, and supported typologies all carry citations.
  4. Amount & chronology tie-outs reconcile: a `ready-for-quality-review` package must have a
     passing tie-out, full party coverage, a complete 5W+H narrative, and supported
     typologies; a tie-out that claims 'pass' must actually reconcile.
  5. No prohibited speculation / conclusions of guilt (fact-based only).
  6. No file/no-file determination, closure, filing, or send/submit language.
  7. Required human approvals are recorded (ledger covers every required role; any 'obtained'
     entry names an approver + date).
  8. Hard-boundary consistency: a hard boundary must yield packaging_status=blocked.
  9. The standing note is present.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_STATUS = {"ready-for-quality-review", "needs-evidence", "blocked"}
REVIEW_PATHS = {"quality-review-and-compliance-approval", "return-for-evidence",
                "hold-pending-investigation"}
APPROVAL_STATES = {"pending", "obtained"}

REQUIRED_SECTIONS = (
    "filing_header", "subjects", "accounts_instruments", "activity_summary", "chronology",
    "amount_tie_out", "typology_assessment", "narrative", "evidence_index",
    "investigation_rationale", "recommendation", "approvals", "sources_citations",
    "standing_note_limitations",
)
WHO_WHAT = ("who", "what", "when", "where", "why", "how")
STANDING_NOTE_KEY = "for compliance quality review and human filing only"

# Completed regulated actions this draft-only skill must never assert (assertive/completed
# statements, not the mere mention of a concept).
DETERMINATION_PATTERNS = [
    r"\bno sar (is )?(warranted|required|needed|necessary)\b",
    r"\bsar is (not )?(warranted|required|justified)\b",
    r"\bwe (have )?determined (that )?(the )?(activity|subject|customer)\b",
    r"\bcase (is |has been )?closed\b", r"\bcase closed\b",
    r"\b(cleared|exonerat|no further action|no-action)\b",
    r"\bdisposition(ed)? (the|this) case\b",
]
FILING_PATTERNS = [
    r"\b(sar|str|ctr|report) (has been |was )?(filed|e-filed|efiled|submitted)\b",
    r"\bfiled (a |the |an )?(sar|str|ctr|report)\b",
    r"\bwe (have )?(filed|e-filed|efiled)\b",
    r"\bsubmitted to (fincen|the regulator|bsa e-filing)\b",
    r"\bfiled with fincen\b", r"\be-filed\b",
]
SEND_PATTERNS = [
    r"\bwe (have )?(sent|submitted|emailed|dispatched|transmitted)\b",
    r"\b(package|report|sar|narrative|dossier) (was|has been) (sent|submitted|emailed|dispatched|transmitted)\b",
    r"\bsent (the|this) (package|report|sar|narrative)\b",
]
# Prohibited speculation / conclusions of guilt — SAR narratives must be fact-based.
SPECULATION_PATTERNS = [
    r"\bobviously\b", r"\bwithout (a )?doubt\b", r"\bundoubtedly\b",
    r"\bmust be (laundering|a criminal|money laundering|structuring)\b",
    r"\b(the )?(subject|customer|account holder) is (a |an )?(criminal|money launderer|terrorist|fraudster|guilty)\b",
    r"\bwe (are (certain|sure)|guarantee|conclude that)\b",
    r"\bdefinitely (laundering|criminal|illegal|structuring)\b",
    r"\bproves (that )?(the )?(subject|customer) (committed|is)\b",
]


def _scan(text: str, patterns, label, errors):
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"{label}: {m.group(0)!r}")


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections") or {}

    status = doc.get("packaging_status")
    if status not in ALLOWED_STATUS:
        errors.append(f"disallowed packaging_status {status!r} (allowed: {sorted(ALLOWED_STATUS)}; "
                      f"no determination/closure/filed state)")

    # Template fidelity.
    for sec in REQUIRED_SECTIONS:
        if sec not in sections:
            errors.append(f"missing required template section: {sec}")

    # No unsupported claims — chronology events must be cited.
    chron = sections.get("chronology") or {}
    for e in chron.get("events") or []:
        if not e.get("citation"):
            errors.append(f"unsupported claim: chronology event {e.get('txn_id')!r} has no citation")
    if chron.get("uncited_events"):
        errors.append(f"unsupported claim: uncited chronology events {chron.get('uncited_events')}")

    # Narrative: 5W+H must be complete and cited.
    narr = sections.get("narrative") or {}
    if "narrative" in sections:
        missing = [w for w in WHO_WHAT if not str(narr.get(w) or "").strip()]
        if missing:
            errors.append(f"narrative incomplete: missing {missing} (5W+H must all be present)")
        if not narr.get("citations"):
            errors.append("unsupported claim: narrative has no supporting citations")

    # Evidence index and rationale must be cited.
    ei = sections.get("evidence_index") or {}
    if "evidence_index" in sections:
        if not ei.get("entries"):
            errors.append("evidence_index is empty (narrative facts must be indexed to sources)")
        for en in ei.get("entries") or []:
            if not en.get("citation"):
                errors.append(f"unsupported claim: evidence_index fact {en.get('fact')!r} has no citation")
    rat = sections.get("investigation_rationale") or {}
    if "investigation_rationale" in sections and not rat.get("citations"):
        errors.append("unsupported claim: investigation_rationale has no citations")

    # Typology support.
    typ = sections.get("typology_assessment") or {}
    for t in typ.get("typologies") or []:
        if t.get("supported") and not t.get("in_library"):
            errors.append(f"typology {t.get('code')!r} marked supported but not in the approved library")
        if t.get("supported") and t.get("missing_indicators"):
            errors.append(f"typology {t.get('code')!r} marked supported with missing indicators {t.get('missing_indicators')}")

    # Amount & chronology tie-out integrity.
    tie = sections.get("amount_tie_out") or {}
    if tie:
        ct, dt = tie.get("computed_total"), tie.get("declared_total")
        reconciles = (isinstance(ct, (int, float)) and isinstance(dt, (int, float))
                      and abs(float(ct) - float(dt)) <= 0.005
                      and tie.get("computed_period") == tie.get("declared_period")
                      and (tie.get("declared_count") is None or tie.get("declared_count") == tie.get("computed_count")))
        if tie.get("status") == "pass" and not reconciles:
            errors.append("amount tie-out claims 'pass' but totals/period/count do not reconcile")
        if tie.get("status") not in ("pass", "break"):
            errors.append(f"amount_tie_out: invalid status {tie.get('status')!r}")

    # Ready-for-quality-review requires everything to reconcile.
    if status == "ready-for-quality-review":
        if tie.get("status") != "pass":
            errors.append("ready-for-quality-review requires a passing amount/chronology tie-out")
        if not (sections.get("subjects") or {}).get("covered", True):
            errors.append("ready-for-quality-review requires full party coverage (uncovered parties present)")
        if not (sections.get("typology_assessment") or {}).get("all_supported", True):
            errors.append("ready-for-quality-review requires all declared typologies to be supported")
        if not narr.get("complete", True):
            errors.append("ready-for-quality-review requires a complete 5W+H narrative")
        if doc.get("hard_boundary"):
            errors.append("ready-for-quality-review inconsistent with hard_boundary=true")

    # Recommendation must be advisory (path enum).
    rec = sections.get("recommendation") or {}
    if rec and rec.get("recommended_review_path") not in REVIEW_PATHS:
        errors.append(f"recommendation: invalid recommended_review_path {rec.get('recommended_review_path')!r}")

    # Required approvals recorded.
    appr = sections.get("approvals") or {}
    required = appr.get("required") or []
    ledger = appr.get("ledger") or []
    if "approvals" in sections and not required:
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

    # Hard-boundary consistency.
    if doc.get("hard_boundary") and status != "blocked":
        errors.append(f"hard boundary present but packaging_status={status!r} (must be 'blocked' and routed to the investigator)")

    # Sources aggregate present.
    src = sections.get("sources_citations") or {}
    if "sources_citations" in sections and not src.get("citations"):
        errors.append("sources_citations: aggregate citation list is empty")

    # Language screens over the whole package.
    scan = json.dumps(doc) + " " + str(doc.get("narrative", ""))
    _scan(scan, DETERMINATION_PATTERNS, "determination/closure language detected", errors)
    _scan(scan, FILING_PATTERNS, "filing language detected", errors)
    _scan(scan, SEND_PATTERNS, "send/submit language detected", errors)
    _scan(scan, SPECULATION_PATTERNS, "prohibited speculation detected", errors)

    # Standing note.
    note = (sections.get("standing_note_limitations") or {}).get("text", "")
    if STANDING_NOTE_KEY not in note.lower() and STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note (draft-only / no-determination / no-filing limitation)")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "sar_package_example.json"
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
