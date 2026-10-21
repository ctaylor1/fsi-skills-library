#!/usr/bin/env python3
"""Bounded input validation for dcf-modeler.

Finite JSON numbers, typed shapes, dates, identifiers and method domains are checked.
Malformed inputs return validation errors. See references/domain-rules.md for supported scope.
"""
from __future__ import annotations
import json, re, sys, math
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("company_id", "as_of", "valuation_date", "config_version",
                "base_year_revenue", "forecast_years", "shares_outstanding",
                "drivers", "wacc", "terminal")
DRIVER_KEYS = ("revenue_growth", "ebit_margin", "tax_rate", "da_pct_revenue",
               "capex_pct_revenue", "nwc_pct_of_revenue_change")


def _v(node):
    return _number(node)


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _prov_cite(node):
    if isinstance(node, dict):
        return (node.get("provenance") or "").strip(), (node.get("citation") or "").strip()
    return "", ""


def _validate_native(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if not DATE_RE.match(str(doc["valuation_date"])):
        errors.append(f"valuation_date must start YYYY-MM-DD, got {doc['valuation_date']!r}")

    fy = _int(doc["forecast_years"])
    if fy is None or fy <= 0:
        errors.append(f"forecast_years must be a positive integer, got {doc['forecast_years']!r}")
    elif fy > 10:
        warnings.append(f"forecast_years {fy} > 10 — long explicit horizons are low-confidence; "
                        f"consider a shorter forecast plus terminal value")
    if (_v(doc["base_year_revenue"]) or 0) <= 0:
        errors.append(f"base_year_revenue must be > 0, got {doc['base_year_revenue']!r}")
    if (_v(doc["shares_outstanding"]) or 0) <= 0:
        errors.append(f"shares_outstanding must be > 0, got {doc['shares_outstanding']!r}")

    # drivers
    drivers = doc.get("drivers") or {}
    for k in DRIVER_KEYS:
        if k not in drivers:
            errors.append(f"drivers.{k} is required")
            continue
        if _v(drivers[k]) is None:
            errors.append(f"drivers.{k} value is not numeric")
        prov, cite = _prov_cite(drivers[k])
        if not prov:
            warnings.append(f"drivers.{k} has no provenance — validate_output will reject the pack")
        if not cite:
            warnings.append(f"drivers.{k} has no citation — validate_output will reject the pack")
    tax = _v(drivers.get("tax_rate"))
    if tax is not None and not (0.0 <= tax < 1.0):
        warnings.append(f"drivers.tax_rate {tax} is outside [0,1) — check the input")

    # wacc
    w = doc.get("wacc") or {}
    wacc_val = None
    if "override" in w:
        wacc_val = _v(w["override"])
        if wacc_val is None:
            errors.append("wacc.override is not numeric")
    else:
        need = ("risk_free", "erp", "beta", "cost_of_debt_pretax", "weight_equity", "weight_debt")
        for k in need:
            if k not in w:
                errors.append(f"wacc.{k} is required when no wacc.override is given")
            elif _v(w[k]) is None:
                errors.append(f"wacc.{k} value is not numeric")
        we, wd = _v(w.get("weight_equity")), _v(w.get("weight_debt"))
        if we is not None and wd is not None and abs((we + wd) - 1.0) > 1e-6:
            warnings.append(f"wacc weights do not sum to 1 (equity {we} + debt {wd}); check the capital structure")
        if None not in (we, wd, _v(w.get("risk_free")), _v(w.get("erp")), _v(w.get("beta")),
                        _v(w.get("cost_of_debt_pretax"))) and tax is not None:
            ke = _v(w["risk_free"]) + _v(w["beta"]) * _v(w["erp"])
            kd_at = _v(w["cost_of_debt_pretax"]) * (1.0 - tax)
            wacc_val = we * ke + wd * kd_at

    # terminal
    term = doc.get("terminal") or {}
    method = term.get("method")
    if method not in ("gordon", "exit_multiple"):
        errors.append(f"terminal.method must be 'gordon' or 'exit_multiple', got {method!r}")
    if method == "gordon":
        g = _v(term.get("growth"))
        if g is None:
            errors.append("terminal.growth is required for the gordon method")
        elif wacc_val is not None and wacc_val - g <= 1e-9:
            warnings.append(f"WACC ({round(wacc_val,4)}) is not greater than terminal growth ({g}); "
                            f"the Gordon terminal value will be invalid")
    if method == "exit_multiple" and _v(term.get("exit_multiple")) is None:
        errors.append("terminal.exit_multiple is required for the exit_multiple method")

    # scenario adjustments (optional but expected for a 3-case model)
    sa = doc.get("scenario_adjustments") or {}
    for scen in ("upside", "downside"):
        if scen not in sa:
            warnings.append(f"no scenario_adjustments.{scen} — {scen} will equal the base case")

    # discounting convention
    conv = (doc.get("discounting") or {}).get("convention", "end_year")
    if conv not in ("end_year", "mid_year"):
        warnings.append(f"discounting.convention {conv!r} unrecognized — defaulting to end_year")

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
    for key in ['drivers', 'wacc', 'terminal', 'bridge', 'discounting', 'scenario_adjustments']:
        if key in doc and not isinstance(doc[key], dict):
            errors.append(key + " must be an object")
    for key in []:
        if key in doc and (not isinstance(doc[key], list) or any(not isinstance(row, dict) for row in doc[key])):
            errors.append(key + " must be a list of objects")
    if errors:
        return errors
    return errors

def _phase1_domains(doc):
    errors = _base_domains(doc)
    n = doc["forecast_years"]
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 100:
        errors.append("forecast_years must be an integer in [1,100]")
    for key in ("base_year_revenue", "shares_outstanding"):
        if _number(doc[key]) is None or _number(doc[key]) <= 0:
            errors.append(key + " must be a positive finite number")
    if doc.get("forecast_mode", "standalone-ratio-fcff") != "standalone-ratio-fcff":
        errors.append("only standalone-ratio-fcff forecasting is implemented; upstream model rows are not consumed")
    if "upstream_model_id" in doc or "forecast_rows" in doc:
        errors.append("no native upstream forecast adapter; map and review standalone assumptions explicitly")
    if set(doc["drivers"]) != set(DRIVER_KEYS):
        errors.append("drivers must contain exactly the supported standalone forecast driver set")
    d = {key: _number(value) for key, value in doc["drivers"].items()}
    for section in ("drivers", "wacc", "terminal", "bridge"):
        for key, node in doc.get(section, {}).items():
            if section == "terminal" and key == "method":
                continue
            if _number(node) is None:
                errors.append(section + "." + key + " must be a finite JSON number or sourced numeric node")
            if not isinstance(node, dict) or not node.get("provenance") or not node.get("citation"):
                errors.append(section + "." + key + " requires provenance and citation")
    if d.get("revenue_growth", -2) <= -1:
        errors.append("revenue_growth must exceed -1")
    if d.get("tax_rate") is None or not 0 <= d["tax_rate"] <= 1:
        errors.append("tax_rate must be in [0,1]")
    for key in ("da_pct_revenue", "capex_pct_revenue", "nwc_pct_of_revenue_change"):
        if d.get(key) is None or d[key] < 0:
            errors.append(key + " must be nonnegative")
    need = {"total_debt","cash_and_equivalents","minority_interest","preferred_equity","investments_associates"}
    if set(doc.get("bridge", {})) != need:
        errors.append("complete explicit equity bridge required, including sourced zeros; unknown is not zero")
    for key, value in doc.get("bridge", {}).items():
        if _number(value) is not None and _number(value) < 0:
            errors.append("bridge." + key + " must be nonnegative")
    w = doc["wacc"]
    if "override" in w:
        if set(w) != {"override"}:
            errors.append("WACC override cannot be combined with component inputs")
        rate = _number(w["override"])
    else:
        we, wd = _number(w["weight_equity"]), _number(w["weight_debt"])
        if not 0 <= we <= 1 or not 0 <= wd <= 1 or abs(we + wd - 1) > 1e-6:
            errors.append("capital weights must be in [0,1] and sum to one")
        rate = we * (_number(w["risk_free"]) + _number(w["beta"]) * _number(w["erp"])) + wd * _number(w["cost_of_debt_pretax"]) * (1-d["tax_rate"])
    if rate is None or rate <= 0:
        errors.append("WACC must be positive in this bounded method")
    term = doc["terminal"]
    if term.get("method") == "gordon" and (rate is None or _number(term.get("growth")) is None or rate <= _number(term["growth"]) or _number(term["growth"]) <= -1):
        errors.append("Gordon terminal value requires WACC > growth > -1")
    if term.get("method") == "exit_multiple" and (_number(term.get("exit_multiple")) is None or _number(term["exit_multiple"]) <= 0):
        errors.append("exit multiple must be positive")
    if doc.get("discounting", {}).get("convention", "end_year") not in ("end_year", "mid_year"):
        errors.append("unsupported discount convention")
    for name, changes in doc.get("scenario_adjustments", {}).items():
        if name not in ("upside", "downside") or not isinstance(changes, dict):
            errors.append("unsupported scenario adjustment shape")
            continue
        resolved = dict(d)
        for key, value in changes.items():
            if key not in DRIVER_KEYS or _number(value) is None:
                errors.append("unsupported/non-numeric scenario adjustment " + key)
            else:
                resolved[key] += value
        if resolved["revenue_growth"] <= -1 or not 0 <= resolved["tax_rate"] <= 1 or any(resolved[k] < 0 for k in ("da_pct_revenue","capex_pct_revenue","nwc_pct_of_revenue_change")):
            errors.append("scenario " + name + " resolves outside supported driver domains")
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
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "dcf_input_example.json"
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
