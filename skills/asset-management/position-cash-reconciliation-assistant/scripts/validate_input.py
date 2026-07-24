#!/usr/bin/env python3
"""Deterministic input validation for position-cash-reconciliation-assistant.

Validates a position/cash reconciliation job (internal book side + external custodian /
prime-broker / administrator / counterparty side) before matching. Fails closed on structural
problems; warns on data-quality gaps that limit matching, materiality, or tie-out.

Input schema (JSON): see references/source-map.md. Key fields:
  entity, as_of (YYYY-MM-DD), config_version, base_currency,
  internal_records[{record_id,match_key,account,source_system,record_type,quantity|amount,
                    currency?,date,settle_date?,source_ref,...}],
  external_records[{...same shape; source_system in custodian|prime_broker|administrator|
                    counterparty...}],
  config{quantity_tolerance,cash_tolerance,quantity_materiality,cash_materiality_base,
         pending_settlement_days,fx_rates{}}

Usage:
  python validate_input.py reconciliation.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("entity", "as_of", "config_version", "base_currency",
                "internal_records", "external_records")
REQUIRED_REC = ("record_id", "match_key", "account", "record_type", "source_ref")
RECORD_TYPES = {"position", "cash"}
EXTERNAL_SYSTEMS = {"custodian", "prime_broker", "administrator", "counterparty"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _value_field(r):
    return "quantity" if str(r.get("record_type")) == "position" else "amount"


def _check_side(name, rows, is_external, seen_ids, cash_ccys, errors, warnings):
    if not isinstance(rows, list):
        errors.append(f"{name} must be a list")
        return
    for i, r in enumerate(rows):
        tag = f"{name}[{i}] ({r.get('record_id', '?')})"
        if not isinstance(r, dict):
            errors.append(f"{tag}: not an object")
            continue
        for k in REQUIRED_REC:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        rtype = str(r.get("record_type"))
        if rtype not in RECORD_TYPES:
            errors.append(f"{tag}: record_type must be one of {sorted(RECORD_TYPES)}, got {rtype!r}")
        vf = _value_field(r)
        if _num(r.get(vf)) is None:
            errors.append(f"{tag}: {vf} not numeric (positions need 'quantity', cash needs 'amount')")
        if rtype == "cash":
            if not r.get("currency"):
                errors.append(f"{tag}: cash record missing 'currency'")
            else:
                cash_ccys.add(str(r["currency"]).upper())
        if is_external:
            src = str(r.get("source_system"))
            if src not in EXTERNAL_SYSTEMS:
                errors.append(f"{tag}: external source_system must be one of "
                              f"{sorted(EXTERNAL_SYSTEMS)}, got {src!r}")
        for df in ("date", "settle_date"):
            if r.get(df) is not None and not DATE_RE.match(str(r.get(df))):
                errors.append(f"{tag}: {df} must start YYYY-MM-DD, got {r.get(df)!r}")
        rid = r.get("record_id")
        if rid in seen_ids:
            errors.append(f"{tag}: duplicate record_id across job (record_id must be unique)")
        seen_ids.add(rid)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    internal = doc.get("internal_records") or []
    external = doc.get("external_records") or []
    if not isinstance(internal, list) or not isinstance(external, list):
        errors.append("internal_records and external_records must both be lists")
        return errors, warnings
    if len(internal) + len(external) == 0:
        errors.append("no records: internal_records and external_records are both empty")
        return errors, warnings

    seen_ids: set = set()
    cash_ccys: set = set()
    _check_side("internal_records", internal, False, seen_ids, cash_ccys, errors, warnings)
    _check_side("external_records", external, True, seen_ids, cash_ccys, errors, warnings)

    # matching feasibility
    if internal and not any(r.get("match_key") for r in internal):
        warnings.append("internal_records have no match_key values — internal items cannot be matched")
    if external and not any(r.get("match_key") for r in external):
        warnings.append("external_records have no match_key values — external items cannot be matched")

    cfg = doc.get("config") or {}
    if not cfg:
        warnings.append("no 'config' block — default tolerances/materiality/fx will be used; "
                        "record the config_version")
    base_ccy = str(doc.get("base_currency") or "").upper()
    fx = {k.upper() for k in (cfg.get("fx_rates") or {})}
    for ccy in sorted(cash_ccys):
        if ccy and ccy != base_ccy and ccy not in fx:
            warnings.append(f"no fx_rate for cash currency {ccy} — base-currency materiality for "
                            f"{ccy} cash breaks will not be evaluable")
    if not internal:
        warnings.append("internal_records empty — every external item will classify as missing_internal")
    if not external:
        warnings.append("external_records empty — every internal item will classify as missing_external")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "reconciliation_example.json"
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
