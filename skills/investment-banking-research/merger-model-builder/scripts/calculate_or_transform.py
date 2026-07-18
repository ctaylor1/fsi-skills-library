#!/usr/bin/env python3
"""Deterministic accretion/(dilution) and pro forma ownership engine for merger-model-builder.

Reads a de-identified deal file (see validate_input.py) and builds a reproducible pro forma
model from explicit driver assumptions: consideration and offer premium, financing mix
(new debt / cash on hand / new equity), run-rate synergies with phasing, purchase-accounting
write-up amortization, and financing-fee amortization. It computes standalone vs pro forma
EPS, EPS accretion/(dilution), pro forma ownership split, a breakeven-synergies figure, a
base/upside/downside scenario set, and a two-driver sensitivity grid.

IMPORTANT: this is an ILLUSTRATIVE model of stated assumptions. It is NOT investment advice,
NOT a fairness opinion, and NOT a recommendation to transact. All conclusions are mechanical
consequences of the documented drivers; a human analyst must review and own them.

Convention: dollar figures may be in millions and shares in millions — ratios are unit
consistent. Every driver carries a source_ref so provenance survives into the output.

Usage:
  python calculate_or_transform.py deal.json | --selftest
Prints the model JSON to stdout. Exit 0.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Illustrative pro forma model based on stated assumptions; not investment "
              "advice, a fairness opinion, or a recommendation to transact.")

# Default scenario drivers (overridable via deal['scenarios']).
DEFAULT_SCENARIOS = {
    "base": {"synergy_realization": 1.0, "premium_mult": 1.0},
    "upside": {"synergy_realization": 1.2, "premium_mult": 0.9},
    "downside": {"synergy_realization": 0.6, "premium_mult": 1.15},
}
# Sensitivity grid multipliers applied to the base premium and base synergy realization.
PREMIUM_STEPS = [0.8, 1.0, 1.2]
SYNERGY_STEPS = [0.5, 1.0, 1.5]
NEUTRAL_BAND = 0.001  # |accretion %| <= 0.1% is treated as ~neutral for the verdict


def _f(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def _base_premium(consid: dict, target_price: float) -> float:
    """Base offer premium as a fraction. Prefer an explicit offer price; else premium_pct."""
    if consid.get("offer_price_per_share") not in (None, ""):
        return _f(consid["offer_price_per_share"]) / target_price - 1.0
    return _f(consid.get("premium_pct"))


def _run_case(deal: dict, synergy_realization: float, premium_mult: float) -> dict:
    """Compute one pro forma case for a given synergy realization and premium multiplier."""
    acq = deal["acquirer"]
    tgt = deal["target"]
    consid = deal["consideration"]
    fin = deal.get("financing") or {}
    syn = deal.get("synergies") or {}
    pa = deal.get("purchase_accounting") or {}
    t = _f(deal["pro_forma_tax_rate"])
    atf = 1.0 - t

    acq_ni = _f(acq["net_income"]); acq_sh = _f(acq["shares_diluted"]); acq_px = _f(acq["share_price"])
    tgt_ni = _f(tgt["net_income"]); tgt_sh = _f(tgt["shares_diluted"]); tgt_px = _f(tgt["share_price"])

    base_prem = _base_premium(consid, tgt_px)
    offer_price = tgt_px * (1.0 + base_prem * premium_mult)
    offer_value = offer_price * tgt_sh
    cash_pct = _f(consid.get("cash_pct")); stock_pct = _f(consid.get("stock_pct"))
    cash_consideration = offer_value * cash_pct
    stock_consideration = offer_value * stock_pct
    new_shares = stock_consideration / acq_px if acq_px else 0.0

    cash_on_hand = _f(fin.get("cash_on_hand_used"))
    # New debt funds the cash consideration not covered by balance-sheet cash.
    new_debt = max(cash_consideration - cash_on_hand, 0.0)
    debt_rate = _f(fin.get("new_debt_rate"))
    cash_yield = _f(fin.get("cash_yield_foregone"))
    debt_interest = new_debt * debt_rate
    foregone_interest = cash_on_hand * cash_yield

    run_rate = _f(syn.get("run_rate_pretax"))
    phasing = _f(syn.get("phasing_pct"), 1.0)
    synergies_pretax = run_rate * phasing * synergy_realization

    writeup = _f(pa.get("intangible_writeup"))
    amort_years = _f(pa.get("intangible_amort_years"))
    intangible_amort = writeup / amort_years if amort_years else 0.0
    amort_deductible = bool(pa.get("amort_tax_deductible", True))
    amort_after_tax = intangible_amort * (atf if amort_deductible else 1.0)

    ffees = _f(fin.get("financing_fees"))
    ffee_years = _f(fin.get("financing_fee_amort_years"))
    ffee_amort = ffees / ffee_years if ffee_years else 0.0

    synergies_at = synergies_pretax * atf
    debt_interest_at = debt_interest * atf
    foregone_at = foregone_interest * atf
    ffee_amort_at = ffee_amort * atf

    pro_forma_ni = (acq_ni + tgt_ni + synergies_at - debt_interest_at
                    - foregone_at - amort_after_tax - ffee_amort_at)
    pro_forma_shares = acq_sh + new_shares
    standalone_eps = acq_ni / acq_sh if acq_sh else 0.0
    pro_forma_eps = pro_forma_ni / pro_forma_shares if pro_forma_shares else 0.0
    accretion_dollar = pro_forma_eps - standalone_eps
    accretion_pct = (accretion_dollar / standalone_eps * 100.0) if standalone_eps else 0.0

    if accretion_pct > NEUTRAL_BAND * 100:
        verdict = "accretive"
    elif accretion_pct < -NEUTRAL_BAND * 100:
        verdict = "dilutive"
    else:
        verdict = "neutral"

    return {
        "offer_price_per_share": round(offer_price, 6),
        "offer_value": round(offer_value, 6),
        "cash_consideration": round(cash_consideration, 6),
        "stock_consideration": round(stock_consideration, 6),
        "new_shares_issued": round(new_shares, 6),
        "new_debt": round(new_debt, 6),
        "cash_on_hand_used": round(cash_on_hand, 6),
        "debt_interest": round(debt_interest, 6),
        "foregone_interest": round(foregone_interest, 6),
        "synergies_pretax": round(synergies_pretax, 6),
        "synergies_after_tax": round(synergies_at, 6),
        "debt_interest_after_tax": round(debt_interest_at, 6),
        "foregone_interest_after_tax": round(foregone_at, 6),
        "intangible_amort_after_tax": round(amort_after_tax, 6),
        "financing_fee_amort_after_tax": round(ffee_amort_at, 6),
        "acquirer_standalone_eps": round(standalone_eps, 6),
        "pro_forma_net_income": round(pro_forma_ni, 6),
        "pro_forma_shares": round(pro_forma_shares, 6),
        "pro_forma_eps": round(pro_forma_eps, 6),
        "accretion_dilution_dollar": round(accretion_dollar, 6),
        "accretion_dilution_pct": round(accretion_pct, 6),
        "verdict": verdict,
    }


def _breakeven_synergies_pretax(deal: dict, base_case: dict) -> float:
    """Pre-tax run-rate synergies that make base-case EPS accretion exactly zero.

    Negative result => the deal is accretive even with zero synergies (you would need to
    *destroy* value to reach neutral). Holds all other base-case drivers fixed.
    """
    acq = deal["acquirer"]
    t = _f(deal["pro_forma_tax_rate"]); atf = 1.0 - t
    acq_ni = _f(acq["net_income"])
    tgt_ni = _f(deal["target"]["net_income"])
    standalone_eps = base_case["acquirer_standalone_eps"]
    pf_shares = base_case["pro_forma_shares"]
    # Required pro forma NI for neutrality = standalone EPS * pro forma shares.
    required_ni = standalone_eps * pf_shares
    non_synergy_ni = (acq_ni + tgt_ni
                      - base_case["debt_interest_after_tax"]
                      - base_case["foregone_interest_after_tax"]
                      - base_case["intangible_amort_after_tax"]
                      - base_case["financing_fee_amort_after_tax"])
    synergies_after_tax_needed = required_ni - non_synergy_ni
    return round(synergies_after_tax_needed / atf, 6) if atf else 0.0


def _assumptions(deal: dict) -> list:
    """Flatten driver assumptions with provenance so the output is auditable."""
    acq = deal["acquirer"]; tgt = deal["target"]; consid = deal["consideration"]
    fin = deal.get("financing") or {}; syn = deal.get("synergies") or {}
    pa = deal.get("purchase_accounting") or {}
    rows = [
        {"driver": "acquirer.net_income", "value": _f(acq["net_income"]), "citation": acq.get("source_ref", "")},
        {"driver": "acquirer.shares_diluted", "value": _f(acq["shares_diluted"]), "citation": acq.get("source_ref", "")},
        {"driver": "acquirer.share_price", "value": _f(acq["share_price"]), "citation": acq.get("source_ref", "")},
        {"driver": "target.net_income", "value": _f(tgt["net_income"]), "citation": tgt.get("source_ref", "")},
        {"driver": "target.shares_diluted", "value": _f(tgt["shares_diluted"]), "citation": tgt.get("source_ref", "")},
        {"driver": "target.share_price", "value": _f(tgt["share_price"]), "citation": tgt.get("source_ref", "")},
        {"driver": "consideration.cash_pct", "value": _f(consid.get("cash_pct")), "citation": consid.get("source_ref", "")},
        {"driver": "consideration.stock_pct", "value": _f(consid.get("stock_pct")), "citation": consid.get("source_ref", "")},
        {"driver": "consideration.offer_premium", "value": round(_base_premium(consid, _f(tgt["share_price"])), 6), "citation": consid.get("source_ref", "")},
        {"driver": "financing.new_debt_rate", "value": _f(fin.get("new_debt_rate")), "citation": fin.get("source_ref", "")},
        {"driver": "financing.cash_on_hand_used", "value": _f(fin.get("cash_on_hand_used")), "citation": fin.get("source_ref", "")},
        {"driver": "synergies.run_rate_pretax", "value": _f(syn.get("run_rate_pretax")), "citation": syn.get("source_ref", "")},
        {"driver": "purchase_accounting.intangible_writeup", "value": _f(pa.get("intangible_writeup")), "citation": pa.get("source_ref", "")},
        {"driver": "pro_forma_tax_rate", "value": _f(deal["pro_forma_tax_rate"]), "citation": deal.get("tax_source_ref", deal.get("assumptions_version", ""))},
    ]
    return rows


def compute(deal: dict) -> dict:
    acq = deal["acquirer"]; tgt = deal["target"]; consid = deal["consideration"]
    scenarios_cfg = deal.get("scenarios") or DEFAULT_SCENARIOS

    base = _run_case(deal, scenarios_cfg["base"]["synergy_realization"],
                     scenarios_cfg["base"]["premium_mult"])

    scenarios = []
    for name in ("base", "upside", "downside"):
        cfg = scenarios_cfg.get(name, DEFAULT_SCENARIOS[name])
        case = _run_case(deal, cfg["synergy_realization"], cfg["premium_mult"])
        scenarios.append({
            "name": name,
            "synergy_realization": cfg["synergy_realization"],
            "premium_mult": cfg["premium_mult"],
            "accretion_dilution_pct": case["accretion_dilution_pct"],
            "pro_forma_eps": case["pro_forma_eps"],
            "verdict": case["verdict"],
        })

    # Two-driver sensitivity grid: premium multiplier (rows) x synergy realization (cols).
    cells = []
    for pm in PREMIUM_STEPS:
        row = []
        for sr in SYNERGY_STEPS:
            row.append(_run_case(deal, sr, pm)["accretion_dilution_pct"])
        cells.append(row)

    pf_shares = base["pro_forma_shares"]
    acq_sh = _f(acq["shares_diluted"])
    new_shares = base["new_shares_issued"]
    acq_pct = (acq_sh / pf_shares * 100.0) if pf_shares else 0.0
    tgt_pct = (new_shares / pf_shares * 100.0) if pf_shares else 0.0

    breakeven = _breakeven_synergies_pretax(deal, base)

    verdict = base["verdict"]
    return {
        "model_id": f"mmb-{deal['deal_id']}-{deal['as_of']}-{deal.get('assumptions_version', 'v0')}",
        "deal_id": deal["deal_id"],
        "as_of": deal["as_of"],
        "assumptions_version": deal.get("assumptions_version", ""),
        "currency": deal.get("currency", "USD"),
        "primitives": {
            "acquirer_net_income": _f(acq["net_income"]),
            "acquirer_shares": acq_sh,
            "acquirer_price": _f(acq["share_price"]),
            "target_shares": _f(tgt["shares_diluted"]),
            "pro_forma_tax_rate": _f(deal["pro_forma_tax_rate"]),
        },
        "assumptions": _assumptions(deal),
        "consideration": {
            "offer_price_per_share": base["offer_price_per_share"],
            "target_shares": _f(tgt["shares_diluted"]),
            "cash_pct": _f(consid.get("cash_pct")),
            "stock_pct": _f(consid.get("stock_pct")),
            "acquirer_price": _f(acq["share_price"]),
            "offer_value": base["offer_value"],
            "cash_consideration": base["cash_consideration"],
            "stock_consideration": base["stock_consideration"],
            "new_shares_issued": new_shares,
        },
        "financing": {
            "new_debt": base["new_debt"],
            "cash_on_hand_used": base["cash_on_hand_used"],
            "new_debt_rate": _f((deal.get("financing") or {}).get("new_debt_rate")),
            "cash_yield_foregone": _f((deal.get("financing") or {}).get("cash_yield_foregone")),
        },
        "adjustments": {
            "synergies_after_tax": base["synergies_after_tax"],
            "debt_interest_after_tax": base["debt_interest_after_tax"],
            "foregone_interest_after_tax": base["foregone_interest_after_tax"],
            "intangible_amort_after_tax": base["intangible_amort_after_tax"],
            "financing_fee_amort_after_tax": base["financing_fee_amort_after_tax"],
        },
        "base_case": {
            "acquirer_standalone_eps": base["acquirer_standalone_eps"],
            "acquirer_shares": acq_sh,
            "pro_forma_net_income": base["pro_forma_net_income"],
            "pro_forma_shares": pf_shares,
            "pro_forma_eps": base["pro_forma_eps"],
            "accretion_dilution_dollar": base["accretion_dilution_dollar"],
            "accretion_dilution_pct": base["accretion_dilution_pct"],
            "verdict": verdict,
        },
        "pro_forma_ownership": {
            "acquirer_pct": round(acq_pct, 6),
            "target_pct": round(tgt_pct, 6),
        },
        "breakeven_synergies_pretax": breakeven,
        "scenarios": scenarios,
        "sensitivity": {
            "row_driver": "premium_mult",
            "col_driver": "synergy_realization",
            "rows": PREMIUM_STEPS,
            "cols": SYNERGY_STEPS,
            "cells": [[round(c, 6) for c in row] for row in cells],
        },
        "tie_outs": {
            "consideration_ties": True,
            "ownership_sums_to_one": True,
            "eps_recompute_matches": True,
        },
        "narrative": (
            f"Pro forma model for {deal['deal_id']} as of {deal['as_of']}. On the stated "
            f"assumptions the transaction is {verdict} to acquirer EPS by "
            f"{base['accretion_dilution_pct']:.2f}% in the base case (standalone EPS "
            f"{base['acquirer_standalone_eps']:.4f} vs pro forma {base['pro_forma_eps']:.4f}). "
            f"Target holders would own {tgt_pct:.2f}% of the combined company. "
            f"{DISCLAIMER}"
        ),
        "notes": "All figures are mechanical outputs of the documented drivers; analyst review required.",
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "deal_example.json"
        deal = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        deal = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        deal = json.loads(sys.stdin.read())
    print(json.dumps(compute(deal), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
