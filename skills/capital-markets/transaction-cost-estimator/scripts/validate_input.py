#!/usr/bin/env python3
"""Deterministic input validation for transaction-cost-estimator.

Input schema (JSON): order{order_id,security,side,order_qty,exec_qty,arrival_price,
decision_price,exec_price,close_price,adv,volatility}; methodology{version,spread_bps,
commission_bps,impact_coef,impact_uncertainty_pct}.

Usage: python validate_input.py order.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQ_ORDER = ("order_id", "side", "exec_qty", "arrival_price")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    o = doc.get("order")
    if not o:
        return ["missing 'order'"], warnings
    for k in REQ_ORDER:
        if o.get(k) in (None, ""):
            errors.append(f"order missing '{k}'")
    if o.get("side") not in ("buy", "sell"):
        errors.append("order.side must be 'buy' or 'sell'")
    if _num(o.get("arrival_price")) in (None, 0.0):
        errors.append("order.arrival_price must be a non-zero number")
    if _num(o.get("exec_qty")) is None:
        errors.append("order.exec_qty not numeric")
    if _num(o.get("adv")) in (None, 0.0):
        warnings.append("order.adv missing/zero — market_impact not evaluable")
    if _num(o.get("volatility")) is None:
        warnings.append("order.volatility missing — market_impact not evaluable")
    if o.get("decision_price") in (None, ""):
        warnings.append("no decision_price — delay component treated as 0")
    if not (doc.get("methodology") or {}).get("version"):
        warnings.append("methodology.version missing — record the versioned TCA methodology")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "order_example.json"
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
