#!/usr/bin/env python3
"""Deterministic input validation for investment-record-normalizer.

Validates a multi-source ingest bundle before canonical normalization. Fails closed on
structural problems that would corrupt lineage (missing envelope fields, non-dict payloads,
duplicate source keys); warns on gaps that will send a record to the rejected-record queue
at transform time rather than silently dropping or guessing.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Envelope:
  bundle_id, as_of (YYYY-MM-DD), ruleset_version, records[
    {source_system, record_type, source_record_id, source_as_of, payload{...raw fields...}}
  ]

The validator NEVER merges, dedupes, or rewrites source records. It only reports structural
readiness; the transform maps each record 1:1 and routes anything unmappable to the queue.

Usage:
  python validate_input.py bundle.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("bundle_id", "as_of", "ruleset_version", "records")
REQUIRED_REC = ("source_system", "record_type", "source_record_id", "source_as_of", "payload")
KNOWN_SYSTEMS = {"custodian", "administrator", "oms", "accounting"}
KNOWN_TYPES = {"position", "cash", "order", "transaction"}


def _validate_shape(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if not isinstance(doc, dict):
        return ["top-level document must be a JSON object"], warnings
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    recs = doc.get("records")
    if not isinstance(recs, list) or not recs:
        errors.append("records must be a non-empty list")
        return errors, warnings

    # (source_system, source_record_id) must be unique: it is the lineage key. A collision
    # would make one canonical record's provenance ambiguous, so it is a hard error.
    seen_keys = set()
    for i, r in enumerate(recs):
        tag = f"records[{i}] ({r.get('source_system','?')}/{r.get('source_record_id','?')})"
        if not isinstance(r, dict):
            errors.append(f"{tag}: record must be an object")
            continue
        for k in REQUIRED_REC:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if not isinstance(r.get("payload"), dict):
            errors.append(f"{tag}: payload must be an object")
        if not DATE_RE.match(str(r.get("source_as_of", ""))):
            errors.append(f"{tag}: source_as_of must start YYYY-MM-DD")
        key = (r.get("source_system"), r.get("source_record_id"))
        if key in seen_keys:
            errors.append(f"{tag}: duplicate lineage key (source_system, source_record_id) — ambiguous provenance")
        seen_keys.add(key)
        if r.get("source_system") not in KNOWN_SYSTEMS:
            warnings.append(f"{tag}: source_system not in {sorted(KNOWN_SYSTEMS)} — will reject as UNMAPPED_SOURCE_SYSTEM")
        if r.get("record_type") not in KNOWN_TYPES:
            warnings.append(f"{tag}: record_type not in {sorted(KNOWN_TYPES)} — will reject as UNMAPPED_RECORD_TYPE")

    if not doc.get("ruleset"):
        warnings.append("no inline 'ruleset' block — the default versioned mapping ruleset will be used; record ruleset_version")
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
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "source_bundle.json"
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
    print(f"input validation: {len(warnings)} warning(s), {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
