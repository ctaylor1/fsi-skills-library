#!/usr/bin/env python3
"""Deterministic, explainable anomaly-signal computation for account-anomaly-screener.

Reads an activity file (see validate_input.py), computes the configured signals, attaches
evidence + citations to each fired signal, and maps the fired set to a review-priority
band. Emits a machine-readable core the SKILL wraps in a plain-language pack.

IMPORTANT: This produces explainable *signals and a triage suggestion* only. It never
produces a fraud determination or an account action. The priority mapping is deterministic
and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py activity.json | --selftest
Prints the screening JSON to stdout.
"""
from __future__ import annotations
import json, statistics, sys
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_CONFIG = {
    "amount_k": 3.0, "velocity_max": 10, "velocity_window_hours": 1,
    "new_payee_amount": 1000.0, "dormancy_days": 120, "reactivation_amount": 500.0,
    "cluster_count": 3, "cluster_days": 7, "cluster_under_threshold": 10000.0,
    "round_multiple": 100.0, "passthrough_hours": 48, "min_baseline_n": 10,
}
DISCLAIMER = "Screening evidence only; not a fraud determination. No account action has been taken."


def _parse_dt(s: str) -> datetime:
    s = str(s)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.strptime(s[:10], "%Y-%m-%d")  # tolerant fallback (date only)


def _has_time(s: str) -> bool:
    return "T" in str(s)


def _cite(t: dict) -> str:
    return f"txns:{t.get('source_ref','?')}@{t.get('date','?')}"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    txns = sorted(doc["transactions"], key=lambda t: str(t["date"]))
    focal_ids = set(doc["focal_txn_ids"])
    focal = [t for t in txns if t["txn_id"] in focal_ids]
    baseline = [t for t in txns if t["txn_id"] not in focal_ids]
    crm = doc.get("crm") or {}
    known_payees = {str(p).lower() for p in crm.get("known_payees", [])}
    travel = {str(c).upper() for c in crm.get("travel_notice_countries", [])}
    as_of = _parse_dt(doc["as_of"])

    signals, not_evaluable = [], []

    def add(name, fired, reason, evidence, baseline_desc, contribution):
        signals.append({"signal": name, "fired": fired, "reason": reason,
                        "evidence": evidence, "baseline": baseline_desc,
                        "contribution": contribution})

    # amount_vs_history (debits)
    base_debits = [float(t["amount"]) for t in baseline if t["direction"] == "debit"]
    if len(base_debits) >= cfg["min_baseline_n"]:
        mean = statistics.mean(base_debits)
        stdev = statistics.pstdev(base_debits) or 0.0
        thr = mean + cfg["amount_k"] * stdev
        hits = [t for t in focal if t["direction"] == "debit" and float(t["amount"]) > thr]
        add("amount_vs_history", bool(hits),
            f"focal debit(s) exceed baseline mean {mean:.2f} + {cfg['amount_k']}*stdev {stdev:.2f} = {thr:.2f}"
            if hits else f"no focal debit exceeds {thr:.2f}",
            [{"txn_id": t["txn_id"], "amount": t["amount"], "citation": _cite(t)} for t in hits],
            {"mean": round(mean, 2), "stdev": round(stdev, 2), "threshold": round(thr, 2), "n": len(base_debits)},
            len(hits))
    else:
        not_evaluable.append({"signal": "amount_vs_history", "why": f"baseline debits {len(base_debits)} < {cfg['min_baseline_n']}"})

    # velocity (needs timestamps)
    timed = [t for t in txns if _has_time(t["date"])]
    if len(timed) >= 2:
        window = timedelta(hours=cfg["velocity_window_hours"])
        times = sorted(_parse_dt(t["date"]) for t in timed)
        max_in_window, burst = 0, []
        for i, ti in enumerate(times):
            grp = [tj for tj in times if ti <= tj < ti + window]
            if len(grp) > max_in_window:
                max_in_window = len(grp)
        fired = max_in_window > cfg["velocity_max"]
        if fired:
            burst = [{"txn_id": t["txn_id"], "date": t["date"], "citation": _cite(t)} for t in timed]
        add("velocity", fired,
            f"max {max_in_window} txns within {cfg['velocity_window_hours']}h (limit {cfg['velocity_max']})",
            burst, {"max_in_window": max_in_window, "limit": cfg["velocity_max"]}, max_in_window if fired else 0)
    else:
        not_evaluable.append({"signal": "velocity", "why": "no timestamps"})

    # new_counterparty_high_value
    prior_payees = {str(t.get("counterparty", "")).lower() for t in baseline if t.get("counterparty")}
    ncp = [t for t in focal if t["direction"] == "debit" and t.get("counterparty")
           and str(t["counterparty"]).lower() not in prior_payees
           and str(t["counterparty"]).lower() not in known_payees
           and float(t["amount"]) >= cfg["new_payee_amount"]]
    add("new_counterparty_high_value", bool(ncp),
        f"first-seen payee with amount >= {cfg['new_payee_amount']}" if ncp else "no new high-value payee",
        [{"txn_id": t["txn_id"], "counterparty": t["counterparty"], "amount": t["amount"], "citation": _cite(t)} for t in ncp],
        {"new_payee_amount": cfg["new_payee_amount"], "known_payees_checked": True}, len(ncp))

    # geo_novelty
    prior_geo = {str(t.get("country", "")).upper() for t in baseline if t.get("country")}
    geo = [t for t in focal if t.get("country") and str(t["country"]).upper() not in prior_geo
           and str(t["country"]).upper() not in travel]
    add("geo_novelty", bool(geo),
        "focal txn in country not seen in lookback and no CRM travel notice" if geo else "no novel geography",
        [{"txn_id": t["txn_id"], "country": t["country"], "citation": _cite(t)} for t in geo],
        {"prior_countries": sorted(prior_geo), "travel_notice": sorted(travel)}, len(geo))

    # dormancy_reactivation
    pre_dates = [_parse_dt(t["date"]) for t in baseline]
    if pre_dates and focal:
        last_active = max(pre_dates)
        first_focal = min(_parse_dt(t["date"]) for t in focal)
        gap = (first_focal - last_active).days
        big = [t for t in focal if t["direction"] == "debit" and float(t["amount"]) >= cfg["reactivation_amount"]]
        fired = gap >= cfg["dormancy_days"] and bool(big)
        add("dormancy_reactivation", fired,
            f"account inactive {gap}d (>= {cfg['dormancy_days']}) then debit >= {cfg['reactivation_amount']}"
            if fired else f"gap {gap}d",
            [{"txn_id": t["txn_id"], "amount": t["amount"], "citation": _cite(t)} for t in big] if fired else [],
            {"last_active": last_active.strftime("%Y-%m-%d"), "gap_days": gap}, 1 if fired else 0)

    # round_amount_clustering (factual pattern only)
    win_start = as_of - timedelta(days=cfg["cluster_days"])
    cluster = [t for t in txns if t["direction"] == "debit"
               and win_start <= _parse_dt(t["date"]) <= as_of
               and float(t["amount"]) % cfg["round_multiple"] == 0
               and 0.5 * cfg["cluster_under_threshold"] <= float(t["amount"]) < cfg["cluster_under_threshold"]]
    fired = len(cluster) >= cfg["cluster_count"]
    add("round_amount_clustering", fired,
        f"{len(cluster)} round debits just under {cfg['cluster_under_threshold']} within {cfg['cluster_days']}d (pattern only, not intent)"
        if fired else f"{len(cluster)} clustered round debits (below count {cfg['cluster_count']})",
        [{"txn_id": t["txn_id"], "amount": t["amount"], "citation": _cite(t)} for t in cluster] if fired else [],
        {"count": len(cluster), "threshold": cfg["cluster_under_threshold"]}, len(cluster) if fired else 0)

    # rapid_in_out (needs timestamps)
    if len(timed) >= 2:
        fired_rows = []
        for c in [t for t in timed if t["direction"] == "credit"]:
            ct = _parse_dt(c["date"])
            outs = [t for t in timed if t["direction"] == "debit"
                    and ct <= _parse_dt(t["date"]) <= ct + timedelta(hours=cfg["passthrough_hours"])]
            if outs and sum(float(o["amount"]) for o in outs) >= 0.8 * float(c["amount"]) and float(c["amount"]) >= cfg["reactivation_amount"]:
                fired_rows.append({"credit": c["txn_id"], "debits": [o["txn_id"] for o in outs],
                                   "citation": _cite(c)})
        add("rapid_in_out", bool(fired_rows),
            "large credit largely withdrawn within pass-through window (pattern only)" if fired_rows else "no rapid in/out",
            fired_rows, {"passthrough_hours": cfg["passthrough_hours"]}, len(fired_rows))
    else:
        not_evaluable.append({"signal": "rapid_in_out", "why": "no timestamps"})

    fired_names = [s["signal"] for s in signals if s["fired"]]
    # deterministic priority mapping (see references/domain-rules.md)
    escalators = {"rapid_in_out", "round_amount_clustering"}
    if len(fired_names) >= 3 or (escalators & set(fired_names)):
        priority = "Elevated"
    elif len(fired_names) >= 1:
        priority = "Review"
    else:
        priority = "Informational"

    benign = []
    if fired_names:
        benign = ["payroll/benefit or tax-refund change", "seasonal spending", "a genuine large purchase",
                  "travel or relocation (verify CRM travel notice)", "a new recurring biller",
                  "customer using a new device/branch"]

    return {
        "screening_id": f"aas-{doc['account_id'].replace('*','')}-{doc['as_of']}-0001",
        "account_id": doc["account_id"],
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "window": {"lookback_days": doc.get("lookback_days"), "as_of": doc["as_of"]},
        "signals": signals,
        "fired_signals": fired_names,
        "not_evaluable": not_evaluable,
        "suggested_priority": priority,
        "benign_prompts": benign,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "activity_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
