#!/usr/bin/env python3
"""Deterministic market-risk limit engine for market-risk-limit-monitor.

Reads a monitoring-run file (see validate_input.py), joins each versioned limit to the
measured risk number for its book/desk/firm unit, classifies every result PASS / WARN /
BREACH against the limit, attaches cited evidence, distinguishes CURRENT breaches from
pre-deal (PROJECTED) breaches, deduplicates against previously-open breaches, checks
measurement freshness, and packages a severity-ranked escalation queue.

IMPORTANT — this is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor (risk tier R3). It computes
and packages alerts and a triage severity for a human market-risk reviewer. It NEVER trades,
hedges, cuts or rebalances a position, grants/raises/resets a limit or temporary excess,
grants or closes a breach waiver, closes/suppresses an alert, files a breach or regulatory
report, or writes any system of record. Limits are versioned configuration (see
references/domain-rules.md), never tuned per-book and never a judgement of intent. Every
disposition is a human decision (R3: mandatory human adjudication).

Usage:
  python calculate_or_transform.py run.json | --selftest
Prints the monitoring pack JSON to stdout.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DISCLAIMER = ("Monitoring alert only; no trade, hedge, position change, limit change, "
              "waiver, breach closure, or system-of-record change has been made. "
              "Market-risk limit exceptions require human risk-management review and "
              "disposition.")
THRESHOLD_METRICS = {"var", "es", "sensitivity", "stress_loss", "notional", "concentration"}
SEVERITY_QUEUE = {"High": "market-risk-escalation",
                  "Medium": "market-risk-review-queue",
                  "Low": "risk-monitoring-watchlist"}
# Indicative triage SLA per severity bucket (packaging only; a human owns the clock).
SEVERITY_SLA = {"High": "same-day escalation", "Medium": "next-business-day review",
                "Low": "next scheduled run"}
EPS = 1e-9


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _parse_dt(s):
    """Parse a date (YYYY-MM-DD) or ISO datetime (trailing 'Z' allowed)."""
    if s is None:
        return None
    t = str(s).strip().replace("Z", "").replace("z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue
    return None


def expected_severity(metric: str, status: str, breach_type: str) -> str:
    """Deterministic severity tie-out (mirrored in validate_output.py)."""
    if metric == "freshness":
        return "Low"
    if status == "WARN":
        return "Low"
    if breach_type == "projected":       # a pending/pre-deal exposure would newly breach
        return "High"
    if metric in ("var", "es", "stress_loss"):   # headline regulatory market-risk measures
        return "High"
    return "Medium"                      # sensitivity / notional / concentration current breach


def _fingerprint(unit_id, limit_id, bucket, breach_type, status) -> str:
    return f"{unit_id}|{limit_id}|{bucket}|{breach_type}|{status}"


def _measure_bucket(metric, m: dict) -> str:
    if metric in ("var", "es"):
        return f"{metric}:{m.get('horizon')}:{m.get('confidence')}"
    if metric == "sensitivity":
        return f"sensitivity:{m.get('sensitivity')}"
    if metric == "stress_loss":
        return f"stress_loss:{m.get('scenario_id')}"
    if metric == "concentration":
        return f"concentration:{m.get('sub_scope')}"
    return str(metric)


def _limit_bucket(r: dict) -> str:
    metric = r.get("metric")
    if metric in ("var", "es"):
        return f"{metric}:{r.get('horizon')}:{r.get('confidence')}"
    if metric == "sensitivity":
        return f"sensitivity:{r.get('sensitivity')}"
    if metric == "stress_loss":
        return f"stress_loss:{r.get('scenario_id')}"
    if metric == "concentration":
        return f"concentration:{r.get('sub_scope')}"
    return str(metric)


def _classify_max(value, limit, warn_buffer_pct):
    if value > limit + EPS:
        return "BREACH"
    warn_line = limit * (1.0 - warn_buffer_pct / 100.0)
    if value >= warn_line - EPS:
        return "WARN"
    return "PASS"


def _classify_min(value, limit, warn_buffer_pct):
    if value < limit - EPS:
        return "BREACH"
    warn_line = limit * (1.0 + warn_buffer_pct / 100.0)
    if value <= warn_line + EPS:
        return "WARN"
    return "PASS"


def _classify(value, limit, warn_buffer_pct, direction):
    if direction == "min":
        return _classify_min(value, limit, warn_buffer_pct)
    return _classify_max(value, limit, warn_buffer_pct)


def _measure_cite(unit_id, bucket, as_of):
    return f"risk:book={unit_id};metric={bucket}@{as_of}"


def _limit_cite(limit_id, config_version):
    return f"limits:limit_id={limit_id}@{config_version}"


def _mk_alert(unit_id, desk, limit_id, metric, scope, bucket, status, breach_type,
              measured, limit, utilization, evidence):
    severity = expected_severity(metric, status, breach_type)
    alert = {
        "fingerprint": _fingerprint(unit_id, limit_id, bucket, breach_type, status),
        "unit_id": unit_id,
        "desk": desk,
        "limit_id": limit_id,
        "metric": metric,
        "scope": scope,
        "bucket": bucket,
        "status": status,
        "breach_type": breach_type,
        "severity": severity,
        "queue": SEVERITY_QUEUE[severity],
        "is_duplicate": False,
        "stale_input": False,
        "evidence": evidence,
    }
    if metric in THRESHOLD_METRICS:
        alert["measured"] = measured
        alert["limit"] = limit
        alert["utilization_pct"] = utilization
    else:  # freshness carries its own measured/limit (hours) for the reviewer
        alert["measured"] = measured
        alert["limit"] = limit
    return alert


def _find_measure(unit, r):
    """Return the measure on this unit matching limit r, or None."""
    want = _limit_bucket(r)
    for m in unit.get("measures") or []:
        if m.get("metric") != r.get("metric"):
            continue
        if _measure_bucket(m.get("metric"), m) == want:
            return m
    return None


def _evaluate_limit(unit, r, as_of, config_version):
    """Evaluate one limit against one matched unit -> list of alert dicts."""
    uid = unit["unit_id"]
    desk = unit.get("desk")
    limit_id = r["limit_id"]
    metric = r["metric"]
    scope = r.get("scope")
    direction = r.get("direction", "max")
    warn_buffer = _num(r.get("warn_buffer_pct"), 0.0)
    limit_value = _num(r.get("limit_value"))
    bucket = _limit_bucket(r)
    alerts = []
    m = _find_measure(unit, r)
    if m is None or limit_value <= 0:
        return alerts  # not evaluable (surfaced as a warning by validate_input)

    value = _num(m.get("value"))
    status = _classify(value, limit_value, warn_buffer, direction)
    util = round(value / limit_value * 100.0, 2) if limit_value else None
    if status != "PASS":
        ev = [{"unit_id": uid, "metric": bucket, "value": round(value, 2),
               "utilization_pct": util, "unit": m.get("unit"),
               "citation": _measure_cite(uid, bucket, as_of)},
              {"limit_id": limit_id, "limit_value": limit_value,
               "citation": _limit_cite(limit_id, config_version)}]
        alerts.append(_mk_alert(uid, desk, limit_id, metric, scope, bucket, status,
                                "current", round(value, 2), limit_value, util, ev))

    # pre-deal / projected pass: a provided what-if exposure that would NEWLY breach
    proj = m.get("projected_value")
    if proj is not None and direction == "max":
        proj_v = _num(proj)
        cur_status = _classify_max(value, limit_value, warn_buffer)
        proj_status = _classify_max(proj_v, limit_value, warn_buffer)
        if proj_status == "BREACH" and cur_status != "BREACH":
            put = round(proj_v / limit_value * 100.0, 2) if limit_value else None
            ev = [{"unit_id": uid, "metric": bucket, "projected_value": round(proj_v, 2),
                   "current_value": round(value, 2), "projected_utilization_pct": put,
                   "citation": _measure_cite(uid, bucket, as_of)},
                  {"limit_id": limit_id, "limit_value": limit_value,
                   "citation": _limit_cite(limit_id, config_version)}]
            alerts.append(_mk_alert(uid, desk, limit_id, metric, scope, bucket, "BREACH",
                                    "projected", round(proj_v, 2), limit_value, put, ev))
    return alerts


def compute(doc: dict) -> dict:
    as_of = doc["as_of"]
    config_version = doc.get("config_version")
    run_dt = _parse_dt(as_of)
    max_stale = doc.get("max_staleness_hours")
    open_fps = {a.get("fingerprint") for a in (doc.get("open_alerts") or [])}
    limits = doc.get("limits") or []
    books = doc.get("books") or []

    all_alerts = []
    freshness = []
    stale_units = set()

    for unit in books:
        uid = unit["unit_id"]
        # freshness (hours)
        m_dt = _parse_dt(unit.get("measured_as_of"))
        staleness = None
        stale = False
        if run_dt and m_dt:
            staleness = round((run_dt - m_dt).total_seconds() / 3600.0, 2)
            if max_stale is not None and staleness > float(max_stale):
                stale = True
        freshness.append({"unit_id": uid, "desk": unit.get("desk"),
                          "measured_as_of": unit.get("measured_as_of"),
                          "staleness_hours": staleness, "stale": stale})
        if stale:
            stale_units.add(uid)

        # limit evaluation — join each limit to this unit
        for r in limits:
            if r.get("scope") == unit.get("unit_type") and r.get("scope_value") == uid:
                all_alerts.extend(_evaluate_limit(unit, r, as_of, config_version))

        # freshness alert — never suppress; flag stale data explicitly
        if stale:
            ev = [{"unit_id": uid, "measured_as_of": unit.get("measured_as_of"),
                   "staleness_hours": staleness,
                   "citation": f"risk:book={uid};measured_as_of={unit.get('measured_as_of')}@{as_of}"}]
            all_alerts.append(_mk_alert(uid, unit.get("desk"), "DATA-FRESHNESS", "freshness",
                                        "data", "staleness", "WARN", "freshness",
                                        staleness, max_stale, None, ev))

    # mark stale_input on every alert from a stale unit (never drop them)
    for a in all_alerts:
        if a["unit_id"] in stale_units:
            a["stale_input"] = True

    # deduplication against previously-open breaches
    new_alerts, still_open = [], []
    for a in all_alerts:
        if a["fingerprint"] in open_fps:
            a["is_duplicate"] = True
            still_open.append(a["fingerprint"])
        else:
            new_alerts.append(a["fingerprint"])

    # escalation packaging (severity buckets over all alerts)
    sev_counts = defaultdict(int)
    for a in all_alerts:
        sev_counts[a["severity"]] += 1
    escalations = [{"severity": sev, "queue": SEVERITY_QUEUE[sev],
                    "sla": SEVERITY_SLA[sev], "count": sev_counts[sev]}
                   for sev in ("High", "Medium", "Low") if sev_counts[sev]]

    status_counts = defaultdict(int)
    for a in all_alerts:
        status_counts[a["status"]] += 1

    return {
        "run_id": doc.get("run_id"),
        "as_of": as_of,
        "config_version": config_version,
        "data_freshness": freshness,
        "alerts": all_alerts,
        "new_alerts": new_alerts,
        "still_open": still_open,
        "summary": {
            "units": len(books),
            "limits_evaluated": len(limits),
            "alerts_total": len(all_alerts),
            "new": len(new_alerts),
            "deduplicated": len(still_open),
            "warn": status_counts.get("WARN", 0),
            "breach": status_counts.get("BREACH", 0),
            "stale_units": sorted(stale_units),
        },
        "escalations": escalations,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
