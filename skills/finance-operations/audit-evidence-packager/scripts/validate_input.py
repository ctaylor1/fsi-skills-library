#!/usr/bin/env python3
"""Deterministic input validation for audit-evidence-packager.

Validates an evidence-request / artifact-catalog file before a package is assembled. Fails
closed on structural problems; warns on data gaps that will force a `needs-data`,
`evidence-gap`, `evidence-stale`, `redaction-required`, or `custody-gap` outcome downstream.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, engagement{entity, framework, audit_period{from,to}, as_of_date, prepared_by,
    reviewed_by?}, remediation{request_id:{owner,target_date,severity}},
  artifacts[{artifact_id, type, as_of_date?, period{from,to}?, source_system, source_ref,
    chain_of_custody{source_system, prepared_by, extracted_on, checksum}, sensitive_fields[]?,
    redaction{applied, method, redacted_fields[], log_ref}?, superseded_by?, in_scope?}],
  requests[{request_id, title, control_ref?, period{from,to}, artifact_refs[],
    not_applicable?, na_justification?}]

Usage: python validate_input.py requests.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise. Final line ends "N error(s)".
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "engagement", "artifacts", "requests")
REQUIRED_ENGAGEMENT = ("entity", "audit_period", "as_of_date", "prepared_by")
CUSTODY_FIELDS = ("source_system", "prepared_by", "extracted_on", "checksum")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    e = doc.get("engagement") or {}
    for k in REQUIRED_ENGAGEMENT:
        if not str(e.get(k, "")).strip() and k != "audit_period":
            errors.append(f"engagement: missing '{k}'")
    ap = e.get("audit_period") or {}
    if not (ap.get("from") and ap.get("to")):
        errors.append("engagement.audit_period requires 'from' and 'to'")
    if e.get("as_of_date") and not DATE_RE.match(str(e.get("as_of_date"))):
        errors.append(f"engagement.as_of_date must be YYYY-MM-DD, got {e.get('as_of_date')!r}")

    # Artifacts + chain of custody.
    artifacts = doc.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must be a non-empty list")
        return errors, warnings
    artifact_ids = set()
    for i, a in enumerate(artifacts):
        aid = a.get("artifact_id")
        tag = f"artifacts[{i}] ({aid or '?'})"
        if not aid:
            errors.append(f"{tag}: missing artifact_id")
        elif aid in artifact_ids:
            errors.append(f"{tag}: duplicate artifact_id")
        artifact_ids.add(aid)
        for k in ("type", "source_ref"):
            if not str(a.get(k, "")).strip():
                errors.append(f"{tag}: missing '{k}'")
        eff = a.get("as_of_date")
        if eff and not DATE_RE.match(str(eff)):
            errors.append(f"{tag}: as_of_date must be YYYY-MM-DD, got {eff!r}")
        coc = a.get("chain_of_custody") or {}
        missing_coc = [k for k in CUSTODY_FIELDS if not str(coc.get(k, "")).strip()]
        if missing_coc:
            warnings.append(f"{tag}: incomplete chain_of_custody ({', '.join(missing_coc)}) -> custody-gap")
        sensitive = a.get("sensitive_fields") or []
        if sensitive:
            red = a.get("redaction") or {}
            if not red.get("applied"):
                warnings.append(f"{tag}: sensitive_fields flagged but redaction not applied -> redaction-required")
            else:
                unredacted = set(sensitive) - set(red.get("redacted_fields") or [])
                if unredacted:
                    warnings.append(f"{tag}: sensitive fields not fully redacted ({', '.join(sorted(unredacted))}) -> redaction-required")

    # Requests.
    reqs = doc.get("requests")
    if not isinstance(reqs, list) or not reqs:
        errors.append("requests must be a non-empty list")
        return errors, warnings
    seen = set()
    for i, r in enumerate(reqs):
        rid = r.get("request_id")
        tag = f"requests[{i}] ({rid or '?'})"
        if not rid:
            errors.append(f"{tag}: missing request_id")
        elif rid in seen:
            errors.append(f"{tag}: duplicate request_id")
        seen.add(rid)
        if not str(r.get("title", "")).strip():
            warnings.append(f"{tag}: missing title")
        per = r.get("period") or {}
        if not (per.get("from") and per.get("to")):
            warnings.append(f"{tag}: period missing from/to -> period coverage cannot be assessed")
        refs = r.get("artifact_refs") or []
        if r.get("not_applicable") and not str(r.get("na_justification", "")).strip():
            warnings.append(f"{tag}: marked N/A without na_justification -> needs-data")
        if not r.get("not_applicable") and not refs:
            warnings.append(f"{tag}: no artifact_refs -> needs-data")
        for aref in refs:
            if aref not in artifact_ids:
                warnings.append(f"{tag}: artifact_ref {aref!r} not in artifact catalog -> evidence-gap")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "requests_example.json"
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
