#!/usr/bin/env python3
"""Deterministic allocation-policy checks for order-allocation-validator.

Tests a PROPOSED allocation against the approved policy: quantity tie-out, pro-rata (or
price-time) target vs proposed within tolerance, eligibility, timestamp ordering, and
documented-deviation rule. Emits an exception-evidence packet with a review-only disposition.
Never allocates, amends, books, or decides — evidence only.

Usage: python calculate_or_transform.py alloc.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_POLICY = {"method": "pro_rata", "tolerance_pct": 0.5, "lot_size": 1.0}
DISCLAIMER = ("Allocation-exception evidence only; not an allocation decision, amendment, or "
              "compliance certification. No order has been allocated or booked.")


def _num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _round_lot(x, lot):
    return round(x / lot) * lot if lot else x


def compute(doc: dict) -> dict:
    o = doc["order"]
    pol = {**DEFAULT_POLICY, **(doc.get("policy") or {})}
    lot = _num(pol.get("lot_size"), 1.0) or 1.0
    tol = _num(pol.get("tolerance_pct"), 0.5)
    executed = _num(o.get("executed_qty"))
    order_ts, cutoff = str(o.get("order_ts")), str(o.get("batch_cutoff"))
    lines = doc["allocations"]

    exceptions = []

    def exc(acct, rule, expected, proposed, reason, ref):
        exceptions.append({"account_id": acct, "rule": rule, "expected": expected,
                           "proposed": proposed, "reason": reason,
                           "citation": f"oms:{ref}"})

    # quantity tie / break
    total = round(sum(_num(a.get("proposed_qty")) for a in lines), 8)
    quantity_break = abs(total - executed) > 1e-6

    for a in lines:
        acct = a.get("account_id")
        ref = a.get("source_ref", "?")
        proposed = _num(a.get("proposed_qty"))
        weight = _num(a.get("participation_weight"))
        target = _round_lot(executed * weight, lot)
        # pro-rata deviation
        dev = abs(proposed - target)
        limit = abs(target) * (tol / 100.0)
        deviated = dev > limit + 1e-9
        if deviated:
            exc(acct, "pro_rata", round(target, 6), round(proposed, 6),
                f"deviation {dev:.4f} > tolerance {limit:.4f}", ref)
            if not (a.get("deviation_reason") or "").strip():
                exc(acct, "deviation_documented", "documented reason", "none",
                    "pro-rata deviation without a documented reason", ref)
        # eligibility
        if a.get("eligible") is False:
            exc(acct, "eligibility", "eligible/entitled", "ineligible",
                "account flagged ineligible/restricted for this instrument", ref)
        # timestamp ordering
        ats = str(a.get("allocation_ts"))
        if ats < order_ts:
            exc(acct, "timestamp", f">= order_ts {order_ts}", ats,
                "allocation timestamp precedes the execution", ref)
        elif cutoff and ats > cutoff:
            exc(acct, "timestamp", f"<= cutoff {cutoff}", ats,
                "allocation timestamp after the batch cutoff", ref)

    disposition = "clean" if not exceptions and not quantity_break else "exceptions-for-review"
    return {
        "validation_id": f"oav-{o.get('order_id','UNKNOWN')}-0001",
        "order_id": o.get("order_id"),
        "policy_version": pol.get("config_version"),
        "executed_qty": executed, "allocated_qty": total,
        "quantity_break": quantity_break,
        "checks_run": ["quantity_tie", "pro_rata", "eligibility", "timestamp", "deviation_documented"],
        "exceptions": exceptions,
        "suggested_disposition": disposition,
        "route": "trade-break-resolver" if quantity_break else None,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "allocation_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
