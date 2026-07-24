#!/usr/bin/env python3
"""Deterministic capital-structure & maturity map for capital-structure-maturity-mapper.

Builds totals by seniority/type, secured-unsecured split, the maturity wall by year,
weighted-average maturity and coupon, and near-term maturities from a debt schedule. Descriptive
only; never advises or recommends.

Usage: python calculate_or_transform.py debt.json | --selftest
"""
from __future__ import annotations
import datetime as _dt
import json, sys
from collections import defaultdict
from pathlib import Path

DISCLAIMER = ("Descriptive capital-structure map only; not financing advice, a recommendation, or "
              "a view on the optimal structure. No transaction is suggested.")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _date(s):
    try:
        return _dt.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def compute(doc: dict) -> dict:
    co = doc["company"]
    as_of = _date(co.get("as_of"))
    instrs = doc["instruments"]

    by_seniority = defaultdict(float)
    by_type = defaultdict(float)
    secured_split = defaultdict(float)
    wall = defaultdict(float)
    total = 0.0
    wam_num = wac_num = 0.0
    near_term = 0.0
    excluded = []

    for it in instrs:
        p = _num(it.get("principal"))
        if p is None:
            excluded.append({"instrument_id": it.get("instrument_id"), "reason": "missing principal"})
            continue
        total += p
        by_seniority[it.get("seniority", "unspecified")] += p
        by_type[it.get("type", "unspecified")] += p
        secured_split["secured" if it.get("secured") else "unsecured"] += p
        wac = _num(it.get("coupon_pct"))
        if wac is not None:
            wac_num += p * wac
        md = _date(it.get("maturity_date"))
        if md is None:
            wall["undated"] += p
            continue
        wall[str(md.year)] += p
        if as_of:
            yrs = (md - as_of).days / 365.25
            wam_num += p * yrs
            if 0 <= (md - as_of).days <= 730:
                near_term += p

    wam = round(wam_num / total, 2) if total else None
    wac = round(wac_num / total, 4) if total else None
    return {
        "map_id": f"csmm-{co.get('company_id', 'UNKNOWN')}-0001",
        "company_id": co.get("company_id"), "as_of": co.get("as_of"),
        "total_debt": round(total, 2),
        "by_seniority": {k: round(v, 2) for k, v in sorted(by_seniority.items())},
        "by_type": {k: round(v, 2) for k, v in sorted(by_type.items())},
        "secured_unsecured": {k: round(v, 2) for k, v in sorted(secured_split.items())},
        "maturity_wall": {k: round(v, 2) for k, v in sorted(wall.items())},
        "near_term_24m": round(near_term, 2),
        "wam_years": wam, "wac_pct": wac,
        "excluded_instruments": excluded,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "debt_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
