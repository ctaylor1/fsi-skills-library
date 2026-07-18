#!/usr/bin/env python3
"""Deterministic input validation for aml-alert-triager.

Validates an alert-queue file before triage. Fails closed on structural problems; warns on
data gaps that force a `needs-data` disposition.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, approved_whitelist[], priority_config{}, open_cases[], alerts[
    {alert_id, entity_id, account_ref, rule_id, period{from,to}, amount_total,
     txn_ids[], customer{risk_rating, high_risk_geo}, flags{sanctions_adverse_media},
     typology_hint, prior_alerts_90d, seasonal_pattern_id, legs_internal, leg_accounts[],
     source_ref}]

Usage: python validate_input.py alerts.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "alerts")
REQUIRED_ALERT = ("alert_id", "entity_id", "rule_id", "period", "source_ref")
RISK = {"High", "Medium", "Low"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    alerts = doc.get("alerts") or []
    if not isinstance(alerts, list) or not alerts:
        errors.append("alerts must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, a in enumerate(alerts):
        tag = f"alerts[{i}] ({a.get('alert_id','?')})"
        for k in REQUIRED_ALERT:
            if k not in a or a[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        aid = a.get("alert_id")
        if aid in ids:
            errors.append(f"{tag}: duplicate alert_id")
        ids.add(aid)
        per = a.get("period") or {}
        if not (per.get("from") and per.get("to")):
            errors.append(f"{tag}: period requires 'from' and 'to'")
        cust = a.get("customer") or {}
        if cust.get("risk_rating") not in RISK:
            warnings.append(f"{tag}: customer.risk_rating missing/invalid -> needs-data")
        if not a.get("txn_ids"):
            warnings.append(f"{tag}: no txn_ids -> escalation bundle will lack transaction evidence (needs-data)")
        if a.get("seasonal_pattern_id") and a.get("flags", {}).get("sanctions_adverse_media"):
            warnings.append(f"{tag}: seasonal suppression will be OVERRIDDEN by sanctions/adverse-media flag (escalate)")
    if doc.get("open_cases") is None:
        warnings.append("no open_cases provided -> duplicate detection limited")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "alerts_example.json"
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
