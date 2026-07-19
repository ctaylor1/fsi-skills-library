#!/usr/bin/env python3
"""Deterministic covenant test / reconciliation / reporting engine for
covenant-compliance-monitor.

Reads a monitoring-run file (see validate_input.py), evaluates each credit facility against
the covenants parsed from its credit agreement, classifies every financial and negative
covenant test PASS / WARN / BREACH against the versioned thresholds, reconciles the
borrower's compliance certificate against the bank's independently calculated value, checks
reporting-covenant deadlines, tracks headroom and period-over-period trend, deduplicates
against previously-open exceptions, checks spread freshness, and packages a severity-ranked
escalation queue with an audit-ready evidence trail.

IMPORTANT — this is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor (risk tier R3, decision
support). It computes and packages exceptions plus a triage severity for a human credit
reviewer. It NEVER declares an event of default, issues a reservation of rights, grants or
recommends a covenant waiver or amendment, changes a risk rating, notifies the borrower,
closes an exception, or writes any system of record. Thresholds and covenant definitions are
versioned configuration parsed from the credit agreement (the definition of record); they are
never tuned per-borrower and never re-interpreted from ambiguous legal language here.

Usage:
  python calculate_or_transform.py run.json | --selftest
Prints the monitoring pack JSON to stdout.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DISCLAIMER = ("Monitoring alert only; no covenant waiver, amendment, reservation of rights, "
              "default declaration, risk-rating change, borrower notice, or system-of-record "
              "change has been made or recommended. Covenant exceptions require human credit "
              "review and adjudication.")
MEASURED_TYPES = {"financial_test", "negative_covenant"}
SEVERITY_QUEUE = {"High": "credit-risk-escalation",
                  "Medium": "credit-review-queue",
                  "Low": "covenant-monitoring-watchlist"}
EPS = 1e-9


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def expected_severity(cov_type: str, status: str, breach_type: str) -> str:
    """Deterministic severity tie-out (mirrored in validate_output.py).

    A covenant/reporting BREACH is a potential event of default -> High. A certificate
    reconciliation break is a discrepancy to investigate before it is a confirmed
    borrower-reporting finding -> Medium. Any WARN (approaching a level, a late but delivered
    filing) or a freshness flag -> Low. Severity is a triage suggestion for a human, never a
    credit determination.
    """
    if breach_type == "freshness":
        return "Low"
    if status == "WARN":
        return "Low"
    if breach_type == "reconciliation":
        return "Medium"
    return "High"  # financial_test / negative_covenant / reporting BREACH


def _fingerprint(facility_id, covenant_id, breach_type, status) -> str:
    return f"{facility_id}|{covenant_id}|{breach_type}|{status}"


def _classify_max(value, limit, cushion):
    """Cap covenant: BREACH strictly over the limit; WARN within `cushion` below it."""
    if value > limit + EPS:
        return "BREACH"
    if value >= limit - cushion - EPS:
        return "WARN"
    return "PASS"


def _classify_min(value, limit, cushion):
    """Floor covenant: BREACH strictly under the limit; WARN within `cushion` above it."""
    if value < limit - EPS:
        return "BREACH"
    if value <= limit + cushion + EPS:
        return "WARN"
    return "PASS"


def _round(value, is_ratio):
    return round(value, 4) if is_ratio else round(value, 2)


def _cite_spread(fid, period, as_of):
    return f"spread:facility={fid};period={period}@{as_of}"


def _cite_cert(fid, period, as_of):
    return f"cert:facility={fid};period={period}@{as_of}"


def _cite_covenant(covenant_id, config_version):
    return f"covlib:covenant_id={covenant_id}@{config_version}"


def _lookup(line_items, keys):
    """Sum the named line items; return (total, missing_keys)."""
    total = 0.0
    missing = []
    for k in (keys or []):
        if k in (line_items or {}) and _num(line_items.get(k), None) is not None:
            total += _num(line_items.get(k))
        else:
            missing.append(k)
    return total, missing


def _measure_financial(line_items, formula):
    """Compute a financial covenant value from a spread. Returns (value, is_ratio) or
    (None, is_ratio) when a required line item is missing / denominator is zero."""
    num_keys = formula.get("numerator") or []
    less_keys = formula.get("numerator_less") or []
    den_keys = formula.get("denominator") or []
    is_ratio = bool(den_keys)
    num_val, m1 = _lookup(line_items, num_keys)
    less_val, m2 = _lookup(line_items, less_keys)
    den_val, m3 = _lookup(line_items, den_keys)
    if m1 or m2 or m3:
        return None, is_ratio
    numerator_total = num_val - less_val
    if not den_keys:
        return numerator_total, is_ratio  # level covenant
    if abs(den_val) <= EPS:
        return None, is_ratio  # undefined ratio
    return numerator_total / den_val, is_ratio


def _mk_alert(fid, covenant, status, breach_type, measured, limit, evidence, extra=None):
    cov_type = covenant["type"]
    covenant_id = covenant["covenant_id"]
    severity = expected_severity(cov_type, status, breach_type)
    alert = {
        "fingerprint": _fingerprint(fid, covenant_id, breach_type, status),
        "facility_id": fid,
        "covenant_id": covenant_id,
        "covenant_type": cov_type,
        "metric": covenant.get("metric") or covenant.get("deliverable"),
        "status": status,
        "breach_type": breach_type,
        "severity": severity,
        "queue": SEVERITY_QUEUE[severity],
        "is_duplicate": False,
        "stale_input": False,
        "evidence": evidence,
    }
    if breach_type in MEASURED_TYPES:
        alert["measured"] = measured
        alert["threshold"] = limit
        alert["unit"] = covenant.get("unit")
    if extra:
        alert.update(extra)
    return alert


def _financial_alerts(fac, covenant, period, as_of, config_version):
    fid = fac["facility_id"]
    line_items = (fac.get("spread") or {}).get("line_items") or {}
    formula = covenant.get("formula") or {}
    direction = covenant.get("direction", "max")
    threshold = _num(covenant.get("threshold"))
    cushion = _num(covenant.get("cushion"), 0.0)
    unit = covenant.get("unit")
    alerts = []

    measured, is_ratio = _measure_financial(line_items, formula)
    if measured is None:
        return alerts  # not evaluable; input validation surfaces the missing line item
    measured_r = _round(measured, is_ratio)

    if direction == "min":
        status = _classify_min(measured, threshold, cushion)
        headroom = measured - threshold
    else:
        status = _classify_max(measured, threshold, cushion)
        headroom = threshold - measured
    headroom_r = _round(headroom, is_ratio)

    # period-over-period trend (approaching-the-limit direction), when a prior spread exists
    trend = None
    prior = fac.get("prior_spread") or {}
    prior_items = prior.get("line_items")
    if prior_items:
        prior_val, _ = _measure_financial(prior_items, formula)
        if prior_val is not None:
            delta = measured - prior_val
            if direction == "min":
                worsening = delta < -EPS
            else:
                worsening = delta > EPS
            direction_word = "flat" if abs(delta) <= EPS else ("deteriorating" if worsening else "improving")
            trend = {"prior_period": prior.get("test_period"),
                     "prior_value": _round(prior_val, is_ratio),
                     "current_value": measured_r,
                     "delta": _round(delta, is_ratio),
                     "direction": direction_word}

    if status in ("WARN", "BREACH"):
        ev = [{"covenant_id": covenant["covenant_id"], "metric": covenant.get("metric"),
               "measured": measured_r, "threshold": threshold, "headroom": headroom_r,
               "unit": unit, "test_period": period,
               "citation": _cite_spread(fid, period, as_of)},
              {"covenant_id": covenant["covenant_id"],
               "citation": _cite_covenant(covenant["covenant_id"], config_version)}]
        extra = {"headroom": headroom_r, "direction": direction}
        if trend:
            extra["trend"] = trend
        alerts.append(_mk_alert(fid, covenant, status, "financial_test", measured_r,
                                threshold, ev, extra))

    # certificate reconciliation: bank-computed value vs borrower-reported value
    cert = fac.get("compliance_certificate") or {}
    reported_map = cert.get("reported") or {}
    if covenant["covenant_id"] in reported_map:
        reported = _num(reported_map.get(covenant["covenant_id"]), None)
        if reported is not None:
            tol = _num(covenant.get("recon_tolerance"), 0.05 if is_ratio else abs(threshold) * 0.005)
            diff = measured - reported
            if abs(diff) > tol + EPS:
                ev = [{"covenant_id": covenant["covenant_id"], "bank_value": measured_r,
                       "reported_value": _round(reported, is_ratio),
                       "difference": _round(diff, is_ratio), "tolerance": _round(tol, is_ratio),
                       "citation": _cite_cert(fid, period, as_of)},
                      {"covenant_id": covenant["covenant_id"], "measured": measured_r,
                       "citation": _cite_spread(fid, period, as_of)},
                      {"covenant_id": covenant["covenant_id"],
                       "citation": _cite_covenant(covenant["covenant_id"], config_version)}]
                alerts.append(_mk_alert(fid, covenant, "BREACH", "reconciliation", measured_r,
                                        _round(reported, is_ratio), ev,
                                        {"reported_value": _round(reported, is_ratio),
                                         "difference": _round(diff, is_ratio)}))
    return alerts


def _negative_alerts(fac, covenant, period, as_of, config_version):
    fid = fac["facility_id"]
    line_items = (fac.get("spread") or {}).get("line_items") or {}
    key = covenant.get("line_item")
    if key is None or key not in line_items or _num(line_items.get(key), None) is None:
        return []
    value = _num(line_items.get(key))
    threshold = _num(covenant.get("threshold"))
    cushion = _num(covenant.get("cushion"), 0.0)
    direction = covenant.get("direction", "max")
    if direction == "min":
        status = _classify_min(value, threshold, cushion)
        headroom = value - threshold
    else:
        status = _classify_max(value, threshold, cushion)
        headroom = threshold - value
    if status not in ("WARN", "BREACH"):
        return []
    ev = [{"covenant_id": covenant["covenant_id"], "line_item": key,
           "measured": round(value, 2), "threshold": threshold,
           "headroom": round(headroom, 2), "unit": covenant.get("unit"), "test_period": period,
           "citation": _cite_spread(fid, period, as_of)},
          {"covenant_id": covenant["covenant_id"],
           "citation": _cite_covenant(covenant["covenant_id"], config_version)}]
    return [_mk_alert(fid, covenant, status, "negative_covenant", round(value, 2), threshold,
                      ev, {"headroom": round(headroom, 2), "direction": direction})]


def _reporting_alerts(fac, covenant, period, as_of, config_version, run_as_of):
    fid = fac["facility_id"]
    due = _parse_date(covenant.get("due_date"))
    grace = int(_num(covenant.get("grace_days"), 0))
    effective_due = due + timedelta(days=grace) if due else None
    received = _parse_date(covenant.get("received_date"))
    deliverable = covenant.get("deliverable")
    if effective_due is None:
        return []
    if received is None:
        if run_as_of and run_as_of > effective_due:
            overdue_days = (run_as_of - effective_due).days
            ev = [{"covenant_id": covenant["covenant_id"], "deliverable": deliverable,
                   "due_date": covenant.get("due_date"), "received_date": None,
                   "overdue_days": overdue_days, "test_period": period,
                   "citation": _cite_cert(fid, period, as_of)},
                  {"covenant_id": covenant["covenant_id"],
                   "citation": _cite_covenant(covenant["covenant_id"], config_version)}]
            return [_mk_alert(fid, covenant, "BREACH", "reporting", None, None, ev,
                              {"overdue_days": overdue_days, "due_date": covenant.get("due_date")})]
        return []
    if received > effective_due:
        late_days = (received - effective_due).days
        ev = [{"covenant_id": covenant["covenant_id"], "deliverable": deliverable,
               "due_date": covenant.get("due_date"), "received_date": covenant.get("received_date"),
               "late_days": late_days, "test_period": period,
               "citation": _cite_cert(fid, period, as_of)},
              {"covenant_id": covenant["covenant_id"],
               "citation": _cite_covenant(covenant["covenant_id"], config_version)}]
        return [_mk_alert(fid, covenant, "WARN", "reporting", None, None, ev,
                          {"late_days": late_days, "due_date": covenant.get("due_date")})]
    return []


def compute(doc: dict) -> dict:
    as_of = doc["as_of"]
    config_version = doc.get("config_version")
    run_as_of = _parse_date(as_of)
    max_stale = doc.get("max_staleness_days")
    open_fps = {a.get("fingerprint") for a in (doc.get("open_alerts") or [])}
    facilities = doc.get("facilities") or []

    all_alerts = []
    freshness = []
    stale_fids = set()
    covenants_evaluated = 0

    for fac in facilities:
        fid = fac["facility_id"]
        period = fac.get("test_period")
        # freshness of the approved spread the tests are computed from
        spread_as_of = _parse_date(fac.get("spread_as_of"))
        staleness = None
        stale = False
        if run_as_of and spread_as_of:
            staleness = (run_as_of - spread_as_of).days
            if max_stale is not None and staleness > int(max_stale):
                stale = True
        freshness.append({"facility_id": fid, "spread_as_of": fac.get("spread_as_of"),
                          "staleness_days": staleness, "stale": stale})
        if stale:
            stale_fids.add(fid)

        for covenant in (fac.get("covenants") or []):
            covenants_evaluated += 1
            ctype = covenant.get("type")
            if ctype == "financial":
                all_alerts.extend(_financial_alerts(fac, covenant, period, as_of, config_version))
            elif ctype == "negative":
                all_alerts.extend(_negative_alerts(fac, covenant, period, as_of, config_version))
            elif ctype == "reporting":
                all_alerts.extend(_reporting_alerts(fac, covenant, period, as_of,
                                                    config_version, run_as_of))

        # freshness alert — never suppress; flag stale data explicitly
        if stale:
            ev = [{"facility_id": fid, "spread_as_of": fac.get("spread_as_of"),
                   "staleness_days": staleness,
                   "citation": _cite_spread(fid, period, as_of)}]
            cov = {"covenant_id": "DATA-FRESHNESS", "type": "reporting", "metric": "spread_staleness"}
            all_alerts.append(_mk_alert(fid, cov, "WARN", "freshness", None, None, ev,
                                        {"staleness_days": staleness, "max_staleness_days": max_stale}))

    # mark stale_input on every alert from a stale facility (do not drop them)
    for a in all_alerts:
        if a["facility_id"] in stale_fids:
            a["stale_input"] = True

    # deduplication against previously-open alerts
    new_alerts, still_open = [], []
    for a in all_alerts:
        if a["fingerprint"] in open_fps:
            a["is_duplicate"] = True
            still_open.append(a["fingerprint"])
        else:
            new_alerts.append(a["fingerprint"])

    sev_counts = defaultdict(int)
    status_counts = defaultdict(int)
    for a in all_alerts:
        sev_counts[a["severity"]] += 1
        status_counts[a["status"]] += 1
    escalations = [{"severity": sev, "queue": SEVERITY_QUEUE[sev], "count": sev_counts[sev]}
                   for sev in ("High", "Medium", "Low") if sev_counts[sev]]

    return {
        "run_id": doc.get("run_id"),
        "as_of": as_of,
        "config_version": config_version,
        "data_freshness": freshness,
        "alerts": all_alerts,
        "new_alerts": new_alerts,
        "still_open": still_open,
        "summary": {
            "facilities": len(facilities),
            "covenants_evaluated": covenants_evaluated,
            "alerts_total": len(all_alerts),
            "new": len(new_alerts),
            "deduplicated": len(still_open),
            "warn": status_counts.get("WARN", 0),
            "breach": status_counts.get("BREACH", 0),
            "stale_facilities": sorted(stale_fids),
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
