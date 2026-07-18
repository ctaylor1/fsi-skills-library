#!/usr/bin/env python3
"""Deterministic input validation for margin-collateral-optimizer.

Validates a collateral file before allocation. Fails closed on structural problems; warns on
data-quality gaps that limit which calls can be fully evaluated (e.g. an eligible asset class
with no haircut-schedule entry, or a call whose eligible inventory is thin).

Input schema (JSON): see references/source-map.md. Key fields:
  portfolio_id, as_of (YYYY-MM-DD), config_version, base_currency,
  margin_calls[{call_id, counterparty, agreement_id, call_type, required_amount, currency,
               eligible_asset_classes[], source_ref}],
  collateral_inventory[{asset_id, asset_class, market_value, available_value, currency,
                        pledge_cost_bps, source_ref}],
  haircut_schedule[{agreement_id, asset_class, haircut, eligible, source_ref}],
  config{max_asset_class_pct_per_call, coverage_tolerance}

Usage:
  python validate_input.py collateral.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("portfolio_id", "as_of", "config_version", "base_currency",
                "margin_calls", "collateral_inventory", "haircut_schedule")
REQUIRED_CALL = ("call_id", "agreement_id", "required_amount", "currency",
                 "eligible_asset_classes", "source_ref")
REQUIRED_ASSET = ("asset_id", "asset_class", "market_value", "pledge_cost_bps", "source_ref")
REQUIRED_HC = ("agreement_id", "asset_class", "haircut", "eligible", "source_ref")


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

    calls = doc.get("margin_calls") or []
    if not isinstance(calls, list) or not calls:
        errors.append("margin_calls must be a non-empty list")
    assets = doc.get("collateral_inventory") or []
    if not isinstance(assets, list) or not assets:
        errors.append("collateral_inventory must be a non-empty list")
    schedule = doc.get("haircut_schedule") or []
    if not isinstance(schedule, list) or not schedule:
        errors.append("haircut_schedule must be a non-empty list")
    if errors:
        return errors, warnings

    # haircut schedule structure + lookup
    hc = {}
    for i, row in enumerate(schedule):
        tag = f"haircut_schedule[{i}]"
        for k in REQUIRED_HC:
            if k not in row or row[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        h = _num(row.get("haircut"))
        if h is None or not (0.0 <= h <= 1.0):
            errors.append(f"{tag}: haircut must be a fraction in [0,1], got {row.get('haircut')!r}")
        if not isinstance(row.get("eligible"), bool):
            errors.append(f"{tag}: eligible must be true/false")
        hc[(row.get("agreement_id"), row.get("asset_class"))] = row

    # calls
    call_ids = set()
    for i, c in enumerate(calls):
        tag = f"margin_calls[{i}] ({c.get('call_id','?')})"
        for k in REQUIRED_CALL:
            if k not in c or c[k] in (None, "", []):
                errors.append(f"{tag}: missing '{k}'")
        if _num(c.get("required_amount")) is None or (_num(c.get("required_amount")) or 0) <= 0:
            errors.append(f"{tag}: required_amount must be a positive number")
        cid = c.get("call_id")
        if cid in call_ids:
            errors.append(f"{tag}: duplicate call_id")
        call_ids.add(cid)
        agreement = c.get("agreement_id")
        for cls in c.get("eligible_asset_classes") or []:
            if (agreement, cls) not in hc:
                warnings.append(f"{tag}: eligible class '{cls}' has no haircut-schedule entry "
                                f"for agreement '{agreement}' — not deliverable for this call")

    # assets
    asset_ids = set()
    for i, a in enumerate(assets):
        tag = f"collateral_inventory[{i}] ({a.get('asset_id','?')})"
        for k in REQUIRED_ASSET:
            if k not in a or a[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(a.get("market_value")) is None:
            errors.append(f"{tag}: market_value not numeric")
        if _num(a.get("pledge_cost_bps")) is None:
            errors.append(f"{tag}: pledge_cost_bps not numeric")
        if a.get("available_value") is None:
            warnings.append(f"{tag}: no available_value — market_value assumed fully available")
        aid = a.get("asset_id")
        if aid in asset_ids:
            errors.append(f"{tag}: duplicate asset_id")
        asset_ids.add(aid)

    # coverage feasibility (warning only): total eligible post-haircut vs total required
    total_required = sum(_num(c.get("required_amount")) or 0.0 for c in calls)
    total_eligible_phv = 0.0
    for a in assets:
        best_h = None
        for c in calls:
            if a.get("asset_class") in (c.get("eligible_asset_classes") or []):
                row = hc.get((c.get("agreement_id"), a.get("asset_class")))
                if row and row.get("eligible"):
                    h = _num(row.get("haircut")) or 0.0
                    best_h = h if best_h is None else min(best_h, h)
        if best_h is not None:
            mv = _num(a.get("available_value", a.get("market_value"))) or 0.0
            total_eligible_phv += mv * (1.0 - best_h)
    if total_eligible_phv + 1e-6 < total_required:
        warnings.append(f"eligible post-haircut inventory ~{total_eligible_phv:.2f} < total "
                        f"required {total_required:.2f} — expect one or more shortfalls "
                        f"(surface, do not hide)")

    if not doc.get("config"):
        warnings.append("no 'config' block — default concentration cap / tolerance will be used; "
                        "record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "collateral_example.json"
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
