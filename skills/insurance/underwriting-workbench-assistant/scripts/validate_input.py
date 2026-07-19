#!/usr/bin/env python3
"""Deterministic input validation for underwriting-workbench-assistant.

Validates a submission batch before the workbench is compiled. Fails closed on structural
problems (missing authority context, malformed submissions); warns on data gaps that will
force a `needs-data` disposition rather than guessing the risk.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, as_of_date (ISO), rules_config?{}, authority{underwriter_id,
  binding_authority_tiv, binding_authority_limit, appetite_classes[]},
  submissions[{submission_id, occupancy_class, tiv, requested_limit, line_of_business,
    insured_name_masked, risk_sections{entity, property, exposure, loss_history,
    catastrophe, financial, third_party -> {present, as_of, source_ref, ...}}}]

Usage: python validate_input.py submissions.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("config_version", "as_of_date", "authority", "submissions")
REQUIRED_AUTH = ("binding_authority_tiv", "binding_authority_limit", "appetite_classes")
REQUIRED_SUB = ("submission_id", "occupancy_class", "tiv", "requested_limit", "risk_sections")
REQUIRED_SECTIONS = ("entity", "property", "exposure", "loss_history",
                     "catastrophe", "financial", "third_party")
CRITICAL_SECTIONS = ("property", "catastrophe", "exposure")


def _iso_ok(s):
    try:
        date.fromisoformat(s)
        return True
    except Exception:
        return False


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not _iso_ok(doc.get("as_of_date")):
        errors.append(f"as_of_date must be ISO YYYY-MM-DD, got {doc.get('as_of_date')!r}")

    auth = doc.get("authority") or {}
    for k in REQUIRED_AUTH:
        if k not in auth or auth[k] in (None, ""):
            errors.append(f"authority: missing '{k}'")
    if "appetite_classes" in auth and not isinstance(auth["appetite_classes"], list):
        errors.append("authority.appetite_classes must be a list")

    subs = doc.get("submissions")
    if not isinstance(subs, list) or not subs:
        errors.append("submissions must be a non-empty list")
        return errors, warnings

    seen = set()
    for i, s in enumerate(subs):
        tag = f"submissions[{i}] ({s.get('submission_id','?')})"
        for k in REQUIRED_SUB:
            if k not in s or s[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        sid = s.get("submission_id")
        if sid in seen:
            errors.append(f"{tag}: duplicate submission_id")
        seen.add(sid)
        for k in ("tiv", "requested_limit"):
            if k in s and not isinstance(s[k], (int, float)):
                errors.append(f"{tag}: '{k}' must be numeric")
        sections = s.get("risk_sections") or {}
        for name in REQUIRED_SECTIONS:
            sec = sections.get(name)
            if not isinstance(sec, dict) or sec.get("present") is False \
                    or not sec.get("source_ref") or not sec.get("as_of"):
                sev = "needs-data (critical)" if name in CRITICAL_SECTIONS else "needs-data"
                warnings.append(f"{tag}: section '{name}' missing/incomplete -> {sev}")
            elif not _iso_ok(sec.get("as_of")):
                errors.append(f"{tag}: section '{name}' as_of not ISO date: {sec.get('as_of')!r}")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "submissions_example.json"
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
