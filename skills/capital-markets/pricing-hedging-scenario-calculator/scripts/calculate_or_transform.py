#!/usr/bin/env python3
"""Deterministic linear scenario/hedge estimate for pricing-hedging-scenario-calculator.

Computes per-scenario illustrative P&L (linear DV01), the delta-neutral hedge units and side, and
the residual DV01 after hedging. Estimate only; never prices firmly or executes.

Usage: python calculate_or_transform.py trade.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Illustrative linear scenario analysis only; not a firm price, a quote, or an "
              "instruction to execute or hedge. Nothing has been priced or traded.")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def compute(doc: dict) -> dict:
    t = doc["trade"]
    dv01 = _num(t.get("position_dv01")) or 0.0
    direction = t.get("direction")
    sign = -1.0 if direction == "long" else 1.0

    scenarios = []
    for s in doc["scenarios"]:
        shock = _num(s.get("shock_bp"))
        pnl = round(sign * dv01 * shock, 2) if shock is not None else None
        scenarios.append({"scenario_id": s.get("scenario_id"), "shock_bp": shock,
                          "illustrative_pnl": pnl})

    hedge = doc["hedge"]
    hdv = _num(hedge.get("hedge_dv01_per_unit"))
    if hdv:
        units = round(dv01 / hdv, 4)
        residual = round(dv01 - units * hdv, 6)
        hedge_out = {"hedge_instrument": hedge.get("hedge_instrument"),
                     "hedge_dv01_per_unit": hdv, "hedge_units": units,
                     "hedge_side": "short" if direction == "long" else "long",
                     "residual_dv01": residual}
    else:
        hedge_out = {"hedge_instrument": hedge.get("hedge_instrument"),
                     "hedge_dv01_per_unit": hdv, "hedge_units": None,
                     "hedge_side": None, "residual_dv01": None,
                     "note": "hedge_dv01_per_unit is 0/missing — hedge sizing not computable"}

    return {
        "scenario_id": f"phsc-{t.get('trade_id', 'UNKNOWN')}-0001",
        "trade_id": t.get("trade_id"), "as_of": t.get("as_of"),
        "instrument_type": t.get("instrument_type"),
        "position_dv01": dv01, "direction": direction,
        "approximation": "linear_dv01_first_order",
        "scenarios": scenarios, "hedge": hedge_out,
        "citation": f"risk:trade={t.get('trade_id')};dv01@{t.get('as_of')}",
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "trade_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
