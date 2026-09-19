#!/usr/bin/env python3
"""Deterministic input validation for payment-api-log-diagnostic-pack.

Input schema (JSON): integration{integration_id,merchant,gateway,window}; taxonomy{code_map{},
next_checks{},config_version}; log_entries[{ts,endpoint,http_status,error_code,message,request_id}].

Usage: python validate_input.py logs.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQ_ENTRY = ("endpoint", "error_code", "request_id")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("integration", "taxonomy", "log_entries"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    if not doc["integration"].get("integration_id"):
        errors.append("integration missing 'integration_id'")
    if not isinstance(doc["taxonomy"].get("code_map"), dict):
        errors.append("taxonomy.code_map must be an object")
    entries = doc.get("log_entries") or []
    if not isinstance(entries, list) or not entries:
        errors.append("log_entries must be a non-empty list")
        return errors, warnings
    for i, e in enumerate(entries):
        for k in REQ_ENTRY:
            if e.get(k) in (None, ""):
                errors.append(f"log_entries[{i}]: missing '{k}'")
    if not doc["taxonomy"].get("config_version"):
        warnings.append("taxonomy.config_version missing — record the versioned taxonomy used")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "logs_example.json"
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
