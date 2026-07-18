#!/usr/bin/env python3
"""Deterministic input validation for customer-onboarding-document-checker.

Validates an onboarding-package file before the completeness checks run. Fails closed on
structural problems; warns on data-quality gaps that limit which checks are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  package_id, as_of (YYYY-MM-DD), config_version, customer_type, product, jurisdiction,
  applicant{legal_name,date_of_birth,address,tin_last4,...},
  documents[{doc_id,type,status,issue_date,expiration_date,signature_present,fields{},source_ref}],
  exceptions[{exception_id,type,status,note}], config{required_documents[],key_identity_fields[],...}

Usage:
  python validate_input.py package.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("package_id", "as_of", "config_version", "customer_type", "documents")
REQUIRED_DOC = ("doc_id", "type", "status", "source_ref")
DOC_STATUS = {"provided", "missing", "illegible"}
EXC_STATUS = {"open", "resolved"}


def _is_date(v) -> bool:
    return bool(DATE_RE.match(str(v)))


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not _is_date(doc["as_of"]):
        errors.append(f"as_of must be YYYY-MM-DD, got {doc['as_of']!r}")

    docs = doc.get("documents") or []
    if not isinstance(docs, list) or not docs:
        errors.append("documents must be a non-empty list")
        return errors, warnings

    cfg = doc.get("config") or {}
    reqs = {str(r.get("type")) for r in (cfg.get("required_documents") or [])}
    expiry_types = {str(r.get("type")) for r in (cfg.get("required_documents") or [])
                    if r.get("expiry_checked")}

    ids = set()
    for i, d in enumerate(docs):
        tag = f"documents[{i}] ({d.get('doc_id', '?')})"
        for k in REQUIRED_DOC:
            if k not in d or d[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if d.get("status") not in DOC_STATUS:
            errors.append(f"{tag}: status must be one of {sorted(DOC_STATUS)}")
        if "signature_present" in d and not isinstance(d["signature_present"], bool):
            errors.append(f"{tag}: signature_present must be true/false")
        for df in ("issue_date", "expiration_date"):
            if d.get(df) and not _is_date(d[df]):
                errors.append(f"{tag}: {df} must be YYYY-MM-DD, got {d[df]!r}")
        did = d.get("doc_id")
        if did in ids:
            errors.append(f"{tag}: duplicate doc_id")
        ids.add(did)
        # evaluability warnings
        if d.get("status") == "provided" and d.get("type") in expiry_types and not d.get("expiration_date"):
            warnings.append(f"{tag}: no expiration_date — expired/expiring checks not evaluable for this doc")
        if d.get("status") == "provided" and not (d.get("fields") or {}):
            warnings.append(f"{tag}: no 'fields' — data-consistency checks not evaluable for this doc")

    for e in (doc.get("exceptions") or []):
        if not e.get("exception_id"):
            errors.append("an exception is missing 'exception_id'")
        if e.get("status") not in EXC_STATUS:
            errors.append(f"exception {e.get('exception_id', '?')}: status must be one of {sorted(EXC_STATUS)}")

    if not cfg:
        warnings.append("no 'config' block — default checklist/thresholds used; record the config_version")
    else:
        present_types = {str(d.get("type")) for d in docs}
        for rt in sorted(reqs - present_types):
            warnings.append(f"required document type '{rt}' has no matching document entry (will be flagged missing)")
    if not (doc.get("applicant") or {}):
        warnings.append("no 'applicant' record — data-consistency checks limited to cross-document comparison")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "package_example.json"
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
