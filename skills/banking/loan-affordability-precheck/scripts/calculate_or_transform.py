#!/usr/bin/env python3
"""Deterministic, explainable affordability computation for loan-affordability-precheck.

Reads a de-identified precheck input (see validate_input.py), computes the proposed monthly
payment (amortization), front-end / back-end DTI, residual income, an INDICATIVE affordability
band from versioned thresholds, and a set of stress scenarios (rate up, income down). Emits a
machine-readable pack the SKILL wraps in a plain-language response.

IMPORTANT: This produces an *indicative affordability estimate and stress cases* only. It never
produces a credit approval, denial, eligibility/qualification determination, adverse-action
decision, or lending commitment. The band mapping is deterministic and documented in
references/domain-rules.md; thresholds are versioned config, never tuned to the individual.

Usage:
  python calculate_or_transform.py precheck.json | --selftest
Prints the precheck JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "frontend_dti_max": 0.28,
    "backend_dti_max": 0.36,
    "backend_dti_stretch": 0.43,
    "residual_income_min": 800.0,
    "stress_rate_bumps_pct": [2.0, 3.0],
    "stress_income_haircuts_pct": [10.0, 20.0],
}
DISCLAIMER = ("Indicative affordability estimate only; not a credit decision, approval, denial, "
              "or adverse-action determination. Any lending decision requires human underwriting.")


def amortized_payment(principal: float, annual_rate_pct: float, term_months: int) -> float:
    """Standard fixed-rate amortized monthly payment. Zero-rate falls back to straight-line."""
    r = (annual_rate_pct / 100.0) / 12.0
    n = int(term_months)
    if r == 0:
        return principal / n
    return principal * r / (1.0 - (1.0 + r) ** (-n))


def _band(front: float, back: float, residual: float, cfg: dict) -> str:
    """Deterministic INDICATIVE band. See references/domain-rules.md. Never a credit decision."""
    if front <= cfg["frontend_dti_max"] and back <= cfg["backend_dti_max"] \
            and residual >= cfg["residual_income_min"]:
        return "Within typical guidelines"
    if back <= cfg["backend_dti_stretch"] and residual >= 0:
        return "Approaching typical limits"
    return "Outside typical guidelines"


def _escrow(loan: dict) -> float:
    return (float(loan.get("monthly_tax", 0) or 0)
            + float(loan.get("monthly_insurance", 0) or 0)
            + float(loan.get("monthly_hoa", 0) or 0))


def _metrics(loan_type, new_loan_payment, existing_debt, existing_housing, total_gross,
             residual_basis, living_expenses, cfg):
    """Return (front_dti, back_dti, residual, housing_payment, total_obligations, band)."""
    if loan_type == "mortgage":
        housing_payment = new_loan_payment          # proposed PITI is the housing cost
        total_obligations = housing_payment + existing_debt
    else:
        housing_payment = existing_housing           # current rent/mortgage stays
        total_obligations = housing_payment + existing_debt + new_loan_payment
    front = housing_payment / total_gross if total_gross else 0.0
    back = total_obligations / total_gross if total_gross else 0.0
    residual = residual_basis - total_obligations - living_expenses
    return front, back, residual, housing_payment, total_obligations, _band(front, back, residual, cfg)


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    loan = doc["loan"]
    income = doc["income"]
    obl = doc.get("obligations") or {}

    ltype = loan["type"]
    principal = float(loan["principal"])
    rate = float(loan["annual_rate_pct"])
    term = int(loan["term_months"])
    escrow = _escrow(loan)

    gross = float(income["gross_monthly"]) + float(income.get("other_monthly", 0) or 0)
    net = income.get("net_monthly")
    residual_basis = float(net) if net not in (None, "") else gross
    residual_basis_is_net = net not in (None, "")

    existing_debt = float(obl.get("existing_monthly_debt", 0) or 0)
    existing_housing = float(obl.get("existing_housing_expense", 0) or 0)
    living = float(obl.get("monthly_living_expenses", 0) or 0)

    pi = amortized_payment(principal, rate, term)
    proposed_payment = round(pi + escrow, 2)

    f, b, res, housing, total_obl, band = _metrics(
        ltype, proposed_payment, existing_debt, existing_housing, gross,
        residual_basis, living, cfg)

    baseline = {
        "proposed_payment": proposed_payment,
        "principal_interest": round(pi, 2),
        "escrow": round(escrow, 2),
        "housing_payment": round(housing, 2),
        "total_obligations": round(total_obl, 2),
        "front_end_dti": round(f, 4),
        "back_end_dti": round(b, 4),
        "residual_income": round(res, 2),
        "affordability_band": band,
    }

    scenarios = []
    # Rate-up stress: recompute payment at higher rate, everything else held.
    for bump in cfg["stress_rate_bumps_pct"]:
        s_rate = rate + float(bump)
        s_pi = amortized_payment(principal, s_rate, term)
        s_payment = round(s_pi + escrow, 2)
        sf, sb, sres, _, _, sband = _metrics(
            ltype, s_payment, existing_debt, existing_housing, gross,
            residual_basis, living, cfg)
        scenarios.append({
            "scenario": f"Rate +{float(bump):.2f}% (to {s_rate:.2f}%)",
            "kind": "rate",
            "annual_rate_pct": round(s_rate, 4),
            "proposed_payment": s_payment,
            "front_end_dti": round(sf, 4),
            "back_end_dti": round(sb, 4),
            "residual_income": round(sres, 2),
            "affordability_band": sband,
        })
    # Income-down stress: reduce gross (and net basis) by the haircut, payment held.
    for hc in cfg["stress_income_haircuts_pct"]:
        factor = 1.0 - float(hc) / 100.0
        s_gross = gross * factor
        s_basis = residual_basis * factor
        sf, sb, sres, _, _, sband = _metrics(
            ltype, proposed_payment, existing_debt, existing_housing, s_gross,
            s_basis, living, cfg)
        scenarios.append({
            "scenario": f"Income -{float(hc):.2f}%",
            "kind": "income",
            "total_gross_monthly": round(s_gross, 2),
            "proposed_payment": proposed_payment,
            "front_end_dti": round(sf, 4),
            "back_end_dti": round(sb, 4),
            "residual_income": round(sres, 2),
            "affordability_band": sband,
        })

    thresholds = {k: cfg[k] for k in
                  ("frontend_dti_max", "backend_dti_max", "backend_dti_stretch", "residual_income_min")}
    assumptions = [
        f"{ltype} loan of {principal:,.2f} at {rate:.2f}% APR over {term} months",
        f"Estimated principal & interest {pi:,.2f}/mo"
        + (f"; escrow (tax/insurance/HOA) {escrow:,.2f}/mo" if escrow else "; no escrow modeled"),
        f"Residual income basis: {'disclosed net income' if residual_basis_is_net else 'gross income (net not disclosed) — indicative only'}",
        f"Thresholds from versioned config {doc.get('config_version')!r}; not tuned to the applicant",
        f"Stress cases: rate +{cfg['stress_rate_bumps_pct']}%, income -{cfg['stress_income_haircuts_pct']}%",
    ]

    narrative = (
        f"Indicative affordability precheck for applicant {doc['applicant_id']} as of {doc['as_of']}. "
        f"Assuming a {ltype} of {principal:,.2f} at {rate:.2f}% APR over {term} months, the estimated "
        f"monthly payment is {proposed_payment:,.2f}. Front-end DTI is {f*100:.1f}%, back-end DTI is "
        f"{b*100:.1f}%, and modeled residual income is {res:,.2f}. Indicative affordability band: "
        f"{band}. Stress scenarios (higher rates, lower income) are provided below for the reviewer to "
        f"weigh. This estimate reflects disclosed figures and versioned thresholds only; a human "
        f"underwriter must review it before any lending decision. " + DISCLAIMER
    )

    return {
        "precheck_id": f"lap-{str(doc['applicant_id']).replace('*','')}-{doc['as_of']}-0001",
        "applicant_id": doc["applicant_id"],
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "loan": {
            "type": ltype, "principal": principal, "annual_rate_pct": rate,
            "term_months": term, "monthly_tax": float(loan.get("monthly_tax", 0) or 0),
            "monthly_insurance": float(loan.get("monthly_insurance", 0) or 0),
            "monthly_hoa": float(loan.get("monthly_hoa", 0) or 0),
        },
        "inputs_summary": {
            "total_gross_monthly": round(gross, 2),
            "residual_basis_is_net": residual_basis_is_net,
            "existing_monthly_debt": existing_debt,
            "existing_housing_expense": existing_housing,
            "monthly_living_expenses": living,
        },
        "thresholds": thresholds,
        "assumptions": assumptions,
        "baseline": baseline,
        "affordability_band": band,
        "stress_scenarios": scenarios,
        "disclaimer": DISCLAIMER,
        "narrative": narrative,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "precheck_input.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
