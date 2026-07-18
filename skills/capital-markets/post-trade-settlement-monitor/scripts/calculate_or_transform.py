#!/usr/bin/env python3
"""Deterministic settlement-exception alert computation for post-trade-settlement-monitor.

Reads a settlement snapshot (see validate_input.py), applies the configured, documented
threshold rules to each instruction, attaches cited evidence to every alert, deduplicates
against already-open alerts, stamps data freshness, and packages a prioritized human queue.

IMPORTANT: This is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor. It computes and prioritizes
alerts and DRAFTS a suggested escalation route. It NEVER matches, affirms, cancels, settles,
initiates a buy-in, contacts a counterparty/custodian, closes a fail, or writes any book of
record. `actions_taken` is always empty. Severity mapping is fixed and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py snapshot.json | --selftest
Prints the alert-queue JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime, date
from pathlib import Path

DEFAULT_CONFIG = {
    "cutoff_warn_minutes": 60,
    "fail_aging_bands": [1, 3, 5],
    "buyin_window_days": 4,
    "cash_impact_material": 1000000.0,
    "penalty_accrual_material": 5000.0,
    "max_source_staleness_minutes": 30,
}
DISCLAIMER = ("Monitoring alerts only; no settlement action has been taken. "
              "A human must review, decide, and act.")

# Fixed severity per alert type (see references/domain-rules.md). Deterministic tie-out.
ALERT_SEVERITY = {
    "unmatched_near_cutoff": "High",
    "cutoff_breach": "Critical",
    "settlement_fail": "Warning",
    "fail_aging_high": "High",
    "fail_aging_critical": "Critical",
    "buyin_exposure": "Critical",
    "material_cash_impact": "High",
    "penalty_accrual": "Warning",
}
SEV_ORDER = {"Info": 0, "Warning": 1, "High": 2, "Critical": 3}


def _parse_dt(s: str) -> datetime:
    s = str(s).replace(" ", "T")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.strptime(s[:10], "%Y-%m-%d")


def _parse_date(s: str) -> date:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()


def _business_days_late(isd: date, as_of_d: date) -> int:
    """Weekday count strictly after ISD up to and including as_of. Holidays are a
    deployment market-calendar config; this stdlib fallback counts Mon-Fri only."""
    if as_of_d <= isd:
        return 0
    n, cur = 0, isd
    while cur < as_of_d:
        cur = date.fromordinal(cur.toordinal() + 1)
        if cur.weekday() < 5:
            n += 1
    return n


def _cite(t: dict) -> str:
    return f"clearing:{t.get('source_ref','?')}@{t.get('source_as_of', t.get('intended_settlement_date','?'))}"


def _route(alert_types: set) -> str:
    if {"buyin_exposure", "material_cash_impact"} & alert_types:
        return "settlement-fails & funding desk"
    if {"cutoff_breach", "unmatched_near_cutoff"} & alert_types:
        return "matching & affirmation ops"
    if "penalty_accrual" in alert_types:
        return "CSDR penalties analyst"
    return "settlement operations queue"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = _parse_dt(doc["as_of"])
    as_of_d = as_of.date()
    bands = cfg["fail_aging_bands"]
    warn_secs = cfg["cutoff_warn_minutes"] * 60
    stale_secs = cfg["max_source_staleness_minutes"] * 60
    open_keys = sorted({a["dedup_key"] for a in (doc.get("open_alerts") or []) if a.get("dedup_key")})
    open_set = set(open_keys)

    queue, stale_ids = [], []
    new_count = dup_count = 0

    for t in doc["instructions"]:
        iid = t["instruction_id"]
        status = t.get("status")
        isd = _parse_date(t["intended_settlement_date"])
        alerts = []

        def add(atype, reason):
            alerts.append({"type": atype, "severity": ALERT_SEVERITY[atype], "reason": reason,
                           "dedup_key": f"{iid}:{atype}",
                           "evidence": [{"instruction_id": iid, "status": status, "citation": _cite(t)}]})

        # --- cutoff rules (need cutoff_time) ---
        cutoff = t.get("cutoff_time")
        unsettled_pre = status in ("unmatched", "pending")
        if cutoff and unsettled_pre and isd <= as_of_d:
            ct = _parse_dt(cutoff)
            delta = (ct - as_of).total_seconds()
            if delta < 0:
                mins = int(-delta // 60)
                add("cutoff_breach", f"cutoff {cutoff} passed {mins} min ago with instruction still unmatched")
            elif delta <= warn_secs:
                mins = int(delta // 60)
                add("unmatched_near_cutoff",
                    f"instruction unmatched {mins} min before cutoff {cutoff} (warn <= {cfg['cutoff_warn_minutes']} min)")

        # --- fail + aging rules ---
        age = _business_days_late(isd, as_of_d)
        is_fail = status == "failed" or (status != "settled" and age >= bands[0] and status not in ("matched", "affirmed"))
        if is_fail:
            add("settlement_fail",
                f"not settled {age} business day(s) past intended settlement date {isd} (status={status})")
            if len(bands) >= 2 and age >= bands[1]:
                add("fail_aging_high", f"fail aged {age} business day(s) >= band {bands[1]}")
            if len(bands) >= 3 and age >= bands[2]:
                add("fail_aging_critical", f"fail aged {age} business day(s) >= band {bands[2]}")
            if age >= cfg["buyin_window_days"]:
                add("buyin_exposure",
                    f"fail aged {age} business day(s) >= buy-in window {cfg['buyin_window_days']}; buy-in exposure (CSDR SDR)")
            cash = t.get("cash_amount")
            if cash is not None and abs(float(cash)) >= cfg["cash_impact_material"]:
                add("material_cash_impact",
                    f"fail cash impact {abs(float(cash)):,.2f} {t.get('currency','')} >= materiality {cfg['cash_impact_material']:,.2f}".strip())
            pen = t.get("penalty_accrued")
            if pen is not None and float(pen) >= cfg["penalty_accrual_material"]:
                add("penalty_accrual",
                    f"accrued penalty {float(pen):,.2f} >= materiality {cfg['penalty_accrual_material']:,.2f}")

        if not alerts:
            continue

        # --- deduplication against already-open alerts ---
        item_new = False
        for a in alerts:
            if a["dedup_key"] in open_set:
                a["state"] = "duplicate"
            else:
                a["state"] = "new"
                item_new = True
        if item_new:
            new_count += 1
        else:
            dup_count += 1

        # --- freshness / staleness stamp ---
        stale = False
        sa = t.get("source_as_of")
        if sa:
            if (as_of - _parse_dt(sa)).total_seconds() > stale_secs:
                stale = True
                stale_ids.append(iid)

        atypes = {a["type"] for a in alerts}
        severity = max((a["severity"] for a in alerts), key=lambda s: SEV_ORDER[s])
        queue.append({
            "instruction_id": iid,
            "trade_id": t.get("trade_id"),
            "security_id": t.get("security_id"),
            "counterparty": t.get("counterparty"),
            "severity": severity,
            "is_new": item_new,
            "stale": stale,
            "suggested_route": _route(atypes),
            "alerts": alerts,
        })

    queue.sort(key=lambda q: (-SEV_ORDER[q["severity"]], q["instruction_id"]))

    return {
        "run_id": doc.get("run_id"),
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "market": doc.get("market"),
        "monitored_count": len(doc["instructions"]),
        "alert_count": len(queue),
        "new_count": new_count,
        "deduplicated_count": dup_count,
        "queue": queue,
        "deduped_against": open_keys,
        "freshness": {
            "as_of": doc["as_of"],
            "max_source_staleness_minutes": cfg["max_source_staleness_minutes"],
            "stale_instruction_ids": sorted(stale_ids),
            "run_stale": bool(stale_ids),
        },
        "actions_taken": [],
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "settlement_snapshot.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
