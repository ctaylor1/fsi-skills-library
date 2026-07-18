#!/usr/bin/env python3
"""Deterministic output validation for merchant-fee-optimizer (R2 guardrail screen).

Validates the final fee-optimization pack before it is presented or delivered. Checks:
  1. Every fired opportunity has >= 1 cited evidence row and >= 1 stated assumption.
  2. Every fired opportunity is a RANGE estimate (est_savings_low <= est_savings_high, both
     >= 0) and is not flagged guaranteed — no single "certain" savings number.
  3. total_estimated_savings ties out to the sum of the fired opportunities, and the annual
     figures equal 12 x the monthly figures (reproducibility / no double counting).
  4. No prohibited/binding language: no savings guarantee, no directive to sign/terminate/
     cancel/switch a processor or contract, no legal/tax/accounting advice.
  5. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = (
    "Estimated savings and analysis only, based on the stated assumptions and the statement "
    "period reviewed. This is not a guarantee of savings and not a recommendation to sign, "
    "terminate, or change any processor or contract; it is not legal, tax, or accounting "
    "advice. Interchange and network fees change frequently; validate against current "
    "published schedules and obtain human review before acting."
)

# Binding-commitment / guarantee / advice assertions an R2 analytical skill must not make.
PROHIBITED_PATTERNS = [
    r"\bguarantee(d|s)?\b", r"\bguaranteed savings\b", r"\brisk[- ]free\b", r"\bno[- ]risk\b",
    r"\byou will save\b", r"\bwe will save\b", r"\bwill save you\b",
    r"\bwe recommend (switching|terminating|cancelling|canceling|signing)\b",
    r"\byou should (switch|terminate|cancel|sign)\b",
    r"\bterminate (the|your) contract\b", r"\bcancel (the|your) contract\b",
    r"\bsign (this|the) (contract|agreement)\b",
    r"\blegally (binding|enforceable|unenforceable|void)\b", r"\bthis is legal advice\b",
]


def _n(v):
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    opps = pack.get("opportunities") or []
    if not isinstance(opps, list):
        return ["opportunities must be a list"]
    fired = [o for o in opps if o.get("fired")]

    for o in fired:
        name = o.get("opportunity", "?")
        ev = o.get("evidence") or []
        if not ev:
            errors.append(f"fired opportunity {name} has no evidence")
        for row in ev:
            if not str(row.get("citation") or "").strip():
                errors.append(f"fired opportunity {name} evidence row missing citation")
        if not (o.get("assumptions") or []):
            errors.append(f"fired opportunity {name} has no stated assumptions")
        lo, hi = _n(o.get("est_savings_low")), _n(o.get("est_savings_high"))
        if lo is None or hi is None:
            errors.append(f"fired opportunity {name} missing numeric est_savings_low/high (must be a range)")
        else:
            if lo < 0 or hi < 0:
                errors.append(f"fired opportunity {name} has negative savings estimate")
            if lo > hi:
                errors.append(f"fired opportunity {name} est_savings_low {lo} > est_savings_high {hi}")
        if o.get("guaranteed") is True:
            errors.append(f"fired opportunity {name} flagged guaranteed (R2 estimates, does not guarantee)")

    # tie-out: totals equal the sum of fired opportunities
    total = pack.get("total_estimated_savings") or {}
    exp_low = round(sum(_n(o.get("est_savings_low")) or 0.0 for o in fired), 2)
    exp_high = round(sum(_n(o.get("est_savings_high")) or 0.0 for o in fired), 2)
    if abs((_n(total.get("monthly_low")) or 0.0) - exp_low) > 0.01:
        errors.append(f"total_estimated_savings.monthly_low {total.get('monthly_low')} != sum of fired lows {exp_low}")
    if abs((_n(total.get("monthly_high")) or 0.0) - exp_high) > 0.01:
        errors.append(f"total_estimated_savings.monthly_high {total.get('monthly_high')} != sum of fired highs {exp_high}")
    if total:
        if abs((_n(total.get("annual_low")) or 0.0) - round(exp_low * 12, 2)) > 0.01:
            errors.append("total_estimated_savings.annual_low != 12 x monthly_low")
        if abs((_n(total.get("annual_high")) or 0.0) - round(exp_high * 12, 2)) > 0.01:
            errors.append("total_estimated_savings.annual_high != 12 x monthly_high")
    if fired and not total:
        errors.append("opportunities fired but no total_estimated_savings provided")

    # prohibited/binding-language scan (everything except the disclaimer field)
    parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    for o in opps:
        parts.append(str(o.get("description", "")))
        parts.extend(str(a) for a in (o.get("assumptions") or []))
    for ob in (pack.get("observations") or []):
        parts.append(str(ob.get("note", "")))
    parts.extend(str(c) for c in (pack.get("contract_flags") or []))
    text = " ".join(parts)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited/binding language detected: {m.group(0)!r} (R2 estimates and advises options; it does not guarantee or direct a binding decision)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
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
