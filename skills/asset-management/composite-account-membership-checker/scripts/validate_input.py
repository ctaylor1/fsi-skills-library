#!/usr/bin/env python3
"""Deterministic input validation for composite-account-membership-checker.

Validates an account/composite dataset before the membership-rule engine runs. Fails closed
on structural problems (missing identifiers, malformed dates, unresolved composite
references); warns on data-quality gaps that limit which membership rules are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  firm_id, as_of (YYYY-MM-DD), ruleset_version, ruleset_effective_date,
  composites[{composite_id, strategy, min_asset_value, inclusion_lag_months,
              requires_discretionary, significant_cash_flow_pct, rule_id, rule_version,
              effective_date}],
  portfolios[{portfolio_id, strategy, discretionary, fee_paying, under_mgmt_date,
              termination_date, market_value, assigned_composite_ids[],
              significant_cash_flow_pct, source_ref}]

Usage:
  python validate_input.py membership_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("firm_id", "as_of", "ruleset_version", "composites", "portfolios")
REQUIRED_COMPOSITE = ("composite_id", "strategy", "rule_id", "rule_version", "effective_date")
REQUIRED_PORTFOLIO = ("portfolio_id", "strategy", "discretionary", "market_value",
                      "under_mgmt_date", "assigned_composite_ids", "source_ref")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _is_date(v) -> bool:
    return bool(DATE_RE.match(str(v)))


def validate(doc: dict) -> tuple[list, list]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not _is_date(doc["as_of"]):
        errors.append(f"as_of must be YYYY-MM-DD, got {doc['as_of']!r}")
    if not doc.get("ruleset_effective_date"):
        warnings.append("no ruleset_effective_date — rule freshness/effective-date cannot be tied out")

    composites = doc.get("composites") or []
    if not isinstance(composites, list) or not composites:
        errors.append("composites must be a non-empty list")
        return errors, warnings

    comp_ids = set()
    for i, c in enumerate(composites):
        tag = f"composites[{i}] ({c.get('composite_id', '?')})"
        for k in REQUIRED_COMPOSITE:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if c.get("effective_date") and not _is_date(c["effective_date"]):
            errors.append(f"{tag}: effective_date must be YYYY-MM-DD")
        cid = c.get("composite_id")
        if cid in comp_ids:
            errors.append(f"{tag}: duplicate composite_id")
        comp_ids.add(cid)
        if _num(c.get("min_asset_value")) is None:
            warnings.append(f"{tag}: no min_asset_value — minimum-asset rule not enforced (treated as 0)")
        if c.get("inclusion_lag_months") is None:
            warnings.append(f"{tag}: no inclusion_lag_months — inclusion-timing rule not enforced (treated as 0)")

    portfolios = doc.get("portfolios") or []
    if not isinstance(portfolios, list) or not portfolios:
        errors.append("portfolios must be a non-empty list")
        return errors, warnings

    pids = set()
    for i, p in enumerate(portfolios):
        tag = f"portfolios[{i}] ({p.get('portfolio_id', '?')})"
        for k in REQUIRED_PORTFOLIO:
            if k not in p or p[k] in (None, ""):
                # assigned_composite_ids may legitimately be an empty list
                if k == "assigned_composite_ids" and isinstance(p.get(k), list):
                    continue
                errors.append(f"{tag}: missing '{k}'")
        if _num(p.get("market_value")) is None:
            errors.append(f"{tag}: market_value not numeric")
        if p.get("under_mgmt_date") and not _is_date(p["under_mgmt_date"]):
            errors.append(f"{tag}: under_mgmt_date must be YYYY-MM-DD")
        if p.get("termination_date") and not _is_date(p["termination_date"]):
            errors.append(f"{tag}: termination_date must be YYYY-MM-DD")
        pid = p.get("portfolio_id")
        if pid in pids:
            errors.append(f"{tag}: duplicate portfolio_id")
        pids.add(pid)
        for cid in (p.get("assigned_composite_ids") or []):
            if cid not in comp_ids:
                warnings.append(f"{tag}: assigned to unknown composite {cid!r} — will be flagged as an exception")
        if "fee_paying" not in p:
            warnings.append(f"{tag}: no fee_paying flag — completeness (unassigned-discretionary) check limited")
        if p.get("significant_cash_flow_pct") is None:
            warnings.append(f"{tag}: no significant_cash_flow_pct — SCF policy not evaluable for this portfolio")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "membership_input.json"
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
