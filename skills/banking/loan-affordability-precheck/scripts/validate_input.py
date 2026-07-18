#!/usr/bin/env python3
"""Deterministic input validation for loan-affordability-precheck.

Validates a precheck input file before affordability computation. Fails closed on structural
problems; warns on data-quality gaps that make a metric indicative rather than reliable.

Input schema (JSON): see references/source-map.md. Key fields:
  applicant_id, as_of (YYYY-MM-DD), config_version,
  loan{type(mortgage|auto|personal), principal, annual_rate_pct, term_months,
       monthly_tax?, monthly_insurance?, monthly_hoa?},
  income{gross_monthly, other_monthly?, net_monthly?},
  obligations{existing_monthly_debt?, existing_housing_expense?, monthly_living_expenses?},
  config{...thresholds...}

Usage:
  python validate_input.py precheck.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("applicant_id", "as_of", "config_version", "loan", "income")
LOAN_TYPES = {"mortgage", "auto", "personal"}
REQUIRED_LOAN = ("type", "principal", "annual_rate_pct", "term_months")


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

    loan = doc.get("loan") or {}
    if not isinstance(loan, dict):
        errors.append("loan must be an object")
        return errors, warnings
    for k in REQUIRED_LOAN:
        if k not in loan or loan[k] in (None, ""):
            errors.append(f"loan: missing '{k}'")
    if loan.get("type") not in LOAN_TYPES:
        errors.append(f"loan.type must be one of {sorted(LOAN_TYPES)}, got {loan.get('type')!r}")
    principal = _num(loan.get("principal"))
    if principal is None or principal <= 0:
        errors.append("loan.principal must be a positive number")
    rate = _num(loan.get("annual_rate_pct"))
    if rate is None or rate < 0:
        errors.append("loan.annual_rate_pct must be a non-negative number")
    term = loan.get("term_months")
    if _num(term) is None or int(_num(term) or 0) <= 0:
        errors.append("loan.term_months must be a positive integer")

    income = doc.get("income") or {}
    gross = _num(income.get("gross_monthly"))
    if gross is None or gross <= 0:
        errors.append("income.gross_monthly must be a positive number")

    if errors:
        return errors, warnings

    obl = doc.get("obligations") or {}
    if not doc.get("obligations"):
        warnings.append("no 'obligations' block — existing debt/housing/living default to 0; DTI and residual will be optimistic")
    if income.get("net_monthly") in (None, ""):
        warnings.append("no income.net_monthly — residual income uses gross income and is indicative only")
    if _num(obl.get("monthly_living_expenses")) in (None, 0):
        warnings.append("no monthly_living_expenses — residual income does not net living costs and is optimistic")
    if loan.get("type") != "mortgage" and _num(obl.get("existing_housing_expense")) in (None, 0):
        warnings.append("non-mortgage loan with no existing_housing_expense — front-end DTI uses 0 housing cost")
    if loan.get("type") == "mortgage" and not _escrow_present(loan):
        warnings.append("mortgage with no tax/insurance/HOA — payment excludes escrow and understates housing cost")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def _escrow_present(loan: dict) -> bool:
    return any(_num(loan.get(k)) not in (None, 0)
              for k in ("monthly_tax", "monthly_insurance", "monthly_hoa"))


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "precheck_input.json"
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
