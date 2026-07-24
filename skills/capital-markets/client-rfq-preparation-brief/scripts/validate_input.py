#!/usr/bin/env python3
"""Deterministic input validation for client-rfq-preparation-brief.

Input schema (JSON): rfq{rfq_id,client_id,instrument{instrument_id,type,notional,currency,side}};
client_context{tier,kyc_status,jurisdiction,restricted_products[]}; prior_activity[{date,
instrument,side,notional}]; checklist{required_sections[],config_version}.

Usage: python validate_input.py rfq.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("rfq", "client_context", "checklist"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    rfq = doc["rfq"]
    if not rfq.get("rfq_id"):
        errors.append("rfq missing 'rfq_id'")
    if not rfq.get("client_id"):
        errors.append("rfq missing 'client_id'")
    instr = rfq.get("instrument")
    if not isinstance(instr, dict) or not instr.get("type"):
        errors.append("rfq.instrument.type missing")
    if not isinstance(doc["checklist"].get("required_sections"), list):
        errors.append("checklist.required_sections must be a list")
    if not doc["client_context"].get("kyc_status"):
        warnings.append("client_context.kyc_status missing — suitability section incomplete; eligibility not assumed")
    if "prior_activity" not in doc:
        warnings.append("no prior_activity provided — prior-activity section will be empty")
    if not doc["checklist"].get("config_version"):
        warnings.append("checklist.config_version missing — record the versioned suitability policy used")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "rfq_example.json"
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
