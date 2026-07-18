#!/usr/bin/env python3
"""Deterministic input validation for fixed-income-pricing-reviewer.

Validates a pricing-review file before the checks run. Fails closed on structural problems;
warns on data-quality gaps that limit which checks are evaluable for an instrument.

Input schema (JSON): see references/source-map.md. Key fields:
  as_of (YYYY-MM-DD), config_version, focal_instrument_ids[],
  instruments[{instrument_id, identifier, asset_class, liquidity_bucket, submitted_price,
    prior_price, independent_price, prior_independent_price, quoted_bid, quoted_ask,
    applied_liquidity_adj_bps, yield_pct, benchmark_yield_pct, assigned_fv_level,
    input_observability, price_source_ts, last_price_change_date, comparables[], source_ref}],
  config{...thresholds...}

Usage:
  python validate_input.py review.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("as_of", "config_version", "focal_instrument_ids", "instruments")
REQUIRED_INSTR = ("instrument_id", "submitted_price", "source_ref")
VALID_LEVELS = {"L1", "L2", "L3"}
VALID_OBS = {"observable", "partially_observable", "unobservable"}


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

    instruments = doc.get("instruments") or []
    if not isinstance(instruments, list) or not instruments:
        errors.append("instruments must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, inst in enumerate(instruments):
        tag = f"instruments[{i}] ({inst.get('instrument_id', '?')})"
        for k in REQUIRED_INSTR:
            if k not in inst or inst[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(inst.get("submitted_price")) is None:
            errors.append(f"{tag}: submitted_price not numeric")
        iid = inst.get("instrument_id")
        if iid in ids:
            errors.append(f"{tag}: duplicate instrument_id")
        ids.add(iid)

        lvl = inst.get("assigned_fv_level")
        if lvl is not None and lvl not in VALID_LEVELS:
            errors.append(f"{tag}: assigned_fv_level {lvl!r} not one of {sorted(VALID_LEVELS)}")
        obs = inst.get("input_observability")
        if obs is not None and obs not in VALID_OBS:
            errors.append(f"{tag}: input_observability {obs!r} not one of {sorted(VALID_OBS)}")

        # evaluability warnings (do not fail; each limits a specific check)
        if _num(inst.get("independent_price")) is None:
            warnings.append(f"{tag}: no independent_price — mark_vs_independent not evaluable")
        if _num(inst.get("prior_price")) is None or _num(inst.get("prior_independent_price")) is None:
            warnings.append(f"{tag}: missing prior_price/prior_independent_price — price_movement not evaluable")
        if not (inst.get("comparables")):
            warnings.append(f"{tag}: no comparables — spread_to_comparables not evaluable")
        elif _num(inst.get("yield_pct")) is None or _num(inst.get("benchmark_yield_pct")) is None:
            warnings.append(f"{tag}: missing yield_pct/benchmark_yield_pct — spread_to_comparables not evaluable")
        if _num(inst.get("applied_liquidity_adj_bps")) is None or not inst.get("liquidity_bucket"):
            warnings.append(f"{tag}: missing applied_liquidity_adj_bps/liquidity_bucket — liquidity_adj not evaluable")
        if not lvl or not obs:
            warnings.append(f"{tag}: missing assigned_fv_level/input_observability — fair_value_level check not evaluable")
        if not inst.get("last_price_change_date") and not inst.get("price_source_ts"):
            warnings.append(f"{tag}: no last_price_change_date/price_source_ts — stale_price not evaluable")

    for fid in doc["focal_instrument_ids"]:
        if fid not in ids:
            errors.append(f"focal_instrument_ids references unknown instrument_id {fid!r}")

    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "review_example.json"
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
