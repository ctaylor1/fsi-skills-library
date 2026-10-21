#!/usr/bin/env python3
"""Deterministic input validation for portfolio-cashflow-forecaster.

Validates a liquidity-forecast input file before the forecast is built. Fails closed on
structural problems (missing fields, non-numeric amounts, unknown categories, non-ascending or
empty bucket dates, collateral without a direction, missing scenarios); warns on data-quality
gaps that weaken the forecast or that validate_output will reject (missing provenance/citation,
cash flows dated before the forecast start or beyond the last bucket, negative multipliers).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  portfolio_id, as_of (YYYY-MM-DD), forecast_start (YYYY-MM-DD), config_version, currency, units,
  opening_cash -> {value, provenance, citation},
  bucket_dates: [YYYY-MM-DD, ...] (ascending, non-empty),
  cashflows: [{id, category, date, amount(>0), direction?, provenance, citation}],
  scenarios: {name -> {provenance, citation, category_multipliers{cat:factor},
              category_date_shift_days{cat:int}, approved_engine_net?, approved_engine_source?}}
  (a scenario named 'base' is required).

Usage:
  python validate_input.py forecast_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from datetime import date
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("portfolio_id", "as_of", "forecast_start", "config_version", "opening_cash",
                "bucket_dates", "cashflows", "scenarios")
CATEGORIES = ("subscription", "redemption", "coupon", "dividend", "maturity", "collateral",
              "funding_need")
DEFAULT_DIRECTION = {
    "subscription": "inflow", "coupon": "inflow", "dividend": "inflow", "maturity": "inflow",
    "redemption": "outflow", "funding_need": "outflow",
}


def _v(node):
    try:
        import math
        value = node.get("value") if isinstance(node, dict) else node
        if isinstance(value, bool): return None
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, AttributeError):
        return None


def _prov_cite(node):
    if isinstance(node, dict):
        return (node.get("provenance") or "").strip(), (node.get("citation") or "").strip()
    return "", ""


def _as_date(s):
    try:
        return date.fromisoformat(str(s)[:10])
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
    fstart = _as_date(doc["forecast_start"])
    if fstart is None:
        errors.append(f"forecast_start must be YYYY-MM-DD, got {doc['forecast_start']!r}")
    if _v(doc["opening_cash"]) is None:
        errors.append("opening_cash value is not numeric")
    prov, cite = _prov_cite(doc["opening_cash"])
    if not prov:
        warnings.append("opening_cash has no provenance — validate_output will reject the pack")
    if not cite:
        warnings.append("opening_cash has no citation — validate_output will reject the pack")

    # bucket_dates: non-empty, ascending, all after forecast_start
    buckets = doc.get("bucket_dates") or []
    bucket_dates = []
    if not isinstance(buckets, list) or not buckets:
        errors.append("bucket_dates must be a non-empty ascending list of YYYY-MM-DD dates")
    else:
        prev = None
        for b in buckets:
            d = _as_date(b)
            if d is None:
                errors.append(f"bucket_dates entry {b!r} is not a valid YYYY-MM-DD date")
                continue
            if prev is not None and d <= prev:
                errors.append(f"bucket_dates must be strictly ascending; {b!r} is not after the previous bucket")
            if fstart is not None and d < fstart:
                errors.append(f"bucket_dates entry {b!r} is before forecast_start {doc['forecast_start']!r}")
            bucket_dates.append(d)
            prev = d
    last_bucket = bucket_dates[-1] if bucket_dates else None

    # cashflows
    cashflows = doc.get("cashflows") or []
    if not isinstance(cashflows, list) or not cashflows:
        errors.append("cashflows must be a non-empty list")
    seen_ids = set()
    for i, item in enumerate(cashflows if isinstance(cashflows, list) else []):
        where = item.get("id", f"index {i}") if isinstance(item, dict) else f"index {i}"
        if not isinstance(item, dict):
            errors.append(f"cashflow {where} must be an object")
            continue
        if "id" not in item:
            errors.append(f"cashflow at index {i} is missing 'id'")
        elif item["id"] in seen_ids:
            errors.append(f"duplicate cashflow id {item['id']!r}")
        else:
            seen_ids.add(item["id"])
        cat = item.get("category")
        if cat not in CATEGORIES:
            errors.append(f"cashflow {where}: category {cat!r} not in {list(CATEGORIES)}")
        amt = _v(item.get("amount"))
        if amt is None:
            errors.append(f"cashflow {where}: amount is not numeric")
        elif amt <= 0:
            errors.append(f"cashflow {where}: amount must be a positive magnitude (sign comes from direction)")
        d = _as_date(item.get("date"))
        if d is None:
            errors.append(f"cashflow {where}: date {item.get('date')!r} is not a valid YYYY-MM-DD date")
        direction = item.get("direction")
        if direction is not None and direction not in ("inflow", "outflow"):
            errors.append(f"cashflow {where}: direction must be 'inflow' or 'outflow', got {direction!r}")
        if cat == "collateral" and not direction:
            errors.append(f"cashflow {where}: collateral cash flows must carry an explicit direction "
                          f"('inflow' for a return, 'outflow' to post)")
        if cat in DEFAULT_DIRECTION and direction and direction != DEFAULT_DIRECTION[cat]:
            warnings.append(f"cashflow {where}: direction {direction!r} overrides the usual "
                            f"{DEFAULT_DIRECTION[cat]!r} for a {cat} — confirm this is intended")
        p, c = _prov_cite(item)
        if not p:
            warnings.append(f"cashflow {where} has no provenance — validate_output will reject the pack")
        if not c:
            warnings.append(f"cashflow {where} has no citation — validate_output will reject the pack")
        if d is not None and fstart is not None and d < fstart:
            warnings.append(f"cashflow {where} is dated before forecast_start — it will be excluded")
        if d is not None and last_bucket is not None and d > last_bucket:
            warnings.append(f"cashflow {where} is dated after the last bucket — it will be excluded (beyond horizon)")

    # scenarios: analyst-supplied; a 'base' scenario is required
    scenarios = doc.get("scenarios") or {}
    if not isinstance(scenarios, dict) or not scenarios:
        errors.append("scenarios must be a non-empty object keyed by scenario name")
    elif "base" not in scenarios:
        errors.append("a scenario named 'base' is required (the analyst supplies every scenario)")
    for name, scen in (scenarios.items() if isinstance(scenarios, dict) else []):
        if not isinstance(scen, dict):
            errors.append(f"scenario {name!r} must be an object")
            continue
        p, c = _prov_cite(scen)
        if not p:
            warnings.append(f"scenario {name!r} has no provenance — validate_output will reject the pack")
        if not c:
            warnings.append(f"scenario {name!r} has no citation — validate_output will reject the pack")
        for cat, factor in (scen.get("category_multipliers") or {}).items():
            if cat not in CATEGORIES:
                warnings.append(f"scenario {name!r}: multiplier for unknown category {cat!r} will be ignored")
            fv = _v(factor)
            if fv is None:
                errors.append(f"scenario {name!r}: multiplier for {cat!r} is not numeric")
            elif fv < 0:
                warnings.append(f"scenario {name!r}: negative multiplier for {cat!r} ({fv}) flips the cash direction — confirm")
        for cat, days in (scen.get("category_date_shift_days") or {}).items():
            try:
                int(days)
            except (TypeError, ValueError):
                errors.append(f"scenario {name!r}: date shift for {cat!r} must be an integer number of days")
        if "approved_engine_net" in scen and _v(scen["approved_engine_net"]) is None:
            errors.append(f"scenario {name!r}: approved_engine_net is not numeric")

    for name, scenario in (doc.get("scenarios") or {}).items():
        for cat, value in (scenario.get("category_multipliers") or {}).items():
            if float(value) < 0: errors.append(f"{name}: negative multiplier unsupported")
        for cat, value in (scenario.get("category_date_shift_days") or {}).items():
            if isinstance(value, bool) or not isinstance(value, int): errors.append(f"{name}: date shifts must be integer calendar days")
    if doc.get("bucket_dates") and doc["bucket_dates"][0] < doc["forecast_start"]: errors.append("first bucket precedes forecast_start")
    if str(doc.get("forecast_start", "")) < str(doc.get("as_of", "")):
        errors.append("forecast_start precedes as_of")
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
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "forecast_input_example.json"
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
