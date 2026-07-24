#!/usr/bin/env python3
"""Deterministic input validation for investment-vendor-feed-reconciler.

Validates a vendor-feed reconciliation job (internal book-of-record side + one vendor feed
side) before matching. Fails closed on structural problems; warns on data-quality gaps that
limit field-level matching, staleness evaluation, or lineage.

Input schema (JSON): see references/source-map.md. Key fields:
  entity, as_of (YYYY-MM-DD), config_version, internal_source, vendor_source, currency,
  internal_observations[{instrument_id,domain,field,value,as_of,source_ref,currency,data_type}],
  vendor_observations[{...same shape...}],
  config{numeric_tolerance_abs,numeric_tolerance_pct,materiality_pct,materiality_abs,
         staleness_max_age_days}

A reconciliation "cell" is one (instrument_id, domain, field) triple. Each side must carry at
most one observation per cell (a repeated cell on the same side is ambiguous and fails closed).

Usage:
  python validate_input.py feed_reconciliation.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("entity", "as_of", "config_version", "internal_source", "vendor_source",
                "internal_observations", "vendor_observations")
REQUIRED_OBS = ("instrument_id", "domain", "field", "value", "as_of", "source_ref")
DOMAINS = {"price", "rating", "index_constituent", "corporate_action", "instrument_attribute"}
DATA_TYPES = {"numeric", "categorical"}


def _missing_value(v) -> bool:
    # A value of 0, 0.0, or False is present; only None / "" / whitespace is missing.
    if v is None:
        return True
    if isinstance(v, str) and v.strip() == "":
        return True
    return False


def _check_side(name, rows, cells, errors, warnings):
    if not isinstance(rows, list):
        errors.append(f"{name} must be a list")
        return
    for i, r in enumerate(rows):
        tag = f"{name}[{i}] ({r.get('instrument_id', '?')}/{r.get('domain', '?')}/{r.get('field', '?')})"
        if not isinstance(r, dict):
            errors.append(f"{tag}: not an object")
            continue
        for k in REQUIRED_OBS:
            if k not in r or _missing_value(r.get(k)):
                errors.append(f"{tag}: missing '{k}'")
        dom = r.get("domain")
        if dom is not None and dom not in DOMAINS:
            errors.append(f"{tag}: domain {dom!r} not in {sorted(DOMAINS)}")
        dt = r.get("data_type")
        if dt is not None and dt not in DATA_TYPES:
            errors.append(f"{tag}: data_type {dt!r} not in {sorted(DATA_TYPES)}")
        if not DATE_RE.match(str(r.get("as_of", ""))):
            errors.append(f"{tag}: as_of must start YYYY-MM-DD, got {r.get('as_of')!r}")
        key = (str(r.get("instrument_id")), str(r.get("domain")), str(r.get("field")))
        if key in cells:
            errors.append(f"{tag}: duplicate cell on the same side (one observation per "
                          f"instrument/domain/field; cannot pair deterministically)")
        cells.add(key)
        if dom == "price" and not r.get("currency"):
            warnings.append(f"{tag}: price observation has no currency - FX differences not evaluable")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    internal = doc.get("internal_observations") or []
    vendor = doc.get("vendor_observations") or []
    if not isinstance(internal, list) or not isinstance(vendor, list):
        errors.append("internal_observations and vendor_observations must both be lists")
        return errors, warnings
    if len(internal) + len(vendor) == 0:
        errors.append("no observations: internal_observations and vendor_observations are both empty")
        return errors, warnings

    _check_side("internal_observations", internal, set(), errors, warnings)
    _check_side("vendor_observations", vendor, set(), errors, warnings)

    cfg = doc.get("config") or {}
    if not cfg:
        warnings.append("no 'config' block - default tolerances/staleness will be used; record the config_version")
    for numk in ("numeric_tolerance_abs", "numeric_tolerance_pct", "materiality_pct",
                 "materiality_abs", "staleness_max_age_days"):
        if numk in cfg:
            try:
                float(cfg[numk])
            except (TypeError, ValueError):
                errors.append(f"config['{numk}'] must be numeric, got {cfg[numk]!r}")
    if not doc.get("currency"):
        warnings.append("no job-level 'currency' - record the reconciliation currency")
    if not internal:
        warnings.append("internal_observations empty - every vendor cell will classify as missing_in_internal")
    if not vendor:
        warnings.append("vendor_observations empty - every internal cell will classify as missing_in_vendor")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "feed_reconciliation_example.json"
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
