#!/usr/bin/env python3
"""Deterministic input validation for investment-reference-data-reviewer.

Validates an enrichment job (candidate securities with identifier and attribute observations
from one or more sources) before the enrichment engine runs. Fails closed on structural
problems; warns on data-quality gaps that limit joining, freshness, or provenance.

Input schema (JSON): see references/source-map.md. Key fields:
  entity, as_of (YYYY-MM-DD), config_version, source_hierarchy[] (ranked, highest first),
  securities[{security_key, identifiers[{scheme,value,source,as_of}],
              attributes[{field,value,source,as_of,effective_date}]}],
  config{required_fields[],material_fields[],numeric_tolerance,freshness_days}

Usage:
  python validate_input.py enrichment.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("entity", "as_of", "config_version", "source_hierarchy", "securities")
ENRICH_FIELDS = {"currency", "exchange", "asset_class", "maturity", "coupon", "rating",
                 "benchmark", "issuer"}


def _check_identifiers(tag, ids, approved, errors, warnings):
    if not isinstance(ids, list):
        errors.append(f"{tag}: 'identifiers' must be a list")
        return
    for j, i in enumerate(ids):
        itag = f"{tag}.identifiers[{j}]"
        if not isinstance(i, dict):
            errors.append(f"{itag}: not an object")
            continue
        for k in ("scheme", "value", "source"):
            if not i.get(k):
                errors.append(f"{itag}: missing '{k}'")
        if i.get("source") and approved and i["source"] not in approved:
            warnings.append(f"{itag}: source {i['source']!r} not in source_hierarchy — will be excluded (unpermitted)")
        if not i.get("as_of"):
            warnings.append(f"{itag}: no as_of — freshness not evaluable")


def _check_attributes(tag, attrs, approved, errors, warnings):
    if not isinstance(attrs, list):
        errors.append(f"{tag}: 'attributes' must be a list")
        return
    for j, a in enumerate(attrs):
        atag = f"{tag}.attributes[{j}]"
        if not isinstance(a, dict):
            errors.append(f"{atag}: not an object")
            continue
        for k in ("field", "source"):
            if not a.get(k):
                errors.append(f"{atag}: missing '{k}'")
        if "value" not in a or a.get("value") in (None, ""):
            errors.append(f"{atag}: missing 'value'")
        if a.get("field") and a["field"] not in ENRICH_FIELDS:
            warnings.append(f"{atag}: field {a['field']!r} not in the enrichment registry — ignored")
        if a.get("source") and approved and a["source"] not in approved:
            warnings.append(f"{atag}: source {a['source']!r} not in source_hierarchy — will be excluded (unpermitted)")
        if not a.get("as_of"):
            warnings.append(f"{atag}: no as_of — freshness not evaluable")


def _validate_shape(doc: dict):
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    hierarchy = doc.get("source_hierarchy")
    if not isinstance(hierarchy, list) or not hierarchy:
        errors.append("source_hierarchy must be a non-empty ranked list (highest first)")
        approved = set()
    else:
        approved = set(hierarchy)
        if len(approved) != len(hierarchy):
            warnings.append("source_hierarchy contains duplicate sources — rank is ambiguous")

    secs = doc.get("securities")
    if not isinstance(secs, list):
        errors.append("securities must be a list")
        return errors, warnings
    if not secs:
        errors.append("no securities: 'securities' is empty")
        return errors, warnings

    seen_keys: set = set()
    for i, sec in enumerate(secs):
        tag = f"securities[{i}] ({sec.get('security_key','?')})"
        if not isinstance(sec, dict):
            errors.append(f"{tag}: not an object")
            continue
        key = sec.get("security_key")
        if not key:
            errors.append(f"{tag}: missing 'security_key'")
        elif key in seen_keys:
            errors.append(f"{tag}: duplicate security_key requires explicit upstream consolidation")
        seen_keys.add(key)

        ids = sec.get("identifiers") or []
        attrs = sec.get("attributes") or []
        if not ids and not attrs:
            errors.append(f"{tag}: no identifiers and no attributes — nothing to enrich")
        _check_identifiers(tag, ids, approved, errors, warnings)
        _check_attributes(tag, attrs, approved, errors, warnings)

    if not doc.get("config"):
        warnings.append("no 'config' block — default required/material fields, tolerance, and freshness window apply; record the config_version")

    return errors, warnings


def validate(doc):
    from native_integrity import canonical_hash
    errors, warnings = [], []
    try:
        canonical_hash(doc)
        errors, warnings = _validate_shape(doc)
        if not errors:
            from calculate_or_transform import compute
            compute(doc)
    except (ValueError, TypeError, KeyError, ArithmeticError, AttributeError) as exc:
        errors.append("unsupported or invalid native input: " + str(exc))
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "enrichment_example.json"
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
