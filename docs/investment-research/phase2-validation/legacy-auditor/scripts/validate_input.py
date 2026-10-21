#!/usr/bin/env python3
"""Bounded input validation for model-roll-forward-auditor.

Finite JSON numbers, typed shapes, dates, identifiers and method domains are checked.
Malformed inputs return validation errors. See references/domain-rules.md for supported scope.
"""
from __future__ import annotations
import json, sys, math
from pathlib import Path


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def _validate_native(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in ("model", "roll_forward"):
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings
    if not doc["model"].get("model_id"):
        errors.append("model missing 'model_id'")
    items = doc.get("roll_forward") or []
    if not isinstance(items, list) or not items:
        errors.append("roll_forward must be a non-empty list")
        return errors, warnings
    for i, it in enumerate(items):
        tag = f"roll_forward[{i}] ({it.get('line_item','?')})"
        if it.get("line_item") in (None, ""):
            errors.append(f"{tag}: missing 'line_item'")
        if _num(it.get("prior_ending")) is None:
            warnings.append(f"{tag}: prior_ending not numeric — item not tieable (structural break)")
        if _num(it.get("current_opening")) is None:
            warnings.append(f"{tag}: current_opening not numeric — item not tieable (structural break)")
        if it.get("tolerance") is not None and _num(it.get("tolerance")) is None:
            errors.append(f"{tag}: tolerance present but not numeric")
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
    for key in ['model']:
        if key in doc and not isinstance(doc[key], dict):
            errors.append(key + " must be an object")
    for key in ['roll_forward']:
        if key in doc and (not isinstance(doc[key], list) or any(not isinstance(row, dict) for row in doc[key])):
            errors.append(key + " must be a list of objects")
    if errors:
        return errors
    return errors

def _phase1_domains(doc):
    errors = _base_domains(doc)
    for key in ("model_id", "prior_version", "current_version"):
        if not isinstance(doc["model"].get(key), str) or not doc["model"][key].strip():
            errors.append("model requires nonempty " + key)
    _unique(doc["roll_forward"], "line_item", "roll_forward", errors)
    for row in doc["roll_forward"]:
        for key in ("prior_ending", "current_opening"):
            if key not in row:
                errors.append(key + " must be supplied; use explicit null for a structural break")
            if row.get(key) is not None and _number(row[key]) is None:
                errors.append(key + " must be numeric or explicit null for a structural break")
        if "tolerance" not in row or _number(row["tolerance"]) is None or row["tolerance"] < 0:
            errors.append("explicit nonnegative tolerance required")
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
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)

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
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_example.json"
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

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
