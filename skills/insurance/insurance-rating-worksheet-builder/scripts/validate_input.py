#!/usr/bin/env python3
"""Deterministic input validation for insurance-rating-worksheet-builder.

Input schema (JSON): policy{policy_id,line,effective_date}; risk{characteristics{}}; rate_manual{
min_premium,policy_fees[{name,amount}],config_version}; coverages[{coverage,base_rate,
factors[{name,value}],fees[{name,amount}]}].

Usage: python validate_input.py rating.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys, math
from pathlib import Path


def _num(v):
    try:
        return float(v) if not isinstance(v, bool) and math.isfinite(float(v)) else None
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("policy", "rate_manual", "coverages"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    if not doc["policy"].get("policy_id"):
        errors.append("policy missing 'policy_id'")
    covs = doc.get("coverages") or []
    if not isinstance(covs, list) or not covs:
        errors.append("coverages must be a non-empty list")
        return errors, warnings
    for i, c in enumerate(covs):
        tag = f"coverages[{i}] ({c.get('coverage','?')})"
        if _num(c.get("base_rate")) is None:
            errors.append(f"{tag}: base_rate not numeric (never assumed)")
        for j, f in enumerate(c.get("factors") or []):
            if _num(f.get("value")) is None:
                errors.append(f"{tag}: factor[{j}] ({f.get('name','?')}) value not numeric")
            if not f.get("name"):
                warnings.append(f"{tag}: factor[{j}] missing name")
    if _num(doc["rate_manual"].get("min_premium")) is None:
        errors.append("rate_manual.min_premium must be explicit numeric, including zero when no floor applies")
    if not doc["rate_manual"].get("config_version"):
        errors.append("rate_manual.config_version missing — record the versioned manual used")
    for owner in [doc["rate_manual"]] + covs:
        for fee in owner.get("fees", owner.get("policy_fees", [])):
            if _num(fee.get("amount")) is None:
                errors.append("fee amount must be finite numeric")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "rating_example.json"
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
