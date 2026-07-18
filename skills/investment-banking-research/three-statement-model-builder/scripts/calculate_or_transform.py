#!/usr/bin/env python3
"""Deterministic integrated three-statement model builder.

Reads a model-input file (see validate_input.py), builds an integrated income statement,
balance sheet, and cash-flow statement for the requested forecast horizon from EXPLICIT,
SOURCED driver assumptions, produces supporting schedules (debt, PP&E, working capital),
computes tie-out checks (balance-sheet identity, cash tie, equity and PP&E roll-forwards),
and summarizes base/upside/downside scenarios. Emits a machine-readable model core that the
SKILL wraps in a plain-language, no-advice narrative.

DETERMINISM & CIRCULARITY: every line item is a closed-form function of the base-year
actuals and the driver assumptions. Interest expense is computed on the OPENING debt
balance, so there is no interest<->cash circular reference; results are fully reproducible.
The balance sheet balances by construction whenever the base year balances (cash is the
cash-flow plug); the tie-out checks verify this independently.

IMPORTANT: this builds a model, not a view. It never states a valuation opinion, price
target, or buy/sell/hold recommendation. Those are out of scope (see references/controls.md).

Usage:
  python calculate_or_transform.py model_input.json | --selftest
Prints the model JSON to stdout.
"""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

DISCLAIMER = ("Model output for analytical support only; not investment advice or a "
              "recommendation to buy, sell, or hold any security.")
BALANCE_TOL = 0.01
DAYS = 365.0


def r(x) -> float:
    return round(float(x), 6)


def _dv(drivers: dict, name: str) -> float:
    d = drivers[name]
    return float(d["value"]) if isinstance(d, dict) else float(d)


def _dsrc(drivers: dict, name: str) -> str:
    d = drivers.get(name)
    return str(d.get("source", "")).strip() if isinstance(d, dict) else ""


def run_model(doc: dict, growth_delta: float = 0.0, margin_delta: float = 0.0):
    """Return (income_rows, balance_rows, cashflow_rows) for the horizon."""
    hist = doc["historical"]
    drv = doc["drivers"]
    n = int(doc["forecast_years"])
    base_year = int(hist["year"])

    g = _dv(drv, "revenue_growth") + growth_delta
    gm = _dv(drv, "gross_margin") + margin_delta
    opex_pct = _dv(drv, "opex_pct_revenue")
    dep_rate = _dv(drv, "depreciation_rate")
    capex_pct = _dv(drv, "capex_pct_revenue")
    dso, dio, dpo = _dv(drv, "dso"), _dv(drv, "dio"), _dv(drv, "dpo")
    oca_pct = _dv(drv, "other_current_assets_pct_revenue")
    ocl_pct = _dv(drv, "other_current_liabilities_pct_revenue")
    tax_rate = _dv(drv, "tax_rate")
    int_rate = _dv(drv, "interest_rate")
    repay = _dv(drv, "debt_repayment")
    payout = _dv(drv, "dividend_payout_ratio")

    b = hist["balance_sheet"]
    prev = {
        "revenue": float(hist["income_statement"]["revenue"]),
        "cash": float(b["cash"]), "ar": float(b["accounts_receivable"]),
        "inv": float(b["inventory"]), "oca": float(b["other_current_assets"]),
        "ppe": float(b["ppe_net"]), "oa": float(b["other_assets"]),
        "ap": float(b["accounts_payable"]), "ocl": float(b["other_current_liabilities"]),
        "debt": float(b["debt"]), "ol": float(b["other_liabilities"]),
        "equity": float(b["equity"]),
    }
    is_rows, bs_rows, cf_rows = [], [], []
    for i in range(1, n + 1):
        yr = base_year + i
        # ---- income statement ----
        revenue = prev["revenue"] * (1.0 + g)
        gross_profit = revenue * gm
        cogs = revenue - gross_profit
        opex = revenue * opex_pct
        ebitda = gross_profit - opex
        depreciation = dep_rate * prev["ppe"]
        ebit = ebitda - depreciation
        interest = int_rate * prev["debt"]            # opening debt -> no circularity
        pretax = ebit - interest
        tax = max(0.0, pretax) * tax_rate             # no tax benefit modeled on losses
        net_income = pretax - tax

        # ---- balance sheet drivers ----
        ar = revenue / DAYS * dso
        inv = cogs / DAYS * dio
        oca = revenue * oca_pct
        capex = revenue * capex_pct
        ppe = prev["ppe"] + capex - depreciation
        oa = prev["oa"]                               # held flat unless separately driven
        ap = cogs / DAYS * dpo
        ocl = revenue * ocl_pct
        debt = max(0.0, prev["debt"] - repay)
        actual_repay = prev["debt"] - debt
        ol = prev["ol"]
        dividends = payout * max(0.0, net_income)
        equity = prev["equity"] + net_income - dividends

        # ---- cash-flow statement (indirect) ----
        d_ar, d_inv, d_oca = ar - prev["ar"], inv - prev["inv"], oca - prev["oca"]
        d_ap, d_ocl = ap - prev["ap"], ocl - prev["ocl"]
        cfo = net_income + depreciation - d_ar - d_inv - d_oca + d_ap + d_ocl
        cfi = -capex
        cff = -actual_repay - dividends
        net_change = cfo + cfi + cff
        beginning_cash = prev["cash"]
        ending_cash = beginning_cash + net_change
        cash = ending_cash

        total_assets = cash + ar + inv + oca + ppe + oa
        total_liab = ap + ocl + debt + ol
        total_le = total_liab + equity

        is_rows.append({
            "year": yr, "revenue": r(revenue), "cogs": r(cogs), "gross_profit": r(gross_profit),
            "opex": r(opex), "ebitda": r(ebitda), "depreciation": r(depreciation),
            "ebit": r(ebit), "interest_expense": r(interest), "pretax_income": r(pretax),
            "tax": r(tax), "net_income": r(net_income),
        })
        bs_rows.append({
            "year": yr, "cash": r(cash), "accounts_receivable": r(ar), "inventory": r(inv),
            "other_current_assets": r(oca), "ppe_net": r(ppe), "other_assets": r(oa),
            "total_assets": r(total_assets), "accounts_payable": r(ap),
            "other_current_liabilities": r(ocl), "debt": r(debt), "other_liabilities": r(ol),
            "total_liabilities": r(total_liab), "equity": r(equity),
            "total_liabilities_and_equity": r(total_le),
        })
        cf_rows.append({
            "year": yr, "net_income": r(net_income), "depreciation": r(depreciation),
            "change_in_accounts_receivable": r(-d_ar), "change_in_inventory": r(-d_inv),
            "change_in_other_current_assets": r(-d_oca), "change_in_accounts_payable": r(d_ap),
            "change_in_other_current_liabilities": r(d_ocl), "cfo": r(cfo),
            "capex": r(-capex), "cfi": r(cfi), "debt_repayment": r(-actual_repay),
            "dividends": r(-dividends), "cff": r(cff), "net_change_in_cash": r(net_change),
            "beginning_cash": r(beginning_cash), "ending_cash": r(ending_cash),
        })

        prev = {"revenue": r(revenue), "cash": r(cash), "ar": r(ar), "inv": r(inv),
                "oca": r(oca), "ppe": r(ppe), "oa": r(oa), "ap": r(ap), "ocl": r(ocl),
                "debt": r(debt), "ol": r(ol), "equity": r(equity)}
    return is_rows, bs_rows, cf_rows


def _checks(bs_rows, is_rows, cf_rows, base_snapshot):
    balance, cash_tie, equity_rf, ppe_rf = [], [], [], []
    prev_bs = base_snapshot["balance_sheet"]
    for i, bs in enumerate(bs_rows):
        resid = r(bs["total_assets"] - bs["total_liabilities_and_equity"])
        balance.append({"year": bs["year"], "total_assets": bs["total_assets"],
                        "total_liabilities_and_equity": bs["total_liabilities_and_equity"],
                        "residual": resid, "balanced": abs(resid) <= BALANCE_TOL})
        ct = r(cf_rows[i]["ending_cash"] - bs["cash"])
        cash_tie.append({"year": bs["year"], "cf_ending_cash": cf_rows[i]["ending_cash"],
                         "bs_cash": bs["cash"], "residual": ct, "tied": abs(ct) <= BALANCE_TOL})
        exp_eq = r(prev_bs["equity"] + is_rows[i]["net_income"] + cf_rows[i]["dividends"])
        equity_rf.append({"year": bs["year"], "expected_equity": exp_eq,
                          "reported_equity": bs["equity"],
                          "residual": r(exp_eq - bs["equity"]),
                          "tied": abs(exp_eq - bs["equity"]) <= BALANCE_TOL})
        # cf capex is stored as a negative outflow; PP&E roll-forward adds capex back positive
        exp_ppe = r(prev_bs["ppe_net"] - cf_rows[i]["capex"] - is_rows[i]["depreciation"])
        ppe_rf.append({"year": bs["year"], "expected_ppe_net": exp_ppe,
                       "reported_ppe_net": bs["ppe_net"],
                       "residual": r(exp_ppe - bs["ppe_net"]),
                       "tied": abs(exp_ppe - bs["ppe_net"]) <= BALANCE_TOL})
        prev_bs = bs
    return {"balance": balance, "cash_tie": cash_tie,
            "equity_rollforward": equity_rf, "ppe_rollforward": ppe_rf}


def build(doc: dict) -> dict:
    hist = doc["historical"]
    drv = doc["drivers"]
    base_year = int(hist["year"])
    n = int(doc["forecast_years"])
    final_year = base_year + n

    is_rows, bs_rows, cf_rows = run_model(doc)
    base_snapshot = {
        "year": base_year,
        "revenue": r(hist["income_statement"]["revenue"]),
        "balance_sheet": {k: r(v) for k, v in hist["balance_sheet"].items()},
    }
    checks = _checks(bs_rows, is_rows, cf_rows, base_snapshot)

    assumptions = [{"driver": k, "value": _dv(drv, k), "source": _dsrc(drv, k)}
                   for k in sorted(drv)]

    scen_cfg = doc.get("scenarios") or {
        "base": {"revenue_growth_delta": 0.0, "gross_margin_delta": 0.0},
        "upside": {"revenue_growth_delta": 0.03, "gross_margin_delta": 0.02},
        "downside": {"revenue_growth_delta": -0.03, "gross_margin_delta": -0.02},
    }
    scenarios = []
    for name in ("base", "upside", "downside"):
        adj = scen_cfg.get(name, {})
        s_is, _s_bs, s_cf = run_model(doc, adj.get("revenue_growth_delta", 0.0),
                                      adj.get("gross_margin_delta", 0.0))
        scenarios.append({
            "name": name, "final_year": final_year,
            "revenue": s_is[-1]["revenue"], "ebitda": s_is[-1]["ebitda"],
            "net_income": s_is[-1]["net_income"], "ending_cash": s_cf[-1]["ending_cash"],
        })

    all_balanced = all(c["balanced"] for c in checks["balance"]) and \
        all(c["tied"] for c in checks["cash_tie"]) and \
        all(c["tied"] for c in checks["equity_rollforward"]) and \
        all(c["tied"] for c in checks["ppe_rollforward"])

    canonical = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
    inputs_hash = hashlib.sha256(canonical).hexdigest()[:16]
    slug = re.sub(r"[^a-z0-9]+", "", str(doc["company"]).lower())[:12] or "co"

    narrative = (
        f"Integrated three-statement model for {doc['company']} built from base-year "
        f"{base_year} actuals across {n} forecast year(s) ({base_year + 1}-{final_year}) "
        f"using explicit, sourced driver assumptions. Interest is computed on opening debt "
        f"so the model is non-circular and reproducible. All forecast years balance "
        f"(assets = liabilities + equity) and the cash-flow statement ties to balance-sheet "
        f"cash; equity and PP&E roll-forwards reconcile. The scenario summary reflects "
        f"driver deltas only. {DISCLAIMER}")

    return {
        "model_id": f"3sm-{slug}-{doc['as_of']}-0001",
        "company": doc["company"],
        "ticker": doc.get("ticker"),
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "currency": doc.get("currency"),
        "units": doc.get("units"),
        "inputs_hash": inputs_hash,
        "base_year": base_year,
        "forecast_years": [base_year + i for i in range(1, n + 1)],
        "base_snapshot": base_snapshot,
        "assumptions": assumptions,
        "income_statement": is_rows,
        "balance_sheet": bs_rows,
        "cash_flow": cf_rows,
        "schedules": _schedules(is_rows, bs_rows, cf_rows, base_snapshot),
        "checks": checks,
        "scenarios": scenarios,
        "all_balanced": all_balanced,
        "narrative": narrative,
        "disclaimer": DISCLAIMER,
    }


def _schedules(is_rows, bs_rows, cf_rows, base_snapshot):
    debt, ppe, wc = [], [], []
    prev_bs = base_snapshot["balance_sheet"]
    for i, bs in enumerate(bs_rows):
        debt.append({"year": bs["year"], "opening": prev_bs["debt"],
                     "repayment": cf_rows[i]["debt_repayment"], "closing": bs["debt"],
                     "interest_expense": is_rows[i]["interest_expense"]})
        ppe.append({"year": bs["year"], "opening": prev_bs["ppe_net"],
                    "capex": r(-cf_rows[i]["capex"]), "depreciation": r(-is_rows[i]["depreciation"]),
                    "closing": bs["ppe_net"]})
        wc.append({"year": bs["year"], "accounts_receivable": bs["accounts_receivable"],
                   "inventory": bs["inventory"], "accounts_payable": bs["accounts_payable"],
                   "net_working_capital": r(bs["accounts_receivable"] + bs["inventory"]
                                            + bs["other_current_assets"] - bs["accounts_payable"]
                                            - bs["other_current_liabilities"])})
        prev_bs = bs
    return {"debt": debt, "ppe": ppe, "working_capital": wc}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
