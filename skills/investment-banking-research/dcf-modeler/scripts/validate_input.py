#!/usr/bin/env python3
"""Deterministic input validation for dcf-modeler.

Validates a DCF-input file before the model is built. Fails closed on structural problems
(missing drivers, non-numeric assumptions, unsupported terminal method); warns on
data-quality gaps that weaken the model (missing provenance/citation, WACC not greater than
terminal growth, capital weights that do not sum to one, very long horizons).

Input schema (JSON): see references/source-map.md. Key fields:
  company_id, as_of (YYYY-MM-DD), valuation_date (YYYY-MM-DD), config_version, currency,
  units, base_year_revenue (> 0), forecast_years (int > 0), shares_outstanding (> 0),
  discounting{convention}, drivers{revenue_growth,ebit_margin,tax_rate,da_pct_revenue,
  capex_pct_revenue,nwc_pct_of_revenue_change -> {value,provenance,citation}},
  wacc{risk_free,erp,beta,cost_of_debt_pretax,weight_equity,weight_debt} or wacc{override},
  terminal{method('gordon'|'exit_multiple'),growth,exit_multiple},
  bridge{total_debt,cash_and_equivalents,minority_interest,preferred_equity,
  investments_associates}, scenario_adjustments{upside{...},downside{...}}

Usage:
  python validate_input.py dcf_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("company_id", "as_of", "valuation_date", "config_version",
                "base_year_revenue", "forecast_years", "shares_outstanding",
                "drivers", "wacc", "terminal")
DRIVER_KEYS = ("revenue_growth", "ebit_margin", "tax_rate", "da_pct_revenue",
               "capex_pct_revenue", "nwc_pct_of_revenue_change")


def _v(node):
    try:
        return float(node.get("value") if isinstance(node, dict) else node)
    except (TypeError, ValueError, AttributeError):
        return None


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _prov_cite(node):
    if isinstance(node, dict):
        return (node.get("provenance") or "").strip(), (node.get("citation") or "").strip()
    return "", ""


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if not DATE_RE.match(str(doc["valuation_date"])):
        errors.append(f"valuation_date must start YYYY-MM-DD, got {doc['valuation_date']!r}")

    fy = _int(doc["forecast_years"])
    if fy is None or fy <= 0:
        errors.append(f"forecast_years must be a positive integer, got {doc['forecast_years']!r}")
    elif fy > 10:
        warnings.append(f"forecast_years {fy} > 10 — long explicit horizons are low-confidence; "
                        f"consider a shorter forecast plus terminal value")
    if (_v(doc["base_year_revenue"]) or 0) <= 0:
        errors.append(f"base_year_revenue must be > 0, got {doc['base_year_revenue']!r}")
    if (_v(doc["shares_outstanding"]) or 0) <= 0:
        errors.append(f"shares_outstanding must be > 0, got {doc['shares_outstanding']!r}")

    # drivers
    drivers = doc.get("drivers") or {}
    for k in DRIVER_KEYS:
        if k not in drivers:
            errors.append(f"drivers.{k} is required")
            continue
        if _v(drivers[k]) is None:
            errors.append(f"drivers.{k} value is not numeric")
        prov, cite = _prov_cite(drivers[k])
        if not prov:
            warnings.append(f"drivers.{k} has no provenance — validate_output will reject the pack")
        if not cite:
            warnings.append(f"drivers.{k} has no citation — validate_output will reject the pack")
    tax = _v(drivers.get("tax_rate"))
    if tax is not None and not (0.0 <= tax < 1.0):
        warnings.append(f"drivers.tax_rate {tax} is outside [0,1) — check the input")

    # wacc
    w = doc.get("wacc") or {}
    wacc_val = None
    if "override" in w:
        wacc_val = _v(w["override"])
        if wacc_val is None:
            errors.append("wacc.override is not numeric")
    else:
        need = ("risk_free", "erp", "beta", "cost_of_debt_pretax", "weight_equity", "weight_debt")
        for k in need:
            if k not in w:
                errors.append(f"wacc.{k} is required when no wacc.override is given")
            elif _v(w[k]) is None:
                errors.append(f"wacc.{k} value is not numeric")
        we, wd = _v(w.get("weight_equity")), _v(w.get("weight_debt"))
        if we is not None and wd is not None and abs((we + wd) - 1.0) > 1e-6:
            warnings.append(f"wacc weights do not sum to 1 (equity {we} + debt {wd}); check the capital structure")
        if None not in (we, wd, _v(w.get("risk_free")), _v(w.get("erp")), _v(w.get("beta")),
                        _v(w.get("cost_of_debt_pretax"))) and tax is not None:
            ke = _v(w["risk_free"]) + _v(w["beta"]) * _v(w["erp"])
            kd_at = _v(w["cost_of_debt_pretax"]) * (1.0 - tax)
            wacc_val = we * ke + wd * kd_at

    # terminal
    term = doc.get("terminal") or {}
    method = term.get("method")
    if method not in ("gordon", "exit_multiple"):
        errors.append(f"terminal.method must be 'gordon' or 'exit_multiple', got {method!r}")
    if method == "gordon":
        g = _v(term.get("growth"))
        if g is None:
            errors.append("terminal.growth is required for the gordon method")
        elif wacc_val is not None and wacc_val - g <= 1e-9:
            warnings.append(f"WACC ({round(wacc_val,4)}) is not greater than terminal growth ({g}); "
                            f"the Gordon terminal value will be invalid")
    if method == "exit_multiple" and _v(term.get("exit_multiple")) is None:
        errors.append("terminal.exit_multiple is required for the exit_multiple method")

    # scenario adjustments (optional but expected for a 3-case model)
    sa = doc.get("scenario_adjustments") or {}
    for scen in ("upside", "downside"):
        if scen not in sa:
            warnings.append(f"no scenario_adjustments.{scen} — {scen} will equal the base case")

    # discounting convention
    conv = (doc.get("discounting") or {}).get("convention", "end_year")
    if conv not in ("end_year", "mid_year"):
        warnings.append(f"discounting.convention {conv!r} unrecognized — defaulting to end_year")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "dcf_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
