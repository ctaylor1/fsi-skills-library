#!/usr/bin/env python3
"""Deterministic, explainable variance computation for fpa-variance-analyzer.

Reads a variance dataset (see validate_input.py), computes actual-vs-budget, actual-vs-
forecast, and actual-vs-prior variances per line, applies a versioned materiality screen,
verifies any supplied driver decomposition ties out to the computed variance, quantifies a
run-rate impact for recurring items, and maps the material-finding profile to a commentary
review priority. Emits a machine-readable core the SKILL wraps in draft commentary.

IMPORTANT: This produces explainable *variances, evidence, and draft commentary* only. It
never makes a management decision, commits a forecast/guidance number, restates the ledger,
or posts a journal. The priority mapping is deterministic and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py variance.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "abs_threshold": 100000.0,   # absolute variance materiality floor
    "pct_threshold": 0.10,       # percent-of-base materiality floor
    "min_base": 50000.0,         # minimum base to apply the percent test (avoids tiny-base blow-ups)
    "run_rate_escalation": 250000.0,  # run-rate impact that escalates commentary priority
    "attribution_tolerance": 1.0,     # currency tolerance for driver tie-out
    "periods_remaining": 0,      # periods remaining in the year for run-rate annualization
}
DISCLAIMER = ("Variance analysis and draft commentary only; not a management decision, "
              "forecast commitment, or restatement of the financial records. Human review "
              "is required before external delivery.")
CAVEATS = [
    "Timing/phasing differences can create variances that reverse in later periods",
    "Reclassifications or mapping changes between actual and plan can distort a variance",
    "Accrual true-ups and one-time items should be separated from run-rate",
    "FX retranslation can move a reported variance independent of operating performance",
    "Allocation or cost-center reorganizations may shift variance between lines",
]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _favorable(account_type: str, var: float):
    """Sign convention: revenue up is favorable; expense down is favorable."""
    if var == 0:
        return None
    if account_type == "revenue":
        return var > 0
    if account_type == "expense":
        return var < 0
    return None


def _cite(source_ref: str, field: str, period: str) -> str:
    return f"gl:{source_ref}#{field}@{period}"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    period = doc.get("period", "?")
    basis = doc.get("basis", "budget")
    tol = cfg["attribution_tolerance"]
    periods_remaining = cfg["periods_remaining"]

    findings, not_evaluable = [], []
    for ln in doc["lines"]:
        acct_type = ln.get("account_type")
        actual = _num(ln.get("actual"))
        budget = _num(ln.get("budget"))
        forecast = _num(ln.get("forecast"))
        prior = _num(ln.get("prior"))
        src = ln.get("source_ref", "?")

        vs_budget = actual - budget
        pct = (vs_budget / budget) if budget not in (0, None) else None
        variance = {
            "vs_budget": round(vs_budget, 2),
            "vs_budget_pct": round(pct, 4) if pct is not None else None,
            "vs_forecast": round(actual - forecast, 2) if forecast is not None else None,
            "vs_prior": round(actual - prior, 2) if prior is not None else None,
        }
        if forecast is None:
            not_evaluable.append({"line_id": ln["line_id"], "measure": "vs_forecast", "why": "no forecast supplied"})
        if prior is None:
            not_evaluable.append({"line_id": ln["line_id"], "measure": "vs_prior", "why": "no prior supplied"})

        # materiality screen (on the managed basis: budget)
        reasons = []
        if abs(vs_budget) >= cfg["abs_threshold"]:
            reasons.append(f"abs variance {abs(vs_budget):,.0f} >= {cfg['abs_threshold']:,.0f}")
        if pct is not None and abs(budget) >= cfg["min_base"] and abs(pct) >= cfg["pct_threshold"]:
            reasons.append(f"pct {pct:.1%} >= {cfg['pct_threshold']:.0%} on base >= {cfg['min_base']:,.0f}")
        material = bool(reasons)

        fav = _favorable(acct_type, vs_budget)
        finding = {
            "line_id": ln["line_id"], "account": ln.get("account"), "account_type": acct_type,
            "variance": variance, "favorable": fav, "material": material,
            "materiality_reasons": reasons, "persistence": ln.get("persistence"),
        }

        if material:
            # driver attribution tie-out (against the managed vs_budget variance)
            drivers = ln.get("drivers")
            if not drivers:
                attribution_status, driver_sum, gap = "unattributed", None, None
            else:
                driver_sum = round(sum(_num(d.get("amount")) or 0.0 for d in drivers), 2)
                gap = round(vs_budget - driver_sum, 2)
                attribution_status = "ok" if abs(gap) <= tol else "fail"
            # run-rate impact (recurring items only)
            if ln.get("persistence") == "recurring" and periods_remaining:
                run_rate = round(vs_budget * periods_remaining, 2)
            else:
                run_rate = 0.0
            # evidence rows (each carries a citation)
            evidence = [
                {"field": "actual", "value": actual, "citation": _cite(src, "actual", period)},
                {"field": "budget", "value": budget, "citation": _cite(src, "budget", period)},
            ]
            if forecast is not None:
                evidence.append({"field": "forecast", "value": forecast, "citation": _cite(src, "forecast", period)})
            if prior is not None:
                evidence.append({"field": "prior", "value": prior, "citation": _cite(src, "prior", period)})
            for d in (drivers or []):
                evidence.append({"field": f"driver:{d.get('name')}", "value": _num(d.get("amount")),
                                 "citation": f"fpa:{d.get('source_ref', src)}#driver@{period}"})

            dir_word = "favorable" if fav else ("unfavorable" if fav is not None else "flat")
            pct_txt = f" ({pct:+.1%})" if pct is not None else ""
            if attribution_status == "ok":
                attr_txt = "supplied drivers tie out to the variance"
            elif attribution_status == "fail":
                attr_txt = f"supplied drivers do not tie out (gap {gap:+,.0f}) - attribution pending"
            else:
                attr_txt = "no driver decomposition supplied - attribution pending"
            rr_txt = f"; estimated run-rate impact {run_rate:+,.0f} over {periods_remaining} remaining period(s)" if run_rate else ""
            commentary = (f"{ln.get('account')}: actual {dir_word} vs budget by {vs_budget:+,.0f}{pct_txt}; "
                          f"{attr_txt}{rr_txt}.")

            finding.update({
                "drivers": drivers, "driver_sum": driver_sum, "attribution_gap": gap,
                "attribution_status": attribution_status,
                "run_rate_impact": run_rate, "run_rate_is_estimate": bool(run_rate),
                "evidence": evidence, "commentary": commentary,
            })
        findings.append(finding)

    material_findings = [f["line_id"] for f in findings if f["material"]]

    # deterministic commentary-priority mapping (see references/domain-rules.md)
    mats = [f for f in findings if f["material"]]
    escalator = any(
        f.get("attribution_status") in ("fail", "unattributed")
        or (f.get("persistence") == "recurring"
            and abs(f.get("run_rate_impact") or 0.0) >= cfg["run_rate_escalation"])
        for f in mats)
    if len(mats) >= 3 or escalator:
        priority = "Elevated"
    elif len(mats) >= 1:
        priority = "Standard"
    else:
        priority = "Routine"

    caveats = CAVEATS if material_findings else []

    return {
        "analysis_id": f"fva-{doc.get('entity','entity').split(' ')[0].lower()}-{doc.get('as_of')}-0001",
        "entity": doc.get("entity"),
        "period": period,
        "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "basis": basis,
        "run_rate_escalation": cfg["run_rate_escalation"],
        "attribution_tolerance": tol,
        "findings": findings,
        "material_findings": material_findings,
        "not_evaluable": not_evaluable,
        "suggested_priority": priority,
        "caveats": caveats,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "variance_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
