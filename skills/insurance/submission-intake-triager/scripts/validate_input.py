#!/usr/bin/env python3
"""Deterministic input validation for submission-intake-triager.

Validates a broker-submission file (documents + platform-extracted fields) before
normalization, reconciliation, and appetite triage. Fails closed on structural problems;
warns on data-quality gaps that limit which appetite rules are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  submission_id, received_date (YYYY-MM-DD), config_version, line_of_business,
  documents[{doc_id, doc_type, source_ref, title?}],
  extracted_fields[{field, value, doc_id, source_ref, unit?, confidence?, doc_type?}],
  config{appetite_states[], excluded_classes[], max_tiv_ceiling, refer_tiv_threshold,
         loss_ratio_refer, cat_refer_zones[], required_fields[], critical_fields[]}

Usage:
  python validate_input.py submission.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("submission_id", "received_date", "config_version", "line_of_business",
                "documents", "extracted_fields")
REQUIRED_DOC = ("doc_id", "doc_type", "source_ref")
REQUIRED_FIELD = ("field", "value", "doc_id", "source_ref")
ALLOWED_DOC_TYPES = {"acord", "sov_spreadsheet", "loss_run", "email", "pdf", "other"}
LOW_CONFIDENCE = 0.5


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["received_date"])):
        errors.append(f"received_date must start YYYY-MM-DD, got {doc['received_date']!r}")

    docs = doc.get("documents") or []
    if not isinstance(docs, list) or not docs:
        errors.append("documents must be a non-empty list")
        return errors, warnings

    doc_ids = set()
    for i, d in enumerate(docs):
        tag = f"documents[{i}] ({d.get('doc_id','?')})"
        for k in REQUIRED_DOC:
            if k not in d or d[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if d.get("doc_type") not in ALLOWED_DOC_TYPES:
            errors.append(f"{tag}: doc_type must be one of {sorted(ALLOWED_DOC_TYPES)}, got {d.get('doc_type')!r}")
        did = d.get("doc_id")
        if did in doc_ids:
            errors.append(f"{tag}: duplicate doc_id")
        doc_ids.add(did)

    fields = doc.get("extracted_fields") or []
    if not isinstance(fields, list) or not fields:
        errors.append("extracted_fields must be a non-empty list")
        return errors, warnings

    seen_fields = set()
    for i, f in enumerate(fields):
        tag = f"extracted_fields[{i}] ({f.get('field','?')})"
        for k in REQUIRED_FIELD:
            if k not in f or f[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if f.get("doc_id") not in doc_ids:
            errors.append(f"{tag}: doc_id {f.get('doc_id')!r} not in documents[]")
        conf = f.get("confidence")
        if isinstance(conf, (int, float)) and conf < LOW_CONFIDENCE:
            warnings.append(f"{tag}: low extraction confidence {conf} — verify against the source document")
        seen_fields.add(f.get("field"))

    cfg = doc.get("config") or {}
    if not cfg:
        warnings.append("no 'config' block — default appetite thresholds will be used; record the config_version")
    critical = cfg.get("critical_fields") or ["insured_state", "class_code", "effective_date", "total_insured_value"]
    for cf in critical:
        if cf not in seen_fields:
            warnings.append(f"critical field '{cf}' not extracted from any document — triage will be blocked pending broker information")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "submission_example.json"
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
