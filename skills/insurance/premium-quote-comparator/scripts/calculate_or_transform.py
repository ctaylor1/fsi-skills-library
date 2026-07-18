#!/usr/bin/env python3
"""Deterministic quote normalization + comparison for premium-quote-comparator.

Reads a quotes file (see validate_input.py), normalizes each quote's premium and fees to a
common annualized basis, builds a coverage/limit/deductible comparison grid, and enumerates
the material differences that make the quotes NOT a like-for-like comparison. Emits a
machine-readable core the SKILL wraps in a plain-language comparison.

IMPORTANT: This produces a normalized *comparison* only. It never selects a policy, gives
insurance/suitability advice, or makes a coverage or eligibility determination. The lowest
annualized cost is reported as a factual figure, not a recommendation; differences in
limits/deductibles/exclusions are surfaced precisely so cost is never compared in isolation.
Normalization rules are documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py quotes.json | --selftest
Prints the comparison JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Payments per year by premium frequency -> used to annualize a per-installment premium.
PAYMENTS_PER_YEAR = {"annual": 1, "semiannual": 2, "quarterly": 4, "monthly": 12}
DISCLAIMER = ("Comparison of quotes only; not insurance advice, a coverage determination, or a "
              "recommendation to purchase. Coverage selection is the customer's decision, made "
              "with a licensed producer.")


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _cite(q: dict) -> str:
    return f"quote:{q.get('source_ref', q.get('quote_id', '?'))}@{q.get('as_of', '?')}"


def _limit_key(limit) -> str:
    """Stable representation of a limit value for equality comparison across quotes."""
    if limit in (None, ""):
        return ""
    if isinstance(limit, dict):
        return json.dumps(limit, sort_keys=True)
    return str(limit)


def compute(doc: dict) -> dict:
    cfg = {**{"round_to": 2}, **(doc.get("config") or {})}
    as_of = doc["as_of"]
    quotes = doc["quotes"]
    doc_ccy = doc.get("currency")

    # ---- normalize premium + fees to an annualized basis ----
    normalized = []
    for q in quotes:
        q = {**q, "as_of": as_of}
        prem = q.get("premium") or {}
        ppy = PAYMENTS_PER_YEAR.get(prem.get("frequency"), 1)
        annualized_premium = round(_num(prem.get("amount")) * ppy, cfg["round_to"])
        term = _num(q.get("term_months"), 12) or 12
        fee_sum = sum(_num(f.get("amount")) for f in (q.get("fees") or []))
        annualized_fees = round(fee_sum * (12.0 / term), cfg["round_to"])
        total = round(annualized_premium + annualized_fees, cfg["round_to"])
        normalized.append({
            "quote_id": q["quote_id"],
            "carrier": q.get("carrier"),
            "product": q.get("product"),
            "term_months": q.get("term_months"),
            "currency": q.get("currency") or doc_ccy,
            "premium_as_quoted": {"amount": _num(prem.get("amount")), "frequency": prem.get("frequency")},
            "annualized_premium": annualized_premium,
            "annualized_fees": annualized_fees,
            "annualized_total_cost": total,
            "citation": _cite(q),
        })

    # ---- coverage comparison grid (union of coverage codes, first-seen order) ----
    code_order, code_name = [], {}
    per_quote_cov = {}  # quote_id -> {code: coverage dict}
    for q in quotes:
        m = {}
        for c in q.get("coverages") or []:
            code = str(c.get("code"))
            m[code] = c
            if code not in code_name:
                code_order.append(code)
                code_name[code] = c.get("name", code)
        per_quote_cov[q["quote_id"]] = m

    coverage_matrix, coverage_diff, deductible_diff, limit_diff = [], [], [], []
    all_ids = [q["quote_id"] for q in quotes]
    for code in code_order:
        cells, included_ids = [], []
        for q in quotes:
            qid = q["quote_id"]
            c = per_quote_cov[qid].get(code)
            if c is not None:
                included_ids.append(qid)
                cells.append({"quote_id": qid, "included": True, "limit": c.get("limit"),
                              "deductible": c.get("deductible"), "citation": _cite({**q, "as_of": as_of})})
            else:
                cells.append({"quote_id": qid, "included": False, "limit": None,
                              "deductible": None, "citation": _cite({**q, "as_of": as_of})})
        coverage_matrix.append({"code": code, "name": code_name[code], "cells": cells})

        if len(included_ids) != len(all_ids):
            coverage_diff.append({"code": code, "name": code_name[code],
                                  "included_in": included_ids,
                                  "missing_from": [i for i in all_ids if i not in included_ids]})

        # differences are only meaningful among quotes that include the coverage
        inc = [qid for qid in included_ids]
        deds = {qid: per_quote_cov[qid][code].get("deductible") for qid in inc}
        if len({_num(v, None) if v is not None else None for v in deds.values()}) > 1:
            deductible_diff.append({"code": code, "name": code_name[code], "values": deds})
        lims = {qid: per_quote_cov[qid][code].get("limit") for qid in inc}
        if len({_limit_key(v) for v in lims.values()}) > 1:
            limit_diff.append({"code": code, "name": code_name[code], "values": lims})

    # ---- exclusions + endorsements + term ----
    def _diff_sets(getter, label_key):
        universe, present = [], {}
        for q in quotes:
            vals = []
            for x in getter(q):
                key = x if isinstance(x, str) else str(x.get(label_key) or x.get("name"))
                vals.append(key)
                if key not in universe:
                    universe.append(key)
            present[q["quote_id"]] = set(vals)
        out = []
        for key in universe:
            present_in = [q["quote_id"] for q in quotes if key in present[q["quote_id"]]]
            if len(present_in) != len(all_ids):
                out.append({"item": key, "present_in": present_in,
                            "absent_from": [i for i in all_ids if i not in present_in]})
        return out

    exclusion_diff = _diff_sets(lambda q: q.get("exclusions") or [], "name")
    endorsement_diff = _diff_sets(lambda q: q.get("endorsements") or [], "code")
    term_diff = []
    if len({q.get("term_months") for q in quotes}) > 1:
        term_diff = [{"quote_id": q["quote_id"], "term_months": q.get("term_months")} for q in quotes]

    differences = {
        "coverage_differences": coverage_diff,
        "deductible_differences": deductible_diff,
        "limit_differences": limit_diff,
        "exclusion_differences": exclusion_diff,
        "endorsement_differences": endorsement_diff,
        "term_differences": term_diff,
    }

    # ---- comparability flags (why cheapest != best fit) ----
    flags = []

    def flag(name, cond, detail, quotes_):
        if cond:
            flags.append({"flag": name, "detail": detail, "quotes": quotes_})

    flag("coverage_mismatch", coverage_diff,
         "quotes do not all include the same coverages; compare only across matching coverages",
         sorted({i for d in coverage_diff for i in d["included_in"] + d["missing_from"]}))
    flag("deductible_mismatch", deductible_diff,
         "deductibles differ for one or more shared coverages; a lower premium may reflect a higher deductible",
         sorted({i for d in deductible_diff for i in d["values"].keys()}))
    flag("limit_mismatch", limit_diff,
         "limits differ for one or more shared coverages; a lower premium may reflect lower limits",
         sorted({i for d in limit_diff for i in d["values"].keys()}))
    flag("exclusion_mismatch", exclusion_diff,
         "exclusions differ across quotes; a cheaper quote may exclude a peril another covers",
         sorted({i for d in exclusion_diff for i in d["present_in"] + d["absent_from"]}))
    flag("endorsement_mismatch", endorsement_diff,
         "endorsements/riders differ across quotes",
         sorted({i for d in endorsement_diff for i in d["present_in"] + d["absent_from"]}))
    flag("term_mismatch", bool(term_diff),
         "quotes have different policy terms; figures are annualized but term-length effects remain",
         all_ids if term_diff else [])
    ccys = {n["currency"] for n in normalized if n["currency"]}
    flag("currency_mismatch", len(ccys) > 1,
         f"quotes span multiple currencies {sorted(ccys)}; annualized totals are not directly comparable without FX",
         all_ids if len(ccys) > 1 else [])

    # ---- factual cost spread + lowest cost (NOT a recommendation) ----
    lowest = min(normalized, key=lambda n: (n["annualized_total_cost"], n["quote_id"]))
    costs = [n["annualized_total_cost"] for n in normalized]
    cost_spread = {"min": min(costs), "max": max(costs), "delta": round(max(costs) - min(costs), cfg["round_to"])}

    return {
        "comparison_id": f"pqc-{doc.get('risk_type', 'na')}-{as_of}-0001",
        "as_of": as_of,
        "config_version": doc.get("config_version"),
        "risk_type": doc.get("risk_type"),
        "currency": doc_ccy,
        "quote_count": len(quotes),
        "normalized_quotes": normalized,
        "coverage_matrix": coverage_matrix,
        "differences": differences,
        "comparability_flags": flags,
        "lowest_annualized_total_cost_quote_id": lowest["quote_id"],
        "cost_spread": cost_spread,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "quotes_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
