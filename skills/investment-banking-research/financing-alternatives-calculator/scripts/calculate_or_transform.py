#!/usr/bin/env python3
"""Deterministic financing-cost comparison for financing-alternatives-calculator.

Computes, per documented alternative, the interest, amortized fees, all-in annual cost, effective
cost rate, total cost over term, and (for equity) shares issued and dilution. Numbers only; never
recommends or ranks.

Usage: python calculate_or_transform.py request.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Illustrative cost comparison only; not a recommendation, ranking, or a view on "
              "which alternative to choose. The financing decision is the banker's/client's.")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _row_debt(amount, a):
    rate = _num(a.get("rate_pct"))
    fees = _num(a.get("fees_pct")) or 0.0
    term = _num(a.get("term_years"))
    row = {"annual_interest": None, "upfront_fees": None, "amortized_fees_annual": None,
           "all_in_annual_cost": None, "effective_cost_pct": None, "total_cost_over_term": None,
           "notes": []}
    if rate is None:
        row["notes"].append("rate_pct missing — interest not computable")
        return row
    ai = amount * rate / 100.0
    uf = amount * fees / 100.0
    row["annual_interest"] = round(ai, 2)
    row["upfront_fees"] = round(uf, 2)
    if term and term > 0:
        amort = uf / term
        row["amortized_fees_annual"] = round(amort, 2)
        row["all_in_annual_cost"] = round(ai + amort, 2)
        row["effective_cost_pct"] = round((ai + amort) / amount * 100.0, 4) if amount else None
        row["total_cost_over_term"] = round(ai * term + uf, 2)
    else:
        row["notes"].append("term_years missing/zero — amortized/total not computable")
    return row


def _row_equity(amount, a):
    price = _num(a.get("share_price"))
    cur = _num(a.get("current_shares"))
    row = {"shares_issued": None, "dilution_pct": None, "annual_interest": 0.0, "notes": []}
    if not price or price <= 0 or cur is None:
        row["notes"].append("share_price/current_shares missing — dilution not computable")
        return row
    issued = amount / price
    row["shares_issued"] = round(issued, 4)
    row["dilution_pct"] = round(issued / (cur + issued) * 100.0, 4) if (cur + issued) else None
    return row


def compute(doc: dict) -> dict:
    req = doc["request"]
    amount = _num(req.get("amount_needed")) or 0.0
    rows = []
    for a in doc["alternatives"]:
        base = {"alt_id": a.get("alt_id"), "type": a.get("type"),
                "terms_used": {k: a.get(k) for k in ("rate_pct", "fees_pct", "term_years", "share_price", "current_shares") if a.get(k) is not None},
                "citation": f"terms:{a.get('source_ref', a.get('alt_id'))}"}
        metrics = _row_equity(amount, a) if a.get("type") == "equity" else _row_debt(amount, a)
        rows.append({**base, **metrics})
    return {
        "calc_id": f"fac-{req.get('request_id', 'UNKNOWN')}-0001",
        "request_id": req.get("request_id"), "amount_needed": round(amount, 2),
        "currency": req.get("currency"), "as_of": req.get("as_of"),
        "alternatives": rows,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
