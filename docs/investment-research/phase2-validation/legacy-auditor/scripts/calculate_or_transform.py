#!/usr/bin/env python3
"""Deterministic roll-forward continuity audit for model-roll-forward-auditor.

Per line item, computes residual = current_opening - prior_ending and flags a break when
|residual| exceeds tolerance (default 0 = exact match). Flags structural breaks (item present in
only one version). Continuity evidence only; never opines on value or approves the model.

Usage: python calculate_or_transform.py model.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Roll-forward continuity check only; not a model approval, a validation, or a "
              "valuation/fair-value opinion. The model has not been approved.")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _calculate_native(doc: dict) -> dict:
    model = doc["model"]
    prior_v, cur_v = model.get("prior_version"), model.get("current_version")
    items, breaks = [], []

    for it in doc["roll_forward"]:
        name = it.get("line_item")
        pe = _num(it.get("prior_ending"))
        co = _num(it.get("current_opening"))
        tol = _num(it.get("tolerance")) or 0.0
        cite = f"model:model={model.get('model_id')};item={name};v={prior_v}->{cur_v}"
        if pe is None or co is None:
            row = {"line_item": name, "prior_ending": pe, "current_opening": co,
                   "residual": None, "within_tolerance": False, "tie_status": "structural_break",
                   "tolerance": tol, "citation": cite}
            breaks.append({"line_item": name, "type": "structural_break",
                           "detail": "balance missing in one version", "citation": cite})
        else:
            residual = round(co - pe, 6)
            within = abs(residual) <= tol
            row = {"line_item": name, "prior_ending": pe, "current_opening": co,
                   "residual": residual, "within_tolerance": within,
                   "tie_status": "tied" if within else "break", "tolerance": tol, "citation": cite}
            if not within:
                breaks.append({"line_item": name, "type": "continuity_break",
                               "detail": f"residual {residual} exceeds tolerance {tol}", "citation": cite})
        items.append(row)

    disposition = "tied" if not breaks else "breaks-for-review"
    return {
        "audit_id": f"mrfa-{model.get('model_id', 'UNKNOWN')}-0001",
        "model_id": model.get("model_id"),
        "prior_version": prior_v, "current_version": cur_v,
        "item_count": len(items), "break_count": len(breaks),
        "review_scope": "supplied-balance-continuity-only",
        "limitations": ["Does not read or update a workbook, compare formulas, review assumptions, establish economic validity or provide independent model assurance."],
        "line_items": items, "breaks": breaks,
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


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

def compute(doc):
    errors, warnings = _local_module("validate_input.py").validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    result = _calculate_native(doc)
    result["validation_warnings"] = warnings
    result["method_id"] = 'model-roll-forward-auditor'
    result["method_version"] = "0.2.0"
    result["result_origin"] = "local-analysis"
    result["review_status"] = "not-requested"
    result["execution_status"] = "not-performed"
    result["method_scope"] = 'model-roll-forward-auditor: bounded supplied-input local analysis; no source authentication, approval or execution'
    return _local_module("native_integrity.py").attach_source(result, doc)

def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_example.json"
        doc = _strict_json(p.read_text(encoding="utf-8"))
    elif argv:
        doc = _strict_json(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = _strict_json(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


_main_checked = main

def main(argv):
    try:
        return _main_checked(argv)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        print("ERROR", str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
