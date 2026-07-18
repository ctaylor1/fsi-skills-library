#!/usr/bin/env python3
"""Deterministic input validation for three-statement-model-builder.

Validates a model-input file before the integrated model is built. Fails closed on
structural problems (missing statements, non-numeric line items, missing required drivers);
warns on data-quality issues that affect model quality but do not block a build (missing
driver provenance, a historical balance sheet that does not tie, an unusually long horizon).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  company, as_of (YYYY-MM-DD), config_version, forecast_years (int),
  historical{year, income_statement{revenue,cogs,opex,depreciation,interest_expense,tax,net_income},
             balance_sheet{cash,accounts_receivable,inventory,other_current_assets,ppe_net,
                           other_assets,accounts_payable,other_current_liabilities,debt,
                           other_liabilities,equity}},
  drivers{<name>: number | {value, source}},
  scenarios{base,upside,downside:{revenue_growth_delta,gross_margin_delta}}

Usage:
  python validate_input.py model_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise. Prints a line ending "N error(s)".
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("company", "as_of", "config_version", "forecast_years", "historical", "drivers")
REQUIRED_IS = ("revenue", "cogs", "opex", "depreciation", "interest_expense", "tax", "net_income")
REQUIRED_BS = (
    "cash", "accounts_receivable", "inventory", "other_current_assets", "ppe_net",
    "other_assets", "accounts_payable", "other_current_liabilities", "debt",
    "other_liabilities", "equity",
)
REQUIRED_DRIVERS = (
    "revenue_growth", "gross_margin", "opex_pct_revenue", "depreciation_rate",
    "capex_pct_revenue", "dso", "dio", "dpo", "other_current_assets_pct_revenue",
    "other_current_liabilities_pct_revenue", "tax_rate", "interest_rate",
    "debt_repayment", "dividend_payout_ratio",
)
BALANCE_TOL = 0.01  # in the model's units (e.g. millions)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _driver_value(d):
    if isinstance(d, dict):
        return _num(d.get("value"))
    return _num(d)


def _driver_source(d):
    if isinstance(d, dict):
        return str(d.get("source", "")).strip()
    return ""


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    n = doc.get("forecast_years")
    if not isinstance(n, int) or n < 1:
        errors.append(f"forecast_years must be an integer >= 1, got {n!r}")
    elif n > 10:
        warnings.append(f"forecast_years={n} is a long horizon (>10); forecast confidence degrades")

    hist = doc.get("historical") or {}
    is_ = hist.get("income_statement") or {}
    bs = hist.get("balance_sheet") or {}
    if "year" not in hist or _num(hist.get("year")) is None:
        errors.append("historical.year missing or non-numeric")
    for k in REQUIRED_IS:
        if k not in is_ or _num(is_.get(k)) is None:
            errors.append(f"historical.income_statement missing/non-numeric '{k}'")
    for k in REQUIRED_BS:
        if k not in bs or _num(bs.get(k)) is None:
            errors.append(f"historical.balance_sheet missing/non-numeric '{k}'")

    drivers = doc.get("drivers") or {}
    for k in REQUIRED_DRIVERS:
        if k not in drivers:
            errors.append(f"missing required driver '{k}'")
        elif _driver_value(drivers[k]) is None:
            errors.append(f"driver '{k}' value is not numeric")
        elif not _driver_source(drivers[k]):
            warnings.append(f"driver '{k}' has no source — provenance check will fail at output unless supplied")

    if errors:
        return errors, warnings

    # historical balance-sheet tie (data-quality warning; the model inherits any imbalance)
    total_assets = sum(_num(bs[k]) for k in (
        "cash", "accounts_receivable", "inventory", "other_current_assets", "ppe_net", "other_assets"))
    total_le = sum(_num(bs[k]) for k in (
        "accounts_payable", "other_current_liabilities", "debt", "other_liabilities", "equity"))
    resid = round(total_assets - total_le, 6)
    if abs(resid) > BALANCE_TOL:
        warnings.append(
            f"historical balance sheet does not tie (assets {total_assets:.2f} vs L+E {total_le:.2f}, "
            f"residual {resid:.2f}); forecast tie-outs will inherit this imbalance")

    # driver sanity ranges (warnings only; thresholds are documented, not judgments)
    gm = _driver_value(drivers.get("gross_margin"))
    if gm is not None and not (0.0 < gm < 1.0):
        warnings.append(f"gross_margin={gm} outside (0,1) — check units (fraction, not percent)")
    tr = _driver_value(drivers.get("tax_rate"))
    if tr is not None and not (0.0 <= tr < 1.0):
        warnings.append(f"tax_rate={tr} outside [0,1) — check units")

    scen = doc.get("scenarios") or {}
    if scen and not all(s in scen for s in ("base", "upside", "downside")):
        warnings.append("scenarios present but missing one of base/upside/downside; defaults will be used")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_input_example.json"
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
