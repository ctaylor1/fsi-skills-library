#!/usr/bin/env python3
"""Deterministic input validation for payment-fraud-rule-impact-analyzer.

Input schema (JSON): rule_change{rule_id,current_rule{field,op,threshold},
proposed_rule{field,op,threshold},current_version,proposed_version}; sample{batch_id,
transactions[{txn_id,<field>,label}]}.

Usage: python validate_input.py sample.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

OPS = {">=", ">", "<=", "<", "=="}


def _check_rule(r, tag, errors):
    if not isinstance(r, dict):
        errors.append(f"{tag} must be an object")
        return
    if not r.get("field"):
        errors.append(f"{tag}.field missing")
    if r.get("op") not in OPS:
        errors.append(f"{tag}.op must be one of {sorted(OPS)}")
    try:
        float(r.get("threshold"))
    except (TypeError, ValueError):
        errors.append(f"{tag}.threshold not numeric")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("rule_change", "sample"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    rc = doc["rule_change"]
    if not rc.get("rule_id"):
        errors.append("rule_change missing 'rule_id'")
    _check_rule(rc.get("current_rule"), "rule_change.current_rule", errors)
    _check_rule(rc.get("proposed_rule"), "rule_change.proposed_rule", errors)
    txns = doc["sample"].get("transactions")
    if not isinstance(txns, list) or not txns:
        errors.append("sample.transactions must be a non-empty list")
        return errors, warnings
    cfield = (rc.get("current_rule") or {}).get("field")
    pfield = (rc.get("proposed_rule") or {}).get("field")
    unlabeled = 0
    for i, t in enumerate(txns):
        if t.get("txn_id") in (None, ""):
            errors.append(f"sample.transactions[{i}]: missing 'txn_id'")
        for f in {cfield, pfield}:
            if f and f not in t:
                errors.append(f"sample.transactions[{i}]: missing rule field '{f}'")
        if t.get("label") not in ("fraud", "legit"):
            unlabeled += 1
    if unlabeled:
        warnings.append(f"{unlabeled} transaction(s) unlabeled — excluded from confusion metrics")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[2] / "evals" / "files" / "sample_example.json"
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
