#!/usr/bin/env python3
"""Deterministic implementation-shortfall TCA for transaction-cost-estimator.

Computes half-spread, commission, square-root market impact (with an uncertainty band),
delay, realized, and opportunity cost in bps and currency, signed by side, from a versioned
methodology. Never routes/executes/amends; estimates cost only.

Usage: python calculate_or_transform.py order.json | --selftest
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path

DEFAULT_M = {"spread_bps": 2.0, "commission_bps": 1.0, "impact_coef": 0.1,
             "impact_uncertainty_pct": 25.0}
DISCLAIMER = ("Estimated transaction cost for review only; not execution, venue, broker, or "
              "best-execution advice. No order has been routed, executed, or amended.")


def _num(v, d=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def compute(doc: dict) -> dict:
    o = doc["order"]
    m = {**DEFAULT_M, **(doc.get("methodology") or {})}
    s = 1.0 if o.get("side") == "buy" else -1.0
    arr = _num(o.get("arrival_price"))
    exec_qty = _num(o.get("exec_qty"), 0.0)
    order_qty = _num(o.get("order_qty"), exec_qty)
    notional = exec_qty * arr
    not_evaluable = []

    comp = {}

    def bps_ccy(bps):
        return {"bps": round(bps, 4), "ccy": round(bps / 10000.0 * notional, 2)}

    comp["half_spread"] = bps_ccy(_num(m.get("spread_bps"), 0.0) / 2.0)
    comp["commission"] = bps_ccy(_num(m.get("commission_bps"), 0.0))

    adv = _num(o.get("adv"))
    vol = _num(o.get("volatility"))
    impact_bps = None
    if adv and adv > 0 and vol is not None:
        impact_bps = _num(m.get("impact_coef"), 0.0) * vol * math.sqrt(exec_qty / adv) * 10000.0
        comp["market_impact"] = bps_ccy(impact_bps)
    else:
        not_evaluable.append("market_impact (missing adv/volatility)")
        comp["market_impact"] = {"bps": 0.0, "ccy": 0.0, "not_evaluable": True}

    dp = _num(o.get("decision_price"))
    comp["delay"] = bps_ccy(s * (arr - dp) / arr * 10000.0 if dp is not None else 0.0)

    ep = _num(o.get("exec_price"))
    comp["realized"] = bps_ccy(s * (ep - arr) / arr * 10000.0 if ep is not None else 0.0)

    cp = _num(o.get("close_price"))
    unfilled = max(order_qty - exec_qty, 0.0)
    if cp is not None and order_qty > 0:
        comp["opportunity"] = bps_ccy(s * (unfilled / order_qty) * (cp - arr) / arr * 10000.0)
    else:
        comp["opportunity"] = bps_ccy(0.0)

    total_bps = round(sum(c["bps"] for c in comp.values()), 4)
    total_ccy = round(sum(c["ccy"] for c in comp.values()), 2)

    # uncertainty band on market impact -> total range
    unc = _num(m.get("impact_uncertainty_pct"), 25.0) / 100.0
    band = abs(impact_bps) * unc if impact_bps is not None else 0.0
    total_bps_range = [round(total_bps - band, 4), round(total_bps + band, 4)]
    total_ccy_range = [round((total_bps - band) / 10000.0 * notional, 2),
                       round((total_bps + band) / 10000.0 * notional, 2)]

    return {
        "tca_id": f"tca-{o.get('order_id','UNKNOWN')}-0001",
        "order_id": o.get("order_id"), "methodology_version": m.get("version"),
        "side": o.get("side"), "exec_qty": exec_qty, "notional": round(notional, 2),
        "components": comp,
        "total_bps": total_bps, "total_ccy": total_ccy,
        "total_bps_range": total_bps_range, "total_ccy_range": total_ccy_range,
        "not_evaluable": not_evaluable,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "order_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
