#!/usr/bin/env python3
"""Deterministic input validation for valuation-reviewer.

Validates a valuation record before the review checks run. Fails closed on structural
problems; warns on data-quality gaps that limit which checks are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  instrument_id, as_of (YYYY-MM-DD), config_version, asset_class, method (market|income|cost),
  fair_value_level (1|2|3), reported_value, currency,
  inputs[{name,value,observability(observable|unobservable),source_ref,source_date}],
  comparables[], adjustments[{type,amount,rationale,source_ref,approver}],
  ipv{performed,independent_value,variance_pct,tolerance_pct,rationale,source_ref,source_date},
  overrides[{ref,from_value,to_value,rationale,approver,source_ref}],
  uncertainty_range{low,high}, config{...thresholds...}

Usage:
  python validate_input.py valuation.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("instrument_id", "as_of", "config_version", "method", "fair_value_level",
                "reported_value", "currency", "inputs")
METHODS = {"market", "income", "cost"}
LEVELS = {"1", "2", "3"}
OBSERVABILITY = {"observable", "unobservable"}


def _num(v):
    try:
        return float(str(v).replace(",", "").replace("%", "").replace("bps", "").strip())
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

    method = str(doc["method"]).strip().lower()
    if method not in METHODS:
        errors.append(f"method must be one of {sorted(METHODS)}, got {doc['method']!r}")

    level = str(doc["fair_value_level"]).strip()
    if level not in LEVELS:
        errors.append(f"fair_value_level must be 1, 2, or 3, got {doc['fair_value_level']!r}")

    if _num(doc.get("reported_value")) is None:
        errors.append("reported_value not numeric")

    inputs = doc.get("inputs") or []
    if not isinstance(inputs, list) or not inputs:
        errors.append("inputs must be a non-empty list")
        return errors, warnings

    names = set()
    for i, inp in enumerate(inputs):
        tag = f"inputs[{i}] ({inp.get('name','?')})"
        if not inp.get("name"):
            errors.append(f"{tag}: missing 'name'")
        if "value" not in inp or inp.get("value") in (None, ""):
            errors.append(f"{tag}: missing 'value'")
        obs = str(inp.get("observability", "")).lower()
        if obs not in OBSERVABILITY:
            errors.append(f"{tag}: observability must be 'observable' or 'unobservable'")
        nm = inp.get("name")
        if nm in names:
            warnings.append(f"{tag}: duplicate input name")
        names.add(nm)
        if not (inp.get("source_ref") or "").strip():
            warnings.append(f"{tag}: no source_ref — input_source_missing will fire (untraceable)")
        if not inp.get("source_date"):
            warnings.append(f"{tag}: no source_date — input_staleness not evaluable for this row")

    if method == "market" and not (doc.get("comparables") or []):
        warnings.append("market approach but no comparables — comparable_sufficiency will fire")
    if level in {"2", "3"} and not (doc.get("ipv") or {}).get("performed"):
        warnings.append(f"Level {level} but no performed IPV block — ipv_missing will fire")
    if level == "3" and not doc.get("uncertainty_range"):
        warnings.append("Level 3 but no uncertainty_range — uncertainty_missing will fire")
    for j, a in enumerate(doc.get("adjustments") or []):
        if not (a.get("rationale") or "").strip() or not (a.get("source_ref") or "").strip():
            warnings.append(f"adjustments[{j}] ({a.get('type','?')}): missing rationale/source — will be flagged")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "valuation_example.json"
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
