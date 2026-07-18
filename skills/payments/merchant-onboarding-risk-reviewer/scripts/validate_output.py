#!/usr/bin/env python3
"""Deterministic output validation for merchant-onboarding-risk-reviewer.

Validates the final review pack (the calculate_or_transform core + a narrative) before it is
presented or delivered to a human adjudicator. This is the R3 prohibited-decision screen: it
fails closed on any onboarding-decision, case-closure, or filing/system-of-record language,
and on any recommendation that does not tie out to the deterministic mapping.

Checks:
  1. fired_findings ties out to findings[].fired (no tampering).
  2. Every fired finding has >= 1 cited evidence row.
  3. recommendation equals the deterministic mapping from the fired-finding set.
  4. recommendation is one of the allowed bands and adjudication_required is true.
  5. Recommend-Approve-with-Conditions carries a non-empty conditions list.
  6. evidence_incomplete fired => evidence_completeness.missing is non-empty.
  7. No decision / closure / filing language in narrative, notes, finding reasons, or conditions.
  8. The standing disclaimer is present (verbatim) in the disclaimer field.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

# Fixed severity contract — mirrors scripts/calculate_or_transform.py (kept local so this
# screen is self-contained and can validate any pack, however produced).
BLOCKING = {"sanctions_screening", "prohibited_business_model"}
INCOMPLETE = {"evidence_incomplete"}
ELEVATED = {
    "restricted_business_model", "adverse_media", "beneficial_ownership_gap",
    "high_risk_geography", "pep_ownership", "expected_activity_outsized",
    "credit_exposure", "website_product_risk",
}
ALLOWED_RECOMMENDATIONS = {
    "Recommend-Approve", "Recommend-Approve-with-Conditions",
    "Recommend-Decline", "Escalate-Insufficient-Evidence",
}
DISCLAIMER = ("Recommendation and evidence only; not an onboarding decision. No approval, "
              "decline, boarding, filing, or system-of-record change has been made. Human "
              "adjudication is required.")

# Onboarding-decision / case-closure / filing language an R3 decision-support skill must
# never assert (word-boundary patterns; the enum recommendation/disclaimer are not scanned).
DECISION_PATTERNS = [
    r"\bmerchant (is|was|has been) (approved|declined|boarded|onboarded|rejected)\b",
    r"\bwe (have |hereby )?(approve|approved|decline|declined|board|boarded|reject|rejected) (the )?merchant\b",
    r"\b(approve|board|onboard|decline|reject) the merchant\b",
    r"\bboarded the merchant\b",
    r"\bonboarding (is )?(complete|approved|finalized|done)\b",
    r"\baccount (is |has been )?(opened|activated|boarded)\b",
    r"\bfinal (onboarding )?decision\b",
    r"\bdecision:\s*(approve|approved|decline|declined|reject|rejected)\b",
    r"\bcase closed\b",
    r"\bclos(e|ed|ing) (the |this )?(case|review)\b",
    r"\bfiled? (a )?sar\b",
    r"\bsar (has been |was )?filed\b",
    r"\bwr(ite|itten|ote) to the system of record\b",
    r"\bpost(ed)? to (the )?(boarding|core|system of record)\b",
    r"\bsubmit(ted)? to the (card )?network\b",
]


def _recommendation(fired: set) -> str:
    if BLOCKING & fired:
        return "Recommend-Decline"
    if INCOMPLETE & fired:
        return "Escalate-Insufficient-Evidence"
    if ELEVATED & fired:
        return "Recommend-Approve-with-Conditions"
    return "Recommend-Approve"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []

    fired_from_findings = {f["finding"] for f in findings if f.get("fired")}
    declared_fired = set(pack.get("fired_findings") or [])
    if fired_from_findings != declared_fired:
        errors.append(f"fired_findings {sorted(declared_fired)} != findings[].fired {sorted(fired_from_findings)}")

    for f in findings:
        if f.get("fired"):
            ev = f.get("evidence") or []
            if not ev:
                errors.append(f"fired finding {f.get('finding')} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired finding {f.get('finding')} evidence row missing citation")

    exp = _recommendation(fired_from_findings)
    rec = pack.get("recommendation")
    if rec not in ALLOWED_RECOMMENDATIONS:
        errors.append(f"recommendation {rec!r} not in {sorted(ALLOWED_RECOMMENDATIONS)}")
    if rec != exp:
        errors.append(f"recommendation {rec!r} != deterministic {exp!r} for fired={sorted(fired_from_findings)}")

    if pack.get("adjudication_required") is not True:
        errors.append("adjudication_required must be true (R3 mandatory human adjudication)")

    if rec == "Recommend-Approve-with-Conditions" and not (pack.get("conditions") or []):
        errors.append("Recommend-Approve-with-Conditions requires a non-empty conditions list")

    if "evidence_incomplete" in fired_from_findings:
        if not ((pack.get("evidence_completeness") or {}).get("missing")):
            errors.append("evidence_incomplete fired but evidence_completeness.missing is empty")

    # scan free text (narrative + notes + finding reasons + conditions); NOT the disclaimer/enum.
    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
        + [str(f.get("reason", "")) for f in findings]
        + [str(c) for c in (pack.get("conditions") or [])]
    )
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"onboarding-decision/closure/filing language detected: {m.group(0)!r} "
                          f"(R3 recommends + evidences; it never decides, closes, or files)")

    if DISCLAIMER.lower() not in str(pack.get("disclaimer", "")).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
