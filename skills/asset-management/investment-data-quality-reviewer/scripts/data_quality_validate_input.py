#!/usr/bin/env python3
"""Deterministic input validation for investment-data-quality-reviewer.

Validates a feed snapshot before the data-quality checks run. Fails closed on structural
problems; warns on evaluability gaps that limit which checks a row can support (never blocks
on a gap that is itself a legitimate finding, e.g. a dangling reference).

Input schema (JSON): see references/data_quality-source-map.md. Key fields:
  portfolio_id, as_of (YYYY-MM-DD), config_version, config{...},
  instruments[{instrument_key, asset_class, held, nav_impacting, identifiers{}, required_factors[], source_ref}],
  prices[{instrument_key, price, prev_price, price_asof, ...}],
  factors[{instrument_key, factor, value}],
  classifications[{instrument_key, scheme, value, feed}],
  mappings[{instrument_key, target, resolved}]

Usage:
  python validate_input.py snapshot.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("portfolio_id", "as_of", "config_version", "instruments")
REQUIRED_INST = ("instrument_key", "asset_class", "source_ref")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _validate_shape(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    insts = doc.get("instruments") or []
    if not isinstance(insts, list) or not insts:
        errors.append("instruments must be a non-empty list")
        return errors, warnings

    keys = set()
    for i, inst in enumerate(insts):
        tag = f"instruments[{i}] ({inst.get('instrument_key','?')})"
        for k in REQUIRED_INST:
            if k not in inst or inst[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        ikey = inst.get("instrument_key")
        if ikey in keys:
            errors.append(f"{tag}: duplicate instrument_key (keys must be unique; "
                          "identity collisions are detected as duplicate_instrument, not here)")
        keys.add(ikey)
        if not (inst.get("identifiers") or {}):
            warnings.append(f"{tag}: no identifiers — duplicate_instrument not evaluable for this row")
        if "held" not in inst:
            warnings.append(f"{tag}: no 'held' flag — treated as not held for absent_factor")
        if "nav_impacting" not in inst:
            warnings.append(f"{tag}: no 'nav_impacting' flag — no severity escalation for this row")

    prices = doc.get("prices") or []
    for i, p in enumerate(prices):
        tag = f"prices[{i}] ({p.get('instrument_key','?')})"
        if not p.get("instrument_key"):
            errors.append(f"{tag}: missing 'instrument_key'")
        if _num(p.get("price")) is None:
            errors.append(f"{tag}: price not numeric")
        if not p.get("price_asof"):
            warnings.append(f"{tag}: no price_asof — stale_price not evaluable (not assumed fresh)")
        if _num(p.get("prev_price")) is None:
            warnings.append(f"{tag}: no numeric prev_price — implausible_move not evaluable")

    for label in ("factors", "classifications", "mappings"):
        for i, r in enumerate(doc.get(label) or []):
            if not r.get("instrument_key"):
                errors.append(f"{label}[{i}]: missing 'instrument_key'")

    # dangling references are a legitimate broken_mapping finding, not an input error
    referenced = set()
    for label in ("prices", "factors", "classifications", "mappings"):
        for r in doc.get(label) or []:
            if r.get("instrument_key"):
                referenced.add(r["instrument_key"])
    dangling = sorted(referenced - keys)
    if dangling:
        warnings.append(f"{len(dangling)} referenced key(s) not in instruments "
                        f"(will surface as broken_mapping): {', '.join(dangling)}")

    if not prices:
        warnings.append("no 'prices' — stale_price and implausible_move cannot run")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")

    return errors, warnings


def validate(doc):
    from native_integrity import canonical_hash
    errors, warnings = [], []
    try:
        canonical_hash(doc)
        errors, warnings = _validate_shape(doc)
        if not errors:
            from data_quality_calculate_or_transform import compute
            compute(doc)
    except (ValueError, TypeError, KeyError, ArithmeticError, AttributeError) as exc:
        errors.append("unsupported or invalid native input: " + str(exc))
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "feed_snapshot.json"
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
