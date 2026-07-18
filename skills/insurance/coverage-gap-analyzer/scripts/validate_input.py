#!/usr/bin/env python3
"""Deterministic input validation for coverage-gap-analyzer.

Validates a needs-and-policy file before gap computation. Fails closed on structural
problems; warns on data-quality gaps that limit which gap types are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  profile_id, as_of (YYYY-MM-DD), config_version, jurisdiction,
  policy{policy_number, coverages[{coverage_id,type,limit,deductible,sublimits?,coinsurance?,source_ref}],
         exclusions[{exclusion_id,peril,source_ref}], endorsements[{endorsement_id,adds,source_ref}]},
  exposures[{exposure_id,category,value,peril?,required_coverage?,sublimit_category?,
             recommended_endorsement?,source_ref}],
  config{...thresholds...}

Usage:
  python validate_input.py needs_and_policy.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("profile_id", "as_of", "config_version", "policy", "exposures")
REQUIRED_EXP = ("exposure_id", "category", "value", "source_ref")
REQUIRED_COV = ("coverage_id", "type", "limit", "source_ref")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    policy = doc.get("policy")
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
        return errors, warnings
    coverages = policy.get("coverages")
    if not isinstance(coverages, list) or not coverages:
        errors.append("policy.coverages must be a non-empty list")
        return errors, warnings

    cov_types = set()
    for i, c in enumerate(coverages):
        tag = f"policy.coverages[{i}] ({c.get('coverage_id', '?')})"
        for k in REQUIRED_COV:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(c.get("limit")) is None:
            errors.append(f"{tag}: limit not numeric")
        cid = str(c.get("type", "")).lower()
        if cid in cov_types:
            warnings.append(f"{tag}: duplicate coverage type '{c.get('type')}' — first match is used")
        cov_types.add(cid)
        subs = c.get("sublimits")
        if subs is not None and not isinstance(subs, dict):
            errors.append(f"{tag}: sublimits must be an object of category->amount")

    exposures = doc.get("exposures")
    if not isinstance(exposures, list) or not exposures:
        errors.append("exposures must be a non-empty list")
        return errors, warnings

    ids = set()
    any_coinsurance = any(_num(c.get("coinsurance")) is not None for c in coverages)
    for i, e in enumerate(exposures):
        tag = f"exposures[{i}] ({e.get('exposure_id', '?')})"
        for k in REQUIRED_EXP:
            if k not in e or e[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if _num(e.get("value")) is None:
            errors.append(f"{tag}: value not numeric")
        eid = e.get("exposure_id")
        if eid in ids:
            errors.append(f"{tag}: duplicate exposure_id")
        ids.add(eid)
        if not e.get("peril"):
            warnings.append(f"{tag}: no peril — exclusion_match not evaluable for this exposure")
        if not e.get("required_coverage"):
            warnings.append(f"{tag}: no required_coverage — missing_coverage/limit/deductible not evaluable for this exposure")
        elif str(e.get("required_coverage")).lower() not in cov_types:
            # not an error: this is exactly a missing-coverage finding, computed downstream.
            pass

    if not policy.get("exclusions"):
        warnings.append("policy has no exclusions block — exclusion_match will find nothing")
    if not any_coinsurance:
        warnings.append("no coverage declares a coinsurance clause — coinsurance_shortfall not evaluable")
    if not any(e.get("recommended_endorsement") for e in exposures):
        warnings.append("no exposure declares a recommended_endorsement — endorsement_gap not evaluable")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "needs_and_policy_example.json"
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
