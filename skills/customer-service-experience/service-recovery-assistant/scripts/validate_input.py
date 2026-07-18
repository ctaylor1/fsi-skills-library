#!/usr/bin/env python3
"""Deterministic input validation for service-recovery-assistant.

Validates a service-failure case file before drafting. Fails closed on structural problems;
warns on data gaps that will force a `needs-data` disposition or a specialist referral.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, config_overrides{}, precedent_cases[], cases[
    {case_id, customer_id, failure_type, failure_date, source_refs[],
     severity_inputs{service_down_hours, repeat_failure, commitment_missed},
     customer_impact{financial_detriment, distress_level, inconvenience_level},
     customer{tenure_years, vulnerability_flag, segment},
     financial_detriment_documented, policy_refs[]}]

Usage: python validate_input.py cases.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "cases")
REQUIRED_CASE = ("case_id", "customer_id", "failure_type", "failure_date", "source_refs")
DISTRESS = {"high", "medium", "low", "none"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    cases = doc.get("cases") or []
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, c in enumerate(cases):
        tag = f"cases[{i}] ({c.get('case_id','?')})"
        for k in REQUIRED_CASE:
            if k not in c or c[k] in (None, "", []):
                errors.append(f"{tag}: missing '{k}'")
        cid = c.get("case_id")
        if cid in ids:
            errors.append(f"{tag}: duplicate case_id")
        ids.add(cid)

        if c.get("failure_type") == "formal_complaint":
            warnings.append(f"{tag}: formal_complaint -> refer to complaint-resolution-assistant (not drafted here)")
            continue

        ci = c.get("customer_impact")
        if ci is None:
            warnings.append(f"{tag}: no customer_impact -> needs-data")
            continue
        if ci.get("distress_level") not in DISTRESS:
            warnings.append(f"{tag}: distress_level missing/invalid -> needs-data")
        fd = float(ci.get("financial_detriment") or 0)
        if fd > 0 and not c.get("financial_detriment_documented"):
            warnings.append(f"{tag}: financial_detriment ${fd:.2f} not documented -> needs-data (no redress proposed)")
        if (c.get("customer") or {}).get("vulnerability_flag"):
            warnings.append(f"{tag}: vulnerability flag set -> Tier 3 approval and vulnerable-customer-support-assistant referral")
        if not c.get("policy_refs"):
            warnings.append(f"{tag}: no policy_refs -> communication will lack policy grounding (review before delivery)")

    if doc.get("precedent_cases") is None:
        warnings.append("no precedent_cases provided -> consistency/precedent context limited")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "cases_example.json"
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
