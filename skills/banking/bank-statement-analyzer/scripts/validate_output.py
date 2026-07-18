#!/usr/bin/env python3
"""Deterministic output validation for bank-statement-analyzer.

Validates the final analysis pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. Checks:
  1. Every extracted income source, recurring obligation, and fee has >= 1 cited evidence row;
     every fired anomaly has >= 1 cited evidence row.
  2. Tie-outs hold: net_cash_flow == total_credits - total_debits; income total == sum of its
     evidence amounts; fee total == sum of its evidence amounts (to the cent).
  3. No lending/credit/affordability decision or personalized-advice language (R2 boundary).
  4. The standing disclaimer is present.
  5. confidence_flags are included when any anomaly fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Analysis and extracted figures only; not a lending decision, eligibility "
              "determination, or financial advice.")

# Decision / advice assertions that an R2 analytical skill must not make:
DECISION_PATTERNS = [
    r"\byou (are )?(pre-?)?approved\b", r"\bapproved for\b", r"\byou qualify\b",
    r"\bpre-?qualif", r"\beligible for (the )?(loan|credit|mortgage|line)\b",
    r"\byou are eligible\b", r"\bdenied\b", r"\bdecline(d)? the (loan|application)\b",
    r"\bcredit ?worthy\b", r"\byou can afford\b", r"\baffordability (is )?approved\b",
    r"\bincome (is )?verified for underwriting\b", r"\bguaranteed approval\b",
    r"\byou should (refinance|invest|consolidate|take out|borrow)\b",
    r"\bwe recommend you (refinance|invest|consolidate|take out|borrow|buy)\b",
    r"\bthis is fraud\b", r"\bfraudulent\b",
]


def _sum_ev(evidence) -> float:
    return round(sum(float(r.get("amount", 0) or 0) for r in (evidence or [])), 2)


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    # 1. evidence + citation coverage
    income = pack.get("income_summary") or {}
    for r in income.get("evidence") or []:
        if not (r.get("citation") or "").strip():
            errors.append("income evidence row missing citation")
    if income.get("count", 0) and not income.get("evidence"):
        errors.append("income_summary reports a count but has no evidence")

    for o in pack.get("recurring_obligations") or []:
        ev = o.get("evidence") or []
        if not ev:
            errors.append(f"recurring obligation {o.get('counterparty')!r} has no evidence")
        for r in ev:
            if not (r.get("citation") or "").strip():
                errors.append(f"recurring obligation {o.get('counterparty')!r} evidence row missing citation")

    fees = pack.get("fees") or {}
    for r in fees.get("evidence") or []:
        if not (r.get("citation") or "").strip():
            errors.append("fee evidence row missing citation")
    if fees.get("count", 0) and not fees.get("evidence"):
        errors.append("fees report a count but have no evidence")

    anomalies = pack.get("anomalies") or []
    fired = [a for a in anomalies if a.get("fired")]
    for a in fired:
        ev = a.get("evidence") or []
        if not ev:
            errors.append(f"fired anomaly {a.get('anomaly')} has no evidence")
        for r in ev:
            if not (r.get("citation") or "").strip():
                errors.append(f"fired anomaly {a.get('anomaly')} evidence row missing citation")

    # 2. tie-outs
    cf = pack.get("cash_flow") or {}
    tc, td, net = cf.get("total_credits"), cf.get("total_debits"), cf.get("net_cash_flow")
    if None not in (tc, td, net):
        if abs(round(tc - td, 2) - round(net, 2)) >= 0.01:
            errors.append(f"cash-flow tie-out failed: {tc} - {td} != net_cash_flow {net}")
    else:
        errors.append("cash_flow missing total_credits/total_debits/net_cash_flow")

    if income.get("evidence") is not None and income.get("total") is not None:
        if abs(_sum_ev(income.get("evidence")) - round(float(income["total"]), 2)) >= 0.01:
            errors.append(f"income tie-out failed: evidence sum {_sum_ev(income.get('evidence'))} "
                          f"!= total {income['total']}")
    if fees.get("evidence") is not None and fees.get("total") is not None:
        if abs(_sum_ev(fees.get("evidence")) - round(float(fees["total"]), 2)) >= 0.01:
            errors.append(f"fee tie-out failed: evidence sum {_sum_ev(fees.get('evidence'))} "
                          f"!= total {fees['total']}")

    # 3. no decision / advice language (narrative + notes + anomaly reasons)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(a.get("reason", "")) for a in anomalies])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"decision/advice language detected: {m.group(0)!r} "
                          f"(R2 extracts and calculates; it does not decide or advise)")

    # 4. standing disclaimer
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer")

    # 5. confidence flags when anomalies fired
    if fired and not (pack.get("confidence_flags")):
        errors.append("anomalies fired but no confidence_flags included")

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
