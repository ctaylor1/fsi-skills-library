#!/usr/bin/env python3
"""Source-bound output validation for three-statement-model-builder.

Requires separately retained original input (--input ORIGINAL). Reconstructs all fields
and retains bounded domain checks. Fidelity does not establish source truth, economic
validity, institutional approval or independent assurance.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

BALANCE_TOL = 0.01
DISCLAIMER = ("Model output for analytical support only; not investment advice or a "
              "recommendation to buy, sell, or hold any security.")
REQUIRED_DRIVERS = {
    "revenue_growth", "gross_margin", "opex_pct_revenue", "depreciation_rate",
    "capex_pct_revenue", "dso", "dio", "dpo", "other_current_assets_pct_revenue",
    "other_current_liabilities_pct_revenue", "tax_rate", "interest_rate",
    "debt_repayment", "dividend_payout_ratio",
}
# Advice / recommendation language an R2 model must never emit:
ADVICE_PATTERNS = [
    r"\bstrong buy\b", r"\bbuy rating\b", r"\bsell rating\b", r"\bprice target\b",
    r"\btarget price\b", r"\boverweight\b", r"\bunderweight\b", r"\bundervalued\b",
    r"\bovervalued\b", r"\bwe recommend\b", r"\brecommend (buying|selling|a position)\b",
    r"\bshould (buy|sell)\b", r"\bfair value (is|of)\b", r"\battractive (entry|valuation)\b",
    r"\binvestment recommendation\b", r"\brecommendation to (buy|sell|hold)\b",
]


def _n(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _by_year(rows):
    return {int(r["year"]): r for r in rows}


def _validate_rules(model: dict) -> list[str]:
    errors: list[str] = []

    is_rows = model.get("income_statement") or []
    bs_rows = model.get("balance_sheet") or []
    cf_rows = model.get("cash_flow") or []
    if not (is_rows and bs_rows and cf_rows):
        errors.append("model missing income_statement / balance_sheet / cash_flow rows")
        return errors
    if not (len(is_rows) == len(bs_rows) == len(cf_rows)):
        errors.append("statement row counts differ across income/balance/cash-flow")

    is_y, bs_y, cf_y = _by_year(is_rows), _by_year(bs_rows), _by_year(cf_rows)
    years = sorted(bs_y)

    base = model.get("base_snapshot") or {}
    prev_bs = base.get("balance_sheet") or {}
    _n(prev_bs.get("cash"))
    prev_equity = _n(prev_bs.get("equity"))
    prev_ppe = _n(prev_bs.get("ppe_net"))

    for y in years:
        bs, is_, cf = bs_y[y], is_y.get(y, {}), cf_y.get(y, {})
        # 1a. balance-sheet identity recomputed from components
        assets = sum(_n(bs.get(k), 0.0) for k in (
            "cash", "accounts_receivable", "inventory", "other_current_assets",
            "ppe_net", "other_assets"))
        liab = sum(_n(bs.get(k), 0.0) for k in (
            "accounts_payable", "other_current_liabilities", "debt", "other_liabilities"))
        equity = _n(bs.get("equity"), 0.0)
        resid = round(assets - (liab + equity), 6)
        if abs(resid) > BALANCE_TOL:
            errors.append(f"year {y}: balance sheet does not balance (residual {resid:.4f})")
        # 1b. cash tie
        if abs(round(_n(cf.get("ending_cash"), 0.0) - _n(bs.get("cash"), 0.0), 6)) > BALANCE_TOL:
            errors.append(f"year {y}: cash-flow ending cash does not tie to balance-sheet cash")
        # 1c. equity roll-forward (dividends stored negative in cash flow)
        if prev_equity is not None:
            exp_eq = round(prev_equity + _n(is_.get("net_income"), 0.0)
                           + _n(cf.get("dividends"), 0.0), 6)
            if abs(exp_eq - equity) > BALANCE_TOL:
                errors.append(f"year {y}: equity roll-forward breaks (expected {exp_eq:.4f}, got {equity:.4f})")
        # 1d. PP&E roll-forward (capex stored negative in cash flow)
        if prev_ppe is not None:
            exp_ppe = round(prev_ppe - _n(cf.get("capex"), 0.0) - _n(is_.get("depreciation"), 0.0), 6)
            if abs(exp_ppe - _n(bs.get("ppe_net"), 0.0)) > BALANCE_TOL:
                errors.append(f"year {y}: PP&E roll-forward breaks (expected {exp_ppe:.4f}, got {bs.get('ppe_net')})")
        prev_bs, prev_equity, prev_ppe = bs, equity, _n(bs.get("ppe_net"))

    # 2. assumption provenance
    assumptions = model.get("assumptions") or []
    covered = set()
    for a in assumptions:
        name = a.get("driver")
        covered.add(name)
        if not str(a.get("source", "")).strip():
            errors.append(f"assumption '{name}' has no source (provenance required)")
    missing = REQUIRED_DRIVERS - covered
    if missing:
        errors.append(f"assumptions missing required drivers: {', '.join(sorted(missing))}")

    # 3. scenario monotonicity on final-year revenue
    scen = {s.get("name"): s for s in (model.get("scenarios") or [])}
    if not all(k in scen for k in ("base", "upside", "downside")):
        errors.append("scenarios must include base, upside, and downside")
    else:
        up, ba, dn = (_n(scen["upside"].get("revenue")), _n(scen["base"].get("revenue")),
                      _n(scen["downside"].get("revenue")))
        if None in (up, ba, dn):
            errors.append("scenario revenue values missing/non-numeric")
        elif not (up >= ba - BALANCE_TOL and ba >= dn - BALANCE_TOL):
            errors.append(f"scenario revenue not monotone (upside {up} >= base {ba} >= downside {dn})")

    # 4. reproducibility
    for k in ("model_id", "config_version", "inputs_hash"):
        if not str(model.get(k, "")).strip():
            errors.append(f"missing reproducibility field '{k}'")

    # 5. no investment advice
    narrative = str(model.get("narrative", ""))
    scan_text = (narrative.replace(DISCLAIMER, "") + " " + str(model.get("notes", ""))).lower()
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, scan_text, re.I)
        if m:
            errors.append(f"investment-advice language detected: {m.group(0)!r} "
                          f"(R2 models do not advise, rate, or recommend)")
    if DISCLAIMER.lower() not in (narrative + " " + str(model.get("disclaimer", ""))).lower():
        errors.append("missing required no-advice disclaimer")

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

def validate(output, original_input=None):
    errors = []
    integrity = _local_module("native_integrity.py")
    calculator = _local_module("calculate_or_transform.py")
    integrity.validate_reconstruction(output, calculator.build, errors, original_input)
    # Existing domain checks operate only on a complete, source-bound reconstruction.
    if not errors and not (isinstance(original_input, dict) and original_input.get("schema_version") == "ir-phase2/1.0"):
        try:
            errors.extend(_validate_rules(output))
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
            errors.append("invalid output: " + str(exc))
    return errors

def main(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Validate against separately retained original input; source truth remains unverified.")
    parser.add_argument("output", nargs="?")
    parser.add_argument("--input", dest="original")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    fixtures = Path(__file__).resolve().parents[1] / "evals" / "files"
    if args.selftest:
        output_path, input_path = fixtures / 'model_example.json', fixtures / 'model_input_example.json'
    elif args.output and args.original:
        output_path, input_path = Path(args.output), Path(args.original)
    else:
        parser.error("output and --input ORIGINAL are required (or --selftest)")
    output = _strict_json(output_path.read_text(encoding="utf-8"))
    original = _strict_json(input_path.read_text(encoding="utf-8"))
    errors = validate(output, original)
    for error in errors:
        print("ERROR", error)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0

_main_checked = main

def main(argv):
    try:
        return _main_checked(argv)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        print("ERROR", str(exc), file=sys.stderr)
        return 1

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
