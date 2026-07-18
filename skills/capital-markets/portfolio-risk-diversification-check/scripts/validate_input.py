#!/usr/bin/env python3
"""Deterministic input validation for portfolio-risk-diversification-check.

Validates a portfolio holdings file before metric computation. Fails closed on structural
problems; warns on data-quality gaps that limit which checks are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  portfolio_id, as_of (YYYY-MM-DD), config_version, base_currency, benchmark,
  positions[{symbol,name,asset_class,sector,region,weight,liquidity_days,
             factor_loadings{factor:value},source_ref}],
  correlation_matrix{symbols[],matrix[[...]]}, config{...thresholds...}

Usage:
  python validate_input.py portfolio.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("portfolio_id", "as_of", "config_version", "positions")
REQUIRED_POS = ("symbol", "weight", "source_ref")
DEFAULT_TOL = 0.02


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    positions = doc.get("positions") or []
    if not isinstance(positions, list) or not positions:
        errors.append("positions must be a non-empty list")
        return errors, warnings

    symbols = set()
    have_sector = have_region = have_asset = have_factor = have_liq = 0
    total_w = 0.0
    for i, p in enumerate(positions):
        tag = f"positions[{i}] ({p.get('symbol', '?')})"
        for k in REQUIRED_POS:
            if k not in p or p[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        w = _num(p.get("weight"))
        if w is None:
            errors.append(f"{tag}: weight not numeric")
        else:
            if w < 0:
                errors.append(f"{tag}: weight is negative ({w})")
            total_w += w
        sym = p.get("symbol")
        if sym in symbols:
            errors.append(f"{tag}: duplicate symbol")
        symbols.add(sym)
        if p.get("sector"):
            have_sector += 1
        if p.get("region"):
            have_region += 1
        if p.get("asset_class"):
            have_asset += 1
        if isinstance(p.get("factor_loadings"), dict) and p["factor_loadings"]:
            have_factor += 1
        if _num(p.get("liquidity_days")) is not None:
            have_liq += 1

    tol = _num((doc.get("config") or {}).get("weight_sum_tolerance")) or DEFAULT_TOL
    if total_w <= 0:
        errors.append(f"position weights sum to {total_w:.4f} (<= 0); cannot compute exposures")
    elif abs(total_w - 1.0) > tol:
        warnings.append(f"position weights sum to {total_w:.4f}, not ~1.0 (tolerance {tol}); "
                        f"confirm weights are portfolio fractions, not notional")

    # correlation matrix (optional) structural check
    cm = doc.get("correlation_matrix")
    if cm:
        syms = cm.get("symbols") or []
        matrix = cm.get("matrix") or []
        if len(matrix) != len(syms):
            errors.append("correlation_matrix: matrix row count != symbols count")
        else:
            for r, row in enumerate(matrix):
                if len(row) != len(syms):
                    errors.append(f"correlation_matrix: row {r} length != symbols count")
    else:
        warnings.append("no correlation_matrix — correlation_concentration not evaluable")

    if have_sector == 0:
        warnings.append("no position has 'sector' — sector_concentration not evaluable")
    if have_region == 0:
        warnings.append("no position has 'region' — geography_concentration not evaluable")
    if have_asset == 0:
        warnings.append("no position has 'asset_class' — asset_class_concentration not evaluable")
    if have_factor == 0:
        warnings.append("no position has 'factor_loadings' — factor_tilt not evaluable")
    if have_liq == 0:
        warnings.append("no position has 'liquidity_days' — liquidity_concentration not evaluable")
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
