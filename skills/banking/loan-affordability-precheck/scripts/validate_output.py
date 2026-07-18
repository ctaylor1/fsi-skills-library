#!/usr/bin/env python3
"""Deterministic output validation for loan-affordability-precheck.

Validates the final precheck pack (the calculate_or_transform core + a narrative) before it is
presented or delivered. This is the R3 tier guardrail: the skill is decision SUPPORT only — it
may not make or imply a credit approval/denial, eligibility/qualification determination, or
adverse-action decision, and it must show its assumptions and stress cases reproducibly.

Checks:
  1. Reproducible payment tie-out: baseline.proposed_payment == amortized recompute (+escrow).
  2. Band tie-out: baseline.affordability_band == deterministic mapping from its own DTIs +
     residual against the carried thresholds; every stress scenario band ties out too.
  3. Stress coverage: at least one rate-stress and one income-stress scenario present.
  4. No credit-decision / adverse-action / qualification / "you should borrow" advice language
     (scanned in narrative + notes + scenario labels + assumptions, NOT the disclaimer field).
  5. Standing disclaimer present.
  6. Assumptions block present and non-empty.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Indicative affordability estimate only; not a credit decision, approval, denial, "
              "or adverse-action determination. Any lending decision requires human underwriting.")

# Prohibited credit-decision / adverse-action / qualification / directive-advice assertions.
# The disclaimer legitimately contains words like "approval"/"denial"/"adverse-action", so the
# disclaimer field is excluded from the scan (see _scan_text below).
DECISION_PATTERNS = [
    r"\bpre-?approved\b",
    r"\bapproved for\b",
    r"\b(loan|mortgage|application|credit)\s+(is\s+)?approved\b",
    r"\byou\s+(are|'re)\s+approved\b",
    r"\byou\s+(do\s+not|don't)\s+qualify\b",
    r"\byou\s+qualify\b",
    r"\bqualif(y|ies|ied)\s+for\s+(the|this|a|an)\b",
    r"\bineligible\b",
    r"\byou\s+(are|'re)\s+(not\s+)?eligible\b",
    r"\beligible\s+for\s+(the|this|a|an)\s+(loan|mortgage|credit|amount)\b",
    r"\b(loan|mortgage|application|credit)\s+(is\s+)?(denied|declined|rejected)\b",
    r"\byou\s+(are|'re)\s+(denied|declined|rejected)\b",
    r"\bwe\s+(will|can|are\s+able\s+to)\s+lend\b",
    r"\bcreditworthy\b",
    r"\badverse\s+action\s+(notice|taken|decision|letter)\b",
    r"\bguarantee(d|s)?\s+(approval|the\s+loan|financing)\b",
    r"\brecommend(ing)?\s+(approval|denial|to\s+approve|to\s+deny)\b",
    r"\byou\s+should\s+(take\s+out|apply\s+for|get|borrow|refinance)\b",
    r"\bi\s+recommend\s+(you|that\s+you)\s+(borrow|take|apply)\b",
]

BANDS = ("Within typical guidelines", "Approaching typical limits", "Outside typical guidelines")


def _band(front, back, residual, thr):
    if front <= thr["frontend_dti_max"] and back <= thr["backend_dti_max"] \
            and residual >= thr["residual_income_min"]:
        return "Within typical guidelines"
    if back <= thr["backend_dti_stretch"] and residual >= 0:
        return "Approaching typical limits"
    return "Outside typical guidelines"


def _amortized(principal, annual_rate_pct, term_months):
    r = (annual_rate_pct / 100.0) / 12.0
    n = int(term_months)
    if r == 0:
        return principal / n
    return principal * r / (1.0 - (1.0 + r) ** (-n))


def _scan_text(pack) -> str:
    parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    parts += [str(a) for a in (pack.get("assumptions") or [])]
    for s in (pack.get("stress_scenarios") or []):
        parts.append(str(s.get("scenario", "")))
    return " ".join(parts)


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    thr = pack.get("thresholds")
    if not isinstance(thr, dict) or not all(
            k in thr for k in ("frontend_dti_max", "backend_dti_max", "backend_dti_stretch", "residual_income_min")):
        errors.append("pack missing thresholds block (needed for reproducible band tie-out)")
        thr = None

    loan = pack.get("loan")
    base = pack.get("baseline") or {}
    if not isinstance(loan, dict) or not all(k in loan for k in ("principal", "annual_rate_pct", "term_months")):
        errors.append("pack missing loan block (needed for payment tie-out)")
    else:
        escrow = (float(loan.get("monthly_tax", 0) or 0) + float(loan.get("monthly_insurance", 0) or 0)
                  + float(loan.get("monthly_hoa", 0) or 0))
        exp_pay = round(_amortized(float(loan["principal"]), float(loan["annual_rate_pct"]),
                                   int(loan["term_months"])) + escrow, 2)
        got_pay = base.get("proposed_payment")
        if got_pay is None or abs(float(got_pay) - exp_pay) > 0.02:
            errors.append(f"baseline proposed_payment {got_pay} != recomputed {exp_pay}")

    # Baseline band tie-out
    if thr is not None:
        exp_band = _band(float(base.get("front_end_dti", 0)), float(base.get("back_end_dti", 0)),
                         float(base.get("residual_income", 0)), thr)
        if base.get("affordability_band") != exp_band:
            errors.append(f"baseline affordability_band {base.get('affordability_band')!r} != deterministic {exp_band!r}")
        if pack.get("affordability_band") != base.get("affordability_band"):
            errors.append("top-level affordability_band does not match baseline.affordability_band")

    # Stress scenarios: coverage + per-scenario band tie-out
    scenarios = pack.get("stress_scenarios") or []
    kinds = {s.get("kind") for s in scenarios}
    if "rate" not in kinds:
        errors.append("no rate-stress scenario present")
    if "income" not in kinds:
        errors.append("no income-stress scenario present")
    if thr is not None:
        for s in scenarios:
            exp = _band(float(s.get("front_end_dti", 0)), float(s.get("back_end_dti", 0)),
                        float(s.get("residual_income", 0)), thr)
            if s.get("affordability_band") != exp:
                errors.append(f"stress scenario {s.get('scenario')!r} band {s.get('affordability_band')!r} != deterministic {exp!r}")

    # Language screen (excludes the disclaimer field by construction)
    text = _scan_text(pack)
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"credit-decision/advice language detected: {m.group(0)!r} (R3 supports a decision; it does not make one)")

    # Standing disclaimer
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    # Assumptions transparency
    if not (pack.get("assumptions") or []):
        errors.append("assumptions block missing or empty (affordability estimate must show its assumptions)")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "precheck_pack.json"
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
