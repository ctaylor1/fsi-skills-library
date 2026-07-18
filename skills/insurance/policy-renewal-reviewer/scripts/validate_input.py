#!/usr/bin/env python3
"""Deterministic input validation for policy-renewal-reviewer.

Validates a renewal comparison file before the findings engine runs. Fails closed on
structural problems; warns on data-quality gaps that limit which findings are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  policy_id, as_of (YYYY-MM-DD), config_version, line_of_business, review_window_days,
  expiring{term_effective, annual_premium, coverages[{coverage,limit,deductible}],
           exposures[{basis,value}], forms[{form_id,edition}], source_ref},
  proposed{...same shape...},
  claims[{claim_id,date_of_loss,incurred,paid,status,cause,source_ref}],
  config{...thresholds...}

Usage:
  python validate_input.py renewal.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("policy_id", "as_of", "config_version", "expiring", "proposed")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _check_term(label: str, term, errors: list, warnings: list) -> None:
    if not isinstance(term, dict):
        errors.append(f"{label} must be an object")
        return
    if _num(term.get("annual_premium")) is None:
        errors.append(f"{label}.annual_premium missing or not numeric")
    if not term.get("source_ref"):
        warnings.append(f"{label}.source_ref missing — evidence citations will be unanchored")
    covs = term.get("coverages")
    if not isinstance(covs, list) or not covs:
        warnings.append(f"{label}.coverages empty — limit/deductible/coverage findings not evaluable")
    else:
        for i, c in enumerate(covs):
            tag = f"{label}.coverages[{i}] ({c.get('coverage','?')})"
            if not c.get("coverage"):
                errors.append(f"{tag}: missing 'coverage' name")
            if _num(c.get("limit")) is None:
                warnings.append(f"{tag}: no numeric 'limit' — limit_reduced not evaluable for this row")
            if _num(c.get("deductible")) is None:
                warnings.append(f"{tag}: no numeric 'deductible' — deductible_increased not evaluable for this row")
    if not term.get("exposures"):
        warnings.append(f"{label}.exposures empty — exposure_change and rate_exposure_divergence not evaluable")
    if not term.get("forms"):
        warnings.append(f"{label}.forms empty — form_endorsement_change not evaluable")


def validate(doc: dict) -> tuple:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    _check_term("expiring", doc.get("expiring"), errors, warnings)
    _check_term("proposed", doc.get("proposed"), errors, warnings)

    claims = doc.get("claims")
    if not claims:
        warnings.append("no claims provided — loss_ratio_flag and large_open_claim not evaluable")
    elif not isinstance(claims, list):
        errors.append("claims must be a list when present")
    else:
        seen = set()
        for i, c in enumerate(claims):
            tag = f"claims[{i}] ({c.get('claim_id','?')})"
            if not c.get("claim_id"):
                errors.append(f"{tag}: missing 'claim_id'")
            if _num(c.get("incurred")) is None:
                warnings.append(f"{tag}: no numeric 'incurred' — treated as 0 in loss ratio")
            if not c.get("source_ref"):
                warnings.append(f"{tag}: no 'source_ref' — claim evidence will be unanchored")
            cid = c.get("claim_id")
            if cid in seen:
                errors.append(f"{tag}: duplicate claim_id")
            seen.add(cid)

    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "renewal_example.json"
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
