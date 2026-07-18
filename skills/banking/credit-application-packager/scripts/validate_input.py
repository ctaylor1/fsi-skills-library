#!/usr/bin/env python3
"""Deterministic input validation for credit-application-packager.

Validates a credit-application intake bundle before packaging. Fails closed on structural
problems; warns on data gaps that will surface as open items (missing components, stale or
undated documents, missing borrower identity on a document).

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, package_id, product, jurisdiction, as_of_date,
  required_components[], required_approvals[],
  borrower{borrower_id, legal_name, entity_type},
  documents[{component, doc_id, title, borrower_id, borrower_name,
             effective_date, expires, source_ref, values{}}],
  approvals[{approval_id, type, approver_role, approver, status, date, source_ref}],
  conditions[{condition_id, description, status, source_ref}]

Usage: python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "package_id", "borrower", "documents",
                "required_components", "as_of_date")
REQUIRED_DOC = ("component", "doc_id", "source_ref")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    borrower = doc.get("borrower") or {}
    if not borrower.get("borrower_id") or not borrower.get("legal_name"):
        errors.append("borrower requires 'borrower_id' and 'legal_name'")

    req = doc.get("required_components")
    if not isinstance(req, list) or not req:
        errors.append("required_components must be a non-empty list")
        return errors, warnings

    documents = doc.get("documents")
    if not isinstance(documents, list):
        errors.append("documents must be a list")
        return errors, warnings

    doc_ids = set()
    provided_components = set()
    for i, d in enumerate(documents):
        tag = f"documents[{i}] ({d.get('doc_id','?')})"
        for k in REQUIRED_DOC:
            if k not in d or d[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        did = d.get("doc_id")
        if did in doc_ids:
            errors.append(f"{tag}: duplicate doc_id")
        doc_ids.add(did)
        provided_components.add(d.get("component"))
        if not d.get("effective_date"):
            warnings.append(f"{tag}: no effective_date -> freshness cannot be evaluated (review)")
        if not d.get("borrower_id") and not d.get("borrower_name"):
            warnings.append(f"{tag}: no borrower identity -> entity-consistency check limited")

    for comp in req:
        if comp not in provided_components:
            warnings.append(f"required component '{comp}' has no supporting document -> open-item (missing)")

    for i, a in enumerate(doc.get("approvals") or []):
        if not a.get("type") or not a.get("status"):
            errors.append(f"approvals[{i}]: requires 'type' and 'status'")
        if a.get("status") == "recorded" and not a.get("source_ref"):
            errors.append(f"approvals[{i}] ({a.get('type','?')}): recorded approval missing 'source_ref'")

    if not doc.get("required_approvals"):
        warnings.append("no required_approvals configured -> approval capture limited")
    if doc.get("approvals") is None:
        warnings.append("no approvals provided -> all required approvals will be outstanding")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "package_intake_example.json"
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
