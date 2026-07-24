#!/usr/bin/env python3
"""Deterministic premium buildup for insurance-rating-quote-worksheet.

Per coverage, applies the base rate and each rating factor in order (with a step trail), enforces
the minimum premium, adds fees, and totals across coverages plus policy fees. Indicated premium
only; never binds coverage or issues a quote.

Usage: python calculate_or_transform.py rating.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Indicated-premium worksheet only; not a bound quote, an issued quote, or an offer "
              "of coverage. Nothing has been bound or quoted.")


def _num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def compute(doc: dict) -> dict:
    policy = doc["policy"]
    manual = doc["rate_manual"]
    min_prem = _num(manual.get("min_premium"), 0.0)
    coverage_rows = []
    grand_total = 0.0

    for c in doc["coverages"]:
        base = _num(c.get("base_rate"))
        running = base
        steps = [{"step": "base_rate", "value": round(base, 6), "running": round(running, 6)}]
        product = 1.0
        for f in c.get("factors") or []:
            val = _num(f.get("value"), 1.0)
            product *= val
            running *= val
            steps.append({"step": f"factor:{f.get('name')}", "value": val, "running": round(running, 6)})
        premium_before_fees = round(base * product, 2)
        min_applied = premium_before_fees < min_prem
        premium_after_min = max(premium_before_fees, min_prem)
        if min_applied:
            steps.append({"step": "minimum_premium", "value": min_prem, "running": round(premium_after_min, 6)})
        fees = c.get("fees") or []
        fees_total = round(sum(_num(x.get("amount")) for x in fees), 2)
        coverage_total = round(premium_after_min + fees_total, 2)
        grand_total += coverage_total
        coverage_rows.append({
            "coverage": c.get("coverage"), "base_rate": round(base, 2),
            "factor_product": round(product, 6), "premium_before_fees": premium_before_fees,
            "minimum_premium_applied": min_applied, "premium_after_min": round(premium_after_min, 2),
            "fees": fees, "fees_total": fees_total, "coverage_total": coverage_total,
            "buildup_steps": steps,
            "citation": f"manual:{manual.get('config_version')}"})

    policy_fees = manual.get("policy_fees") or []
    policy_fees_total = round(sum(_num(x.get("amount")) for x in policy_fees), 2)
    indicated = round(grand_total + policy_fees_total, 2)
    return {
        "worksheet_id": f"irqw-{policy.get('policy_id', 'UNKNOWN')}-0001",
        "policy_id": policy.get("policy_id"), "line": policy.get("line"),
        "effective_date": policy.get("effective_date"),
        "manual_version": manual.get("config_version"),
        "coverages": coverage_rows,
        "policy_fees": policy_fees, "policy_fees_total": policy_fees_total,
        "indicated_premium": indicated,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "rating_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
