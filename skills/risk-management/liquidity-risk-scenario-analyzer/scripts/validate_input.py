#!/usr/bin/env python3
"""Deterministic input validation for liquidity-risk-scenario-analyzer.

Validates a liquidity position + scenarios file before stress computation. Fails closed on
structural problems; warns on data-quality gaps that limit the reliability of the analysis.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  entity_id, as_of (YYYY-MM-DD), currency, config_version, reporting_horizon_days,
  buckets[{bucket,end_day}], limits{min_survival_days,min_coverage_ratio,concentration_limit_pct?},
  counterbalancing[{asset_id,asset_class,market_value,base_haircut,source_ref}],
  positions[{item_id,direction,category,bucket,amount,source_ref}],
  scenarios[{scenario_id,name,outflow_rates{},inflow_rates{},default_outflow_rate,
             default_inflow_rate,cb_haircut_addon{}}]

Usage:
  python validate_input.py position.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("entity_id", "as_of", "config_version", "reporting_horizon_days",
                "buckets", "limits", "counterbalancing", "positions", "scenarios")
REQUIRED_ITEM = ("item_id", "direction", "category", "bucket", "amount", "source_ref")
REQUIRED_CB = ("asset_id", "asset_class", "market_value", "base_haircut", "source_ref")
REQUIRED_LIMITS = ("min_survival_days", "min_coverage_ratio")


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
    if _num(doc.get("reporting_horizon_days")) is None:
        errors.append("reporting_horizon_days must be numeric")

    # buckets
    buckets = doc.get("buckets") or []
    if not isinstance(buckets, list) or not buckets:
        errors.append("buckets must be a non-empty list")
        return errors, warnings
    bucket_names, end_days = set(), []
    for i, b in enumerate(buckets):
        if not b.get("bucket"):
            errors.append(f"buckets[{i}]: missing 'bucket'")
        if _num(b.get("end_day")) is None:
            errors.append(f"buckets[{i}] ({b.get('bucket','?')}): end_day must be numeric")
        else:
            end_days.append(_num(b["end_day"]))
        bucket_names.add(b.get("bucket"))
    if end_days != sorted(end_days):
        warnings.append("buckets are not in ascending end_day order — they will be sorted before computation")

    # limits
    limits = doc.get("limits") or {}
    for k in REQUIRED_LIMITS:
        if _num(limits.get(k)) is None:
            errors.append(f"limits.{k} must be numeric")

    # counterbalancing
    cb = doc.get("counterbalancing") or []
    if not isinstance(cb, list) or not cb:
        errors.append("counterbalancing must be a non-empty list")
    for i, a in enumerate(cb):
        tag = f"counterbalancing[{i}] ({a.get('asset_id','?')})"
        for k in REQUIRED_CB:
            if k not in a or a[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(a.get("market_value")) is None:
            errors.append(f"{tag}: market_value not numeric")
        bh = _num(a.get("base_haircut"))
        if bh is None:
            errors.append(f"{tag}: base_haircut not numeric")
        elif not (0.0 <= bh <= 1.0):
            errors.append(f"{tag}: base_haircut {bh} outside [0,1]")

    # positions
    items = doc.get("positions") or []
    if not isinstance(items, list) or not items:
        errors.append("positions must be a non-empty list")
        return errors, warnings
    ids, categories = set(), set()
    for i, t in enumerate(items):
        tag = f"positions[{i}] ({t.get('item_id','?')})"
        for k in REQUIRED_ITEM:
            if k not in t or t[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(t.get("amount")) is None:
            errors.append(f"{tag}: amount not numeric")
        elif _num(t.get("amount")) < 0:
            errors.append(f"{tag}: amount must be non-negative (direction encodes sign)")
        if t.get("direction") not in ("inflow", "outflow"):
            errors.append(f"{tag}: direction must be 'inflow' or 'outflow'")
        if t.get("bucket") not in bucket_names:
            errors.append(f"{tag}: bucket {t.get('bucket')!r} not declared in buckets[]")
        if t.get("item_id") in ids:
            errors.append(f"{tag}: duplicate item_id")
        ids.add(t.get("item_id"))
        if t.get("category"):
            categories.add(t.get("category"))

    # scenarios
    scenarios = doc.get("scenarios") or []
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("scenarios must be a non-empty list")
        return errors, warnings
    for i, s in enumerate(scenarios):
        tag = f"scenarios[{i}] ({s.get('scenario_id','?')})"
        if not s.get("scenario_id"):
            errors.append(f"{tag}: missing 'scenario_id'")
        for rk, dk in (("outflow_rates", "default_outflow_rate"), ("inflow_rates", "default_inflow_rate")):
            if rk not in s and dk not in s:
                errors.append(f"{tag}: needs '{rk}' or '{dk}'")
        covered = set((s.get("outflow_rates") or {}).keys()) | set((s.get("inflow_rates") or {}).keys())
        uncovered = sorted(categories - covered)
        if uncovered and ("default_outflow_rate" not in s or "default_inflow_rate" not in s):
            warnings.append(f"{tag}: categories {uncovered} rely on defaults; confirm default rates are intended")

    if len(scenarios) < 2:
        warnings.append("only one scenario supplied — a liquidity review normally spans idiosyncratic, "
                        "market-wide, and combined stresses")
    if not doc.get("config") and not doc.get("config_version"):
        warnings.append("no inline 'config' block and no config_version — record the config version so the analysis is reproducible")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "position_example.json"
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
