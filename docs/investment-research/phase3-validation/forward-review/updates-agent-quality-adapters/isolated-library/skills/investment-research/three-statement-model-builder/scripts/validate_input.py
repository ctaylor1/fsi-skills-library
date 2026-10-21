#!/usr/bin/env python3
"""Bounded input validation for three-statement-model-builder.

Finite JSON numbers, typed shapes, dates, identifiers and method domains are checked.
Malformed inputs return validation errors. See references/domain-rules.md for supported scope.
"""
from __future__ import annotations
import json, re, sys, math
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
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def _driver_value(d):
    if isinstance(d, dict):
        return _num(d.get("value"))
    return _num(d)


def _driver_source(d):
    if isinstance(d, dict):
        return str(d.get("source", "")).strip()
    return ""


def _validate_native(doc: dict) -> tuple[list[str], list[str]]:
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


def _number(value):
    if isinstance(value, dict):
        value = value.get("value")
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def _base_domains(doc):
    from datetime import date
    errors = []
    for key in ("as_of", "as_of_date", "valuation_date"):
        if key in doc:
            try:
                date.fromisoformat(doc[key])
            except (TypeError, ValueError):
                errors.append(key + " must be an exact valid YYYY-MM-DD date")
    for key in ("company", "company_id", "entity_id", "config_version", "analysis_id", "model_id", "currency", "units"):
        if key in doc and (not isinstance(doc[key], str) or not doc[key].strip()):
            errors.append(key + " must be a nonempty string")
    return errors


def _unique(rows, field, label, errors):
    seen = set()
    for row in rows:
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(label + ": " + field + " must be a nonempty string")
        elif value in seen:
            errors.append(label + ": duplicate " + field + " " + value)
        else:
            seen.add(value)

def _phase1_shapes(doc):
    errors = []
    for key in ['historical', 'drivers', 'scenarios']:
        if key in doc and not isinstance(doc[key], dict):
            errors.append(key + " must be an object")
    for key in []:
        if key in doc and (not isinstance(doc[key], list) or any(not isinstance(row, dict) for row in doc[key])):
            errors.append(key + " must be a list of objects")
    if errors:
        return errors
    for key in ("income_statement", "balance_sheet"):
        if key in doc.get("historical", {}) and not isinstance(doc["historical"][key], dict):
            errors.append("historical." + key + " must be an object")
    return errors

def _phase1_domains(doc):
    errors = _base_domains(doc)
    n = doc["forecast_years"]
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 100:
        errors.append("forecast_years must be an integer in [1,100]")
    year = doc["historical"].get("year")
    if isinstance(year, bool) or not isinstance(year, int) or not 1900 <= year <= 9900:
        errors.append("historical.year must be an integer calendar year in [1900,9900]")
    d = {key: _number(value) for key, value in doc["drivers"].items()}
    if set(d) != set(REQUIRED_DRIVERS):
        errors.append("drivers must contain exactly the supported driver set")
    for key in REQUIRED_DRIVERS:
        if not _driver_source(doc["drivers"].get(key)):
            errors.append("driver " + key + " requires source provenance")
    if d.get("revenue_growth", -2) <= -1:
        errors.append("revenue_growth must exceed -1")
    for key in ("gross_margin", "opex_pct_revenue", "depreciation_rate", "tax_rate", "dividend_payout_ratio"):
        if d.get(key) is None or not 0 <= d[key] <= 1:
            errors.append(key + " must be in [0,1]")
    for key in set(REQUIRED_DRIVERS) - {"revenue_growth", "gross_margin", "opex_pct_revenue", "depreciation_rate", "tax_rate", "dividend_payout_ratio"}:
        if d.get(key) is None or d[key] < 0:
            errors.append(key + " must be nonnegative")
    bs = doc["historical"]["balance_sheet"]
    residual = sum(bs[k] for k in ("cash","accounts_receivable","inventory","other_current_assets","ppe_net","other_assets")) - sum(bs[k] for k in ("accounts_payable","other_current_liabilities","debt","other_liabilities","equity"))
    if abs(residual) > BALANCE_TOL:
        errors.append("historical balance sheet must reconcile before forecasting")
    if set(doc.get("scenarios", {})) != {"base", "upside", "downside"}:
        errors.append("explicit base/upside/downside scenario assumptions are required; no invented default deltas")
    for name, values in doc.get("scenarios", {}).items():
        if not isinstance(values, dict) or set(values) - {"revenue_growth_delta","gross_margin_delta"}:
            errors.append("unsupported scenario shape or driver delta: " + name)
            continue
        for key in ("revenue_growth_delta", "gross_margin_delta"):
            if _number(values.get(key)) is None:
                errors.append("scenario " + name + " requires numeric " + key)
        if errors:
            continue
        if d["revenue_growth"] + values["revenue_growth_delta"] <= -1 or not 0 <= d["gross_margin"] + values["gross_margin_delta"] <= 1:
            errors.append("scenario " + name + " resolved growth/margin outside supported domains")
        if name == "base" and any(values.values()):
            errors.append("base scenario deltas must be zero to match the base forecast")
    return errors

def _strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON object key: " + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError("non-finite JSON constant: " + value)
    return _read_json(text, object_pairs_hook=pairs, parse_constant=constant)

def _local_module(filename):
    import importlib.util
    spec = importlib.util.spec_from_file_location("_local_" + filename.replace(".", "_"), Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def validate(doc):
    """Reject invalid JSON/shapes without treating an exception as a passing validation."""
    if not isinstance(doc, dict):
        return ["input must be an object"], []
    try:
        _local_module("native_integrity.py").canonical_hash(doc)
        shape_errors = _phase1_shapes(doc)
        if shape_errors:
            return shape_errors, []
        errors, warnings = _validate_native(doc)
        if not errors:
            errors.extend(_phase1_domains(doc))
        return errors, warnings
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
        return ["invalid input: " + str(exc)], []

def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_input_example.json"
        doc = _strict_json(p.read_text(encoding="utf-8"))
    elif argv:
        doc = _strict_json(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = _strict_json(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


_main_checked = main

def main(argv):
    try:
        return _main_checked(argv)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        print("ERROR", str(exc), file=sys.stderr)
        return 1

_validate_phase1 = validate

def validate(doc):
    if isinstance(doc, dict) and doc.get('schema_version') == 'ir-phase2/1.0':
        try:
            _local_module('phase2_domain.py').validate_document(doc)
            return [], []
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
            return ['invalid Phase2 input: ' + str(exc)], []
    return _validate_phase1(doc)

def _read_json(raw, **options):
    """Reject duplicate object keys and nonfinite constants before binding."""
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('duplicate JSON object key: '+key)
            result[key]=value
        return result
    def constant(value): raise ValueError('non-finite JSON constant: '+value)
    options.setdefault('object_pairs_hook',pairs)
    options.setdefault('parse_constant',constant)
    return json.loads(raw,**options)


_phase2_json_main = main

def main(*args, **kwargs):
    try: return _phase2_json_main(*args, **kwargs)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:
        print('ERROR:', str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
