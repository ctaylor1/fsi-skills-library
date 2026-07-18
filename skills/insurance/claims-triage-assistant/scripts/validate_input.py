#!/usr/bin/env python3
"""Deterministic input validation for claims-triage-assistant.

Validates a claims intake file before triage. Fails closed on structural problems; warns on
data gaps that will force a `needs-data` / `needs-review` disposition rather than a guessed
triage outcome.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, triage_config{}, severity_map{}, claims[
    {claim_id, policy_id, product, claim_type, loss_date, reported_date,
     policy_period{from,to}, policy_status, estimated_exposure, injuries, fatality,
     litigation, fraud_indicators[], subrogation_potential, catastrophe_code,
     exclusion_hits[], parties[], liability_clear(bool|null), statutory_deadline_date,
     business_interruption, claimant{vulnerability_flag}, source_ref}]

Usage: python validate_input.py claims.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("config_version", "claims")
REQUIRED_CLAIM = ("claim_id", "policy_id", "claim_type", "loss_date", "reported_date", "source_ref")
LIABILITY_TYPES = {"bodily_injury_liability", "general_liability", "auto_liability",
                   "products_liability", "professional_liability"}


def _is_date(v):
    try:
        date.fromisoformat(str(v))
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

    claims = doc.get("claims") or []
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, c in enumerate(claims):
        tag = f"claims[{i}] ({c.get('claim_id','?')})"
        for k in REQUIRED_CLAIM:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        cid = c.get("claim_id")
        if cid in ids:
            errors.append(f"{tag}: duplicate claim_id")
        ids.add(cid)

        for df in ("loss_date", "reported_date"):
            if c.get(df) and not _is_date(c.get(df)):
                errors.append(f"{tag}: {df} not ISO yyyy-mm-dd")
        per = c.get("policy_period") or {}
        if not (per.get("from") and per.get("to")):
            warnings.append(f"{tag}: policy_period incomplete -> coverage-period screen skipped (confirm cover manually)")
        elif not (_is_date(per.get("from")) and _is_date(per.get("to"))):
            errors.append(f"{tag}: policy_period dates not ISO yyyy-mm-dd")
        if not isinstance(c.get("claimant") or {}, dict):
            errors.append(f"{tag}: claimant must be an object")

        # data-gap warnings (drive needs-data / needs-review, not a hard fail)
        if c.get("estimated_exposure") in (None, ""):
            warnings.append(f"{tag}: no estimated_exposure -> severity omits the exposure driver")
        if c.get("claim_type") in LIABILITY_TYPES and c.get("liability_clear") is None:
            warnings.append(f"{tag}: liability undetermined on a liability claim -> needs-review (human adjudication)")
        if c.get("fraud_indicators"):
            warnings.append(f"{tag}: fraud indicators present -> SIU referral (triage concludes no fraud)")
        if c.get("catastrophe_code"):
            warnings.append(f"{tag}: catastrophe event -> route to CAT/major-loss unit")
        if (c.get("claimant") or {}).get("vulnerability_flag"):
            warnings.append(f"{tag}: vulnerability indicator -> accommodation review before contact")

    if doc.get("severity_map") in (None, {}):
        warnings.append("no severity_map provided -> using engine defaults; confirm the approved claim-severity map at deployment")
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
