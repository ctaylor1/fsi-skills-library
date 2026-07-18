#!/usr/bin/env python3
"""Deterministic, explainable cash-flow forecast engine for cashflow-forecaster.

Reads a forecast-input file (see validate_input.py), derives recurring inflow/outflow
levels and net-flow volatility from history, ranks the key drivers, and projects a running
balance forward over the horizon for three scenarios (base, upside, downside) using
documented, versioned scenario factors plus explicit user-supplied one-off assumptions.
Every scenario carries its own tie-out; every assumption carries a provenance tag.

IMPORTANT: This produces a transparent *planning model* only. It never gives financial,
investment, tax, or credit advice, never approves or denies credit, and never guarantees a
future balance. Scenario factors are configuration (versioned), not per-user judgments.
See references/domain-rules.md.

Usage:
  python calculate_or_transform.py forecast_input.json | --selftest
Prints the forecast JSON to stdout.
"""
from __future__ import annotations
import json, statistics, sys
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_CONFIG = {
    "base_inflow_factor": 1.0, "base_outflow_factor": 1.0,
    "upside_inflow_factor": 1.05, "upside_outflow_factor": 0.95,
    "downside_inflow_factor": 0.90, "downside_outflow_factor": 1.10,
    "volatility_k": 1.0, "tolerance": 0.01, "min_history_periods": 3,
}
DISCLAIMER = ("Forecast for planning purposes only; not financial, investment, tax, or "
              "credit advice, and not a guarantee of future account balances. Assumptions "
              "are estimates and actual results will vary.")


def _parse_dt(s: str) -> datetime:
    s = str(s)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.strptime(s[:10], "%Y-%m-%d")


def _hist_key(date_str: str, period: str) -> str:
    if period == "month":
        return str(date_str)[:7]
    iso = _parse_dt(date_str).isocalendar()
    return f"{iso[0]:04d}-W{iso[1]:02d}"


def _future_labels(as_of: str, period: str, n: int) -> list[str]:
    dt = _parse_dt(as_of)
    labels = []
    if period == "month":
        for i in range(1, n + 1):
            mm = dt.month + i
            yy = dt.year + (mm - 1) // 12
            mmm = (mm - 1) % 12 + 1
            labels.append(f"{yy:04d}-{mmm:02d}")
    else:
        for i in range(1, n + 1):
            iso = (dt + timedelta(days=7 * i)).isocalendar()
            labels.append(f"{iso[0]:04d}-W{iso[1]:02d}")
    return labels


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    tol = float(cfg["tolerance"])
    period = doc["period"]
    horizon = int(doc["horizon_periods"])
    opening = round(float(doc["opening_balance"]), 2)
    txns = doc["transactions"]

    # --- historical spread by period and by driver -------------------------------------
    buckets: dict[str, dict] = {}
    drivers_net: dict[str, float] = {}
    for t in txns:
        key = _hist_key(t["date"], period)
        b = buckets.setdefault(key, {"inflow": 0.0, "outflow": 0.0})
        amt = float(t["amount"])
        signed = amt if t["direction"] == "credit" else -amt
        b["inflow" if t["direction"] == "credit" else "outflow"] += amt
        label = t.get("category") or t.get("counterparty") or "Uncategorized"
        drivers_net[label] = drivers_net.get(label, 0.0) + signed

    hist_keys = sorted(buckets)
    per_inflow = [buckets[k]["inflow"] for k in hist_keys]
    per_outflow = [buckets[k]["outflow"] for k in hist_keys]
    per_net = [i - o for i, o in zip(per_inflow, per_outflow)]
    avg_inflow = statistics.mean(per_inflow) if per_inflow else 0.0
    avg_outflow = statistics.mean(per_outflow) if per_outflow else 0.0
    net_vol = statistics.pstdev(per_net) if len(per_net) >= 2 else 0.0

    # --- drivers (ranked by absolute net contribution) ---------------------------------
    total_abs = sum(abs(v) for v in drivers_net.values()) or 1.0
    drivers = [{"category": k, "net": round(v, 2), "share": round(abs(v) / total_abs, 4)}
               for k, v in drivers_net.items()]
    drivers.sort(key=lambda d: abs(d["net"]), reverse=True)

    # --- assumptions: derived (from history) + user-supplied one-offs -------------------
    register = [
        {"id": "derived:avg_inflow", "provenance": "derived-from-history",
         "value": round(avg_inflow, 2), "description": "mean historical inflow per period"},
        {"id": "derived:avg_outflow", "provenance": "derived-from-history",
         "value": round(avg_outflow, 2), "description": "mean historical outflow per period"},
        {"id": "derived:net_volatility", "provenance": "derived-from-history",
         "value": round(net_vol, 2), "description": "population stdev of historical net flow"},
    ]
    oneoffs: dict[int, float] = {}
    for a in doc.get("assumptions") or []:
        off = int(a["offset"])
        signed = float(a["amount"]) * (1 if a["direction"] == "credit" else -1)
        if 1 <= off <= horizon:
            oneoffs[off] = oneoffs.get(off, 0.0) + signed
        register.append({"id": a["id"], "provenance": (a.get("provenance") or "user-supplied"),
                         "value": float(a["amount"]), "direction": a["direction"],
                         "offset": off, "description": a.get("description", "")})

    labels = _future_labels(doc["as_of"], period, horizon)

    def project(name: str, inflow_factor: float, outflow_factor: float) -> dict:
        inflow = round(avg_inflow * inflow_factor, 2)
        outflow = round(avg_outflow * outflow_factor, 2)
        bal = opening
        rows = []
        for i, label in enumerate(labels, start=1):
            one = round(oneoffs.get(i, 0.0), 2)
            net = round(inflow - outflow + one, 2)
            bal = round(bal + net, 2)
            rows.append({"period_index": i, "label": label, "inflow": inflow,
                         "outflow": outflow, "one_off": one, "net": net, "balance": bal})
        ending = rows[-1]["balance"] if rows else opening
        sum_net = round(sum(r["net"] for r in rows), 2)
        low = min(rows, key=lambda r: r["balance"]) if rows else {"balance": opening, "label": None}
        return {
            "name": name,
            "factors": {"inflow_factor": inflow_factor, "outflow_factor": outflow_factor},
            "recurring_inflow": inflow, "recurring_outflow": outflow,
            "periods": rows, "ending_balance": ending,
            "lowest_balance": low["balance"], "lowest_period": low["label"],
            "tieout": {"opening": opening, "sum_net": sum_net, "ending": ending,
                       "ok": abs(opening + sum_net - ending) <= tol},
        }

    scenarios = [
        project("base", cfg["base_inflow_factor"], cfg["base_outflow_factor"]),
        project("upside", cfg["upside_inflow_factor"], cfg["upside_outflow_factor"]),
        project("downside", cfg["downside_inflow_factor"], cfg["downside_outflow_factor"]),
    ]

    raw_sum_net = round(sum((float(t["amount"]) if t["direction"] == "credit"
                             else -float(t["amount"])) for t in txns), 2)
    recon_sum_net = round(sum(per_net), 2)

    entity = str(doc["entity_id"])
    return {
        "forecast_id": f"cff-{entity.replace('*', '')}-{doc['as_of']}-0001",
        "entity_id": entity,
        "as_of": doc["as_of"],
        "period": period,
        "horizon_periods": horizon,
        "config_version": doc.get("config_version"),
        "opening_balance": opening,
        "history": {
            "periods": [{"label": k, "inflow": round(buckets[k]["inflow"], 2),
                         "outflow": round(buckets[k]["outflow"], 2),
                         "net": round(buckets[k]["inflow"] - buckets[k]["outflow"], 2)}
                        for k in hist_keys],
            "n_periods": len(hist_keys),
            "avg_inflow": round(avg_inflow, 2),
            "avg_outflow": round(avg_outflow, 2),
            "net_volatility": round(net_vol, 2),
        },
        "drivers": drivers,
        "scenarios": scenarios,
        "uncertainty": {
            "method": "historical net-flow volatility (population stdev)",
            "k": cfg["volatility_k"],
            "band_per_period": round(cfg["volatility_k"] * net_vol, 2),
        },
        "assumptions_register": register,
        "history_tieout": {"raw_sum_net": raw_sum_net, "reconstructed_sum_net": recon_sum_net,
                           "ok": abs(raw_sum_net - recon_sum_net) <= tol},
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "forecast_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
