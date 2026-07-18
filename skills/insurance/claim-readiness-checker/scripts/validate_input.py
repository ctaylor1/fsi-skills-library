#!/usr/bin/env python3
"""Deterministic input validation for claim-readiness-checker.

Validates a claim readiness file before the readiness checks run. Fails closed on
structural problems; warns on data-quality gaps that limit which checks are evaluable.
Business gaps (a missing required document, an unsigned form, a near deadline) are NOT
input errors -- they are exactly what the readiness check is meant to surface downstream.

Input schema (JSON): see references/source-map.md. Key fields:
  claim_id, policy_number, as_of (YYYY-MM-DD), config_version, claim_type,
  dates{date_of_loss,date_reported,date_prepared,policy_effective,policy_expiration},
  deadlines[{name,due_date,hard}], fields{...}, documents[{doc_id,type,status,...}], config{...}

Usage:
  python validate_input.py claim.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("claim_id", "policy_number", "as_of", "config_version", "claim_type", "documents")
REQUIRED_DOC = ("doc_id", "type", "status")
VALID_STATUS = ("present", "missing", "illegible", "pending")
DATE_KEYS = ("date_of_loss", "date_reported", "date_prepared",
             "policy_effective", "policy_expiration")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    docs = doc.get("documents")
    if not isinstance(docs, list) or not docs:
        errors.append("documents must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, d in enumerate(docs):
        tag = f"documents[{i}] ({d.get('doc_id', '?')})"
        for k in REQUIRED_DOC:
            if k not in d or d[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        st = d.get("status")
        if st is not None and st not in VALID_STATUS:
            errors.append(f"{tag}: status {st!r} not in {VALID_STATUS}")
        did = d.get("doc_id")
        if did in ids:
            errors.append(f"{tag}: duplicate doc_id")
        ids.add(did)
        if d.get("signed") is not None and not isinstance(d.get("signed"), bool):
            errors.append(f"{tag}: 'signed' must be boolean when present")
        if st == "present" and not d.get("source_ref"):
            warnings.append(f"{tag}: present but no source_ref -- cannot cite this document")

    # dates block: any provided date must parse; key dates gate chronology checks
    dates = doc.get("dates") or {}
    for k in DATE_KEYS:
        v = dates.get(k)
        if v not in (None, "") and not DATE_RE.match(str(v)):
            errors.append(f"dates.{k} must start YYYY-MM-DD, got {v!r}")
    if not (dates.get("policy_effective") and dates.get("policy_expiration") and dates.get("date_of_loss")):
        warnings.append("missing policy_effective/expiration or date_of_loss -- loss-in-period chronology not evaluable")

    # deadlines: each must have a name and a parseable due_date
    deadlines = doc.get("deadlines") or []
    if not deadlines:
        warnings.append("no deadlines provided -- timeliness check not evaluable")
    for i, dl in enumerate(deadlines):
        if not dl.get("name"):
            errors.append(f"deadlines[{i}]: missing 'name'")
        if not DATE_RE.match(str(dl.get("due_date", ""))):
            errors.append(f"deadlines[{i}] ({dl.get('name', '?')}): due_date must start YYYY-MM-DD, got {dl.get('due_date')!r}")

    if not doc.get("config"):
        warnings.append("no 'config' block -- default required-item catalog will be used; record the config_version")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "claim_example.json"
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
