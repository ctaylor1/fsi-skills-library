#!/usr/bin/env python3
"""Deterministic, explainable fixed-income pricing-review checks.

Reads a pricing-review file (see validate_input.py), and for each focal instrument
recomputes a set of configured, explainable *pricing-exception checks* against
independent prices, comparable spreads, prior marks, liquidity-adjustment bands, and the
assigned fair-value level. Each flagged check carries its own evidence + citation, and the
flagged set maps deterministically to a review-priority band per
references/domain-rules.md.

IMPORTANT: This produces explainable *checks and a triage suggestion* only. It never
approves, overrides, restates, or books a mark, signs off IPV, or issues a valuation
determination. The band mapping is deterministic and documented.

Usage:
  python calculate_or_transform.py review.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, statistics, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "mark_dev_bps": 30.0,            # |submitted - independent| in bps of independent price
    "spread_tol_bps": 40.0,         # |instrument spread - comparable median| in bps
    "move_bps": 50.0,               # day-over-day |submitted - prior| in bps of prior price
    "corroboration_ratio": 0.5,     # independent move must be >= ratio*submitted move to explain
    "staleness_days": 10,           # calendar days since last_price_change_date
    "source_staleness_days": 4,     # calendar days between price_source_ts and as_of
    "min_comparables": 3,           # comparables needed to form a spread median
    "max_comp_dispersion_bps": 60.0,  # comparable spread (max-min) dispersion ceiling
    "liquidity_bands": {            # plausible applied liquidity/bid-offer adj (bps) by bucket
        "liquid": [0.0, 10.0],
        "normal": [0.0, 25.0],
        "illiquid": [5.0, 60.0],
    },
}
DISCLAIMER = ("Pricing-review evidence only; not a valuation determination or price "
              "approval. No mark has been changed, approved, or booked.")
ESCALATORS = {"stale_price", "fair_value_level_inconsistent"}
BAND_RANK = {"Informational": 0, "Review": 1, "Elevated": 2}
OBS_RANK = {"observable": 3, "partially_observable": 2, "unobservable": 1}


def _parse_date(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _bps(a: float, b: float) -> float:
    """Difference a-b expressed in bps of |b|."""
    if b == 0:
        return 0.0
    return abs(a - b) / abs(b) * 10000.0


def _cite(instr: dict, as_of: str) -> str:
    return f"mark:{instr.get('source_ref', '?')}@{as_of}"


def _band(flagged: list[str]) -> str:
    if len(flagged) >= 3 or (ESCALATORS & set(flagged)):
        return "Elevated"
    return "Review" if flagged else "Informational"


def _review_instrument(instr: dict, cfg: dict, as_of: datetime, as_of_str: str) -> dict:
    checks: list[dict] = []
    not_evaluable: list[dict] = []
    cite = _cite(instr, as_of_str)

    submitted = _num(instr.get("submitted_price"))
    prior = _num(instr.get("prior_price"))
    independent = _num(instr.get("independent_price"))
    prior_independent = _num(instr.get("prior_independent_price"))

    def add(name, flagged, reason, evidence, basis, contribution):
        checks.append({"check": name, "flagged": flagged, "reason": reason,
                       "evidence": evidence, "basis": basis, "contribution": contribution})

    # 1. mark_vs_independent -------------------------------------------------
    if submitted is not None and independent is not None:
        dev = _bps(submitted, independent)
        fired = dev > cfg["mark_dev_bps"]
        add("mark_vs_independent", fired,
            (f"submitted mark {submitted} deviates from independent price {independent} "
             f"by {dev:.1f} bps (tolerance {cfg['mark_dev_bps']:.0f})") if fired else
            f"submitted mark within {cfg['mark_dev_bps']:.0f} bps of independent price ({dev:.1f})",
            [{"instrument_id": instr["instrument_id"], "submitted_price": submitted,
              "independent_price": independent, "deviation_bps": round(dev, 1),
              "citation": cite}] if fired else [],
            {"deviation_bps": round(dev, 1), "tolerance_bps": cfg["mark_dev_bps"]},
            1 if fired else 0)
    else:
        not_evaluable.append({"check": "mark_vs_independent", "why": "no independent_price"})

    # 2. spread_to_comparables + comparable_support_thin ---------------------
    comps = instr.get("comparables") or []
    comp_spreads = [_num(c.get("spread_bps")) for c in comps if _num(c.get("spread_bps")) is not None]
    yld = _num(instr.get("yield_pct"))
    bench = _num(instr.get("benchmark_yield_pct"))
    if not comps:
        not_evaluable.append({"check": "spread_to_comparables", "why": "no comparables provided"})
        not_evaluable.append({"check": "comparable_support_thin", "why": "no comparables provided"})
    else:
        dispersion = (max(comp_spreads) - min(comp_spreads)) if comp_spreads else 0.0
        thin = len(comp_spreads) < cfg["min_comparables"] or dispersion > cfg["max_comp_dispersion_bps"]
        add("comparable_support_thin", thin,
            (f"comparable set weak: {len(comp_spreads)} comps, dispersion {dispersion:.1f} bps "
             f"(min {cfg['min_comparables']}, max dispersion {cfg['max_comp_dispersion_bps']:.0f})")
            if thin else f"{len(comp_spreads)} comps, dispersion {dispersion:.1f} bps (adequate)",
            [{"instrument_id": instr["instrument_id"], "comparable_count": len(comp_spreads),
              "dispersion_bps": round(dispersion, 1), "citation": cite}] if thin else [],
            {"comparable_count": len(comp_spreads), "dispersion_bps": round(dispersion, 1)},
            1 if thin else 0)
        if len(comp_spreads) >= cfg["min_comparables"] and yld is not None and bench is not None:
            inst_spread = (yld - bench) * 100.0
            median = statistics.median(comp_spreads)
            diff = abs(inst_spread - median)
            fired = diff > cfg["spread_tol_bps"]
            add("spread_to_comparables", fired,
                (f"instrument spread {inst_spread:.1f} bps deviates from comparable median "
                 f"{median:.1f} bps by {diff:.1f} bps (tolerance {cfg['spread_tol_bps']:.0f})")
                if fired else f"instrument spread within tolerance of comparable median ({diff:.1f} bps)",
                [{"instrument_id": instr["instrument_id"], "instrument_spread_bps": round(inst_spread, 1),
                  "comparable_median_bps": round(median, 1), "citation": cite}] if fired else [],
                {"instrument_spread_bps": round(inst_spread, 1),
                 "comparable_median_bps": round(median, 1), "tolerance_bps": cfg["spread_tol_bps"]},
                1 if fired else 0)
        else:
            not_evaluable.append({"check": "spread_to_comparables",
                                  "why": "fewer than min_comparables spreads or missing yield/benchmark"})

    # 3. price_movement_unexplained ------------------------------------------
    if submitted is not None and prior is not None and prior_independent is not None and independent is not None:
        sub_move = _bps(submitted, prior)
        ind_move = _bps(independent, prior_independent)
        fired = sub_move > cfg["move_bps"] and ind_move < cfg["corroboration_ratio"] * sub_move
        add("price_movement_unexplained", fired,
            (f"submitted mark moved {sub_move:.1f} bps day-over-day while independent price moved only "
             f"{ind_move:.1f} bps (below {cfg['corroboration_ratio']:.0%} corroboration)")
            if fired else f"day-over-day move {sub_move:.1f} bps (independent moved {ind_move:.1f} bps)",
            [{"instrument_id": instr["instrument_id"], "prior_price": prior, "submitted_price": submitted,
              "submitted_move_bps": round(sub_move, 1), "independent_move_bps": round(ind_move, 1),
              "citation": cite}] if fired else [],
            {"submitted_move_bps": round(sub_move, 1), "independent_move_bps": round(ind_move, 1),
             "move_tolerance_bps": cfg["move_bps"]}, 1 if fired else 0)
    else:
        not_evaluable.append({"check": "price_movement_unexplained",
                              "why": "missing prior_price, prior_independent_price, or independent_price"})

    # 4. stale_price (escalator) ---------------------------------------------
    lpc = instr.get("last_price_change_date")
    pts = instr.get("price_source_ts")
    if lpc or pts:
        reasons = []
        change_gap = source_gap = None
        if lpc:
            change_gap = (as_of - _parse_date(lpc)).days
            if change_gap >= cfg["staleness_days"]:
                reasons.append(f"mark unchanged {change_gap}d (>= {cfg['staleness_days']})")
        if pts:
            source_gap = (as_of - _parse_date(pts)).days
            if source_gap >= cfg["source_staleness_days"]:
                reasons.append(f"price source {source_gap}d old (>= {cfg['source_staleness_days']})")
        fired = bool(reasons)
        add("stale_price", fired,
            "; ".join(reasons) if fired else
            f"price fresh (change gap {change_gap}d, source gap {source_gap}d)",
            [{"instrument_id": instr["instrument_id"], "last_price_change_date": lpc,
              "price_source_ts": pts, "citation": cite}] if fired else [],
            {"change_gap_days": change_gap, "source_gap_days": source_gap,
             "staleness_days": cfg["staleness_days"], "source_staleness_days": cfg["source_staleness_days"]},
            1 if fired else 0)
    else:
        not_evaluable.append({"check": "stale_price", "why": "no last_price_change_date or price_source_ts"})

    # 5. liquidity_adj_plausibility ------------------------------------------
    adj = _num(instr.get("applied_liquidity_adj_bps"))
    bucket = instr.get("liquidity_bucket")
    band = cfg["liquidity_bands"].get(str(bucket)) if bucket else None
    if adj is not None and band:
        lo, hi = band
        fired = adj < lo or adj > hi
        bid = _num(instr.get("quoted_bid"))
        ask = _num(instr.get("quoted_ask"))
        half_spread_bps = None
        if bid is not None and ask is not None and (bid + ask):
            half_spread_bps = round((ask - bid) / 2.0 / ((ask + bid) / 2.0) * 10000.0, 1)
        add("liquidity_adj_plausibility", fired,
            (f"applied liquidity adj {adj} bps outside {bucket} band [{lo:.0f}, {hi:.0f}]")
            if fired else f"applied liquidity adj {adj} bps within {bucket} band [{lo:.0f}, {hi:.0f}]",
            [{"instrument_id": instr["instrument_id"], "applied_liquidity_adj_bps": adj,
              "bucket": bucket, "band": [lo, hi], "quoted_half_spread_bps": half_spread_bps,
              "citation": cite}] if fired else [],
            {"applied_bps": adj, "band": [lo, hi], "quoted_half_spread_bps": half_spread_bps},
            1 if fired else 0)
    else:
        not_evaluable.append({"check": "liquidity_adj_plausibility",
                              "why": "missing applied_liquidity_adj_bps or unknown liquidity_bucket"})

    # 6. fair_value_level_inconsistent (escalator) ---------------------------
    level = instr.get("assigned_fv_level")
    obs = instr.get("input_observability")
    if level and obs and obs in OBS_RANK:
        expected = None
        if level == "L1" and obs != "observable":
            expected, fired = "L2/L3", True
        elif level == "L2" and obs == "unobservable":
            expected, fired = "L3", True
        elif level == "L3" and obs == "observable":
            expected, fired = "L1/L2", True
        else:
            fired = False
        add("fair_value_level_inconsistent", fired,
            (f"assigned level {level} inconsistent with {obs} inputs (expected {expected})")
            if fired else f"assigned level {level} consistent with {obs} inputs",
            [{"instrument_id": instr["instrument_id"], "assigned_fv_level": level,
              "input_observability": obs, "expected_level": expected, "citation": cite}] if fired else [],
            {"assigned_fv_level": level, "input_observability": obs, "expected_level": expected},
            1 if fired else 0)
    else:
        not_evaluable.append({"check": "fair_value_level_inconsistent",
                              "why": "missing assigned_fv_level or input_observability"})

    flagged = [c["check"] for c in checks if c["flagged"]]
    return {
        "instrument_id": instr["instrument_id"],
        "identifier": instr.get("identifier"),
        "asset_class": instr.get("asset_class"),
        "liquidity_bucket": instr.get("liquidity_bucket"),
        "checks": checks,
        "flagged_checks": flagged,
        "not_evaluable": not_evaluable,
        "suggested_priority": _band(flagged),
    }


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    # merge liquidity_bands if partially overridden
    cfg["liquidity_bands"] = {**DEFAULT_CONFIG["liquidity_bands"],
                              **((doc.get("config") or {}).get("liquidity_bands") or {})}
    as_of_str = str(doc["as_of"])[:10]
    as_of = _parse_date(as_of_str)
    by_id = {i["instrument_id"]: i for i in doc["instruments"]}
    focal_ids = doc.get("focal_instrument_ids") or list(by_id.keys())

    instruments = [_review_instrument(by_id[fid], cfg, as_of, as_of_str)
                   for fid in focal_ids if fid in by_id]

    overall = "Informational"
    for ir in instruments:
        if BAND_RANK[ir["suggested_priority"]] > BAND_RANK[overall]:
            overall = ir["suggested_priority"]

    any_flagged = any(ir["flagged_checks"] for ir in instruments)
    benign = []
    if any_flagged:
        benign = [
            "a genuine idiosyncratic move (issuer news, rating action, coupon/call event)",
            "a benchmark or curve shift the comparable set has not yet reflected",
            "an approved, documented liquidity or model reserve for a thinly traded line",
            "a stale vendor feed rather than a stale trader mark (verify source timestamps)",
            "a legitimate fair-value level given documented input observability",
        ]

    return {
        "review_id": f"fipr-{as_of_str}-0001",
        "as_of": as_of_str,
        "config_version": doc.get("config_version"),
        "focal_instrument_ids": focal_ids,
        "instruments": instruments,
        "overall_suggested_priority": overall,
        "benign_prompts": benign,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "review_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
