#!/usr/bin/env python3
"""Deterministic KRI monitoring engine for key-risk-indicator-monitor.

Reads a KRI monitoring-run file (see validate_input.py), evaluates each Key Risk Indicator
across five lenses — threshold band, adverse trend, seasonal-expectation deviation,
data quality, and freshness — classifies every result PASS / WARN / BREACH against the
VERSIONED appetite/amber/red thresholds, attaches cited evidence and any linked incidents,
deduplicates against previously-open alerts, and packages a severity-ranked escalation queue.

IMPORTANT — this is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor at risk tier R3 (decision
support with mandatory human adjudication). It computes and packages alerts and a triage
severity for a human risk reviewer. It NEVER accepts a risk, grants a breach waiver, changes
a limit/threshold or risk appetite, changes a risk or control rating, opens/closes/suppresses
an alert/incident/case, files a regulatory report, or writes any system of record. Thresholds
are versioned configuration (see references/domain-rules.md), never tuned per-metric and never
a judgement of intent.

Usage:
  python calculate_or_transform.py run.json | --selftest
Prints the monitoring pack JSON to stdout. With --selftest it also runs bundled invariant
checks and prints a final line ending "N error(s)" (exit 0 pass / 1 fail).
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DISCLAIMER = ("Monitoring alert only; no risk acceptance, breach waiver, limit or appetite "
              "change, risk- or control-rating change, incident or case closure, regulatory "
              "filing, or system-of-record change has been made or recommended. KRI exceptions "
              "require human risk review and adjudication.")
MEASURED_TYPES = {"threshold", "seasonal"}
SEVERITY_QUEUE = {"High": "risk-committee-escalation",
                  "Medium": "risk-review-queue",
                  "Low": "kri-monitoring-watchlist"}
DEFAULT_TREND_MIN_MOVES = 3
EPS = 1e-9


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def expected_severity(breach_type: str, status: str, critical: bool) -> str:
    """Deterministic severity tie-out (mirrored in validate_output.py)."""
    if breach_type == "freshness":
        return "Low"
    if breach_type == "data_quality":
        return "Medium" if critical else "Low"
    if status == "WARN":                       # amber threshold, adverse trend
        return "Low"
    if breach_type == "threshold":             # red-band BREACH
        return "High" if critical else "Medium"
    return "Medium"                            # seasonal BREACH


def _fingerprint(kri_id, breach_type, status) -> str:
    return f"{kri_id}|{breach_type}|{status}"


def _obs_cite(kid, period, as_of):
    return f"kri:kri_id={kid};period={period}@{as_of}"


def _cfg_cite(kid, config_version):
    return f"register:kri_id={kid}@{config_version}"


def _classify_threshold(value, amber, red, direction):
    """Return (status, band, threshold_used). Boundary convention: a value exactly on the red
    limit is an at-limit WARN; only a value strictly beyond red is a BREACH."""
    if direction == "lower_is_worse":
        if value < red - EPS:
            return "BREACH", "red", red
        if amber is not None and value <= amber + EPS:
            return "WARN", "amber", amber
        return "PASS", None, None
    # higher_is_worse (default)
    if value > red + EPS:
        return "BREACH", "red", red
    if amber is not None and value >= amber - EPS:
        return "WARN", "amber", amber
    return "PASS", None, None


def _mk_alert(k, breach_type, status, measured, threshold, band, evidence, extra=None):
    kid = k["kri_id"]
    critical = bool(k.get("critical"))
    severity = expected_severity(breach_type, status, critical)
    alert = {
        "fingerprint": _fingerprint(kid, breach_type, status),
        "kri_id": kid,
        "kri_name": k.get("name"),
        "category": k.get("category"),
        "owner": k.get("owner"),
        "unit": k.get("unit"),
        "direction": k.get("direction", "higher_is_worse"),
        "critical": critical,
        "status": status,
        "breach_type": breach_type,
        "severity": severity,
        "queue": SEVERITY_QUEUE[severity],
        "is_duplicate": False,
        "stale_input": False,
        "linked_incidents": list(k.get("linked_incidents") or []),
        "evidence": evidence,
    }
    if breach_type in MEASURED_TYPES:
        alert["measured"] = measured
        alert["threshold"] = threshold
        alert["band"] = band
    elif measured is not None:
        alert["measured"] = measured
    if extra:
        alert.update(extra)
    return alert


def _latest_obs(k):
    obs = k.get("observations") or []
    return obs[-1] if obs else None


def _threshold_lens(k, as_of, config_version, latest):
    amber, red = _num(k.get("amber")), _num(k.get("red"))
    if red is None:
        return []
    value = _num(latest.get("value"))
    if value is None:
        return []
    direction = k.get("direction", "higher_is_worse")
    status, band, thr = _classify_threshold(value, amber, red, direction)
    if status == "PASS":
        return []
    period = latest.get("period")
    ev = [{"period": period, "value": value, "band": band,
           "citation": _obs_cite(k["kri_id"], period, as_of)},
          {"kri_id": k["kri_id"], "amber": amber, "red": red,
           "citation": _cfg_cite(k["kri_id"], config_version)}]
    return [_mk_alert(k, "threshold", status, value, thr, band, ev)]


def _trend_lens(k, as_of, config_version, latest, threshold_status):
    """Adverse-trend early warning: raise a WARN when the KRI has moved in the adverse
    direction for `trend_min_moves` consecutive observations AND it is not already a red
    BREACH (a breach already escalates on its own)."""
    if threshold_status == "BREACH":
        return []
    obs = [o for o in (k.get("observations") or []) if _num(o.get("value")) is not None]
    min_moves = int(_num(k.get("trend_min_moves"), DEFAULT_TREND_MIN_MOVES))
    if len(obs) < min_moves + 1:
        return []
    direction = k.get("direction", "higher_is_worse")
    moves = 0
    for i in range(len(obs) - 1, 0, -1):
        cur, prev = _num(obs[i]["value"]), _num(obs[i - 1]["value"])
        adverse = (cur > prev + EPS) if direction == "higher_is_worse" else (cur < prev - EPS)
        if adverse:
            moves += 1
        else:
            break
    if moves < min_moves:
        return []
    first = obs[-(min_moves + 1)]
    ev = [{"from_period": first.get("period"), "from_value": _num(first.get("value")),
           "to_period": latest.get("period"), "to_value": _num(latest.get("value")),
           "consecutive_adverse_moves": moves,
           "citation": _obs_cite(k["kri_id"], latest.get("period"), as_of)},
          {"kri_id": k["kri_id"], "citation": _cfg_cite(k["kri_id"], config_version)}]
    return [_mk_alert(k, "trend", "WARN", _num(latest.get("value")), None, None, ev,
                      extra={"consecutive_adverse_moves": moves})]


def _seasonal_lens(k, as_of, config_version, latest):
    sb = k.get("seasonal_baseline") or {}
    period = latest.get("period")
    if period not in sb:
        return []
    expected = _num(sb.get(period))
    value = _num(latest.get("value"))
    if expected is None or value is None or abs(expected) < EPS:
        return []
    tol = _num(k.get("seasonal_tolerance_pct"), 0.0)
    direction = k.get("direction", "higher_is_worse")
    if direction == "lower_is_worse":
        bound = expected * (1 - tol / 100.0)
        adverse = value < bound - EPS
    else:
        bound = expected * (1 + tol / 100.0)
        adverse = value > bound + EPS
    if not adverse:
        return []
    deviation_pct = round((value - expected) / expected * 100.0, 2)
    ev = [{"period": period, "value": value, "seasonal_expected": expected,
           "seasonal_bound": round(bound, 4), "deviation_pct": deviation_pct,
           "tolerance_pct": tol, "citation": _obs_cite(k["kri_id"], period, as_of)},
          {"kri_id": k["kri_id"], "citation": _cfg_cite(k["kri_id"], config_version)}]
    return [_mk_alert(k, "seasonal", "BREACH", value, round(bound, 4), "seasonal", ev,
                      extra={"seasonal_expected": expected, "deviation_pct": deviation_pct})]


def _data_quality_lens(k, as_of, latest):
    kid = k["kri_id"]
    obs = k.get("observations") or []
    reason = None
    period = latest.get("period") if latest else None
    if not obs:
        reason = "no observations reported"
    elif latest.get("value") is None:
        reason = f"latest observation ({period}) value is missing"
    else:
        pr = k.get("plausible_range")
        val = _num(latest.get("value"))
        if isinstance(pr, list) and len(pr) == 2 and val is not None:
            lo, hi = _num(pr[0]), _num(pr[1])
            if (lo is not None and val < lo - EPS) or (hi is not None and val > hi + EPS):
                reason = f"latest observation {val} outside plausible range {pr}"
    if reason is None:
        return []
    ev = [{"period": period, "value": (latest.get("value") if latest else None),
           "reason": reason, "citation": _obs_cite(kid, period, as_of)}]
    return [_mk_alert(k, "data_quality", "WARN", None, None, None, ev,
                      extra={"reason": reason})]


def compute(doc: dict) -> dict:
    as_of = doc["as_of"]
    config_version = doc.get("config_version")
    run_as_of = _parse_date(as_of)
    max_stale = doc.get("max_staleness_days")
    open_fps = {a.get("fingerprint") for a in (doc.get("open_alerts") or [])}
    kris = doc.get("kris") or []

    all_alerts = []
    freshness = []
    stale_ids = set()

    for k in kris:
        kid = k["kri_id"]
        # freshness
        o_asof = _parse_date(k.get("observation_as_of"))
        staleness = None
        stale = False
        if run_as_of and o_asof:
            staleness = (run_as_of - o_asof).days
            if max_stale is not None and staleness > int(max_stale):
                stale = True
        freshness.append({"kri_id": kid, "observation_as_of": k.get("observation_as_of"),
                          "staleness_days": staleness, "stale": stale})
        if stale:
            stale_ids.add(kid)

        latest = _latest_obs(k)

        # data quality first — if the KRI is not measurable, only raise the DQ alert
        dq = _data_quality_lens(k, as_of, latest)
        if dq:
            all_alerts.extend(dq)
            if latest is None or latest.get("value") is None:
                # unmeasurable → do not attempt threshold/trend/seasonal
                if stale:
                    all_alerts.extend(_freshness_alert(k, as_of, staleness, max_stale))
                continue

        if latest is not None and latest.get("value") is not None:
            thr_alerts = _threshold_lens(k, as_of, config_version, latest)
            all_alerts.extend(thr_alerts)
            thr_status = thr_alerts[0]["status"] if thr_alerts else "PASS"
            all_alerts.extend(_trend_lens(k, as_of, config_version, latest, thr_status))
            all_alerts.extend(_seasonal_lens(k, as_of, config_version, latest))

        if stale:
            all_alerts.extend(_freshness_alert(k, as_of, staleness, max_stale))

    # mark stale_input on every alert from a stale KRI (never drop them)
    for a in all_alerts:
        if a["kri_id"] in stale_ids:
            a["stale_input"] = True

    # deduplication against previously-open alerts
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
    escalations = [{"severity": sev, "queue": SEVERITY_QUEUE[sev], "count": sev_counts[sev]}
                   for sev in ("High", "Medium", "Low") if sev_counts[sev]]

    status_counts = defaultdict(int)
    for a in all_alerts:
        status_counts[a["status"]] += 1
    linked = sorted({inc for a in all_alerts for inc in (a.get("linked_incidents") or [])})

    return {
        "run_id": doc.get("run_id"),
        "as_of": as_of,
        "config_version": config_version,
        "data_freshness": freshness,
        "alerts": all_alerts,
        "new_alerts": new_alerts,
        "still_open": still_open,
        "summary": {
            "kris": len(kris),
            "kris_evaluated": len(kris),
            "alerts_total": len(all_alerts),
            "new": len(new_alerts),
            "deduplicated": len(still_open),
            "warn": status_counts.get("WARN", 0),
            "breach": status_counts.get("BREACH", 0),
            "stale_kris": sorted(stale_ids),
            "linked_incidents": linked,
        },
        "escalations": escalations,
        "disclaimer": DISCLAIMER,
    }


def _freshness_alert(k, as_of, staleness, max_stale):
    kid = k["kri_id"]
    ev = [{"kri_id": kid, "observation_as_of": k.get("observation_as_of"),
           "staleness_days": staleness, "max_staleness_days": max_stale,
           "citation": f"kri:kri_id={kid};observation_as_of={k.get('observation_as_of')}@{as_of}"}]
    return [_mk_alert(k, "freshness", "WARN", staleness, None, None, ev)]


# ---- bundled self-test -------------------------------------------------------------------

def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    pack = compute(doc)
    print(json.dumps(pack, indent=2))
    errs = []
    s = pack["summary"]
    exp = {"alerts_total": 9, "breach": 3, "warn": 6, "new": 8, "deduplicated": 1}
    for key, want in exp.items():
        if s.get(key) != want:
            errs.append(f"summary.{key} expected {want}, got {s.get(key)}")
    if s.get("stale_kris") != ["KRI-MR-VAR"]:
        errs.append(f"stale_kris expected ['KRI-MR-VAR'], got {s.get('stale_kris')}")
    if sum(int(e["count"]) for e in pack["escalations"]) != len(pack["alerts"]):
        errs.append("escalation counts do not sum to alert count")
    # every alert well-formed and severity ties out
    for a in pack["alerts"]:
        if expected_severity(a["breach_type"], a["status"], a["critical"]) != a["severity"]:
            errs.append(f"severity tie-out failed for {a['fingerprint']}")
        if a["queue"] != SEVERITY_QUEUE[a["severity"]]:
            errs.append(f"queue tie-out failed for {a['fingerprint']}")
    for e in errs:
        print("ERROR", e)
    print(f"compute selftest: {len(errs)} error(s)")
    return 1 if errs else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
