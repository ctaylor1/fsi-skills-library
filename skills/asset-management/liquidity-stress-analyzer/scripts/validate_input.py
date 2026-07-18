#!/usr/bin/env python3
"""Deterministic input validation for liquidity-stress-analyzer.

Validates a portfolio + scenario file before liquidity computation. Fails closed on
structural problems; warns on data-quality gaps that limit which metrics are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  portfolio_id, as_of (YYYY-MM-DD), config_version, base_currency, nav,
  scenario{name, adv_haircut, spread_multiple, price_shock, redemption_pct, redemption_notice_days},
  collateral{buffer, margin_positions[{position_id, notional, source_ref}]},
  positions[{position_id, instrument, asset_class, market_value, adv_value, spread_bps, source_ref}],
  config{...thresholds...}

Usage:
  python validate_input.py portfolio.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("portfolio_id", "as_of", "config_version", "nav", "scenario", "positions")
REQUIRED_POS = ("position_id", "market_value", "adv_value", "source_ref")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list, list]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if _num(doc.get("nav")) is None or _num(doc.get("nav")) <= 0:
        errors.append("nav must be a positive number")

    scn = doc.get("scenario")
    if not isinstance(scn, dict):
        errors.append("scenario must be an object with transparent assumptions")
        scn = {}
    else:
        for key in ("adv_haircut", "spread_multiple", "price_shock", "redemption_pct",
                    "redemption_notice_days"):
            if key not in scn:
                warnings.append(f"scenario missing '{key}' — baseline default will be used; record the assumption")
        if _num(scn.get("adv_haircut", 1.0)) == 0:
            warnings.append("scenario adv_haircut is 0 — no liquidity assumed; horizons will be infinite")

    positions = doc.get("positions")
    if not isinstance(positions, list) or not positions:
        errors.append("positions must be a non-empty list")
        return errors, warnings

    ids = set()
    mv_total = 0.0
    for i, p in enumerate(positions):
        tag = f"positions[{i}] ({p.get('position_id', '?')})"
        for k in REQUIRED_POS:
            if k not in p or p[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        mv = _num(p.get("market_value"))
        adv = _num(p.get("adv_value"))
        if mv is None:
            errors.append(f"{tag}: market_value not numeric")
        else:
            mv_total += mv
        if adv is None:
            errors.append(f"{tag}: adv_value not numeric")
        elif adv <= 0:
            warnings.append(f"{tag}: adv_value <= 0 — treated as beyond max horizon (illiquid)")
        if p.get("spread_bps") is not None and _num(p.get("spread_bps")) is None:
            errors.append(f"{tag}: spread_bps present but not numeric")
        elif p.get("spread_bps") is None:
            warnings.append(f"{tag}: no spread_bps — liquidation-cost contribution uses impact only")
        pid = p.get("position_id")
        if pid in ids:
            errors.append(f"{tag}: duplicate position_id")
        ids.add(pid)

    nav = _num(doc.get("nav")) or 0.0
    if nav and abs(mv_total - nav) / nav > 0.05:
        warnings.append(f"sum of position market_value ({mv_total:.0f}) differs from nav ({nav:.0f}) by >5% "
                        "— unmodeled cash/other; coverage percentages are relative to nav")

    coll = doc.get("collateral") or {}
    for j, m in enumerate(coll.get("margin_positions") or []):
        mtag = f"collateral.margin_positions[{j}] ({m.get('position_id', '?')})"
        if _num(m.get("notional")) is None:
            errors.append(f"{mtag}: notional not numeric")
        if not m.get("source_ref"):
            errors.append(f"{mtag}: missing source_ref")
    if not coll.get("margin_positions"):
        warnings.append("no collateral.margin_positions — collateral_buffer_shortfall not evaluable")

    if _num((doc.get("scenario") or {}).get("redemption_pct", 0)) in (None, 0.0):
        warnings.append("scenario redemption_pct is 0 or missing — redemption coverage not evaluable")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "portfolio_example.json"
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
