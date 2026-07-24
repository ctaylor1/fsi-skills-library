#!/usr/bin/env python3
"""Deterministic input validation for pricing-hedging-scenario-calculator.

Input schema (JSON): trade{trade_id,instrument_type,notional,direction,position_dv01,as_of};
scenarios[{scenario_id,shock_bp}]; hedge{hedge_instrument,hedge_dv01_per_unit}.

Usage: python validate_input.py trade.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("trade", "scenarios", "hedge"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    t = doc["trade"]
    if not t.get("trade_id"):
        errors.append("trade missing 'trade_id'")
    if _num(t.get("position_dv01")) is None:
        errors.append("trade.position_dv01 not numeric (required; never assumed)")
    if t.get("direction") not in ("long", "short"):
        errors.append("trade.direction must be 'long' or 'short'")
    scen = doc.get("scenarios") or []
    if not isinstance(scen, list) or not scen:
        errors.append("scenarios must be a non-empty list")
    else:
        for i, s in enumerate(scen):
            if _num(s.get("shock_bp")) is None:
                errors.append(f"scenarios[{i}]: shock_bp not numeric")
    hdv = _num(doc["hedge"].get("hedge_dv01_per_unit"))
    if hdv is None:
        errors.append("hedge.hedge_dv01_per_unit not numeric")
    elif hdv == 0:
        warnings.append("hedge.hedge_dv01_per_unit is 0 — hedge sizing not computable")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "trade_example.json"
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
