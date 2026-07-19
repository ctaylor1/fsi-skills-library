#!/usr/bin/env python3
"""Deterministic input validation for payment-fraud-case-investigator.

Validates a fraud case/alert bundle before investigation. Fails closed on structural
problems; warns on evidence gaps that force a `needs-evidence` disposition (a case is never
cleared by guessing over missing evidence).

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, rules_version, scoring_config{}, cases[
    {alert_id, customer_id, account_ref, channel, amount, currency, opened_at,
     primary_beneficiary_ref, transactions[{txn_id, ts, direction, amount, beneficiary_ref,
     source_ref}], timeline_events[{ts, type, detail, source_ref}],
     evidence{device{}, identity{}, behavior{}, transaction{}, beneficiary{}, network{}},
     flags{sanctions_adverse_media, app_scam_reported, bec_indicator},
     linked_fraud_case_ids[], prior_fraud_cases_180d, source_refs{...}}]

Usage: python validate_input.py cases.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "cases")
REQUIRED_CASE = ("alert_id", "customer_id", "channel", "opened_at", "source_refs")
REQUIRED_EVIDENCE = ("device", "identity", "behavior", "transaction", "beneficiary")
CHANNELS = {"card-cnp", "card-present", "wire", "rtp", "ach", "other"}


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
        tag = f"cases[{i}] ({c.get('alert_id','?')})"
        for k in REQUIRED_CASE:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        aid = c.get("alert_id")
        if aid in ids:
            errors.append(f"{tag}: duplicate alert_id")
        ids.add(aid)

        if c.get("channel") and c.get("channel") not in CHANNELS:
            warnings.append(f"{tag}: unrecognized channel '{c.get('channel')}' (treated as 'other')")

        srefs = c.get("source_refs") or {}
        if "case" not in srefs:
            errors.append(f"{tag}: source_refs.case is required (durable citation anchor)")

        evidence = c.get("evidence") or {}
        missing = [cat for cat in REQUIRED_EVIDENCE if not (evidence.get(cat) or {})]
        if missing:
            warnings.append(f"{tag}: incomplete evidence {missing} -> needs-evidence unless signals are decisive")
        for cat in REQUIRED_EVIDENCE:
            if cat in evidence and cat not in srefs:
                warnings.append(f"{tag}: evidence '{cat}' present but source_refs['{cat}'] missing -> citation will fall back to case")

        if not c.get("transactions"):
            warnings.append(f"{tag}: no transactions -> chronology will be sparse")
        for j, t in enumerate(c.get("transactions") or []):
            if not t.get("ts"):
                warnings.append(f"{tag}: transactions[{j}] missing 'ts' -> chronology ordering degraded")
            if not (t.get("txn_id") and t.get("source_ref")):
                warnings.append(f"{tag}: transactions[{j}] missing txn_id/source_ref -> weak transaction evidence")

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
