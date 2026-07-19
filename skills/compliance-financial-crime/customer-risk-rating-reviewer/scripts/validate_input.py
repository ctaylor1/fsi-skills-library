#!/usr/bin/env python3
"""Deterministic input validation for customer-risk-rating-reviewer.

Validates a risk-rating case file before recomputation. Fails closed on structural
problems; warns on data-quality gaps that make the recomputation low-confidence or a factor
non-evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  customer_id, as_of (YYYY-MM-DD), methodology_version,
  rating_of_record{band, effective_date, source_ref},
  factors[{factor, value, risk_value, weight, scale_max, observed_date, source_ref}],
  overrides[{from_band, to_band, rationale, approver_role, approved_date, expiry_date, source_ref}],
  trigger_events[{type, date, severity, assessed, source_ref}], config{...}

Usage:
  python validate_input.py risk_case.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from datetime import datetime
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("customer_id", "as_of", "methodology_version", "rating_of_record", "factors")
REQUIRED_FACTOR = ("factor", "risk_value", "weight", "source_ref")
BANDS = {"Low", "Medium", "High", "Prohibited"}
# Methodology-required factors (mirrors calculate_or_transform DEFAULT_CONFIG required set).
REQUIRED_FACTORS = {"customer_type", "geography", "product_channel", "pep_status", "sanctions_nexus"}
STALENESS_DAYS = 365


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except ValueError:
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
    as_of = _parse_date(doc["as_of"])

    rec = doc.get("rating_of_record") or {}
    if not isinstance(rec, dict) or not rec.get("band"):
        errors.append("rating_of_record must include a 'band'")
    elif rec["band"] not in BANDS:
        errors.append(f"rating_of_record.band {rec['band']!r} not in {sorted(BANDS)}")
    if isinstance(rec, dict) and not rec.get("source_ref"):
        warnings.append("rating_of_record has no source_ref — the discrepancy finding cannot cite the record")

    factors = doc.get("factors") or []
    if not isinstance(factors, list) or not factors:
        errors.append("factors must be a non-empty list")
        return errors, warnings

    seen = set()
    for i, f in enumerate(factors):
        tag = f"factors[{i}] ({f.get('factor','?')})"
        for k in REQUIRED_FACTOR:
            if k not in f or f[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(f.get("risk_value")) is None:
            errors.append(f"{tag}: risk_value not numeric")
        if _num(f.get("weight")) is None:
            errors.append(f"{tag}: weight not numeric")
        name = f.get("factor")
        if name in seen:
            errors.append(f"{tag}: duplicate factor name")
        seen.add(name)
        od = f.get("observed_date")
        if not od:
            warnings.append(f"{tag}: no observed_date — staleness not evaluable for this factor")
        elif as_of and _parse_date(od) and (as_of - _parse_date(od)).days > STALENESS_DAYS:
            warnings.append(f"{tag}: observed {od} is older than {STALENESS_DAYS}d — factor is stale (data-quality finding)")

    missing_required = REQUIRED_FACTORS - seen
    for name in sorted(missing_required):
        warnings.append(f"required factor '{name}' absent — recomputation will be low-confidence (missing_required_factor)")

    for i, ov in enumerate(doc.get("overrides") or []):
        tag = f"overrides[{i}]"
        if not str(ov.get("approver_role") or "").strip():
            warnings.append(f"{tag}: no approver_role — will surface as undocumented_override")
        if not str(ov.get("rationale") or "").strip():
            warnings.append(f"{tag}: no rationale — will surface as undocumented_override")
        if not ov.get("expiry_date"):
            warnings.append(f"{tag}: no expiry_date — override validity window cannot be checked")
        if not ov.get("source_ref"):
            warnings.append(f"{tag}: no source_ref — override finding cannot cite a record")

    for i, ev in enumerate(doc.get("trigger_events") or []):
        tag = f"trigger_events[{i}] ({ev.get('type','?')})"
        if not ev.get("date"):
            warnings.append(f"{tag}: no date")
        if not ev.get("severity"):
            warnings.append(f"{tag}: no severity — trigger cannot be prioritised")
        if not ev.get("source_ref"):
            warnings.append(f"{tag}: no source_ref — trigger finding cannot cite a record")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "risk_case_example.json"
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
