#!/usr/bin/env python3
"""Deterministic input validation for claim-settlement-authority-request-builder.

Input schema (JSON): claim{claim_id,claim_type,adjuster}; evaluation{indemnity_estimate,
expense_estimate,currency,basis_note}; authority_matrix{tiers[{tier,max_amount,approver_role}],
config_version}; evidence_refs[{ref,description}]; checklist{required_items[]}.

Usage: python validate_input.py claim.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _num(v):
    try:
        from insurance_contract import amount

        return float(amount(v))
    except (TypeError, ValueError):
        return None


def _validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("claim", "evaluation", "authority_matrix", "checklist"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    if not doc["claim"].get("claim_id"):
        errors.append("claim missing 'claim_id'")
    ev = doc["evaluation"]
    for k in ("indemnity_estimate", "expense_estimate"):
        if _num(ev.get(k)) is None:
            errors.append(f"evaluation.{k} not numeric (exposure is taken from the evaluation, never assumed)")
    tiers = doc["authority_matrix"].get("tiers")
    if not isinstance(tiers, list) or not tiers:
        errors.append("authority_matrix.tiers must be a non-empty list")
    else:
        for i, t in enumerate(tiers):
            if _num(t.get("max_amount")) is None:
                errors.append(f"authority_matrix.tiers[{i}]: max_amount not numeric")
            if not t.get("approver_role"):
                errors.append(f"authority_matrix.tiers[{i}]: missing approver_role")
    if not isinstance(doc["checklist"].get("required_items"), list):
        errors.append("checklist.required_items must be a list")
    if not doc["authority_matrix"].get("config_version"):
        warnings.append("authority_matrix.config_version missing — record the versioned matrix used")
    return errors, warnings


def validate(doc: dict) -> tuple[list[str], list[str]]:
    if not isinstance(doc, dict):
        return ["input must be an object"], []
    try:
        errors, warnings = _validate(doc)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        return ["malformed input: " + str(exc)], []
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
