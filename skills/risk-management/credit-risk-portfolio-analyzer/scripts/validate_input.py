#!/usr/bin/env python3
"""Deterministic input validation for credit-risk-portfolio-analyzer.

Validates a portfolio file before analytics. Fails closed on structural problems; warns on
data-quality gaps that limit which metrics/exceptions are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  portfolio_id, as_of (YYYY-MM-DD), config_version, currency,
  exposures[{exposure_id, obligor_id, segment, sector, geography, rating, prior_rating,
             ead, pd, lgd, collateral_value, days_past_due, vintage, source_ref}],
  limits{single_name_max_pct, sector_max_pct, geography_max_pct, delinquency_90plus_max_pct,
         max_ltv, el_budget_pct, downgrade_rate_max, scenario_el_max_pct},
  scenario{name, pd_multiplier, lgd_multiplier}

Usage:
  python validate_input.py portfolio.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("portfolio_id", "as_of", "config_version", "exposures", "limits")
REQUIRED_EXP = ("exposure_id", "ead", "pd", "lgd", "days_past_due", "source_ref")
LIMIT_KEYS = ("single_name_max_pct", "sector_max_pct", "geography_max_pct",
              "delinquency_90plus_max_pct", "max_ltv", "el_budget_pct")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if not isinstance(doc, dict):
        return ["top-level JSON must be an object"], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    exps = doc.get("exposures")
    if not isinstance(exps, list) or not exps:
        errors.append("exposures must be a non-empty list")
        return errors, warnings

    ids = set()
    n_obligor = n_sector = n_geo = n_prior = n_collat = 0
    for i, e in enumerate(exps):
        tag = f"exposures[{i}] ({e.get('exposure_id', '?')})"
        for k in REQUIRED_EXP:
            if k not in e or e[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        ead = _num(e.get("ead"))
        if ead is None or ead <= 0:
            errors.append(f"{tag}: ead must be a positive number")
        for prob in ("pd", "lgd"):
            v = _num(e.get(prob))
            if v is None:
                errors.append(f"{tag}: {prob} not numeric")
            elif not (0.0 <= v <= 1.0):
                errors.append(f"{tag}: {prob} must be within [0,1], got {e.get(prob)!r}")
        dpd = _num(e.get("days_past_due"))
        if dpd is None or dpd < 0:
            errors.append(f"{tag}: days_past_due must be a non-negative number")
        eid = e.get("exposure_id")
        if eid in ids:
            errors.append(f"{tag}: duplicate exposure_id")
        ids.add(eid)
        n_obligor += 1 if e.get("obligor_id") else 0
        n_sector += 1 if e.get("sector") else 0
        n_geo += 1 if e.get("geography") else 0
        n_prior += 1 if e.get("prior_rating") else 0
        n_collat += 1 if _num(e.get("collateral_value")) else 0

    limits = doc.get("limits") or {}
    if not isinstance(limits, dict):
        errors.append("limits must be an object")
    else:
        for k in LIMIT_KEYS:
            if k not in limits:
                warnings.append(f"limits missing '{k}' — the packaged default will be used")
            elif _num(limits.get(k)) is None:
                errors.append(f"limits['{k}'] must be numeric")

    if len(exps) < 10:
        warnings.append(f"thin portfolio ({len(exps)} exposures) — metrics are low-confidence")
    if n_obligor < len(exps):
        warnings.append("some exposures have no obligor_id — single-name concentration not fully evaluable")
    if n_sector == 0:
        warnings.append("no exposure has a sector — sector concentration not evaluable")
    if n_geo == 0:
        warnings.append("no exposure has a geography — geographic concentration not evaluable")
    if n_prior == 0:
        warnings.append("no exposure has prior_rating — rating migration not evaluable")
    if n_collat == 0:
        warnings.append("no exposure has collateral_value — LTV not evaluable; all treated unsecured")
    if not doc.get("scenario"):
        warnings.append("no 'scenario' block — scenario impact not evaluable")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "portfolio_example.json"
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
