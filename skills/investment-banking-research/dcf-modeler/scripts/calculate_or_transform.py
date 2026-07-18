#!/usr/bin/env python3
"""Deterministic, source-linked unlevered DCF engine for dcf-modeler.

Reads a DCF-input file (see validate_input.py), builds an explicit driver-based unlevered
free-cash-flow (UFCF) forecast for base / upside / downside scenarios, discounts at a WACC
computed from its stated components, adds a terminal value (Gordon growth or exit multiple),
and walks enterprise value down an explicit enterprise-to-equity bridge to a value per
share. Every scenario carries its own formula tie-outs; every assumption carries a
provenance tag and citation; the model is reproducible from a hash of its inputs.

IMPORTANT: This produces an *illustrative valuation model* only. It never issues investment
advice, a buy/sell/hold recommendation, a price target, or a fairness opinion. Scenario
adjustments and WACC/terminal inputs are documented assumptions, not the skill's judgment.
See references/domain-rules.md.

Usage:
  python calculate_or_transform.py dcf_input.json | --selftest
Prints the model JSON to stdout.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROUND = 4            # money precision (units are typically millions)
DF_ROUND = 8         # discount-factor precision
TOL = 0.01           # tie-out tolerance
DISCLAIMER = ("Illustrative valuation model for analytical purposes only; not investment "
              "advice, not a recommendation to buy, sell, or hold any security, not a price "
              "target, and not a fairness opinion. Outputs depend entirely on the stated "
              "assumptions, which a qualified human must review.")

DRIVER_KEYS = ("revenue_growth", "ebit_margin", "tax_rate", "da_pct_revenue",
               "capex_pct_revenue", "nwc_pct_of_revenue_change")


def _v(node):
    """Return the numeric value from either a bare scalar or a {value, provenance,...} dict.

    A bare scalar has no provenance; the register will carry an empty provenance so
    validate_output flags it. This keeps the engine permissive but the controls strict.
    """
    if isinstance(node, dict):
        return float(node.get("value"))
    return float(node)


def _prov(node):
    return (node.get("provenance", "") if isinstance(node, dict) else "")


def _cite(node):
    return (node.get("citation", "") if isinstance(node, dict) else "")


def compute(doc: dict) -> dict:
    forecast_years = int(doc["forecast_years"])
    base_rev = float(doc["base_year_revenue"])
    shares = float(doc["shares_outstanding"])
    tax_rate = _v(doc["drivers"]["tax_rate"])

    # --- WACC from stated components (CAPM cost of equity + after-tax cost of debt) -------
    w = doc["wacc"]
    if "override" in w:
        wacc = round(_v(w["override"]), 8)
        wacc_detail = {"method": "explicit override", "value": wacc}
    else:
        rf, erp, beta = _v(w["risk_free"]), _v(w["erp"]), _v(w["beta"])
        kd_pre = _v(w["cost_of_debt_pretax"])
        we, wd = _v(w["weight_equity"]), _v(w["weight_debt"])
        ke = rf + beta * erp
        kd_at = kd_pre * (1.0 - tax_rate)
        wacc = round(we * ke + wd * kd_at, 8)
        wacc_detail = {
            "method": "CAPM cost of equity + after-tax cost of debt",
            "cost_of_equity": round(ke, 8), "after_tax_cost_of_debt": round(kd_at, 8),
            "weight_equity": we, "weight_debt": wd, "value": wacc,
        }

    # --- terminal-value setup ----------------------------------------------------------
    term = doc["terminal"]
    method = term.get("method", "gordon")
    g = round(_v(term["growth"]), 8) if "growth" in term else None
    exit_mult = _v(term["exit_multiple"]) if "exit_multiple" in term else None
    gordon_guard_ok = (method != "gordon") or (g is not None and wacc - g > 1e-9)

    # --- discounting convention --------------------------------------------------------
    convention = (doc.get("discounting") or {}).get("convention", "end_year")
    if convention not in ("end_year", "mid_year"):
        convention = "end_year"

    def exponent(t: int) -> float:
        return t - 0.5 if convention == "mid_year" else float(t)

    # --- bridge (explicit enterprise-to-equity walk) -----------------------------------
    br = doc.get("bridge") or {}
    total_debt = _v(br.get("total_debt", 0.0))
    cash = _v(br.get("cash_and_equivalents", 0.0))
    minority = _v(br.get("minority_interest", 0.0))
    preferred = _v(br.get("preferred_equity", 0.0))
    assoc = _v(br.get("investments_associates", 0.0))

    def resolve_drivers(name: str) -> dict:
        base = {k: _v(doc["drivers"][k]) for k in DRIVER_KEYS}
        if name == "base":
            return base
        adj = (doc.get("scenario_adjustments") or {}).get(name, {})
        for k, delta in adj.items():
            if k in base:
                base[k] = round(base[k] + float(delta), 8)
        return base

    def project(name: str) -> dict:
        d = resolve_drivers(name)
        rows = []
        prev_rev = base_rev
        sum_pv = 0.0
        for t in range(1, forecast_years + 1):
            rev = round(prev_rev * (1.0 + d["revenue_growth"]), ROUND)
            ebit = round(rev * d["ebit_margin"], ROUND)
            nopat = round(ebit * (1.0 - d["tax_rate"]), ROUND)
            da = round(rev * d["da_pct_revenue"], ROUND)
            capex = round(rev * d["capex_pct_revenue"], ROUND)
            delta_nwc = round(d["nwc_pct_of_revenue_change"] * (rev - prev_rev), ROUND)
            ufcf = round(nopat + da - capex - delta_nwc, ROUND)
            df = round(1.0 / ((1.0 + wacc) ** exponent(t)), DF_ROUND)
            pv = round(ufcf * df, ROUND)
            sum_pv = round(sum_pv + pv, ROUND)
            rows.append({
                "year": t, "revenue": rev, "ebit": ebit, "nopat": nopat, "da": da,
                "capex": capex, "delta_nwc": delta_nwc, "ufcf": ufcf,
                "discount_factor": df, "pv_ufcf": pv,
            })
            prev_rev = rev

        last = rows[-1]
        df_n = last["discount_factor"]
        if method == "exit_multiple":
            ebitda_n = round(last["ebit"] + last["da"], ROUND)
            tv = round(exit_mult * ebitda_n, ROUND)
            tv_basis = {"basis": "EV/EBITDA exit", "ebitda_n": ebitda_n, "exit_multiple": exit_mult}
        else:  # gordon
            if gordon_guard_ok:
                tv = round(last["ufcf"] * (1.0 + g) / (wacc - g), ROUND)
            else:
                tv = 0.0
            tv_basis = {"basis": "Gordon growth", "ufcf_n": last["ufcf"], "growth": g,
                        "guard_ok": gordon_guard_ok}
        pv_tv = round(tv * df_n, ROUND)

        ev = round(sum_pv + pv_tv, ROUND)
        bridge_items = [
            {"item": "enterprise value", "amount": ev},
            {"item": "less: total debt", "amount": round(-total_debt, ROUND)},
            {"item": "plus: cash & equivalents", "amount": round(cash, ROUND)},
            {"item": "less: minority interest", "amount": round(-minority, ROUND)},
            {"item": "less: preferred equity", "amount": round(-preferred, ROUND)},
            {"item": "plus: investments in associates", "amount": round(assoc, ROUND)},
        ]
        equity_value = round(ev - total_debt + cash - minority - preferred + assoc, ROUND)
        value_per_share = round(equity_value / shares, 6) if shares else None

        # tie-outs (each must hold within TOL; validate_output re-checks independently)
        ev_ok = abs(round(sum_pv + pv_tv, ROUND) - ev) <= TOL
        bridge_adj = round(sum(i["amount"] for i in bridge_items[1:]), ROUND)
        bridge_ok = abs(ev + bridge_adj - equity_value) <= TOL
        per_share_ok = (value_per_share is not None
                        and abs(value_per_share * shares - equity_value) <= TOL)
        df_monotonic_ok = all(rows[i]["discount_factor"] >= rows[i + 1]["discount_factor"] - 1e-12
                              for i in range(len(rows) - 1))
        pv_recompute_ok = all(abs(round(r["ufcf"] * r["discount_factor"], ROUND) - r["pv_ufcf"]) <= TOL
                              for r in rows)

        return {
            "name": name,
            "drivers_resolved": d,
            "years": rows,
            "sum_pv_ufcf": sum_pv,
            "terminal_value": tv,
            "terminal_basis": tv_basis,
            "pv_terminal_value": pv_tv,
            "enterprise_value": ev,
            "equity_bridge": bridge_items,
            "equity_value": equity_value,
            "value_per_share": value_per_share,
            "tieouts": {
                "ev_ok": ev_ok, "bridge_ok": bridge_ok, "per_share_ok": per_share_ok,
                "df_monotonic_ok": df_monotonic_ok, "pv_recompute_ok": pv_recompute_ok,
            },
        }

    scenarios = [project("base"), project("upside"), project("downside")]
    by = {s["name"]: s for s in scenarios}
    ev_monotonic_ok = (by["downside"]["enterprise_value"] <= by["base"]["enterprise_value"] + TOL
                       and by["base"]["enterprise_value"] <= by["upside"]["enterprise_value"] + TOL)

    # --- assumptions register (provenance + citation for every input assumption) --------
    register = []
    for k in DRIVER_KEYS:
        node = doc["drivers"][k]
        register.append({"id": f"driver:{k}", "scope": "forecast-driver", "value": _v(node),
                         "provenance": _prov(node), "citation": _cite(node)})
    if "override" not in w:
        for k in ("risk_free", "erp", "beta", "cost_of_debt_pretax", "weight_equity", "weight_debt"):
            node = w[k]
            register.append({"id": f"wacc:{k}", "scope": "discount-rate", "value": _v(node),
                             "provenance": _prov(node), "citation": _cite(node)})
    else:
        node = w["override"]
        register.append({"id": "wacc:override", "scope": "discount-rate", "value": _v(node),
                         "provenance": _prov(node), "citation": _cite(node)})
    if "growth" in term:
        register.append({"id": "terminal:growth", "scope": "terminal-value", "value": _v(term["growth"]),
                         "provenance": _prov(term["growth"]), "citation": _cite(term["growth"])})
    if method == "exit_multiple" and "exit_multiple" in term:
        register.append({"id": "terminal:exit_multiple", "scope": "terminal-value", "value": _v(term["exit_multiple"]),
                         "provenance": _prov(term["exit_multiple"]), "citation": _cite(term["exit_multiple"])})
    for k in ("total_debt", "cash_and_equivalents", "minority_interest", "preferred_equity", "investments_associates"):
        if k in br:
            node = br[k]
            register.append({"id": f"bridge:{k}", "scope": "equity-bridge", "value": _v(node),
                             "provenance": _prov(node), "citation": _cite(node)})

    # --- reproducibility hash over the assumption inputs --------------------------------
    hash_src = json.dumps({
        "base_year_revenue": base_rev, "forecast_years": forecast_years,
        "shares_outstanding": shares, "drivers": {k: _v(doc["drivers"][k]) for k in DRIVER_KEYS},
        "wacc": wacc, "terminal": {"method": method, "growth": g, "exit_multiple": exit_mult},
        "bridge": {"total_debt": total_debt, "cash": cash, "minority": minority,
                   "preferred": preferred, "assoc": assoc},
        "convention": convention,
        "scenario_adjustments": doc.get("scenario_adjustments") or {},
    }, sort_keys=True)
    inputs_hash = hashlib.sha256(hash_src.encode("utf-8")).hexdigest()[:16]

    return {
        "model_id": f"dcf-{str(doc['company_id']).replace('*', '')}-{doc['valuation_date']}-{inputs_hash}",
        "company_id": doc["company_id"],
        "as_of": doc["as_of"],
        "valuation_date": doc["valuation_date"],
        "currency": doc.get("currency"),
        "units": doc.get("units"),
        "config_version": doc.get("config_version"),
        "inputs_hash": inputs_hash,
        "forecast_years": forecast_years,
        "shares_outstanding": shares,
        "discount_convention": convention,
        "wacc": wacc,
        "wacc_detail": wacc_detail,
        "terminal": {"method": method, "growth": g, "exit_multiple": exit_mult,
                     "gordon_guard_ok": gordon_guard_ok},
        "scenarios": scenarios,
        "assumptions_register": register,
        "model_checks": {
            "ev_monotonic_ok": ev_monotonic_ok,
            "all_tieouts_ok": all(all(s["tieouts"].values()) for s in scenarios),
            "gordon_guard_ok": gordon_guard_ok,
        },
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "dcf_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
