#!/usr/bin/env python3
"""Validate structure, finite values and explicit financial comparison bases."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from insurance_contract import amount, as_of_value, iso_date


def validate(doc):
    errors, warnings = [], []
    if not isinstance(doc, dict):
        return ["input must be an object"], []
    try:
        as_of_value(doc.get("as_of"))
    except (TypeError, ValueError):
        errors.append("as_of must be a valid ISO date or timezone-aware timestamp")
    for side in ("current", "prior"):
        rows = doc.get(side, [])
        if not isinstance(rows, list) or (side == "current" and not rows):
            errors.append(f"{side} must be a {'nonempty ' if side == 'current' else ''}list")
            continue
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"{side}[{i}] must be an object")
                continue
            for field in ("key", "metric", "period", "source_ref"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    errors.append(f"{side}[{i}].{field} required")
            try:
                amount(row.get("value"))
            except ValueError:
                errors.append(f"{side}[{i}].value must be finite numeric, not boolean/unknown")
            for field in ("definition_version", "currency", "unit", "financial_basis", "date_basis", "valuation_date"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    warnings.append(f"{side}[{i}].{field} unavailable; affected comparison not evaluable")
            if row.get("valuation_date"):
                try:
                    iso_date(row["valuation_date"])
                except ValueError:
                    errors.append(f"{side}[{i}].valuation_date invalid")
            if row.get("currency") and (not isinstance(row["currency"], str) or len(row["currency"]) != 3 or not row["currency"].isupper()):
                errors.append(f"{side}[{i}].currency must be uppercase three-letter code")
            if row.get("documented_reason") is not None and not isinstance(row["documented_reason"], str):
                errors.append(f"{side}[{i}].documented_reason must be text")
    if not doc.get("prior"):
        warnings.append("prior dataset absent; movement and missing-current checks not evaluable")
    periods = doc.get("expected_periods", [])
    if not isinstance(periods, list) or not all(isinstance(v, str) and v.strip() for v in periods):
        errors.append("expected_periods must be a list of period labels")
    elif not periods:
        warnings.append("expected_periods absent; period completeness not evaluable")
    series = doc.get("expected_series", [])
    if not isinstance(series, list) or not all(isinstance(r, dict) and isinstance(r.get("key"), str) and isinstance(r.get("metric"), str) for r in series):
        errors.append("expected_series must contain key/metric objects")
    cfg = doc.get("config", {})
    if not isinstance(cfg, dict):
        errors.append("config must be an object")
    else:
        try:
            if amount(cfg.get("movement_pct", 20)) < 0:
                raise ValueError()
        except ValueError:
            errors.append("movement_pct must be finite and nonnegative")
    if not isinstance(doc.get("config_version"), str) or not doc.get("config_version"):
        warnings.append("config_version unavailable")
    return errors, warnings


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/data_example.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    errors, warnings = validate(json.loads(path.read_text() if path else sys.stdin.read()))
    for message in warnings:
        print("WARN", message)
    for message in errors:
        print("ERROR", message)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
