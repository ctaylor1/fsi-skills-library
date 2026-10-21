#!/usr/bin/env python3
"""Validate supplied regulatory evidence; source labels are not authenticated law."""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path
from native_integrity import canonical_hash

LEVELS = {"law", "regulation", "supervisory_guidance", "standard", "rule", "institution_policy"}
STATES = {"proposed", "adopted", "effective", "stayed", "withdrawn", "superseded", "unknown"}

def valid_date(value):
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False

def _validate_impl(doc):
    errors, warnings = [], []
    if not isinstance(doc, dict):
        return ["input must be an object"], warnings
    for key in ("change_id", "as_of", "config_version", "instrument", "obligations", "firm_profile"):
        if key not in doc:
            errors.append(f"missing {key}")
    if errors:
        return errors, warnings
    if not valid_date(doc["as_of"]):
        errors.append("as_of must be a real YYYY-MM-DD date")
    inst = doc["instrument"]
    if not isinstance(inst, dict):
        return errors + ["instrument must be an object"], warnings
    for key in ("authority", "citation", "authority_level", "jurisdiction", "source_ref", "lifecycle_state", "status_as_of"):
        if not isinstance(inst.get(key), str) or not inst[key].strip():
            errors.append(f"instrument.{key} is required")
    if inst.get("authority_level") not in LEVELS:
        errors.append("unsupported authority_level")
    if inst.get("lifecycle_state") not in STATES:
        errors.append("unsupported lifecycle_state")
    for key in ("publication_date", "effective_date", "compliance_date", "status_as_of"):
        value = inst.get(key)
        if value is not None and not valid_date(value):
            errors.append(f"instrument.{key} must be a real date or null")
        if key in ("publication_date", "status_as_of") and valid_date(value) and valid_date(doc["as_of"]) and value > doc["as_of"]:
            errors.append(f"instrument.{key} is after assessment as_of")
    if inst.get("lifecycle_state") == "effective" and not inst.get("effective_date"):
        errors.append("effective state requires effective_date")
    if inst.get("lifecycle_state") == "effective" and valid_date(inst.get("effective_date")) and valid_date(doc["as_of"]) and inst["effective_date"] > doc["as_of"]:
        errors.append("effective state conflicts with future effective_date")
    if not inst.get("compliance_date"):
        warnings.append("no compliance deadline supplied; elapsed effective date is not an overdue finding")
    firm = doc["firm_profile"]
    if not isinstance(firm, dict):
        errors.append("firm_profile must be an object")
    else:
        for key in ("jurisdictions", "business_lines"):
            if not isinstance(firm.get(key, []), list) or any(not isinstance(v, str) or not v.strip() for v in firm.get(key, [])):
                errors.append(f"firm_profile.{key} must be a list")
    obligations = doc["obligations"]
    if not isinstance(obligations, list) or not obligations:
        return errors + ["obligations must be a nonempty list"], warnings
    ids = set()
    for o in obligations:
        if not isinstance(o, dict):
            errors.append("each obligation must be an object")
            continue
        for key in ("obligation_id", "text", "obligation_type", "source_ref"):
            if not isinstance(o.get(key), str) or not o[key].strip():
                errors.append(f"obligation.{key} required")
        oid = o.get("obligation_id")
        if isinstance(oid, str):
            if oid in ids: errors.append("duplicate obligation_id")
            ids.add(oid)
        if not isinstance(o.get("applies_to_lines", []), list) or any(not isinstance(v, str) or not v.strip() for v in o.get("applies_to_lines", [])):
            errors.append("applies_to_lines must be a list")
        assessment = o.get("applicability_assessment")
        if assessment is not None:
            if not isinstance(assessment, dict) or assessment.get("status") not in ("applicable", "not_applicable", "unknown"):
                errors.append("invalid applicability_assessment")
            elif assessment.get("status") != "unknown":
                for key in ("rationale", "source_ref", "reviewed_by", "reviewed_on"):
                    if not assessment.get(key): errors.append(f"applicability_assessment.{key} required")
                if not valid_date(assessment.get("reviewed_on")):
                    errors.append("applicability reviewed_on must be a real date")
                elif valid_date(doc["as_of"]) and assessment["reviewed_on"] > doc["as_of"]:
                    errors.append("applicability review is after as_of")
    inv = doc.get("inventory", {})
    if not isinstance(inv, dict) or not isinstance(inv.get("mappings", []), list):
        errors.append("inventory.mappings must be a list")
    else:
        seen = set()
        for mapping in inv.get("mappings", []):
            if not isinstance(mapping, dict):
                errors.append("mapping must be an object"); continue
            oid = mapping.get("obligation_id")
            if not isinstance(oid, str) or oid not in ids or oid in seen:
                errors.append("unknown or duplicate mapping obligation_id")
            if isinstance(oid, str): seen.add(oid)
            for key in ("policies", "controls", "systems", "data_elements", "training"):
                if not isinstance(mapping.get(key, []), list): errors.append(f"mapping.{key} must be a list")
            if not isinstance(mapping.get("owner", {}), dict): errors.append("mapping.owner must be an object")
            if not isinstance(mapping.get("mapping_exceptions", {}), dict) or any(not isinstance(v, str) or not v.strip() for v in mapping.get("mapping_exceptions", {}).values()): errors.append("mapping_exceptions needs nonempty justifications")
            implementation = mapping.get("implementation", {})
            if not isinstance(implementation, dict) or implementation.get("status", "unknown") not in ("complete", "incomplete", "unknown"):
                errors.append("invalid implementation status")
            elif implementation.get("status") in ("complete", "incomplete") and not implementation.get("source_ref"):
                errors.append("asserted implementation status requires source_ref")
    cfg = doc.get("config", {})
    if not isinstance(cfg, dict):
        errors.append("config must be an object")
    elif type(cfg.get("near_term_days", 30)) is not int or cfg.get("near_term_days", 30) <= 0:
        errors.append("near_term_days must be a positive integer")
    return errors, warnings

def validate(doc):
    try:
        canonical_hash(doc)  # Reject non-finite and non-JSON values anywhere, before the method.
        return _validate_impl(doc)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        return ["malformed input: " + str(exc)], []


def main(argv):
    path = Path(__file__).resolve().parents[1]/"evals/files/change_example.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    try:
        errors, warnings = validate(json.loads(path.read_text() if path else sys.stdin.read()))
    except (ValueError, TypeError, OSError) as exc:
        errors, warnings = [str(exc)], []
    for item in warnings: print("WARN", item)
    for item in errors: print("ERROR", item)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return bool(errors)
if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
