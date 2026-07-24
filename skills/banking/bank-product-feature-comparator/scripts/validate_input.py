#!/usr/bin/env python3
"""Deterministic input validation for bank-product-feature-comparator.

Validates a comparison request + product records before the factual comparison runs. Fails
closed on structural problems (missing fields, unknown requested products, malformed dates);
warns on data-quality gaps that reduce citation coverage. It does NOT decide approval or
staleness — that gate lives in calculate_or_transform.py / validate_output.py.

Input schema (JSON): see references/source-map.md. Key fields:
  request_id, as_of (YYYY-MM-DD), approved_catalog_version, requested_products[] (>=2),
  products[{product_id, name, approval_status, effective_date, expiry_date?, version,
            superseded_by?, source_ref, attributes{eligibility[],fees[],features[]},
            disclosures[], discovery_questions[]}]
  each attribute row: {name, value, unit?, citation}

Usage:
  python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("request_id", "as_of", "approved_catalog_version", "requested_products", "products")
REQUIRED_PRODUCT = ("product_id", "name", "approval_status", "effective_date", "version", "source_ref")
FAMILIES = ("eligibility", "fees", "features")


def _bad_date(v) -> bool:
    return not DATE_RE.match(str(v))


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if _bad_date(doc["as_of"]):
        errors.append(f"as_of must be YYYY-MM-DD, got {doc['as_of']!r}")

    requested = doc.get("requested_products")
    if not isinstance(requested, list) or len(requested) < 2:
        errors.append("requested_products must list >= 2 product_id(s) to compare")
        requested = requested if isinstance(requested, list) else []

    products = doc.get("products")
    if not isinstance(products, list) or not products:
        errors.append("products must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, p in enumerate(products):
        tag = f"products[{i}] ({p.get('product_id', '?')})"
        for k in REQUIRED_PRODUCT:
            if k not in p or p[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        pid = p.get("product_id")
        if pid in ids:
            errors.append(f"{tag}: duplicate product_id")
        ids.add(pid)
        if p.get("effective_date") and _bad_date(p["effective_date"]):
            errors.append(f"{tag}: effective_date must be YYYY-MM-DD, got {p['effective_date']!r}")
        if p.get("expiry_date") and _bad_date(p["expiry_date"]):
            errors.append(f"{tag}: expiry_date must be YYYY-MM-DD, got {p['expiry_date']!r}")

        attrs = p.get("attributes") or {}
        if not isinstance(attrs, dict):
            errors.append(f"{tag}: attributes must be an object")
            attrs = {}
        present_families = [f for f in FAMILIES if attrs.get(f)]
        if not present_families:
            errors.append(f"{tag}: no comparable attributes in any of {list(FAMILIES)}")
        for fam in FAMILIES:
            for row in attrs.get(fam) or []:
                if not isinstance(row, dict) or not row.get("name"):
                    errors.append(f"{tag}: {fam} row missing 'name'")
                    continue
                if "value" not in row:
                    errors.append(f"{tag}: {fam} '{row.get('name')}' missing 'value'")
                if not str(row.get("citation", "")).strip():
                    warnings.append(f"{tag}: {fam} '{row.get('name')}' has no citation - cell will be uncited")
        if not p.get("discovery_questions"):
            warnings.append(f"{tag}: no discovery_questions - banker fact-gathering prompts will be thin")
        if not p.get("disclosures"):
            warnings.append(f"{tag}: no disclosures listed - disclosure comparison not evaluable for this product")

    for rid in requested:
        if rid not in ids:
            errors.append(f"requested product {rid!r} not present in products[] (cannot compare unknown product)")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "request_example.json"
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
