#!/usr/bin/env python3
"""Deterministic input validation for portfolio-holdings-summarizer.

Validates a holdings file against the documented schema BEFORE summarizing. Fails closed
on structural problems; warns (does not fail) on data-quality gaps the summary must
surface (unpriced lines, currency mismatches, stale prices).

Input schema (JSON):
{
  "account_id": "str",
  "as_of_date": "YYYY-MM-DD",
  "base_currency": "USD",
  "positions": [
    {"instrument_id","id_type","description","quantity","price","market_value",
     "currency","asset_class"(opt),"sector"(opt),"source":{"system","ref"}}
  ]
}

Usage:
  python validate_input.py holdings.json
  python validate_input.py --selftest        # validate the bundled fixture
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("account_id", "as_of_date", "base_currency", "positions")
REQUIRED_POS = ("instrument_id", "description", "currency", "source")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of_date"])):
        errors.append(f"as_of_date must be YYYY-MM-DD, got {doc['as_of_date']!r}")

    positions = doc.get("positions") or []
    if not isinstance(positions, list) or not positions:
        errors.append("positions must be a non-empty list")
        return errors, warnings

    base_ccy = doc["base_currency"]
    as_of_dates = set()
    for i, p in enumerate(positions):
        tag = f"positions[{i}] ({p.get('instrument_id', '?')})"
        for k in REQUIRED_POS:
            if k not in p or p[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        src = p.get("source") or {}
        if not (src.get("system") and src.get("ref")):
            errors.append(f"{tag}: source must include 'system' and 'ref' (citation)")

        mv = _num(p.get("market_value"))
        qty = _num(p.get("quantity"))
        px = _num(p.get("price"))
        # price_factor handles per-100 bond quoting (0.01), contract multipliers, etc.
        factor = _num(p.get("price_factor")) or 1.0
        if mv is None:
            if qty is not None and px is not None:
                warnings.append(f"{tag}: market_value missing; derivable from quantity*price*price_factor")
            else:
                warnings.append(f"{tag}: unpriced (no market_value and no quantity*price) — report as 'not valued'")
        elif qty is not None and px is not None:
            derived = qty * px * factor
            if abs(derived - mv) > max(0.01, abs(mv) * 0.005):
                warnings.append(
                    f"{tag}: market_value {mv} != quantity*price*price_factor {derived:.2f} (>0.5%); "
                    f"set 'price_factor' (e.g. 0.01 for bonds quoted per 100) if intentional")

        if p.get("currency") and base_ccy and p["currency"] != base_ccy:
            warnings.append(f"{tag}: currency {p['currency']} != base {base_ccy} — requires cited FX to include in base total")
        if not p.get("asset_class"):
            warnings.append(f"{tag}: no asset_class — classify via reference data or exclude from allocation")
        if p.get("as_of"):
            as_of_dates.add(p["as_of"])

    if len(as_of_dates) > 1:
        errors.append(f"positions carry multiple as-of dates {sorted(as_of_dates)} — do not merge; confirm a single date")

    return errors, warnings


def _report(errors, warnings) -> int:
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "holdings_example.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
    elif len(argv) >= 1:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    return _report(*validate(doc))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
