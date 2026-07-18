#!/usr/bin/env python3
"""Deterministic, explainable portfolio diversification/concentration metrics.

Reads a portfolio file (see validate_input.py), computes transparent concentration,
sector/geography/asset-class, factor, correlation, and liquidity exposure checks, attaches
evidence + citations to each flagged check, and maps the flagged set to a descriptive
diversification band. Emits a machine-readable core the SKILL wraps in a plain-language,
educational profile.

IMPORTANT: This produces explainable *exposure observations* only. It never produces
personalized investment advice, a suitability judgment, a forecast, or a buy/sell/hold/
rebalance recommendation. Every metric and threshold is documented in
references/domain-rules.md and comes from versioned config, never tuned to an individual.

Usage:
  python calculate_or_transform.py portfolio.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path

DEFAULT_CONFIG = {
    "single_name_max": 0.10, "topn": 5, "topn_max": 0.40, "sector_max": 0.30,
    "geography_max": 0.50, "asset_class_max": 0.90, "factor_band": 0.50,
    "corr_max": 0.60, "liquidity_days_threshold": 7, "illiquid_weight_max": 0.15,
    "weight_sum_tolerance": 0.02,
}
DISCLAIMER = ("Educational risk analysis only; not personalized investment advice or a "
             "recommendation to buy, sell, or hold any security.")
# Checks that on their own push the band to the top tier (see references/domain-rules.md).
ESCALATORS = {"single_name_concentration", "correlation_concentration"}


def _cite(p: dict) -> str:
    return f"positions:{p.get('source_ref', '?')}@{p.get('as_of', '')}"


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _bucket_weights(positions, key):
    agg = defaultdict(float)
    covered = 0.0
    for p in positions:
        k = p.get(key)
        if k in (None, ""):
            continue
        agg[k] += float(p["weight"])
        covered += float(p["weight"])
    return dict(agg), covered


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = doc.get("as_of", "")
    positions = [dict(p, as_of=as_of) for p in doc["positions"]]
    total_w = sum(float(p["weight"]) for p in positions)

    checks, not_evaluable = [], []

    def add(name, flagged, reason, evidence, threshold, contribution):
        checks.append({"check": name, "flagged": bool(flagged), "reason": reason,
                       "evidence": evidence, "threshold": threshold,
                       "contribution": contribution})

    # --- summary metrics (always reported) ---
    hhi = sum(float(p["weight"]) ** 2 for p in positions)
    effective_holdings = round(1.0 / hhi, 2) if hhi > 0 else None
    ranked = sorted(positions, key=lambda p: float(p["weight"]), reverse=True)
    topn = int(cfg["topn"])
    topn_weight = round(sum(float(p["weight"]) for p in ranked[:topn]), 6)
    top10_weight = round(sum(float(p["weight"]) for p in ranked[:10]), 6)

    # --- single_name_concentration (escalator) ---
    big = [p for p in positions if float(p["weight"]) > cfg["single_name_max"]]
    add("single_name_concentration", bool(big),
        (f"{len(big)} position(s) exceed the {cfg['single_name_max']:.0%} single-name reference"
         if big else f"no single position exceeds {cfg['single_name_max']:.0%}"),
        [{"symbol": p["symbol"], "weight": round(float(p["weight"]), 6), "citation": _cite(p)}
         for p in sorted(big, key=lambda x: float(x["weight"]), reverse=True)],
        {"single_name_max": cfg["single_name_max"]}, len(big))

    # --- topN_concentration ---
    add("topN_concentration", topn_weight > cfg["topn_max"],
        (f"top-{topn} weight {topn_weight:.2%} exceeds {cfg['topn_max']:.0%}"
         if topn_weight > cfg["topn_max"] else f"top-{topn} weight {topn_weight:.2%} within {cfg['topn_max']:.0%}"),
        [{"symbol": p["symbol"], "weight": round(float(p["weight"]), 6), "citation": _cite(p)}
         for p in ranked[:topn]] if topn_weight > cfg["topn_max"] else [],
        {"topn": topn, "topn_max": cfg["topn_max"], "topn_weight": topn_weight}, 1 if topn_weight > cfg["topn_max"] else 0)

    # --- sector_concentration ---
    sec_w, sec_cov = _bucket_weights(positions, "sector")
    if sec_cov > 0:
        top_sec, top_sec_w = max(sec_w.items(), key=lambda kv: kv[1])
        sec_hhi = sum(w ** 2 for w in sec_w.values())
        fired = top_sec_w > cfg["sector_max"]
        add("sector_concentration", fired,
            (f"sector '{top_sec}' is {top_sec_w:.2%}, above {cfg['sector_max']:.0%}"
             if fired else f"largest sector '{top_sec}' {top_sec_w:.2%} within {cfg['sector_max']:.0%}"),
            [{"symbol": p["symbol"], "sector": p.get("sector"), "weight": round(float(p["weight"]), 6), "citation": _cite(p)}
             for p in positions if p.get("sector") == top_sec] if fired else [],
            {"sector_max": cfg["sector_max"], "top_sector": top_sec, "top_sector_weight": round(top_sec_w, 6), "sector_hhi": round(sec_hhi, 6)},
            1 if fired else 0)
    else:
        not_evaluable.append({"check": "sector_concentration", "why": "no sector data on any position"})

    # --- geography_concentration ---
    geo_w, geo_cov = _bucket_weights(positions, "region")
    if geo_cov > 0:
        top_geo, top_geo_w = max(geo_w.items(), key=lambda kv: kv[1])
        fired = top_geo_w > cfg["geography_max"]
        add("geography_concentration", fired,
            (f"region '{top_geo}' is {top_geo_w:.2%}, above {cfg['geography_max']:.0%}"
             if fired else f"largest region '{top_geo}' {top_geo_w:.2%} within {cfg['geography_max']:.0%}"),
            [{"region": top_geo, "weight": round(top_geo_w, 6), "citation": f"positions:pf={doc['portfolio_id']};region={top_geo}@{as_of}"}] if fired else [],
            {"geography_max": cfg["geography_max"], "top_region": top_geo, "top_region_weight": round(top_geo_w, 6)},
            1 if fired else 0)
    else:
        not_evaluable.append({"check": "geography_concentration", "why": "no region data on any position"})

    # --- asset_class_concentration ---
    ac_w, ac_cov = _bucket_weights(positions, "asset_class")
    if ac_cov > 0:
        top_ac, top_ac_w = max(ac_w.items(), key=lambda kv: kv[1])
        fired = top_ac_w > cfg["asset_class_max"]
        add("asset_class_concentration", fired,
            (f"asset class '{top_ac}' is {top_ac_w:.2%}, above {cfg['asset_class_max']:.0%}"
             if fired else f"largest asset class '{top_ac}' {top_ac_w:.2%} within {cfg['asset_class_max']:.0%}"),
            [{"asset_class": top_ac, "weight": round(top_ac_w, 6), "citation": f"positions:pf={doc['portfolio_id']};asset_class={top_ac}@{as_of}"}] if fired else [],
            {"asset_class_max": cfg["asset_class_max"], "top_asset_class": top_ac, "top_asset_class_weight": round(top_ac_w, 6)},
            1 if fired else 0)
    else:
        not_evaluable.append({"check": "asset_class_concentration", "why": "no asset_class data on any position"})

    # --- factor_tilt (needs factor_loadings) ---
    with_factors = [p for p in positions if isinstance(p.get("factor_loadings"), dict) and p["factor_loadings"]]
    if with_factors:
        factors = sorted({f for p in with_factors for f in p["factor_loadings"]})
        tilts = {}
        for f in factors:
            tilts[f] = round(sum(float(p["weight"]) * float(p["factor_loadings"].get(f, 0.0)) for p in with_factors), 6)
        exceed = {f: t for f, t in tilts.items() if abs(t) > cfg["factor_band"]}
        add("factor_tilt", bool(exceed),
            (f"weighted tilt exceeds +/-{cfg['factor_band']} on: " + ", ".join(f"{f} ({t:+.2f})" for f, t in exceed.items())
             if exceed else f"no factor tilt exceeds +/-{cfg['factor_band']}"),
            [{"factor": f, "tilt": t, "citation": f"factors:pf={doc['portfolio_id']};factor={f}@{as_of}"} for f, t in exceed.items()],
            {"factor_band": cfg["factor_band"], "tilts": tilts}, len(exceed))
    else:
        not_evaluable.append({"check": "factor_tilt", "why": "no factor_loadings on any position"})

    # --- correlation_concentration (escalator; needs correlation_matrix) ---
    cm = doc.get("correlation_matrix") or {}
    syms = cm.get("symbols") or []
    matrix = cm.get("matrix") or []
    if len(syms) >= 2 and len(matrix) == len(syms):
        pairs = []
        for i in range(len(syms)):
            for j in range(i + 1, len(syms)):
                try:
                    pairs.append((syms[i], syms[j], float(matrix[i][j])))
                except (IndexError, TypeError, ValueError):
                    continue
        if pairs:
            avg_corr = round(sum(c for _, _, c in pairs) / len(pairs), 6)
            fired = avg_corr > cfg["corr_max"]
            top_pairs = sorted(pairs, key=lambda x: x[2], reverse=True)[:5]
            add("correlation_concentration", fired,
                (f"average pairwise correlation {avg_corr:.2f} exceeds {cfg['corr_max']:.2f}"
                 if fired else f"average pairwise correlation {avg_corr:.2f} within {cfg['corr_max']:.2f}"),
                [{"pair": f"{a}-{b}", "correlation": round(c, 4),
                  "citation": f"corr:pf={doc['portfolio_id']};pair={a}-{b}@{as_of}"} for a, b, c in top_pairs] if fired else [],
                {"corr_max": cfg["corr_max"], "avg_pairwise_correlation": avg_corr, "n_pairs": len(pairs)},
                1 if fired else 0)
        else:
            not_evaluable.append({"check": "correlation_concentration", "why": "correlation matrix has no usable pairs"})
    else:
        not_evaluable.append({"check": "correlation_concentration", "why": "no correlation_matrix (>=2 symbols) provided"})

    # --- liquidity_concentration (needs liquidity_days) ---
    with_liq = [p for p in positions if _num(p.get("liquidity_days")) is not None]
    if with_liq:
        illiquid = [p for p in with_liq if _num(p["liquidity_days"]) > cfg["liquidity_days_threshold"]]
        illiquid_w = round(sum(float(p["weight"]) for p in illiquid), 6)
        fired = illiquid_w > cfg["illiquid_weight_max"]
        add("liquidity_concentration", fired,
            (f"illiquid-bucket weight {illiquid_w:.2%} exceeds {cfg['illiquid_weight_max']:.0%} "
             f"(>{cfg['liquidity_days_threshold']}d to liquidate)"
             if fired else f"illiquid-bucket weight {illiquid_w:.2%} within {cfg['illiquid_weight_max']:.0%}"),
            [{"symbol": p["symbol"], "liquidity_days": _num(p["liquidity_days"]), "weight": round(float(p["weight"]), 6), "citation": _cite(p)}
             for p in illiquid] if fired else [],
            {"illiquid_weight_max": cfg["illiquid_weight_max"], "liquidity_days_threshold": cfg["liquidity_days_threshold"], "illiquid_weight": illiquid_w},
            1 if fired else 0)
    else:
        not_evaluable.append({"check": "liquidity_concentration", "why": "no liquidity_days on any position"})

    flagged = [c["check"] for c in checks if c["flagged"]]
    # deterministic band mapping (see references/domain-rules.md)
    if len(flagged) >= 3 or (ESCALATORS & set(flagged)):
        band = "Highly concentrated"
    elif flagged:
        band = "Moderately concentrated"
    else:
        band = "Well-diversified"

    educational_prompts = []
    if flagged:
        educational_prompts = [
            "Concentration is a description of current exposures, not a verdict; a concentrated portfolio can reflect a deliberate, informed strategy.",
            "Diversification metrics depend on the classification scheme, reference data, and window used; correlations in particular change over time and can rise in stressed markets.",
            "Factor tilts and correlation figures are model estimates sensitive to the bundled reference data and the config version.",
            "Whether these exposures fit an investor's objectives, time horizon, liquidity needs, and risk tolerance is a question for the investor and a licensed financial professional.",
        ]

    return {
        "analysis_id": f"prdc-{str(doc['portfolio_id']).replace('*', '')}-{as_of}-0001",
        "portfolio_id": doc["portfolio_id"],
        "as_of": as_of,
        "config_version": doc.get("config_version"),
        "base_currency": doc.get("base_currency"),
        "benchmark": doc.get("benchmark"),
        "metrics": {
            "n_positions": len(positions),
            "weight_sum": round(total_w, 6),
            "hhi": round(hhi, 6),
            "effective_holdings": effective_holdings,
            "topN": topn,
            "topN_weight": topn_weight,
            "top10_weight": top10_weight,
        },
        "checks": checks,
        "flagged_checks": flagged,
        "not_evaluable": not_evaluable,
        "diversification_band": band,
        "educational_prompts": educational_prompts,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "portfolio_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
