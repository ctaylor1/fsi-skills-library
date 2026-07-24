#!/usr/bin/env python3
"""Deterministic P&L attribution for desk-pnl-risk-attribution-pack.

Computes explained = Σ components, residual = reported − explained, flags the residual as a break
when it exceeds tolerance, and ranks component contributions. Evidence only; never adjusts,
restates, or signs off P&L.

Usage: python calculate_or_transform.py pnl.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Attribution evidence only; not a P&L adjustment, restatement, or sign-off. No P&L "
              "has been adjusted or certified.")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def compute(doc: dict) -> dict:
    desk = doc["desk"]
    reported = _num(doc.get("reported_pnl")) or 0.0
    tol = _num(doc.get("tolerance_abs")) or 0.0
    contributions = []
    explained = 0.0
    incomplete = False
    for c in doc["components"]:
        v = _num(c.get("value"))
        if v is None:
            incomplete = True
            contributions.append({"name": c.get("name"), "value": None, "note": "non-numeric — excluded",
                                  "citation": f"risk:{c.get('source_ref', c.get('name'))}"})
            continue
        explained += v
        contributions.append({"name": c.get("name"), "value": round(v, 2),
                              "citation": f"risk:{c.get('source_ref', c.get('name'))}"})
    contributions.sort(key=lambda x: (x.get("value") is None, -abs(x.get("value") or 0.0)))
    residual = round(reported - explained, 2)
    unexplained = abs(residual) > tol
    disposition = "breaks-for-review" if (unexplained or incomplete) else "tied"
    return {
        "attribution_id": f"dpra-{desk.get('desk_id', 'UNKNOWN')}-0001",
        "desk_id": desk.get("desk_id"), "as_of": desk.get("as_of"),
        "config_version": doc.get("config_version"),
        "reported_pnl": round(reported, 2),
        "explained": round(explained, 2),
        "residual": residual, "abs_residual": round(abs(residual), 2),
        "tolerance_abs": tol, "unexplained_break": unexplained,
        "attribution_incomplete": incomplete,
        "contributions": contributions,
        "suggested_disposition": disposition,
        "citation_reported": f"pnl:desk={desk.get('desk_id')}@{desk.get('as_of')}",
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pnl_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
