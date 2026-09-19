#!/usr/bin/env python3
"""Deterministic output validation for pc-reserving-analysis-assistant.

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
    "Indicated ultimate and reserve measures",
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
    from insurance_contract import validate_artifact
    errors.extend(validate_artifact(doc.get("artifact"), input_doc=doc.get("calculation_inputs"), output=doc))

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

        measure = "total_unpaid" if s.get("triangle_basis") == "paid" else "ibnr"
        diagonal = "paid" if s.get("triangle_basis") == "paid" else "reported_incurred"
        if s.get("reserve_measure") != measure:
            errors.append(f"{sid}: reserve_measure does not match triangle_basis")
        origins = s.get("origin_results") or []
        if not origins:
            errors.append(f"{sid}: packageable but origin_results is empty")
        for o in origins:
            if not o.get("citations"):
                errors.append(f"{sid}: origin has no citation")
            if s.get("triangle_basis") == "paid" and "ibnr" in o:
                errors.append(f"{sid}: paid development is total unpaid, not IBNR without case outstanding")
            if not _tie_out(o.get("ultimate"), o.get(diagonal), o.get(measure)):
                errors.append(f"{sid}: origin tie-out fails for {measure}")
        totals = s.get("totals") or {}
        if s.get("triangle_basis") == "paid" and "ibnr" in totals:
            errors.append(f"{sid}: paid total cannot be labeled IBNR")
        for key in ("ultimate", diagonal, measure):
            try:
                if abs(float(totals[key]) - sum(float(o[key]) for o in origins)) > TOL * max(1,len(origins)):
                    errors.append(f"{sid}: totals.{key} does not equal sum of origins")
            except (KeyError, TypeError, ValueError):
                errors.append(f"{sid}: missing/non-numeric reserve measure {key}")
        if not _tie_out(totals.get("ultimate"), totals.get(diagonal), totals.get(measure)):
            errors.append(f"{sid}: totals tie-out fails for {measure}")

        ra = s.get("reserve_analysis") or {}
        if not ra.get("reviewer_signoff_required"):
            errors.append(f"{sid}: reserve_analysis missing reviewer_signoff_required=true")
        if not ra.get("actuarial_review_required"):
            errors.append(f"{sid}: reserve_analysis missing actuarial_review_required=true")

    calculation_inputs = doc.get("calculation_inputs")
    if not isinstance(calculation_inputs, dict):
        errors.append("missing calculation_inputs for independent recomputation")
    else:
        try:
            from calculate_or_transform import build
            expected = build(calculation_inputs)
            if doc.get("segments") != expected["segments"] or doc.get("summary") != expected["summary"]:
                errors.append("reserve calculations do not reproduce supplied calculation_inputs")
        except (ValueError, TypeError, KeyError) as exc:
            errors.append(f"invalid calculation_inputs: {exc}")

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
