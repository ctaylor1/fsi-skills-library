#!/usr/bin/env python3
"""Deterministic volume-weighted chain-ladder for actuarial-model-run-assistant.

Computes age-to-age (LDF) factors, cumulative development factors (CDF) with a configured tail,
and per-origin ultimate and IBNR from the latest diagonal. Produces an indication for review
only; never books, sets, or certifies a reserve.

Usage: python calculate_or_transform.py triangle.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Actuarial indication for review only; not a booked reserve, a reserving decision, "
              "or a certification of adequacy.")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def compute(doc: dict) -> dict:
    t = doc["triangle"]
    a = doc["assumptions"]
    origins = t["origin_periods"]
    ages = t["dev_ages"]
    mat = [[_num(v) for v in row] for row in t["cumulative_paid"]]
    tail = _num(a.get("tail_factor")) or 1.0
    ncol = len(ages)

    # age-to-age factors (volume-weighted)
    ldf = []
    for j in range(ncol - 1):
        num = den = 0.0
        pairs = 0
        for row in mat:
            if row[j] is not None and row[j + 1] is not None:
                num += row[j + 1]
                den += row[j]
                pairs += 1
        ldf.append(round(num / den, 6) if den > 0 and pairs > 0 else None)

    # cumulative development factors to ultimate
    cdf = [None] * ncol
    cdf[ncol - 1] = round(tail, 6)
    running = tail
    for j in range(ncol - 2, -1, -1):
        if ldf[j] is None:
            cdf[j] = None
            continue
        running = running * ldf[j]
        cdf[j] = round(running, 6)

    # per-origin ultimate / IBNR from latest diagonal
    per_origin = []
    tot_ult = tot_ibnr = 0.0
    for i, row in enumerate(mat):
        filled = [j for j, v in enumerate(row) if v is not None]
        if not filled:
            per_origin.append({"origin": origins[i], "latest_age": None, "latest": None,
                               "cdf": None, "ultimate": None, "ibnr": None,
                               "note": "no filled cells"})
            continue
        j = filled[-1]
        latest = row[j]
        c = cdf[j]
        if c is None:
            per_origin.append({"origin": origins[i], "latest_age": ages[j], "latest": round(latest, 2),
                               "cdf": None, "ultimate": None, "ibnr": None,
                               "note": "CDF not computable (missing LDF)"})
            continue
        ult = round(latest * c, 2)
        ibnr = round(ult - latest, 2)
        tot_ult += ult
        tot_ibnr += ibnr
        per_origin.append({"origin": origins[i], "latest_age": ages[j], "latest": round(latest, 2),
                           "cdf": c, "ultimate": ult, "ibnr": ibnr})

    return {
        "run_id": f"amra-{t.get('triangle_id', 'UNKNOWN')}-0001",
        "triangle_id": t.get("triangle_id"),
        "claim_type": t.get("claim_type"),
        "method": a.get("method", "volume_weighted_chain_ladder"),
        "tail_factor": tail,
        "assumptions_version": a.get("config_version"),
        "age_to_age_factors": [{"from_age": ages[j], "to_age": ages[j + 1], "ldf": ldf[j]}
                               for j in range(ncol - 1)],
        "cdf_by_age": [{"age": ages[j], "cdf": cdf[j]} for j in range(ncol)],
        "per_origin": per_origin,
        "total_ultimate": round(tot_ult, 2),
        "total_ibnr": round(tot_ibnr, 2),
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "triangle_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
