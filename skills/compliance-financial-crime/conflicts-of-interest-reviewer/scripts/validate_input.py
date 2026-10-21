#!/usr/bin/env python3
"""Deterministic input validation for conflicts-of-interest-reviewer.

Validates a matter file before conflict analysis. Fails closed on structural problems; warns
on data-quality gaps that limit which findings are reliable.

Input schema (JSON): see references/source-map.md. Key fields:
  matter_id, as_of (YYYY-MM-DD), config_version, subject{party_id,role,business_unit},
  items[{item_id, conflict_type, description, counterparties[], affected_parties[],
         incentive, magnitude{ownership_pct,annual_value,gift_value}, mnpi_access,
         disclosures[{to,date,type,source_ref}], controls[{type,status,source_ref}],
         approvals[{by,date,source_ref}], source_ref}]

Usage:
  python validate_input.py matter.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys, math
from datetime import date
from pathlib import Path
from native_integrity import canonical_hash

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("matter_id", "as_of", "config_version", "items")
REQUIRED_ITEM = ("item_id", "conflict_type", "source_ref")
CONFLICT_TYPES = {
    "personal_financial_interest", "outside_business_activity", "gift_entertainment",
    "personal_relationship", "personal_trading", "dual_role", "related_party_transaction",
    "incentive_misalignment", "information_barrier",
}


def _num(v):
    try:
        value = float(v)
        return value if not isinstance(v, bool) and math.isfinite(value) and value >= 0 else None
    except (TypeError, ValueError):
        return None


def _date_ok(value):
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False

def _validate_impl(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if not isinstance(doc, dict): return ["input must be an object"], warnings
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not _date_ok(doc["as_of"]):
        errors.append(f"as_of must be a real YYYY-MM-DD date, got {doc['as_of']!r}")

    items = doc.get("items") or []
    if not isinstance(items, list) or not items:
        errors.append("items must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            errors.append("item must be an object"); continue
        tag = f"items[{i}] ({it.get('item_id','?')})"
        for k in REQUIRED_ITEM:
            if k not in it or it[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        ctype = it.get("conflict_type")
        if ctype is not None and ctype not in CONFLICT_TYPES:
            errors.append(f"{tag}: unknown conflict_type {ctype!r} (allowed: {sorted(CONFLICT_TYPES)})")
        iid = it.get("item_id")
        if iid in ids:
            errors.append(f"{tag}: duplicate item_id")
        ids.add(iid)

        mag = it.get("magnitude") or {}
        if not isinstance(mag, dict):
            errors.append(f"{tag}: magnitude must be an object"); continue
        for mk in ("ownership_pct", "annual_value", "gift_value"):
            if mk in mag and mag[mk] is not None and _num(mag[mk]) is None:
                errors.append(f"{tag}: magnitude.{mk} not numeric ({mag[mk]!r})")

        if ctype == "gift_entertainment" and (mag.get("gift_value") is None):
            warnings.append(f"{tag}: gift_entertainment has no magnitude.gift_value — de-minimis check not evaluable")
        if ctype in ("personal_financial_interest", "outside_business_activity", "incentive_misalignment") \
                and mag.get("ownership_pct") is None and mag.get("annual_value") is None:
            warnings.append(f"{tag}: no ownership_pct/annual_value — materiality escalation not evaluable")
        if ctype == "personal_trading" and "mnpi_access" not in it:
            warnings.append(f"{tag}: personal_trading missing mnpi_access — indicator unevaluable; no non-MNPI assumption")

        if "mnpi_access" in it and it["mnpi_access"] is not None and type(it["mnpi_access"]) is not bool:
            errors.append(f"{tag}: mnpi_access must be boolean or null")
        for collection in ("disclosures", "controls", "approvals"):
            rows = it.get(collection, [])
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                errors.append(f"{tag}: {collection} must be a list of objects")
        if errors: continue
        for row in it.get("approvals", []) + it.get("disclosures", []):
            for field in ("date", "expires_on"):
                if row.get(field) and not _date_ok(row[field]):
                    errors.append(f"{tag}: {field} must be a real date")
        # disclosure dates parseable
        for d in it.get("disclosures") or []:
            if d.get("date") and not _date_ok(d["date"]):
                errors.append(f"{tag}: disclosure date not YYYY-MM-DD ({d['date']!r})")
        if not it.get("disclosures"):
            warnings.append(f"{tag}: no disclosures recorded — disclosure requirement will read as missing")
        if not it.get("affected_parties"):
            warnings.append(f"{tag}: no affected_parties listed")

    cfg = doc.get("config", {})
    if not isinstance(cfg, dict):
        errors.append("config must be an object")
    else:
        for key in ("gift_deminimis", "ownership_material_pct", "annual_value_material", "disclosure_staleness_days"):
            if key in cfg and _num(cfg[key]) is None: errors.append(f"config.{key} must be finite and nonnegative")
        if cfg.get("policy_source_ref"):
            for key in ("gift_deminimis", "ownership_material_pct", "annual_value_material", "disclosure_staleness_days"):
                if key not in cfg: errors.append(f"supplied policy must explicitly specify {key}; no silent numeric defaults")
        if not cfg.get("policy_source_ref"):
            warnings.append("no institution policy evidence; numeric thresholds are unevaluable")
        if "requirements" in cfg and not isinstance(cfg["requirements"], dict): errors.append("config.requirements must be an object")
    if not doc.get("config"):
        warnings.append("no 'config' block — illustrative control checklist only; numeric policy tests remain unevaluable")
    if not doc.get("subject"):
        warnings.append("no 'subject' block — subject will read as unknown in the review_id")

    return errors, warnings


def validate(doc):
    try:
        canonical_hash(doc)  # Reject non-finite and non-JSON values anywhere, before the method.
        return _validate_impl(doc)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        return ["malformed input: " + str(exc)], []


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "matter_example.json"
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
