#!/usr/bin/env python3
"""Deterministic, explainable best-execution checks for best-execution-reviewer.

Reads an executions file (see validate_input.py), evaluates each execution against the
versioned firm best-execution policy thresholds, attaches evidence + citations to each
finding, and maps the fired finding-set to a SUGGESTED review disposition band.

IMPORTANT: This produces explainable *findings and a triage suggestion* only. It never
makes a best-execution or compliance determination, closes a case/exception, files, or
writes a system of record. The disposition mapping is deterministic and documented in
references/domain-rules.md. Escalation and any regulated decision are human.

Usage:
  python calculate_or_transform.py executions.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "price_tolerance_bps": 5.0,    # adverse price deviation vs benchmark that flags for review
    "price_hard_bps": 25.0,        # adverse deviation treated as material (escalator)
    "latency_max_seconds": 60.0,   # arrival->execution latency ceiling
    "min_fill_rate": 0.90,         # minimum fill rate for evaluated order types
    "fill_order_types": ["market"],  # order types for which low fill is a finding
    "cost_cap_bps": 30.0,          # explicit + implicit cost ceiling in bps of notional
    "approved_venues": [],         # effective venue list; empty = venue check not enforced
    "min_population": 5,
}
DISCLAIMER = ("Best-execution review evidence only; not a best-execution or compliance "
              "determination. No case has been closed, no exception has been dispositioned, "
              "no filing has been made, and no system of record has been updated.")
# Findings that escalate on their own (material price miss, off-policy venue, undocumented exception).
ESCALATORS = {"price_materially_off", "venue_off_policy", "exception_undocumented"}
KNOWN_FINDINGS = [
    "price_outside_benchmark", "price_materially_off", "slow_execution",
    "low_fill_rate", "high_cost", "venue_off_policy", "exception_undocumented",
]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_dt(s):
    if not s:
        return None
    s = str(s)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _cite(e):
    when = e.get("execution_ts") or e.get("arrival_ts") or "?"
    return f"oms:{e.get('source_ref','?')}@{when}"


def _adverse_bps(side, price, bench):
    """Client-adverse deviation in bps: positive = worse for the client."""
    if bench in (None, 0) or price is None:
        return None
    if side == "buy":
        return (price - bench) / bench * 10000.0
    return (bench - price) / bench * 10000.0


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    exes = doc["executions"]
    approved = {str(v).upper() for v in (cfg.get("approved_venues") or [])}
    fill_types = {str(t).lower() for t in (cfg.get("fill_order_types") or [])}
    as_of = doc["as_of"]

    # evidence buckets per finding type + not-evaluable counters
    ev = {name: [] for name in KNOWN_FINDINGS}
    ne = {"price": 0, "latency": 0, "venue": 0, "cost": 0, "fill": 0}

    for e in exes:
        side = e.get("side")
        price = _num(e.get("execution_price"))
        bench = _num(e.get("benchmark_price"))
        oq, xq = _num(e.get("order_qty")), _num(e.get("executed_qty"))
        commission = _num(e.get("commission"))
        adv = _adverse_bps(side, price, bench)
        cite = _cite(e)

        # price checks (need a benchmark)
        if adv is None:
            ne["price"] += 1
        else:
            if adv > cfg["price_tolerance_bps"]:
                ev["price_outside_benchmark"].append({
                    "execution_id": e.get("execution_id"), "side": side,
                    "execution_price": price, "benchmark_price": bench,
                    "benchmark_type": e.get("benchmark_type"),
                    "adverse_bps": round(adv, 2), "citation": cite})
            if adv > cfg["price_hard_bps"]:
                ev["price_materially_off"].append({
                    "execution_id": e.get("execution_id"), "side": side,
                    "adverse_bps": round(adv, 2), "hard_bps": cfg["price_hard_bps"],
                    "citation": cite})

        # latency (needs both timestamps)
        a_dt, x_dt = _parse_dt(e.get("arrival_ts")), _parse_dt(e.get("execution_ts"))
        if a_dt and x_dt:
            lat = (x_dt - a_dt).total_seconds()
            if lat > cfg["latency_max_seconds"]:
                ev["slow_execution"].append({
                    "execution_id": e.get("execution_id"), "latency_seconds": round(lat, 2),
                    "limit_seconds": cfg["latency_max_seconds"], "citation": cite})
        else:
            ne["latency"] += 1

        # fill rate (only for configured order types)
        otype = str(e.get("order_type") or "").lower()
        if otype in fill_types and oq:
            fill = xq / oq if oq else 1.0
            if fill < cfg["min_fill_rate"]:
                ev["low_fill_rate"].append({
                    "execution_id": e.get("execution_id"), "order_type": otype,
                    "fill_rate": round(fill, 4), "min_fill_rate": cfg["min_fill_rate"],
                    "citation": cite})
        elif otype and otype not in fill_types:
            ne["fill"] += 1

        # cost (explicit commission bps + implicit adverse bps; needs benchmark + commission)
        notional = (xq * price) if (xq is not None and price is not None) else None
        if bench is None or commission is None or not notional:
            ne["cost"] += 1
        else:
            explicit_bps = commission / notional * 10000.0
            implicit_bps = max(adv, 0.0) if adv is not None else 0.0
            cost_bps = explicit_bps + implicit_bps
            if cost_bps > cfg["cost_cap_bps"]:
                ev["high_cost"].append({
                    "execution_id": e.get("execution_id"),
                    "explicit_bps": round(explicit_bps, 2),
                    "implicit_bps": round(implicit_bps, 2),
                    "cost_bps": round(cost_bps, 2), "cap_bps": cfg["cost_cap_bps"],
                    "citation": cite})

        # venue policy (needs an effective approved-venue list)
        venue = e.get("venue")
        if not approved:
            ne["venue"] += 1
        elif venue and str(venue).upper() not in approved:
            ev["venue_off_policy"].append({
                "execution_id": e.get("execution_id"), "venue": venue,
                "citation": cite})

        # undocumented exception
        if e.get("exception_flag") and not str(e.get("exception_rationale_ref") or "").strip():
            ev["exception_undocumented"].append({
                "execution_id": e.get("execution_id"),
                "exception_flag": True, "exception_rationale_ref": None, "citation": cite})

    reasons = {
        "price_outside_benchmark": f"execution price adverse to benchmark by more than {cfg['price_tolerance_bps']} bps",
        "price_materially_off": f"execution price adverse to benchmark by more than {cfg['price_hard_bps']} bps (material)",
        "slow_execution": f"arrival-to-execution latency exceeds {cfg['latency_max_seconds']}s",
        "low_fill_rate": f"fill rate below policy minimum {cfg['min_fill_rate']} for an evaluated order type",
        "high_cost": f"explicit + implicit cost exceeds {cfg['cost_cap_bps']} bps of notional",
        "venue_off_policy": "executed on a venue not in the effective approved-venue list",
        "exception_undocumented": "manual/exception route flagged with no documented rationale reference",
    }
    findings = []
    for name in KNOWN_FINDINGS:
        rows = ev[name]
        fired = bool(rows)
        findings.append({
            "finding": name, "fired": fired,
            "reason": reasons[name] if fired else f"no execution triggered {name}",
            "evidence": rows, "count": len(rows),
        })

    fired_findings = [f["finding"] for f in findings if f["fired"]]
    if any(x in ESCALATORS for x in fired_findings) or len(fired_findings) >= 3:
        disposition = "Escalate"
    elif fired_findings:
        disposition = "Review"
    else:
        disposition = "Pass"

    not_evaluable = []
    labels = {"price": "price/cost (missing benchmark)", "latency": "slow_execution (missing timestamps)",
              "venue": "venue_off_policy (no approved-venue list)", "cost": "high_cost (missing benchmark/commission)",
              "fill": "low_fill_rate (order type not in scope)"}
    for k, n in ne.items():
        if n:
            not_evaluable.append({"check": labels[k], "executions_affected": n})

    fp_checks = []
    if fired_findings:
        fp_checks = [
            "benchmark source/timestamp: confirm the arrival benchmark (NBBO/EBBO/arrival mid) matches the order's decision time and market convention",
            "order type & client instruction: a limit or client-directed order may legitimately show partial fills or off-touch prices",
            "market conditions: volatility, auctions, halts, or thin liquidity can widen spreads within policy",
            "venue list version: verify the execution venue against the approved-venue list effective on the trade date",
            "documented exception: check the OMS/EMS annotation and communications archive for a rationale before treating an exception as undocumented",
            "order size & working strategy: large or illiquid orders may be worked over time by design",
        ]

    return {
        "review_id": f"ber-{as_of}-0001",
        "as_of": as_of,
        "policy_version": doc.get("policy_version"),
        "client_classification": doc.get("client_classification"),
        "population": {"executions": len(exes), "fired_finding_types": len(fired_findings)},
        "findings": findings,
        "fired_findings": fired_findings,
        "not_evaluable": not_evaluable,
        "suggested_disposition": disposition,
        "fp_checks": fp_checks,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "executions_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
