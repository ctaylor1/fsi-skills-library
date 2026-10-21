#!/usr/bin/env python3
"""Deterministic input validation for portfolio-exposure-analyzer.

Validates a portfolio holdings file before exposure computation. Fails closed on structural
problems; warns on data-quality gaps that limit which exposure dimensions are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  portfolio_id, as_of (YYYY-MM-DD), base_currency, config_version,
  limits{single_issuer_max_pct, sector_max_pct, country_max_pct, non_base_currency_max_pct,
         illiquid_max_pct, illiquid_horizon_days, duration_target, duration_tolerance,
         home_country, issuer_sector_exempt_asset_classes[]},
  positions[{position_id, instrument_id, asset_class, market_value, issuer, sector, country,
             currency, modified_duration, liquidity_days, factors{...},
             look_through[{issuer,sector,country,currency,weight}], source_ref}]

Positions carry market_value already converted to base_currency (the market-data service
performs FX conversion upstream; see references/source-map.md).

Usage:
  python validate_input.py portfolio.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("portfolio_id", "as_of", "base_currency", "config_version", "positions", "nav", "nav_source_ref")
REQUIRED_POS = ("position_id", "instrument_id", "asset_class", "market_value", "source_ref")
FI_CLASSES = ("corp_bond", "govt_bond")


def _num(v):
    try:
        import math
        if isinstance(v, bool): return None
        number = float(v)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _validate_legacy(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    if _num(doc.get("nav")) is None or _num(doc.get("nav")) <= 0:
        errors.append("authoritative nav must be positive")
    positions = doc.get("positions") or []
    if not isinstance(positions, list) or not positions:
        errors.append("positions must be a non-empty list")
        return errors, warnings

    ids = set()
    nav = 0.0
    any_factors = False
    for i, p in enumerate(positions):
        tag = f"positions[{i}] ({p.get('position_id','?')})"
        for k in REQUIRED_POS:
            if k not in p or p[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        mv = _num(p.get("market_value"))
        if mv is None:
            errors.append(f"{tag}: market_value not numeric")
        else:
            if mv < 0: errors.append(f"{tag}: short/signed holdings unsupported by this bounded exposure method")
            nav += mv
        pid = p.get("position_id")
        if pid in ids:
            errors.append(f"{tag}: duplicate position_id")
        ids.add(pid)

        ac = p.get("asset_class")
        lt = p.get("look_through")
        if lt:
            if not isinstance(lt, list) or not lt:
                errors.append(f"{tag}: look_through must be a non-empty list when present")
            else:
                wsum = 0.0
                for j, c in enumerate(lt):
                    w = _num(c.get("weight"))
                    if w is None:
                        errors.append(f"{tag}: look_through[{j}] weight not numeric")
                    else:
                        if w < 0: errors.append(f"{tag}: negative constituent weight")
                        wsum += w
                    if c.get("look_through"): errors.append(f"{tag}: nested look-through unsupported")
                    if not c.get("issuer"):
                        warnings.append(f"{tag}: look_through[{j}] missing issuer — issuer look-through incomplete")
                if wsum > 1.0 + 1e-10: errors.append(f"{tag}: constituent weights exceed one")
                if abs(wsum - 1.0) > 0.01:
                    warnings.append(f"{tag}: look_through weights sum to {wsum:.3f} (expected ~1.0)")
        else:
            # dimension coverage warnings (only for positions without look-through)
            exempt = ac in (doc.get("limits", {}) or {}).get("issuer_sector_exempt_asset_classes", ["govt_bond", "cash"])
            if not p.get("issuer") and not exempt:
                warnings.append(f"{tag}: no issuer — issuer exposure not evaluable for this row")
            if not p.get("sector") and not exempt:
                warnings.append(f"{tag}: no sector — sector exposure not evaluable for this row")
            if not p.get("country"):
                warnings.append(f"{tag}: no country — country exposure not evaluable for this row")
            if not p.get("currency"):
                warnings.append(f"{tag}: no currency — currency exposure not evaluable for this row")
        if p.get("liquidity_days") is not None and (_num(p["liquidity_days"]) is None or _num(p["liquidity_days"]) < 0): errors.append(f"{tag}: invalid liquidity_days")
        if p.get("liquidity_days") is None:
            warnings.append(f"{tag}: no liquidity_days — liquidity horizon not evaluable for this row")
        if ac in FI_CLASSES and _num(p.get("modified_duration")) is None:
            warnings.append(f"{tag}: fixed-income row missing modified_duration — duration not evaluable for this row")
        if p.get("factors"):
            any_factors = True

    if nav <= 0:
        errors.append(f"portfolio NAV (sum of market_value) must be > 0, got {nav}")
    if not any_factors:
        warnings.append("no position carries factor loadings — factor exposure not evaluable (requires factor-model service)")
    if not doc.get("limits"):
        warnings.append("no 'limits' block — default limits will be used; record the config_version")
    return errors, warnings


def validate(doc: dict):
    """Validate finite source data and real ISO dates before package-specific checks."""
    import math
    from datetime import datetime
    errors = []
    def walk(value, path="input", key=""):
        if isinstance(value, str) and value.strip().lower() in {"nan", "inf", "infinity", "-inf", "+inf", "-infinity", "+infinity"}:
            errors.append(f"{path}: non-finite numeric string")
        if isinstance(value, float) and not math.isfinite(value):
            errors.append(f"{path}: non-finite number")
        if isinstance(value, dict):
            for k, v in value.items(): walk(v, f"{path}.{k}", k)
        elif isinstance(value, list):
            for i, v in enumerate(value): walk(v, f"{path}[{i}]", key)
        elif value not in (None, "") and (key in {"as_of", "prior_as_of", "date", "valuation_date", "run_date", "forecast_start", "effective_date", "holdings_as_of", "prices_as_of", "bucket_dates", "effective_from", "effective_to"}):
            try: datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError: errors.append(f"{path}: invalid ISO date/timestamp")
    if not isinstance(doc, dict): return ["input must be an object"], []
    walk(doc)
    if errors: return errors, []
    try:
        native_errors, warnings = _validate_legacy(doc)
        return native_errors, warnings
    except (TypeError, ValueError, KeyError, AttributeError, OverflowError) as exc:
        return [f"malformed input: {exc}"], []


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
