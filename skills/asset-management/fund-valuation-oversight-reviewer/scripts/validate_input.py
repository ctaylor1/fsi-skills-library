#!/usr/bin/env python3
"""Deterministic input validation for fund-valuation-oversight-reviewer.

Validates a fund-book pricing file before exception investigation. Fails closed on structural
problems; warns on data gaps that force a `needs-data` or `missing` disposition downstream.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  config_version, as_of (YYYY-MM-DD), book, asset_class_tolerances{} (optional overrides),
  instruments[
    {instrument_id, asset_class, prior_price?, prior_price_date?, market_value?,
     benchmark_return_pct?, open_challenge?,
     candidate_prices?[{source_id, source_type, price, as_of, firm?, size?}],
     source_ref}]

Usage: python validate_input.py prices.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("config_version", "as_of", "instruments")
REQUIRED_INSTRUMENT = ("instrument_id", "source_ref")
KNOWN_SOURCE_TYPES = {
    "exchange_close", "vendor_evaluated", "executable_quote", "trade_print",
    "indicative_quote", "matrix_price", "model_price", "carry_forward",
}
REQUIRED_PRICE = ("source_id", "source_type", "price", "as_of")


def _is_isodate(s) -> bool:
    try:
        date.fromisoformat(str(s)[:10])
        return True
    except (ValueError, TypeError):
        return False


def _validate_shape(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not _is_isodate(doc.get("as_of")):
        errors.append(f"as_of is not an ISO date: {doc.get('as_of')!r}")
    if not str(doc.get("config_version") or "").strip():
        errors.append("config_version is empty (tolerance config must be a versioned contract)")

    instruments = doc.get("instruments") or []
    if not isinstance(instruments, list) or not instruments:
        errors.append("instruments must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, ins in enumerate(instruments):
        tag = f"instruments[{i}] ({ins.get('instrument_id','?')})"
        for k in REQUIRED_INSTRUMENT:
            if k not in ins or ins[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        iid = ins.get("instrument_id")
        if iid in ids:
            errors.append(f"{tag}: duplicate instrument_id")
        ids.add(iid)

        if not ins.get("asset_class"):
            warnings.append(f"{tag}: no asset_class -> needs-data (cannot select tolerances)")

        prices = ins.get("candidate_prices")
        if prices is None or (isinstance(prices, list) and not prices):
            warnings.append(f"{tag}: no candidate_prices -> possible 'missing' exception")
        elif not isinstance(prices, list):
            errors.append(f"{tag}: candidate_prices must be a list")
        else:
            for j, p in enumerate(prices):
                ptag = f"{tag}.candidate_prices[{j}]"
                for k in REQUIRED_PRICE:
                    if k not in p or p[k] in (None, ""):
                        errors.append(f"{ptag}: missing '{k}'")
                if "price" in p and not isinstance(p.get("price"), (int, float)):
                    errors.append(f"{ptag}: price must be a number, got {p.get('price')!r}")
                if "as_of" in p and not _is_isodate(p.get("as_of")):
                    errors.append(f"{ptag}: as_of is not an ISO date: {p.get('as_of')!r}")
                st = p.get("source_type")
                if st and st not in KNOWN_SOURCE_TYPES:
                    warnings.append(f"{ptag}: unknown source_type {st!r} (not in the pricing hierarchy)")

        if ins.get("prior_price") is not None and not isinstance(ins["prior_price"], (int, float)):
            errors.append(f"{tag}: prior_price must be a number, got {ins['prior_price']!r}")
        if ins.get("prior_price") is None:
            warnings.append(f"{tag}: no prior_price -> outlier (day-over-day) check limited")
    return errors, warnings


def validate(doc):
    from native_integrity import canonical_hash
    errors, warnings = [], []
    try:
        canonical_hash(doc)
        errors, warnings = _validate_shape(doc)
        if not errors:
            from calculate_or_transform import compute
            compute(doc)
    except (ValueError, TypeError, KeyError, ArithmeticError, AttributeError) as exc:
        errors.append("unsupported or invalid native input: " + str(exc))
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "prices_example.json"
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
    print(f"input validation: {len(warnings)} warning(s), {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
