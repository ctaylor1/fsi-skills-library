#!/usr/bin/env python3
"""Deterministic output validation for liquidity-stress-analyzer.

Validates the final liquidity-stress pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Checks:
  1. Every breached metric has >= 1 cited evidence row.
  2. suggested_band equals the deterministic mapping from breached_metrics.
  3. Scenario assumptions are recorded (transparent scenarios are mandatory).
  4. No investment/trading recommendation, fund-liquidity-action, or breach-determination
     language (narrative + notes + metric reasons).
  5. The standing disclaimer is present.
  6. Modeling caveats are included when any metric breached.

Usage:
  python validate_output.py analysis.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

STRESS_LEVEL = {"redemption_coverage_shortfall", "full_liquidation_horizon_exceeded",
                "collateral_buffer_shortfall"}
WATCH_LEVEL = {"redemption_coverage_thin", "liquidation_cost_elevated", "illiquid_concentration"}
DISCLAIMER = ("Liquidity analysis and evidence only under stated scenario assumptions; not "
              "an investment, trading, or fund-liquidity-action determination. No trade, "
              "redemption gate, or other liquidity action has been taken.")

# Recommendation / action / determination assertions that an R2 analysis must not make:
PROHIBITED_PATTERNS = [
    r"\bsuspend redemptions?\b", r"\bsuspend the fund\b", r"\bgate the fund\b",
    r"\bimpose (a )?(redemption )?gate\b", r"\braise the gate\b", r"\bactivate (a )?side.?pocket\b",
    r"\bliquidate the (fund|portfolio)\b", r"\bwe should (sell|liquidate|buy|trade)\b",
    r"\byou should (sell|liquidate|buy|trade)\b", r"\bmust (gate|suspend|liquidate|sell)\b",
    r"\bexecute the (liquidation|trade|sale|order)\b", r"\bplace the (order|trade)\b",
    r"\bthe fund is (in breach|illiquid|insolvent)\b", r"\bin breach of (the |its )?(mandate|guideline)\b",
    r"\bdeclare .* illiquid\b", r"\bguaranteed (liquidity|return|redemption)\b",
]


def _expected_band(breached: list) -> str:
    s = set(breached)
    if s & STRESS_LEVEL:
        return "Stressed"
    if s & WATCH_LEVEL:
        return "Watch"
    return "Adequate"


def validate(pack: dict) -> list:
    errors = []
    metrics = pack.get("metrics") or []
    breached = [m["metric"] for m in metrics if m.get("breached")]

    for m in metrics:
        if m.get("breached"):
            ev = m.get("evidence") or []
            if not ev:
                errors.append(f"breached metric {m.get('metric')} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"breached metric {m.get('metric')} evidence row missing citation")

    exp = _expected_band(breached)
    if pack.get("suggested_band") != exp:
        errors.append(f"suggested_band {pack.get('suggested_band')!r} != deterministic {exp!r} for breached={breached}")

    scn = pack.get("scenario_assumptions") or {}
    required_scn = ("adv_haircut", "spread_multiple", "price_shock", "redemption_pct", "redemption_notice_days")
    if not scn or any(k not in scn for k in required_scn):
        errors.append("scenario_assumptions missing or incomplete (transparent scenarios are mandatory)")

    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(m.get("reason", "")) for m in metrics])
    for pat in PROHIBITED_PATTERNS:
        mt = re.search(pat, text, re.I)
        if mt:
            errors.append(f"recommendation/action/determination language detected: {mt.group(0)!r} "
                          "(R2 evidences under scenarios; it does not recommend, act, or determine breach)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer")

    if breached and not (pack.get("caveats")):
        errors.append("metrics breached but no modeling caveats included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "analysis_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
