#!/usr/bin/env python3
"""Deterministic input validation for insurance-fraud-referral-reviewer.

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

import json
import sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("config_version", "claims")
REQUIRED_CLAIM = ("claim_id", "insured_id", "policy_ref", "peril", "loss_date", "report_date", "source_ref")


def _isdate(v) -> bool:
    try:
        date.fromisoformat(str(v))
        return True
    except (ValueError, TypeError):
        return False


def _validate(doc: dict) -> tuple[list[str], list[str]]:
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


def validate(doc: dict) -> tuple[list[str], list[str]]:
    if not isinstance(doc, dict):
        return ["input must be an object"], []
    try:
        errors, warnings = _validate(doc)
        from insurance_contract import amount

        for c in doc.get("claims", []):
            for k in ("prior_claims_24m", "statement_inconsistencies"):
                if c.get(k) is not None:
                    try:
                        number = amount(c[k])
                        if number < 0 or number != int(number):
                            raise ValueError("invalid count")
                    except ValueError:
                        errors.append(k + " must be a nonnegative integer or null")
            for k in (
                "reportable_loss",
                "police_report",
                "documentation_complete",
                "coverage_lapse_reinstatement",
                "prior_siu_flag",
            ):
                if c.get(k) is not None and not isinstance(c[k], bool):
                    errors.append(k + " must be boolean or null")
            if not isinstance(c.get("counterevidence", []), list) or any(
                not isinstance(e, dict) or not e.get("source_ref") or not e.get("description")
                for e in c.get("counterevidence", [])
            ):
                errors.append("counterevidence requires source_ref and description")
        cfg = doc.get("indicator_config") or {}
        try:
            refer, monitor = amount(cfg.get("refer_min", 6)), amount(cfg.get("monitor_min", 3))
            if not refer > monitor > 0:
                raise ValueError("invalid threshold ordering")
            for k, value in cfg.items():
                if k != "weights" and amount(value) < 0:
                    raise ValueError("negative threshold")
            for value in cfg.get("weights", {}).values():
                if amount(value) < 0:
                    raise ValueError("negative weight")
        except (ValueError, TypeError):
            errors.append("invalid fraud threshold/weight configuration")
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        return ["malformed input: " + str(exc)], []
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
