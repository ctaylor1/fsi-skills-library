#!/usr/bin/env python3
"""Bounded input validation for financials-normalizer.

Finite JSON numbers, typed shapes, dates, identifiers and method domains are checked.
Malformed inputs return validation errors. See references/domain-rules.md for supported scope.
"""
from __future__ import annotations
import json, re, sys, math
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("entity_id", "as_of", "config_version", "reporting_framework", "currency",
                "mapping", "line_items")
STATEMENTS = {"income_statement", "balance_sheet", "cash_flow"}
ROLES = {"total_assets", "total_liabilities", "total_equity"}


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def _missing(v) -> bool:
    """True if a required field is absent or an empty/whitespace string."""
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip() == ""
    return False


def _validate_native(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    mapping = doc.get("mapping") or []
    if not isinstance(mapping, list) or not mapping:
        errors.append("mapping must be a non-empty list")
    mapped_keys = set()
    for i, m in enumerate(mapping):
        tag = f"mapping[{i}] ({m.get('source_label','?')})"
        for k in ("source_label", "std_account", "statement"):
            if _missing(m.get(k)):
                errors.append(f"{tag}: missing '{k}'")
        if m.get("statement") and m["statement"] not in STATEMENTS:
            errors.append(f"{tag}: statement must be one of {sorted(STATEMENTS)}")
        ns = str(m.get("normal_sign", "")).lower()
        if ns and ns not in ("positive", "negative"):
            warnings.append(f"{tag}: normal_sign should be 'positive' or 'negative'")
        mapped_keys.add((str(m.get("source_label")), str(m.get("statement"))))

    lines = doc.get("line_items") or []
    if not isinstance(lines, list) or not lines:
        errors.append("line_items must be a non-empty list")
        return errors, warnings

    ids = set()
    detail_labels_unmapped = 0
    roles_present = set()
    for i, ln in enumerate(lines):
        tag = f"line_items[{i}] ({ln.get('line_id','?')})"
        for k in ("line_id", "raw_label", "statement", "period"):
            if _missing(ln.get(k)):
                errors.append(f"{tag}: missing '{k}'")
        if _num(ln.get("value")) is None:
            errors.append(f"{tag}: value not numeric")
        if ln.get("statement") and ln["statement"] not in STATEMENTS:
            errors.append(f"{tag}: statement must be one of {sorted(STATEMENTS)}")
        lid = ln.get("line_id")
        if lid in ids:
            errors.append(f"{tag}: duplicate line_id")
        ids.add(lid)

        if ln.get("is_subtotal"):
            comps = ln.get("components")
            role = ln.get("role")
            if role in ROLES:
                roles_present.add(role)
            elif not comps:
                warnings.append(f"{tag}: subtotal has neither 'components' nor an identity 'role' — not tie-out-checkable")
        else:
            if not (ln.get("source_ref") or "").strip():
                warnings.append(f"{tag}: no source_ref — missing_provenance will fire (untraceable)")
            if (str(ln.get("raw_label")), str(ln.get("statement"))) not in mapped_keys:
                detail_labels_unmapped += 1

    # subtotal component references must resolve
    for ln in lines:
        if ln.get("is_subtotal") and ln.get("components"):
            for c in ln["components"]:
                if c not in ids:
                    errors.append(f"line_items ({ln.get('line_id')}): component {c!r} not a known line_id")

    if detail_labels_unmapped:
        warnings.append(f"{detail_labels_unmapped} detail line(s) have no mapping — unmapped_line_item will fire")
    if not (ROLES <= roles_present):
        missing = sorted(ROLES - roles_present)
        warnings.append(f"balance-sheet identity anchors missing ({', '.join(missing)}) — balance_sheet_identity_break not evaluable")
    for j, a in enumerate(doc.get("adjustments") or []):
        if not (a.get("rationale") or "").strip() or not (a.get("source_ref") or "").strip():
            warnings.append(f"adjustments[{j}] ({a.get('adj_id','?')}): missing rationale/source — will be flagged")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
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
    for key in ['config']:
        if key in doc and not isinstance(doc[key], dict):
            errors.append(key + " must be an object")
    for key in ['mapping', 'line_items', 'adjustments']:
        if key in doc and (not isinstance(doc[key], list) or any(not isinstance(row, dict) for row in doc[key])):
            errors.append(key + " must be a list of objects")
    if errors:
        return errors
    return errors

def _phase1_domains(doc):
    errors = _base_domains(doc)
    mappings = doc["mapping"]
    keys = [(m["source_label"], m["statement"]) for m in mappings]
    if len(set(keys)) != len(keys):
        errors.append("duplicate source_label/statement mapping")
    _unique(doc.get("adjustments", []), "adj_id", "adjustments", errors)
    periods = {row["period"] for row in doc["line_items"]}
    by_id = {row["line_id"]: row for row in doc["line_items"]}
    roles = set()
    for row in doc["line_items"]:
        if "is_subtotal" in row and not isinstance(row["is_subtotal"], bool):
            errors.append("is_subtotal must be boolean")
        if row.get("role"):
            key = (row["period"], row["role"])
            if key in roles or row["statement"] != "balance_sheet" or not row.get("is_subtotal"):
                errors.append("identity roles require unique balance-sheet subtotal anchors per period")
            roles.add(key)
        components = row.get("components", [])
        if not isinstance(components, list) or len(set(components)) != len(components):
            errors.append("subtotal components must be a unique list")
            continue
        for cid in components:
            if cid in by_id and (by_id[cid]["period"] != row["period"] or by_id[cid]["statement"] != row["statement"] or cid == row["line_id"]):
                errors.append("subtotal components must share period/statement and cannot self-reference")
    def check_cycle(lid, trail=()):
        if lid in trail:
            errors.append("cyclic subtotal component graph")
            return
        for child in by_id[lid].get("components", []):
            if child in by_id:
                check_cycle(child, trail + (lid,))
    for lid in by_id:
        check_cycle(lid)
    mapping_index = {(m["source_label"], m["statement"]):m["std_account"] for m in mappings}
    known_accounts = {(mapping_index[(row["raw_label"], row["statement"])], row["statement"], row["period"]) for row in doc["line_items"] if not row.get("is_subtotal") and (row["raw_label"], row["statement"]) in mapping_index}
    for adjustment in doc.get("adjustments", []):
        for key in ("std_account", "type", "period", "statement"):
            if not isinstance(adjustment.get(key), str) or not adjustment[key].strip():
                errors.append("adjustment requires explicit " + key)
        if (adjustment.get("std_account"), adjustment.get("statement"), adjustment.get("period")) not in known_accounts:
            errors.append("adjustment requires a mapped reported account/statement/period; absent starting values cannot default to zero")
        if adjustment.get("statement") not in STATEMENTS:
            errors.append("adjustment.statement must select an existing statement type")
        if adjustment.get("period") not in periods or _number(adjustment.get("amount")) is None:
            errors.append("adjustment requires a known period and finite amount")
    cfg = doc.get("config", {})
    for key in ("tie_out_tolerance", "adjustment_materiality_pct", "escalate_finding_count"):
        if key in cfg and (_number(cfg[key]) is None or cfg[key] < (1 if key == "escalate_finding_count" else 0)):
            errors.append("invalid config threshold: " + key)
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
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "financials_example.json"
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
