#!/usr/bin/env python3
"""Deterministic input validation for credit-memo-drafter.

Validates a credit-memo request bundle before a memo is drafted. Fails closed on structural
problems (a memo must not be assembled from an ill-formed or unsourced bundle); warns on data
gaps that force a `needs-data` outcome rather than a guessed figure.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  memo_id, policy_version, template_version,
  borrower{obligor_id, name_masked, entity_type, industry},
  facilities[{facility_id, type, amount, tenor_months, purpose, source_ref}],
  financial_spread{source_ref, spread_provider, periods[],
                   cfads, total_debt_service, total_debt, ebitda,
                   ratios{dscr, leverage}},
  collateral[{collateral_id, type, appraised_value, advance_rate, source_ref}],
  risk_rating{model, grade, source_ref},
  covenants[{covenant_id, type(min|max), threshold, tested_metric, source_ref}],
  policy_requirements[{requirement_id, description, applies, addressed_section}],
  exceptions[{exception_id, policy_ref, description, mitigant}],
  evidence[{ref, source}]

Usage: python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("memo_id", "policy_version", "template_version", "borrower",
                "facilities", "financial_spread")
REQUIRED_FACILITY = ("facility_id", "type", "amount", "source_ref")
REQUIRED_SPREAD = ("source_ref", "cfads", "total_debt_service", "total_debt", "ebitda")
COVENANT_TYPES = {"min", "max"}


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    borrower = doc.get("borrower") or {}
    if not borrower.get("obligor_id"):
        errors.append("borrower.obligor_id is required")

    facilities = doc.get("facilities") or []
    if not isinstance(facilities, list) or not facilities:
        errors.append("facilities must be a non-empty list")
    else:
        seen = set()
        for i, f in enumerate(facilities):
            tag = f"facilities[{i}] ({f.get('facility_id','?')})"
            for k in REQUIRED_FACILITY:
                if k not in f or f[k] in (None, ""):
                    errors.append(f"{tag}: missing '{k}'")
            if not _num(f.get("amount")) or float(f.get("amount") or 0) <= 0:
                errors.append(f"{tag}: amount must be a positive number")
            fid = f.get("facility_id")
            if fid in seen:
                errors.append(f"{tag}: duplicate facility_id")
            seen.add(fid)

    spread = doc.get("financial_spread") or {}
    for k in REQUIRED_SPREAD:
        if k not in spread:
            errors.append(f"financial_spread: missing '{k}'")
        elif k != "source_ref" and not _num(spread.get(k)):
            errors.append(f"financial_spread.{k} must be numeric")
    if _num(spread.get("total_debt_service")) and float(spread.get("total_debt_service") or 0) <= 0:
        errors.append("financial_spread.total_debt_service must be > 0 (DSCR denominator)")
    if _num(spread.get("ebitda")) and float(spread.get("ebitda") or 0) <= 0:
        warnings.append("financial_spread.ebitda <= 0 -> leverage undefined; repayment analysis needs-data")
    if not spread.get("spread_provider"):
        warnings.append("financial_spread.spread_provider not recorded (expected approved spread source)")

    for i, c in enumerate(doc.get("collateral") or []):
        tag = f"collateral[{i}] ({c.get('collateral_id','?')})"
        if not c.get("source_ref"):
            errors.append(f"{tag}: missing source_ref")
        if not _num(c.get("appraised_value")):
            errors.append(f"{tag}: appraised_value must be numeric")
        ar = c.get("advance_rate")
        if not _num(ar) or not (0 < float(ar) <= 1):
            errors.append(f"{tag}: advance_rate must be a fraction in (0, 1]")

    for i, c in enumerate(doc.get("covenants") or []):
        tag = f"covenants[{i}] ({c.get('covenant_id','?')})"
        if c.get("type") not in COVENANT_TYPES:
            errors.append(f"{tag}: type must be one of {sorted(COVENANT_TYPES)}")
        if not _num(c.get("threshold")) or not _num(c.get("tested_metric")):
            errors.append(f"{tag}: threshold and tested_metric must be numeric")
        if not c.get("source_ref"):
            errors.append(f"{tag}: missing source_ref (covenant must trace to the credit agreement)")

    if doc.get("risk_rating") is None or not (doc.get("risk_rating") or {}).get("grade"):
        warnings.append("risk_rating.grade missing -> risk-rating section will be needs-data")

    for i, e in enumerate(doc.get("exceptions") or []):
        tag = f"exceptions[{i}] ({e.get('exception_id','?')})"
        if not e.get("mitigant"):
            warnings.append(f"{tag}: exception has no mitigant -> memo cannot mark it addressed (needs-data)")

    for i, p in enumerate(doc.get("policy_requirements") or []):
        if p.get("applies") and not (p.get("addressed_section") or p.get("exception_ref")):
            warnings.append(f"policy_requirements[{i}] ({p.get('requirement_id','?')}): applicable but "
                            f"not mapped to a section or exception -> policy-coverage gap")

    if not doc.get("evidence"):
        warnings.append("no evidence[] provided -> citations will be sparse; verify source-to-memo traceability")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "memo_request_example.json"
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
