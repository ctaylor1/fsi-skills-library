#!/usr/bin/env python3
"""Deterministic input validation for claims-fraud-referral-assistant.

Validates a claim-candidate file before fraud-indicator scoring. Fails closed on structural
problems; warns on data gaps that force a `needs-data` recommendation (never guessed away).

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, indicator_config{}, claims[
    {claim_id, insured_id, policy_ref, peril, loss_date, report_date,
     policy_inception_date, coverage_increase_date, claim_amount, prior_claims_24m,
     police_report, reportable_loss, documentation_complete, statement_inconsistencies,
     coverage_lapse_reinstatement, prior_siu_flag, source_ref, adjuster_notes_ref}]

Usage: python validate_input.py claims.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("config_version", "claims")
REQUIRED_CLAIM = ("claim_id", "insured_id", "policy_ref", "peril", "loss_date",
                  "report_date", "source_ref")


def _isdate(v) -> bool:
    try:
        date.fromisoformat(str(v))
        return True
    except (ValueError, TypeError):
        return False


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    claims = doc.get("claims") or []
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, c in enumerate(claims):
        tag = f"claims[{i}] ({c.get('claim_id', '?')})"
        for k in REQUIRED_CLAIM:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        cid = c.get("claim_id")
        if cid in ids:
            errors.append(f"{tag}: duplicate claim_id")
        ids.add(cid)
        for k in ("loss_date", "report_date"):
            if c.get(k) and not _isdate(c[k]):
                errors.append(f"{tag}: '{k}' is not an ISO date (yyyy-mm-dd)")
        if _isdate(c.get("loss_date")) and _isdate(c.get("report_date")):
            if date.fromisoformat(c["report_date"]) < date.fromisoformat(c["loss_date"]):
                errors.append(f"{tag}: report_date precedes loss_date")
        # data gaps that force needs-data (not hard errors)
        if not _isdate(c.get("policy_inception_date")):
            warnings.append(f"{tag}: policy_inception_date missing/invalid -> needs-data")
        if c.get("reportable_loss") is None:
            warnings.append(f"{tag}: reportable_loss classification missing -> needs-data")
        if c.get("documentation_complete") is None:
            warnings.append(f"{tag}: documentation_complete unknown -> DOC-GAP indicator not evaluable")
    if doc.get("indicator_config") is None:
        warnings.append("no indicator_config provided -> using default versioned weights")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "claims_example.json"
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
