#!/usr/bin/env python3
"""Deterministic financial-spreading model for financial-spreading-assistant.

Reads a spreading-input file (see validate_input.py), classifies each raw line item into a
standard template taxonomy, spreads the classified amounts into balance-sheet and
income-statement subtotals per period, computes standard credit ratios and an operating
cash-flow proxy, ties the spread out against the borrower's own reported totals, applies
documented analyst add-backs to produce a normalized (as-adjusted) view, and routes any
line item it cannot confidently classify to an ambiguous-mappings queue for a human.

Explicit driver assumptions (all versioned / documented, never guessed per borrower):
  * classification map + taxonomy   -> which raw label maps to which template line
  * ratio definitions               -> the exact formulas (see references/domain-rules.md)
  * analyst adjustments             -> each carries provenance + a document citation

IMPORTANT: This produces an analytical *spread* only. It never makes or implies a credit
decision, credit rating, eligibility determination, or investment advice, and never approves,
declines, or recommends any facility. Ambiguous mappings are escalated, not guessed.

Usage:
  python calculate_or_transform.py spread_input.json | --selftest
Prints the spread JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {"tolerance": 1.0, "classification_map": {}}
DISCLAIMER = (
    "Spread, ratios, and cash-flow figures are analytical support prepared from "
    "borrower-supplied documents and analyst-documented adjustments. They are not a credit "
    "decision, credit rating, eligibility determination, or investment advice, and are not an "
    "approval, a denial, or a recommendation regarding any facility. Figures depend on the "
    "accuracy of the source documents; a credit officer must resolve any flagged mappings and "
    "make all lending decisions."
)

TAXONOMY_BS = {
    "cash", "accounts_receivable", "inventory", "other_current_assets",
    "net_fixed_assets", "intangibles", "other_noncurrent_assets",
    "accounts_payable", "current_portion_ltd", "accrued_liabilities",
    "other_current_liabilities", "long_term_debt", "other_noncurrent_liabilities",
    "common_equity", "retained_earnings",
}
IS_CODES = ("revenue", "cogs", "operating_expenses", "depreciation_amortization",
            "interest_expense", "taxes", "other_income_expense")
TAXONOMY = TAXONOMY_BS | set(IS_CODES)

CURRENT_ASSETS = ("cash", "accounts_receivable", "inventory", "other_current_assets")
NONCURRENT_ASSETS = ("net_fixed_assets", "intangibles", "other_noncurrent_assets")
CURRENT_LIABS = ("accounts_payable", "current_portion_ltd", "accrued_liabilities",
                 "other_current_liabilities")
NONCURRENT_LIABS = ("long_term_debt", "other_noncurrent_liabilities")
EQUITY = ("common_equity", "retained_earnings")

RATIO_DEFINITIONS = {
    "current_ratio": "total_current_assets / total_current_liabilities",
    "quick_ratio": "(cash + accounts_receivable) / total_current_liabilities",
    "debt_to_equity": "total_liabilities / total_equity",
    "debt_to_ebitda": "(long_term_debt + current_portion_ltd) / ebitda",
    "gross_margin": "gross_profit / revenue",
    "net_margin": "net_income / revenue",
    "interest_coverage": "ebit / interest_expense",
    "dscr": "ebitda / (interest_expense + current_portion_ltd)",
}


def _round(v):
    return round(float(v), 2)


def _ratio(numer, denom, tol):
    if denom is None or abs(denom) <= tol:
        return None
    return round(numer / denom, 4)


def _resolve(item, class_map):
    code = (item.get("code") or "").strip()
    if code and code in TAXONOMY:
        return code
    if not code:
        mapped = class_map.get(str(item.get("raw_label", "")).strip().lower())
        if mapped in TAXONOMY:
            return mapped
    return None


def _bs_view(comp):
    lambda k: _round(comp.get(k, 0.0))
    tca = _round(sum(comp.get(k, 0.0) for k in CURRENT_ASSETS))
    tnca = _round(sum(comp.get(k, 0.0) for k in NONCURRENT_ASSETS))
    ta = _round(tca + tnca)
    tcl = _round(sum(comp.get(k, 0.0) for k in CURRENT_LIABS))
    tncl = _round(sum(comp.get(k, 0.0) for k in NONCURRENT_LIABS))
    tl = _round(tcl + tncl)
    te = _round(sum(comp.get(k, 0.0) for k in EQUITY))
    return {
        "total_current_assets": tca, "total_noncurrent_assets": tnca, "total_assets": ta,
        "total_current_liabilities": tcl, "total_noncurrent_liabilities": tncl,
        "total_liabilities": tl, "total_equity": te,
    }


def _is_view(comp):
    g = lambda k: float(comp.get(k, 0.0))
    revenue, cogs = g("revenue"), g("cogs")
    opex, da = g("operating_expenses"), g("depreciation_amortization")
    interest, taxes = g("interest_expense"), g("taxes")
    other = g("other_income_expense")
    gross = revenue - cogs
    ebitda = gross - opex
    ebit = ebitda - da
    pretax = ebit - interest + other
    net_income = pretax - taxes
    return {
        "revenue": _round(revenue), "cogs": _round(cogs), "gross_profit": _round(gross),
        "operating_expenses": _round(opex), "ebitda": _round(ebitda),
        "depreciation_amortization": _round(da), "ebit": _round(ebit),
        "interest_expense": _round(interest), "other_income_expense": _round(other),
        "pretax_income": _round(pretax), "taxes": _round(taxes),
        "net_income": _round(net_income),
    }


def _ratios(bs, is_view, comp, tol):
    tcl = bs["total_current_liabilities"]
    total_debt = _round(comp.get("long_term_debt", 0.0) + comp.get("current_portion_ltd", 0.0))
    return {
        "current_ratio": _ratio(bs["total_current_assets"], tcl, tol),
        "quick_ratio": _ratio(comp.get("cash", 0.0) + comp.get("accounts_receivable", 0.0), tcl, tol),
        "debt_to_equity": _ratio(bs["total_liabilities"], bs["total_equity"], tol),
        "debt_to_ebitda": _ratio(total_debt, is_view["ebitda"], tol),
        "gross_margin": _ratio(is_view["gross_profit"], is_view["revenue"], tol),
        "net_margin": _ratio(is_view["net_income"], is_view["revenue"], tol),
        "interest_coverage": _ratio(is_view["ebit"], is_view["interest_expense"], tol),
        "dscr": _ratio(is_view["ebitda"],
                       is_view["interest_expense"] + comp.get("current_portion_ltd", 0.0), tol),
    }


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    tol = float(cfg["tolerance"])
    class_map = {str(k).strip().lower(): v for k, v in (cfg.get("classification_map") or {}).items()}
    periods = list(doc["periods"])

    # index reported anchors
    reported = {}
    for r in doc.get("reported_totals") or []:
        reported[(r["period"], r["statement"], r["key"])] = _round(r["amount"])

    # classify line items into components per (period, statement)
    comp_bs = {p: {} for p in periods}
    comp_is = {p: {} for p in periods}
    ambiguous = []
    for it in doc["line_items"]:
        p, stmt = it.get("period"), it.get("statement")
        code = _resolve(it, class_map)
        if code is None:
            ambiguous.append({
                "period": p, "statement": stmt, "raw_label": it.get("raw_label"),
                "amount": _round(it.get("amount", 0.0)),
                "proposed_code": (it.get("code") or None),
                "citation": it.get("source_ref"),
                "why": "raw label not found in classification map and no valid taxonomy code supplied",
            })
            continue
        bucket = comp_bs if stmt == "balance_sheet" else comp_is
        bucket.setdefault(p, {})
        bucket[p][code] = bucket[p].get(code, 0.0) + float(it.get("amount", 0.0))

    # adjustments register (income-statement add-backs only), keyed for normalized view
    register = []
    adj_by_pc = {}  # (period, code) -> signed delta
    for a in doc.get("adjustments") or []:
        signed = float(a["amount"]) * (1.0 if a["direction"] == "add" else -1.0)
        adj_by_pc[(a["period"], a["code"])] = adj_by_pc.get((a["period"], a["code"]), 0.0) + signed
        register.append({
            "id": a["id"], "statement": a["statement"], "period": a["period"], "code": a["code"],
            "amount": _round(a["amount"]), "direction": a["direction"],
            "signed_effect": _round(signed), "reason": a.get("reason", ""),
            "provenance": (a.get("provenance") or ""), "citation": (a.get("citation") or ""),
        })

    spreads = []
    prior_wc = None
    for p in periods:
        bs_comp = comp_bs.get(p, {})
        is_comp = comp_is.get(p, {})
        norm_comp = dict(is_comp)
        for code in IS_CODES:
            delta = adj_by_pc.get((p, code))
            if delta:
                norm_comp[code] = norm_comp.get(code, 0.0) + delta

        bs = _bs_view(bs_comp)
        is_view = _is_view(is_comp)
        norm_view = _is_view(norm_comp)

        # ----- tie-outs (formula correctness) -----
        assets = bs["total_assets"]
        liab_plus_eq = _round(bs["total_liabilities"] + bs["total_equity"])
        bs_tie = {
            "balances": {"computed_assets": assets, "computed_liab_plus_equity": liab_plus_eq,
                         "diff": _round(assets - liab_plus_eq), "ok": abs(assets - liab_plus_eq) <= tol}
        }
        for key, val in (("total_assets", bs["total_assets"]),
                         ("total_liabilities", bs["total_liabilities"]),
                         ("total_equity", bs["total_equity"])):
            rep = reported.get((p, "balance_sheet", key))
            if rep is not None:
                bs_tie[key] = {"computed": val, "reported": rep, "diff": _round(val - rep),
                               "ok": abs(val - rep) <= tol}

        is_tie = {}
        rep_ni = reported.get((p, "income_statement", "net_income"))
        if rep_ni is not None:
            is_tie["net_income"] = {"computed": is_view["net_income"], "reported": rep_ni,
                                    "diff": _round(is_view["net_income"] - rep_ni),
                                    "ok": abs(is_view["net_income"] - rep_ni) <= tol}

        ratios = _ratios(bs, is_view, bs_comp, tol)

        # ----- operating cash-flow proxy (needs a prior period for working-capital change) -----
        wc = _round(bs["total_current_assets"] - bs["total_current_liabilities"])
        if prior_wc is None:
            cash_flow = {"evaluable": False, "operating_cash_flow_proxy": None,
                         "reason": "no prior period for the working-capital change term"}
        else:
            change_wc = _round(wc - prior_wc)
            ocf = _round(is_view["net_income"] + is_view["depreciation_amortization"] - change_wc)
            cash_flow = {"evaluable": True, "operating_cash_flow_proxy": ocf,
                         "components": {"net_income": is_view["net_income"],
                                        "depreciation_amortization": is_view["depreciation_amortization"],
                                        "working_capital": wc, "prior_working_capital": prior_wc,
                                        "change_in_working_capital": change_wc}}
        prior_wc = wc

        spreads.append({
            "period": p,
            "balance_sheet": {"components": {k: _round(v) for k, v in sorted(bs_comp.items())},
                              "subtotals": bs, "reported": {
                                  k: reported.get((p, "balance_sheet", k))
                                  for k in ("total_assets", "total_liabilities", "total_equity")},
                              "tieouts": bs_tie},
            "income_statement": {"components": {k: _round(is_comp.get(k, 0.0)) for k in IS_CODES},
                                 "as_reported": is_view,
                                 "normalized_components": {k: _round(norm_comp.get(k, 0.0)) for k in IS_CODES},
                                 "normalized": norm_view,
                                 "reported_net_income": rep_ni,
                                 "tieouts": is_tie},
            "ratios": ratios,
            "cash_flow": cash_flow,
        })

    # period-over-period trends (as-reported)
    trends = {}
    for i in range(1, len(periods)):
        prev, cur = spreads[i - 1], spreads[i]
        for metric, path in (("revenue", ("income_statement", "as_reported", "revenue")),
                             ("ebitda", ("income_statement", "as_reported", "ebitda")),
                             ("net_income", ("income_statement", "as_reported", "net_income"))):
            pv = prev[path[0]][path[1]][path[2]]
            cv = cur[path[0]][path[1]][path[2]]
            growth = round((cv - pv) / pv, 4) if abs(pv) > tol else None
            trends.setdefault(f"{metric}_growth", []).append(
                {"from": prev["period"], "to": cur["period"], "prior": pv, "current": cv, "growth": growth})

    borrower = str(doc["borrower_id"])
    return {
        "spread_id": f"fsa-{borrower.replace('*', '')}-{doc['as_of']}-0001",
        "borrower_id": borrower,
        "borrower_name": doc.get("borrower_name"),
        "as_of": doc["as_of"],
        "template_version": doc.get("template_version"),
        "classification_map_version": doc.get("classification_map_version"),
        "config_version": doc.get("config_version"),
        "tolerance": tol,
        "periods": periods,
        "spreads": spreads,
        "trends": trends,
        "adjustments_register": register,
        "ambiguous_mappings": ambiguous,
        "requires_human_mapping": bool(ambiguous),
        "drivers": {
            "template_version": doc.get("template_version"),
            "classification_map_version": doc.get("classification_map_version"),
            "ratio_definitions": RATIO_DEFINITIONS,
            "tolerance": tol,
            "adjustment_policy": "Add-backs are pre-tax and applied only to the normalized view; each carries provenance and a citation. Taxes are held as reported unless a tax effect is separately documented.",
        },
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "spread_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
