#!/usr/bin/env python3
"""Deterministic input validation for next-best-action-assistant.

Validates a customer-context + approved-action-catalog file before the engine runs. Fails
closed on structural problems; warns on data gaps that weaken or gate recommendations.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, context_refs[], customer{customer_ref, segment, products[], tenure_months,
    do_not_contact, vulnerability_flag, open_complaint, consent{}, signals{}},
  action_catalog[{action_id, type, title, eligibility{}, requires_consent, requires_specialist,
    binding_category, required_disclosures[], source_refs[], benefit_score}]

Usage: python validate_input.py context.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "customer", "action_catalog")
REQUIRED_CUSTOMER = ("customer_ref", "segment", "products")
ALLOWED_TYPES = {"education", "service", "retention", "cross-sell", "referral", "advice"}
PROHIBITED_BINDING = {
    "credit_decision", "claim_decision", "investment_advice", "suitability_determination",
}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    cust = doc.get("customer") or {}
    if not isinstance(cust, dict):
        errors.append("customer must be an object")
        return errors, warnings
    for k in REQUIRED_CUSTOMER:
        if k not in cust or cust[k] in (None, ""):
            errors.append(f"customer: missing '{k}'")
    if not isinstance(cust.get("products", []), list):
        errors.append("customer.products must be a list")
    if not isinstance(cust.get("consent", {}), dict):
        warnings.append("customer.consent missing/invalid -> outbound actions will be consent-gated")
    if not isinstance(cust.get("signals", {}), dict):
        warnings.append("customer.signals missing/invalid -> signal-gated actions become ineligible")
    if not doc.get("context_refs"):
        warnings.append("no context_refs -> package sources/citations will be thin")

    catalog = doc.get("action_catalog") or []
    if not isinstance(catalog, list) or not catalog:
        errors.append("action_catalog must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, a in enumerate(catalog):
        tag = f"action_catalog[{i}] ({a.get('action_id','?')})"
        aid = a.get("action_id")
        if not aid:
            errors.append(f"{tag}: missing 'action_id'")
        elif aid in ids:
            errors.append(f"{tag}: duplicate action_id")
        ids.add(aid)
        if a.get("type") not in ALLOWED_TYPES:
            warnings.append(f"{tag}: type {a.get('type')!r} not in {sorted(ALLOWED_TYPES)}")
        bc = a.get("binding_category")
        if bc and bc not in PROHIBITED_BINDING:
            warnings.append(f"{tag}: unknown binding_category {bc!r}")
        # A recommendable (non-binding) action should carry citations; otherwise it will be
        # dropped by validate_output as unsupported.
        if not bc and not a.get("source_refs"):
            warnings.append(f"{tag}: no source_refs -> would be dropped as unsupported")
        if not isinstance(a.get("eligibility", {}), dict):
            errors.append(f"{tag}: eligibility must be an object")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "context_example.json"
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
    print(f"input validation warnings: {len(warnings)}")
    print(f"input validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
