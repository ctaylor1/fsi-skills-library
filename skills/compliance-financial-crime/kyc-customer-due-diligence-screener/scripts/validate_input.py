#!/usr/bin/env python3
"""Deterministic input validation for kyc-customer-due-diligence-screener.

Validates a KYC case file before CDD screening. Fails closed on structural problems; warns
on data-quality gaps that limit which signals are evaluable (a thin case yields
low-confidence findings, never an inflated risk conclusion).

Input schema (JSON): see references/source-map.md. Key fields:
  case_id, as_of (YYYY-MM-DD), config_version,
  customer{customer_id, customer_type: individual|entity, legal_name, country, ...},
  documents[{type, issue_date?, expiry_date?, verified?, source_ref}],
  identity_checks[{attribute, sources, match: bool, source_ref}],
  screening_hits{sanctions[], pep[], adverse_media[]},
  beneficial_owners[{name, ownership_pct, verified, country, source_ref}],  # entity only
  config{...thresholds...}

Usage:
  python validate_input.py case.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("case_id", "as_of", "config_version", "customer", "documents")
VALID_TYPES = ("individual", "entity")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict):
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    cust = doc.get("customer")
    if not isinstance(cust, dict) or not cust:
        errors.append("customer must be a non-empty object")
        return errors, warnings
    ctype = cust.get("customer_type")
    if ctype not in VALID_TYPES:
        errors.append(f"customer.customer_type must be one of {VALID_TYPES}, got {ctype!r}")
    if not str(cust.get("legal_name", "")).strip():
        errors.append("customer.legal_name is required")

    docs = doc.get("documents")
    if not isinstance(docs, list):
        errors.append("documents must be a list")
        return errors, warnings
    if not docs:
        warnings.append("no documents provided — completeness/identity signals will fire or be low-confidence")
    for i, d in enumerate(docs):
        tag = f"documents[{i}]"
        if not str(d.get("type", "")).strip():
            errors.append(f"{tag}: missing 'type'")
        for df in ("issue_date", "expiry_date"):
            if d.get(df) and not DATE_RE.match(str(d[df])):
                errors.append(f"{tag}: {df} must be YYYY-MM-DD, got {d[df]!r}")

    owners = doc.get("beneficial_owners") or []
    if ctype == "entity" and not owners:
        warnings.append("entity with no beneficial_owners — UBO coverage/verification signals not evaluable")
    for i, o in enumerate(owners):
        tag = f"beneficial_owners[{i}] ({o.get('name','?')})"
        if _num(o.get("ownership_pct")) is None:
            errors.append(f"{tag}: ownership_pct not numeric")
        if not str(o.get("name", "")).strip():
            errors.append(f"{tag}: missing 'name'")

    hits = doc.get("screening_hits")
    if not isinstance(hits, dict):
        warnings.append("no screening_hits block — sanctions/PEP/adverse-media signals not evaluable")
    if not doc.get("identity_checks"):
        warnings.append("no identity_checks provided — identity_mismatch not evaluable")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds/lists used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "case_example.json"
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
