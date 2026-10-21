#!/usr/bin/env python3
"""Bounded input validation for comps-analysis-builder.

Finite JSON numbers, typed shapes, dates, identifiers and method domains are checked.
Malformed inputs return validation errors. See references/domain-rules.md for supported scope.
"""
from __future__ import annotations
import json, sys, math
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("config_version", "analysis_id", "as_of_date", "currency", "subject", "peers")
REQUIRED_COMPANY = ("ticker", "share_price", "diluted_shares", "source_ref")


def _num(v):
    return _number(v) is not None


def _days_old(as_of, price_date):
    try:
        return (date.fromisoformat(str(as_of)) - date.fromisoformat(str(price_date))).days
    except Exception:
        return None


def _check_company(tag, c, currency, as_of, max_age, errors, warnings, *, is_subject=False):
    for k in REQUIRED_COMPANY:
        if k not in c or c[k] in (None, ""):
            errors.append(f"{tag}: missing '{k}'")
    for k in ("share_price", "diluted_shares"):
        if k in c and not _num(c[k]):
            errors.append(f"{tag}: '{k}' must be numeric")
    if _num(c.get("diluted_shares")) and c.get("diluted_shares", 0) <= 0:
        errors.append(f"{tag}: diluted_shares must be > 0 (equity value would be undefined)")
    if c.get("currency") and currency and c.get("currency") != currency:
        warnings.append(f"{tag}: currency {c.get('currency')!r} != analysis currency {currency!r} "
                        f"-> FX normalization required before multiples are comparable (open-item)")
    ltm = c.get("ltm") or {}
    for m in ("revenue", "ebitda"):
        if not _num(ltm.get(m)):
            warnings.append(f"{tag}: ltm.{m} missing/non-numeric -> some multiples will be non-meaningful (open-item)")
    if _num(ltm.get("ebitda")) and ltm.get("ebitda", 0) <= 0:
        warnings.append(f"{tag}: ltm.ebitda <= 0 -> EV/EBITDA will be flagged non-meaningful (nm)")
    if not is_subject and c.get("include", True) and not c.get("rationale"):
        warnings.append(f"{tag}: included peer has no 'rationale' -> peer-inclusion rationale incomplete")
    if not c.get("include", True) and not c.get("exclude_reason"):
        warnings.append(f"{tag}: excluded peer has no 'exclude_reason' -> exclusion is not human-confirmable")
    pd = c.get("price_date")
    if not pd:
        warnings.append(f"{tag}: no price_date -> market-data freshness cannot be verified (stale/open-item)")
    else:
        age = _days_old(as_of, pd)
        if age is not None and age > max_age:
            warnings.append(f"{tag}: market data is {age}d old (> {max_age}d) -> stale; refresh before use (open-item)")


def _validate_native(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    currency = doc.get("currency")
    as_of = doc.get("as_of_date")
    cfg = doc.get("config") or {}
    max_age = cfg.get("max_price_age_days", 5)
    min_peers = cfg.get("min_peers", 3)

    subject = doc.get("subject") or {}
    _check_company("subject", subject, currency, as_of, max_age, errors, warnings, is_subject=True)

    peers = doc.get("peers")
    if not isinstance(peers, list) or not peers:
        errors.append("peers must be a non-empty list")
        return errors, warnings

    tickers = set()
    included = 0
    for i, p in enumerate(peers):
        tag = f"peers[{i}] ({p.get('ticker','?')})"
        _check_company(tag, p, currency, as_of, max_age, errors, warnings)
        tk = p.get("ticker")
        if tk in tickers:
            errors.append(f"{tag}: duplicate ticker")
        tickers.add(tk)
        if p.get("include", True):
            included += 1
    if subject.get("ticker") in tickers:
        warnings.append(f"subject ticker {subject.get('ticker')!r} also appears in the peer set -> remove the subject from peers")
    if included < min_peers:
        warnings.append(f"only {included} included peer(s) (< min_peers {min_peers}) -> thin peer set; summary statistics will be flagged")

    for i, a in enumerate(doc.get("approvals") or []):
        if not a.get("type") or not a.get("status"):
            errors.append(f"approvals[{i}]: requires 'type' and 'status'")
        if a.get("status") == "recorded" and not a.get("source_ref"):
            errors.append(f"approvals[{i}] ({a.get('type','?')}): recorded approval missing 'source_ref'")
    if not doc.get("required_approvals"):
        warnings.append("no required_approvals configured -> approval capture limited")
    if doc.get("approvals") is None:
        warnings.append("no approvals provided -> all required approvals will be outstanding")
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
    for key in ['subject', 'config']:
        if key in doc and not isinstance(doc[key], dict):
            errors.append(key + " must be an object")
    for key in ['peers', 'approvals']:
        if key in doc and (not isinstance(doc[key], list) or any(not isinstance(row, dict) for row in doc[key])):
            errors.append(key + " must be a list of objects")
    if errors:
        return errors
    for company in [doc.get("subject", {})] + doc.get("peers", []):
        for key in ("ltm", "fy1"):
            if key in company and not isinstance(company[key], dict):
                errors.append(key + " must be an object")
    return errors

def _phase1_domains(doc):
    from datetime import date
    errors = _base_domains(doc)
    cfg = doc.get("config", {})
    for key in ("max_price_age_days", "min_peers"):
        value = cfg.get(key, 5 if key == "max_price_age_days" else 3)
        if isinstance(value, bool) or not isinstance(value, int) or value < (0 if key == "max_price_age_days" else 1):
            errors.append("config." + key + " outside supported integer domain")
    labels = {"EV/Revenue LTM","EV/EBITDA LTM","EV/EBIT LTM","P/E LTM","EV/Revenue FY1","EV/EBITDA FY1"}
    if not isinstance(cfg.get("bands", {}), dict):
        errors.append("config.bands must be an object")
    for key, band in cfg.get("bands", {}).items():
        if key not in labels or not isinstance(band, list) or len(band) != 2 or any(_number(v) is None for v in band) or band[0] > band[1]:
            errors.append("invalid configured multiple band: " + key)
    implied = cfg.get("implied_multiples", ["EV/EBITDA LTM", "EV/Revenue LTM"])
    if not isinstance(implied, list) or not implied or len(set(implied)) != len(implied) or any(label not in labels for label in implied):
        errors.append("implied_multiples requires unique supported multiple names")
    all_companies = [doc["subject"]] + doc["peers"]
    _unique(all_companies, "ticker", "companies", errors)
    for c in all_companies:
        if "include" in c and not isinstance(c["include"], bool):
            errors.append("include must be boolean")
        if _number(c.get("share_price")) is None or c["share_price"] <= 0:
            errors.append(str(c.get("ticker")) + ": share_price must be positive")
        if c.get("include", True):
            if not isinstance(c.get("market_source_ref"), str) or not c["market_source_ref"].strip():
                errors.append(str(c.get("ticker")) + ": market_source_ref required for supplied prices")
            for key in ("total_debt", "cash_and_equivalents", "preferred_equity", "minority_interest"):
                if _number(c.get(key)) is None or c[key] < 0:
                    errors.append(str(c.get("ticker")) + ": explicit nonnegative " + key + " required; unknown is not zero")
            if c.get("currency") != doc["currency"]:
                errors.append(str(c.get("ticker")) + ": normalize currency explicitly before comparison")
        for period in ("ltm", "fy1"):
            for key, value in c.get(period, {}).items():
                if value is not None and _number(value) is None:
                    errors.append(period + "." + key + " must be numeric or null")
        if c.get("price_date") is not None:
            try:
                if date.fromisoformat(c["price_date"]) > date.fromisoformat(doc["as_of_date"]):
                    errors.append("price_date cannot be after as_of_date")
            except (TypeError, ValueError):
                errors.append("price_date must be a valid YYYY-MM-DD date")
    _unique(doc.get("approvals", []), "type", "approvals", errors)
    required = doc.get("required_approvals", [])
    if not isinstance(required, list) or any(not isinstance(item, str) or not item.strip() for item in required) or len(required) != len(set(required)):
        errors.append("required_approvals must be a unique list of role/type strings")
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
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "comps_intake_example.json"
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
