#!/usr/bin/env python3
"""Deterministic input validation for covenant-compliance-monitor.

Validates a monitoring-run file before the covenant engine evaluates it. Fails closed on
structural problems; warns on data-quality gaps that limit which covenants are evaluable or
that disable freshness / reconciliation / deduplication for this run.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  run_id, as_of (YYYY-MM-DD), config_version, max_staleness_days,
  open_alerts[{fingerprint}],                       # previously-open alerts, for dedup
  facilities[{facility_id, borrower_id, agreement_id, test_period, spread_as_of,
              spread{line_items{<metric>: number}}, prior_spread{line_items{}},   # optional
              compliance_certificate{received_date, reported{<covenant_id>: number}},
              covenants[{covenant_id, type, ...}]}]
  covenant type = financial   -> direction(max|min), threshold, cushion, unit,
                                 formula{numerator[], numerator_less[], denominator[]}
                  negative    -> direction(max|min), threshold, cushion, unit, line_item
                  reporting   -> deliverable, due_date, received_date, grace_days

Usage:
  python validate_input.py run.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("run_id", "as_of", "config_version", "facilities")
REQUIRED_FACILITY = ("facility_id", "borrower_id", "spread")
COVENANT_TYPES = {"financial", "negative", "reporting"}
DIRECTIONS = {"max", "min"}


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

    if "max_staleness_days" not in doc:
        warnings.append("no 'max_staleness_days' — spread freshness is not evaluable this run; tests may be based on stale financials")
    if "open_alerts" not in doc:
        warnings.append("no 'open_alerts' baseline — deduplication is disabled; every exception will be reported as new")

    facilities = doc.get("facilities") or []
    if not isinstance(facilities, list) or not facilities:
        errors.append("facilities must be a non-empty list")
        return errors, warnings

    fids = set()
    for i, f in enumerate(facilities):
        tag = f"facilities[{i}] ({f.get('facility_id','?')})"
        for k in REQUIRED_FACILITY:
            if k not in f or f[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        fid = f.get("facility_id")
        if fid in fids:
            errors.append(f"{tag}: duplicate facility_id")
        fids.add(fid)

        spread = f.get("spread") or {}
        line_items = spread.get("line_items") if isinstance(spread, dict) else None
        if not isinstance(line_items, dict) or not line_items:
            warnings.append(f"{tag}: spread has no line_items — financial / negative covenants not evaluable")
            line_items = {}
        if not f.get("spread_as_of"):
            warnings.append(f"{tag}: no spread_as_of — freshness not evaluable for this facility")
        if not f.get("compliance_certificate"):
            warnings.append(f"{tag}: no compliance_certificate — certificate reconciliation not evaluable")

        covenants = f.get("covenants") or []
        if not isinstance(covenants, list) or not covenants:
            errors.append(f"{tag}: covenants must be a non-empty list")
            continue
        cids = set()
        for j, cov in enumerate(covenants):
            ctag = f"{tag}.covenants[{j}] ({cov.get('covenant_id','?')})"
            cid = cov.get("covenant_id")
            if not cid:
                errors.append(f"{ctag}: missing covenant_id")
            if cid in cids:
                errors.append(f"{ctag}: duplicate covenant_id within facility")
            cids.add(cid)
            ctype = cov.get("type")
            if ctype not in COVENANT_TYPES:
                errors.append(f"{ctag}: type must be one of {sorted(COVENANT_TYPES)}, got {ctype!r}")
                continue

            if ctype == "financial":
                if cov.get("direction") not in DIRECTIONS:
                    errors.append(f"{ctag}: financial covenant needs direction in {sorted(DIRECTIONS)}")
                if _num(cov.get("threshold")) is None:
                    errors.append(f"{ctag}: financial covenant needs numeric threshold")
                formula = cov.get("formula") or {}
                numer = formula.get("numerator")
                if not isinstance(numer, list) or not numer:
                    errors.append(f"{ctag}: financial covenant needs formula.numerator (non-empty list)")
                    continue
                keys = list(numer) + list(formula.get("numerator_less") or []) + list(formula.get("denominator") or [])
                for key in keys:
                    if key not in line_items:
                        warnings.append(f"{ctag}: line item {key!r} missing from spread — covenant not evaluable this run")
                        break
            elif ctype == "negative":
                if not cov.get("line_item"):
                    errors.append(f"{ctag}: negative covenant needs line_item")
                elif cov.get("line_item") not in line_items:
                    warnings.append(f"{ctag}: line item {cov.get('line_item')!r} missing from spread — covenant not evaluable this run")
                if _num(cov.get("threshold")) is None:
                    errors.append(f"{ctag}: negative covenant needs numeric threshold")
                if cov.get("direction") and cov.get("direction") not in DIRECTIONS:
                    errors.append(f"{ctag}: negative covenant direction must be in {sorted(DIRECTIONS)}")
            elif ctype == "reporting":
                if not cov.get("deliverable"):
                    errors.append(f"{ctag}: reporting covenant needs deliverable")
                if not DATE_RE.match(str(cov.get("due_date", ""))):
                    errors.append(f"{ctag}: reporting covenant needs due_date (YYYY-MM-DD)")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
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
