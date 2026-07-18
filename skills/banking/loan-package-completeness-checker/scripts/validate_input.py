#!/usr/bin/env python3
"""Deterministic input validation for loan-package-completeness-checker.

Validates a loan package file before the completeness engine runs. Fails closed on
structural problems; warns on data-quality gaps that limit which checks are evaluable
(e.g., a doc with a validity window but no effective_date -> expiration not evaluable).

Input schema (JSON): see references/source-map.md. Key fields:
  loan_id, package_type, as_of (YYYY-MM-DD), config_version, jurisdiction, product,
  expected_terms{...}, approval{...}, checklist[{item_id,doc_type,required,validity_days,
  needs_signatures[],jurisdictions[]}], documents[{doc_id,doc_type,effective_date,fields{},
  signatures[{party,signed,date}],source_ref}], conditions[{condition_id,status,type}]

Usage:
  python validate_input.py loan_package.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("loan_id", "as_of", "config_version", "jurisdiction", "checklist", "documents")
REQUIRED_CL = ("item_id", "doc_type", "required")
REQUIRED_DOC = ("doc_id", "doc_type", "source_ref")
KNOWN_COND_STATUS = ("cleared", "outstanding", "waived")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    checklist = doc.get("checklist") or []
    if not isinstance(checklist, list) or not checklist:
        errors.append("checklist must be a non-empty list")
        return errors, warnings

    cl_ids = set()
    for i, c in enumerate(checklist):
        tag = f"checklist[{i}] ({c.get('item_id','?')})"
        for k in REQUIRED_CL:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if not isinstance(c.get("required"), bool):
            errors.append(f"{tag}: 'required' must be true/false")
        if c.get("validity_days") is not None:
            try:
                int(c["validity_days"])
            except (TypeError, ValueError):
                errors.append(f"{tag}: validity_days not an integer")
        iid = c.get("item_id")
        if iid in cl_ids:
            errors.append(f"{tag}: duplicate item_id")
        cl_ids.add(iid)

    docs = doc.get("documents")
    if not isinstance(docs, list):
        errors.append("documents must be a list")
        return errors, warnings
    if not docs:
        warnings.append("documents is empty — every required checklist item will be reported missing")

    doc_ids = set()
    for i, d in enumerate(docs):
        tag = f"documents[{i}] ({d.get('doc_id','?')})"
        for k in REQUIRED_DOC:
            if k not in d or d[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        did = d.get("doc_id")
        if did in doc_ids:
            errors.append(f"{tag}: duplicate doc_id")
        doc_ids.add(did)
        eff = d.get("effective_date")
        if eff is not None and not DATE_RE.match(str(eff)):
            errors.append(f"{tag}: effective_date must start YYYY-MM-DD, got {eff!r}")
        for s in d.get("signatures") or []:
            if "party" not in s or "signed" not in s:
                errors.append(f"{tag}: signature entry needs 'party' and 'signed'")

    # data-quality warnings (limit evaluability, not fatal)
    doc_types_present = {d.get("doc_type") for d in docs}
    for c in checklist:
        if c.get("validity_days") is not None and c.get("doc_type") in doc_types_present:
            for d in docs:
                if d.get("doc_type") == c.get("doc_type") and not d.get("effective_date"):
                    warnings.append(f"{d.get('doc_id')}: no effective_date — expiration not evaluable for {c.get('item_id')}")
    if not doc.get("expected_terms"):
        warnings.append("no 'expected_terms' — cross-document consistency checks will be limited")
    if not doc.get("approval"):
        warnings.append("no 'approval' block — approval-envelope checks (amount/rate/expiry) not evaluable")
    for i, cond in enumerate(doc.get("conditions") or []):
        if cond.get("status") not in KNOWN_COND_STATUS:
            errors.append(f"conditions[{i}] ({cond.get('condition_id','?')}): status must be one of {KNOWN_COND_STATUS}")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "loan_package.json"
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
