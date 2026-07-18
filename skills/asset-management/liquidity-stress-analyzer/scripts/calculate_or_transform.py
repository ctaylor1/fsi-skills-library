#!/usr/bin/env python3
"""Deterministic, explainable liquidity-stress computation for liquidity-stress-analyzer.

Reads a portfolio file (see validate_input.py), applies a transparent, fully-parameterized
liquidity scenario, and computes:
  * a liquidation profile (value liquidatable within each horizon bucket + full-liquidation
    horizon), using a documented participation-of-ADV model;
  * a set of liquidity metrics, each with a threshold, a breached flag, and cited evidence;
  * a deterministic suggested liquidity-risk band mapped from the breached-metric set.

IMPORTANT: This produces explainable *metrics and a triage suggestion* only, under stated
scenario assumptions. It never produces an investment/trading recommendation, a fund-
liquidity-action (gate / suspension / side-pocket) determination, or a mandate-breach
finding. The band mapping is deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py portfolio.json | --selftest
Normal mode prints the analysis JSON to stdout (exit 0). --selftest additionally verifies
bundled-fixture invariants and prints a line ending "N error(s)" (exit 0 pass / 1 fail).
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "participation_rate": 0.20,      # max fraction of ADV assumed tradable per day
    "horizon_buckets_days": [1, 7, 30],
    "max_horizon_days": 30,          # full-liquidation horizon cap (days)
    "spread_cost_weight": 0.5,       # fraction of quoted spread paid to cross
    "impact_coeff_bps": 10.0,        # linear market-impact coeff (bps at 100% participation)
    "coverage_watch_multiple": 1.25, # coverage below this (but >= 1.0) is "thin"
    "cost_watch_bps": 75.0,          # portfolio liquidation cost above this is "elevated"
    "illiquid_bucket_days": 30,      # bucket used for the illiquid-concentration test
    "illiquid_nav_watch_frac": 0.20, # NAV fraction not liquidatable within that bucket
}
# Scenario assumptions (transparent; recorded in the output). Baseline = no stress.
DEFAULT_SCENARIO = {
    "name": "baseline", "adv_haircut": 1.0, "spread_multiple": 1.0,
    "price_shock": 0.0, "redemption_pct": 0.0, "redemption_notice_days": 7,
}
DISCLAIMER = ("Liquidity analysis and evidence only under stated scenario assumptions; not "
              "an investment, trading, or fund-liquidity-action determination. No trade, "
              "redemption gate, or other liquidity action has been taken.")

# Metric severity classes drive the deterministic band mapping (see references/domain-rules.md).
STRESS_LEVEL = {"redemption_coverage_shortfall", "full_liquidation_horizon_exceeded",
                "collateral_buffer_shortfall"}
WATCH_LEVEL = {"redemption_coverage_thin", "liquidation_cost_elevated", "illiquid_concentration"}


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def band_for(breached: list) -> str:
    """Deterministic mapping from the set of breached metric names to a suggested band."""
    s = set(breached)
    if s & STRESS_LEVEL:
        return "Stressed"
    if s & WATCH_LEVEL:
        return "Watch"
    return "Adequate"


def _cite(p: dict, as_of: str) -> str:
    return f"pos:{p.get('source_ref', '?')}@{as_of}"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    scn = {**DEFAULT_SCENARIO, **(doc.get("scenario") or {})}
    as_of = str(doc["as_of"])
    nav = _num(doc.get("nav"))
    positions = doc["positions"]

    part = cfg["participation_rate"]
    adv_factor = scn["adv_haircut"]           # <1.0 shrinks tradable ADV under stress
    spread_mult = scn["spread_multiple"]      # >1.0 widens spreads under stress
    notice_days = scn["redemption_notice_days"]
    max_h = cfg["max_horizon_days"]

    # ---- per-position liquidation profile (participation-of-ADV model) ----
    def daily_capacity(p):
        return _num(p.get("adv_value")) * part * adv_factor

    def liquidatable_within(days):
        total = 0.0
        for p in positions:
            cap = daily_capacity(p) * days
            total += min(_num(p.get("market_value")), cap)
        return total

    def days_to_liquidate(p):
        cap = daily_capacity(p)
        if cap <= 0:
            return float("inf")
        return _num(p.get("market_value")) / cap

    buckets = {str(d): round(liquidatable_within(d), 2) for d in cfg["horizon_buckets_days"]}
    horizons = [(p, days_to_liquidate(p)) for p in positions]
    full_liq_days = max((d for _, d in horizons), default=0.0)

    # ---- liquidation cost (bps + currency), MV-weighted ----
    cost_ccy = 0.0
    per_pos_cost = []
    for p in positions:
        mv = _num(p.get("market_value"))
        cost_bps = _num(p.get("spread_bps")) * cfg["spread_cost_weight"] * spread_mult \
            + cfg["impact_coeff_bps"] * part
        per_pos_cost.append((p, cost_bps))
        cost_ccy += mv * cost_bps / 10000.0
    port_cost_bps = round((cost_ccy / nav * 10000.0) if nav else 0.0, 2)

    # ---- redemption coverage ----
    redemption_demand = round(nav * scn["redemption_pct"], 2)
    available_at_notice = round(liquidatable_within(notice_days), 2)
    coverage_ratio = round((available_at_notice / redemption_demand), 4) if redemption_demand > 0 else None

    # ---- collateral / margin buffer ----
    coll = doc.get("collateral") or {}
    margin_positions = coll.get("margin_positions") or []
    buffer = _num(coll.get("buffer"))
    additional_margin = round(sum(_num(m.get("notional")) * scn["price_shock"] for m in margin_positions), 2)
    buffer_coverage = round((buffer / additional_margin), 4) if additional_margin > 0 else None

    # ---- illiquid concentration ----
    liq_at_illiquid_bucket = liquidatable_within(cfg["illiquid_bucket_days"])
    illiquid_frac = round(((nav - liq_at_illiquid_bucket) / nav), 4) if nav else 0.0

    metrics = []
    not_evaluable = []

    def add(metric, breached, value, threshold, reason, evidence, basis):
        metrics.append({"metric": metric, "breached": bool(breached), "value": value,
                        "threshold": threshold, "reason": reason,
                        "evidence": evidence, "basis": basis})

    # redemption coverage (shortfall vs thin) -- only evaluable if a redemption is modeled
    if coverage_ratio is None:
        not_evaluable.append({"metric": "redemption_coverage", "why": "scenario redemption_pct is 0"})
    else:
        liq_src = sorted(positions, key=lambda p: daily_capacity(p), reverse=True)
        cover_ev = [{"position_id": p["position_id"], "liquidatable_at_notice":
                     round(min(_num(p.get("market_value")), daily_capacity(p) * notice_days), 2),
                     "citation": _cite(p, as_of)} for p in liq_src[:3]]
        shortfall = coverage_ratio < 1.0
        thin = (not shortfall) and coverage_ratio < cfg["coverage_watch_multiple"]
        add("redemption_coverage_shortfall", shortfall, coverage_ratio, 1.0,
            f"available at notice {available_at_notice:.2f} vs redemption demand {redemption_demand:.2f} "
            f"= coverage {coverage_ratio}" + (" (< 1.0)" if shortfall else " (>= 1.0)"),
            cover_ev if shortfall else [],
            {"available_at_notice": available_at_notice, "redemption_demand": redemption_demand,
             "notice_days": notice_days})
        add("redemption_coverage_thin", thin, coverage_ratio, cfg["coverage_watch_multiple"],
            f"coverage {coverage_ratio} within [1.0, {cfg['coverage_watch_multiple']}) buffer band"
            if thin else f"coverage {coverage_ratio} not in thin band",
            cover_ev if thin else [],
            {"available_at_notice": available_at_notice, "redemption_demand": redemption_demand})

    # full-liquidation horizon
    long_pos = [(p, d) for p, d in horizons if d > max_h]
    add("full_liquidation_horizon_exceeded", bool(long_pos),
        (None if full_liq_days == float("inf") else round(full_liq_days, 2)), max_h,
        f"{len(long_pos)} position(s) exceed the {max_h}-day full-liquidation horizon"
        if long_pos else f"full liquidation within {max_h} days",
        [{"position_id": p["position_id"],
          "days_to_liquidate": (None if d == float("inf") else round(d, 2)),
          "citation": _cite(p, as_of)} for p, d in long_pos],
        {"max_horizon_days": max_h, "participation_rate": part, "adv_haircut": adv_factor})

    # collateral buffer
    if additional_margin <= 0:
        not_evaluable.append({"metric": "collateral_buffer_shortfall", "why": "no margin positions / price_shock 0"})
    else:
        short = buffer_coverage < 1.0
        add("collateral_buffer_shortfall", short, buffer_coverage, 1.0,
            f"liquidity buffer {buffer:.2f} vs additional margin {additional_margin:.2f} "
            f"= coverage {buffer_coverage}" + (" (< 1.0)" if short else " (>= 1.0)"),
            [{"position_id": m.get("position_id"), "notional": _num(m.get("notional")),
              "citation": f"pos:{m.get('source_ref', '?')}@{as_of}"} for m in margin_positions] if short else [],
            {"buffer": buffer, "additional_margin": additional_margin, "price_shock": scn["price_shock"]})

    # liquidation cost
    cost_elev = port_cost_bps > cfg["cost_watch_bps"]
    top_cost = sorted(per_pos_cost, key=lambda pc: pc[1], reverse=True)[:3]
    add("liquidation_cost_elevated", cost_elev, port_cost_bps, cfg["cost_watch_bps"],
        f"portfolio liquidation cost {port_cost_bps} bps vs watch {cfg['cost_watch_bps']} bps",
        [{"position_id": p["position_id"], "cost_bps": round(c, 2), "citation": _cite(p, as_of)}
         for p, c in top_cost] if cost_elev else [],
        {"cost_ccy": round(cost_ccy, 2), "spread_multiple": spread_mult})

    # illiquid concentration
    illiquid_pos = [(p, d) for p, d in horizons if d > cfg["illiquid_bucket_days"]]
    illiquid_breach = illiquid_frac > cfg["illiquid_nav_watch_frac"]
    add("illiquid_concentration", illiquid_breach, illiquid_frac, cfg["illiquid_nav_watch_frac"],
        f"{illiquid_frac:.4f} of NAV not liquidatable within {cfg['illiquid_bucket_days']} days "
        f"(watch {cfg['illiquid_nav_watch_frac']})",
        [{"position_id": p["position_id"],
          "days_to_liquidate": (None if d == float("inf") else round(d, 2)),
          "citation": _cite(p, as_of)} for p, d in illiquid_pos] if illiquid_breach else [],
        {"liquidatable_by_bucket": round(liq_at_illiquid_bucket, 2), "bucket_days": cfg["illiquid_bucket_days"]})

    breached = [m["metric"] for m in metrics if m["breached"]]
    band = band_for(breached)

    caveats = []
    if breached:
        caveats = [
            "ADV and spread inputs are point-in-time estimates; realized liquidity may differ",
            "the participation-of-ADV model assumes orderly trading and ignores second-order price impact",
            "redemptions and market stress may be correlated across positions and investors",
            "scenario parameters are assumptions, not forecasts; vary them before drawing conclusions",
            "netting, credit lines, and lines of last resort outside the modeled buffer are not counted",
        ]

    return {
        "analysis_id": f"lsa-{str(doc['portfolio_id']).replace('/', '-')}-{as_of}-0001",
        "portfolio_id": doc["portfolio_id"],
        "as_of": as_of,
        "config_version": doc.get("config_version"),
        "base_currency": doc.get("base_currency"),
        "scenario_name": scn.get("name"),
        "inputs_summary": {"nav": nav, "redemption_demand": redemption_demand,
                           "notice_days": notice_days, "participation_rate": part},
        "liquidity_profile": {
            "liquidatable_by_bucket": buckets,
            "pct_liquidatable_by_bucket": {k: (round(v / nav, 4) if nav else None) for k, v in buckets.items()},
            "full_liquidation_days": (None if full_liq_days == float("inf") else round(full_liq_days, 2)),
            "portfolio_cost_bps": port_cost_bps,
        },
        "metrics": metrics,
        "breached_metrics": breached,
        "not_evaluable": not_evaluable,
        "suggested_band": band,
        "scenario_assumptions": {
            "name": scn.get("name"), "adv_haircut": scn["adv_haircut"],
            "spread_multiple": scn["spread_multiple"], "price_shock": scn["price_shock"],
            "redemption_pct": scn["redemption_pct"], "redemption_notice_days": notice_days,
            "participation_rate": part,
        },
        "caveats": caveats,
        "disclaimer": DISCLAIMER,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "portfolio_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    out = compute(doc)
    print(json.dumps(out, indent=2))
    errors = []
    if out["suggested_band"] != "Stressed":
        errors.append(f"expected band Stressed, got {out['suggested_band']!r}")
    for name in ("redemption_coverage_shortfall", "full_liquidation_horizon_exceeded",
                 "collateral_buffer_shortfall"):
        if name not in out["breached_metrics"]:
            errors.append(f"expected {name} breached")
    if band_for(out["breached_metrics"]) != out["suggested_band"]:
        errors.append("band mapping not deterministic vs breached_metrics")
    for m in out["metrics"]:
        if m["breached"] and not m["evidence"]:
            errors.append(f"breached metric {m['metric']} has no evidence")
    for e in errors:
        print("ERROR", e)
    print(f"compute self-check: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
