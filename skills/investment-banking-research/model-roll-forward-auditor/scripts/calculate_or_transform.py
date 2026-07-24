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


def compute(doc: dict) -> dict:
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
        "line_items": items, "breaks": breaks,
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
