#!/usr/bin/env python3
"""Deterministic output validation for reserving-analysis-assistant.

Enforces the R2 "Draft & package" guardrails before a reserve-analysis exhibit is handed to
a qualified actuary for review, selection, and approval:
  1. Template fidelity: every required output-template section is present.
  2. Required approvals recorded: the actuarial sign-off block lists the qualified actuary and
     is PENDING (the skill never self-approves a reserve selection or opinion).
  3. Method fidelity: every analysed segment uses an approved development method.
  4. Completeness + source mapping: a packageable segment carries development factors, CDFs,
     per-origin ultimate/IBNR, totals, and citations on every figure.
  5. No unsupported assertions: per-origin and total ultimate/IBNR tie out exactly
     (ultimate == reported + IBNR); no reserve-adequacy opinion, no booking/filing, no
     "signed opinion" language.
  6. The standing note (draft-only; no selection/booking; no opinion) is present.

Fails closed on any miss so a defective or overreaching analysis cannot be presented as a
finished, approved, or bookable reserve.

Usage: python validate_output.py analysis.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = {
    "Cover and valuation basis",
    "Data sources and reconciliation",
    "Development method and factors",
    "Indicated ultimate and IBNR",
    "Severity, frequency, and large-loss analysis",
    "Uncertainty and sensitivity",
    "Assumptions and limitations",
    "Actuarial review and approval",
}
APPROVED_METHODS = {
    "volume-weighted chain-ladder",
    "simple-average chain-ladder",
}
SELF_APPROVED = {"approved", "signed", "accepted", "final", "booked"}
STANDING_NOTE = (
    "Draft reserving analysis for qualified actuarial review only; this skill computes "
    "method-indicated estimates from the supplied data, does not select or book carried "
    "reserves, does not issue or sign a Statement of Actuarial Opinion, and does not opine "
    "on reserve adequacy"
)
TOL = 0.05

# Binding reserve opinion / adequacy language this skill must never assert.
OPINION_PATTERNS = [
    r"\breserves are (adequate|sufficient|deficient|inadequate|reasonable)\b",
    r"\b(the )?ibnr is (adequate|sufficient|appropriate)\b",
    r"\bstatement of actuarial opinion\b",
    r"\bi opine\b", r"\bwe opine\b", r"\bin my opinion the reserves\b",
    r"\bactuarial opinion (is|that)\b", r"\breserves? (meet|satisfy) (the )?requirements\b",
]
# Booking / filing / selection-as-final language (draft-only skill).
BOOKING_PATTERNS = [
    r"\bbook (the )?(reserve|ibnr)\b", r"\bpost (the )?(reserve|ibnr) to (the )?(gl|general ledger|ledger)\b",
    r"\brecord (the )?(reserve|ibnr) in\b", r"\bcarried reserve is (set|selected|final)\b",
    r"\bfile[d]? (the )?(opinion|statement of actuarial opinion|reserves?)\b",
    r"\bsubmitted to (the )?(board|regulator|naic|state)\b", r"\bsigned (the )?opinion\b",
    r"\bfinal selected reserve\b",
]


def _tie_out(ultimate, reported, ibnr):
    try:
        return abs(float(ultimate) - (float(reported) + float(ibnr))) <= TOL
    except (TypeError, ValueError):
        return False


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    # 1. Template fidelity
    document = doc.get("document") or {}
    sections = set(document.get("sections") or [])
    missing_sections = REQUIRED_SECTIONS - sections
    if missing_sections:
        errors.append(f"missing required template section(s): {sorted(missing_sections)}")

    # 2. Required approvals recorded (and never self-approved)
    approvals = document.get("approvals") or []
    if not approvals:
        errors.append("no required approvals recorded in the document approval block")
    else:
        if not any(re.search(r"actuary", str(a.get("role", "")), re.I) for a in approvals):
            errors.append("required approvals do not include a qualified/appointed actuary")
        for a in approvals:
            st = str(a.get("status", "")).lower()
            if st in SELF_APPROVED:
                errors.append(f"approval for {a.get('role')!r} is pre-marked {st!r}; the skill must not self-approve (status must be pending/required)")
            elif st not in ("pending", "required"):
                errors.append(f"approval for {a.get('role')!r} has an invalid status {a.get('status')!r} (expected pending/required)")

    segments = doc.get("segments") or []
    if not segments:
        errors.append("analysis output has no segments")

    for s in segments:
        sid = s.get("segment_id", "?")
        method = s.get("method")
        if method is not None and method not in APPROVED_METHODS:
            errors.append(f"{sid}: unapproved development method {method!r}")

        if not s.get("packageable"):
            continue

        # 3/4. Completeness + source mapping for a packageable segment
        if s.get("status") != "draft-analysis":
            errors.append(f"{sid}: packageable but status is {s.get('status')!r} (expected draft-analysis)")
        if not s.get("development_factors"):
            errors.append(f"{sid}: packageable but development_factors are empty")
        if not s.get("cdf_to_ultimate"):
            errors.append(f"{sid}: packageable but cdf_to_ultimate is empty")
        if not s.get("citations"):
            errors.append(f"{sid}: packageable but has no citations")

        origins = s.get("origin_results") or []
        if not origins:
            errors.append(f"{sid}: packageable but origin_results is empty")
        for o in origins:
            if not o.get("citations"):
                errors.append(f"{sid}: origin {o.get('origin')!r} figure has no citation (source mapping incomplete)")
            if not _tie_out(o.get("ultimate"), o.get("reported"), o.get("ibnr")):
                errors.append(f"{sid}: origin {o.get('origin')!r} tie-out fails: ultimate != reported + IBNR")

        totals = s.get("totals") or {}
        if origins:
            sum_ult = sum(float(o.get("ultimate", 0)) for o in origins)
            sum_rep = sum(float(o.get("reported", 0)) for o in origins)
            sum_ibnr = sum(float(o.get("ibnr", 0)) for o in origins)
            if abs(float(totals.get("ultimate", 0)) - sum_ult) > TOL * max(1, len(origins)):
                errors.append(f"{sid}: totals.ultimate does not equal the sum of origin ultimates")
            if abs(float(totals.get("reported", 0)) - sum_rep) > TOL * max(1, len(origins)):
                errors.append(f"{sid}: totals.reported does not equal the sum of origin reported")
            if abs(float(totals.get("ibnr", 0)) - sum_ibnr) > TOL * max(1, len(origins)):
                errors.append(f"{sid}: totals.ibnr does not equal the sum of origin IBNR")
        if not _tie_out(totals.get("ultimate"), totals.get("reported"), totals.get("ibnr")):
            errors.append(f"{sid}: totals tie-out fails: ultimate != reported + IBNR")

        ra = s.get("reserve_analysis") or {}
        if not ra.get("reviewer_signoff_required"):
            errors.append(f"{sid}: reserve_analysis missing reviewer_signoff_required=true")
        if not ra.get("actuarial_review_required"):
            errors.append(f"{sid}: reserve_analysis missing actuarial_review_required=true")

    # 5. Prohibited opinion / booking / filing language
    scan = json.dumps(segments) + " " + json.dumps(document) + " " + str(doc.get("narrative", ""))
    for pat in OPINION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited reserve-opinion/adequacy language detected: {m.group(0)!r} (this skill never opines on adequacy)")
    for pat in BOOKING_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited booking/filing language detected: {m.group(0)!r} (this skill drafts only; it never books, files, or signs)")

    # 6. Standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "analysis_example.json"
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
