#!/usr/bin/env python3
"""Deterministic output validation for pricing-hedging-scenario-calculator.

Enforces the R3 guardrails before the worksheet is presented:
  1. Per scenario: illustrative_pnl == sign(direction) * position_dv01 * shock_bp (within tol).
  2. Hedge sizing: hedge_units * hedge_dv01_per_unit == position_dv01 (within tol), when computable.
  3. No firm-price / execution language.
  4. Standing disclaimer present.

Usage: python validate_output.py worksheet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER_RE = re.compile(r"not a firm price", re.I)
PROHIBITED = [
    r"\bfirm price\b", r"\bwe quote\b", r"\bexecute the hedge\b", r"\bput on the (trade|hedge)\b",
    r"\bwe filled\b", r"\blifted the offer\b", r"\bhit the bid\b", r"\bprice it firm\b",
]
TOL = 0.5


def validate(p: dict) -> list[str]:
    errors = []
    dv01 = p.get("position_dv01")
    sign = -1.0 if p.get("direction") == "long" else 1.0
    if dv01 is not None:
        for s in p.get("scenarios") or []:
            shock, pnl = s.get("shock_bp"), s.get("illustrative_pnl")
            if None in (shock, pnl):
                continue
            expected = sign * dv01 * shock
            if abs(expected - pnl) > TOL:
                errors.append(f"scenario {s.get('scenario_id')}: pnl {pnl} != sign*dv01*shock {round(expected, 2)}")
    h = p.get("hedge") or {}
    if h.get("hedge_units") is not None and h.get("hedge_dv01_per_unit") and dv01 is not None:
        recon = h["hedge_units"] * h["hedge_dv01_per_unit"]
        if abs(recon - dv01) > max(TOL, abs(dv01) * 1e-6):
            errors.append(f"hedge sizing: units*dv01_per_unit {round(recon, 2)} != position_dv01 {dv01}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"firm-price/execution language detected: {m.group(0)!r} (R3 estimates, desk prices/executes)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (illustrative scenario only / not a firm price or execution)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "worksheet_example.json"
        p = json.loads(pth.read_text(encoding="utf-8"))
    elif argv:
        p = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        p = json.loads(sys.stdin.read())
    errors = validate(p)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
